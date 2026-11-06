#!/usr/bin/env python3
"""Scan exactly five immutable images; retain public evidence on every failure."""

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

SCANNER = "aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df"
TARGETS = {"runtime", "builder", "postgres", "redis", "node"}


def require(value):
    if not value:
        raise ValueError("image scan guard")


def command(argv, **kwargs):
    return subprocess.run(argv, capture_output=True, check=False, timeout=360, **kwargs)


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def saved_config(archive):
    with tarfile.open(archive) as saved:
        manifest = json.load(saved.extractfile("manifest.json"))
        require(len(manifest) == 1)
        name = manifest[0]["Config"]
        require(not name.startswith("/") and ".." not in Path(name).parts)
        config_bytes = saved.extractfile(name).read()
        config_id = "sha256:" + hashlib.sha256(config_bytes).hexdigest()
        require(name in {config_id[7:] + ".json", "blobs/sha256/" + config_id[7:]})
        config = json.loads(config_bytes)
        require(config["os"] == "linux" and config["architecture"] == "amd64")
        return config_id


def isolated():
    return [
        "docker",
        "run",
        "--rm",
        "--pull",
        "never",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=512m",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
    ]


def db_metadata(cache):
    metadata = json.loads((cache / "db/metadata.json").read_text())
    require(metadata["Version"] == 2)
    stamps = {
        k: datetime.datetime.fromisoformat(metadata[k])
        for k in ["UpdatedAt", "DownloadedAt", "NextUpdate"]
    }
    require(all(v.tzinfo is not None for v in stamps.values()))
    now = datetime.datetime.now(datetime.UTC)
    require(stamps["NextUpdate"] > now)
    require(stamps["UpdatedAt"] <= now + datetime.timedelta(minutes=10))
    require(stamps["DownloadedAt"] <= now + datetime.timedelta(minutes=10))
    return metadata


def run_scans(output, targets):
    require(set(targets) == TARGETS and len(set(targets.values())) == 5)
    require(
        all(
            re.fullmatch(r"(?:[a-z0-9./:_-]+@)?sha256:[0-9a-f]{64}", ref)
            for ref in targets.values()
        )
    )
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.umask(0o077)
    evidence = {"scanner": {"reference": SCANNER}, "targets": {}, "ok": False}
    version_ok = False
    try:
        inspected = command(["docker", "image", "inspect", SCANNER])
        require(inspected.returncode == 0)
        evidence["scanner"]["inspection"] = json.loads(inspected.stdout)
        version = command(isolated() + [SCANNER, "--version", "--format", "json"])
        (output / "scanner-version.json").write_bytes(version.stdout)
        (output / "scanner-version.log").write_bytes(version.stderr)
        require(version.returncode == 0)
        evidence["scanner"]["version"] = json.loads(version.stdout)
        require(evidence["scanner"]["version"]["Version"] == "0.76.1")
        version_ok = True
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        evidence["scanner"]["error"] = type(error).__name__
    with tempfile.TemporaryDirectory(prefix="birja-image-scan-") as temporary:
        work = Path(temporary)
        cache = work / "cache"
        cache.mkdir(mode=0o700)
        identities = set()
        for name in ["runtime", "builder", "postgres", "redis", "node"]:
            started = time.monotonic()
            record = {"requested_reference": targets[name], "ok": False}
            evidence["targets"][name] = record
            archive = work / (name + ".tar")
            try:
                inspected = command(["docker", "image", "inspect", targets[name]])
                (output / (name + "-inspect.log")).write_bytes(inspected.stderr)
                require(inspected.returncode == 0)
                rows = json.loads(inspected.stdout)
                require(len(rows) == 1)
                image = rows[0]
                require(re.fullmatch(r"sha256:[0-9a-f]{64}", image["Id"]))
                require(image["Id"] not in identities)
                identities.add(image["Id"])
                require(
                    not targets[name].startswith("sha256:")
                    or image["Id"] == targets[name]
                )
                require(image["Os"] == "linux" and image["Architecture"] == "amd64")
                record.update(
                    engine_image_id=image["Id"],
                    repo_digests=image.get("RepoDigests", []),
                    platform="linux/amd64",
                    descriptor=image.get("Descriptor"),
                )
                exported = command(
                    ["docker", "image", "save", "-o", str(archive), targets[name]]
                )
                (output / (name + "-export.log")).write_bytes(exported.stderr)
                require(
                    exported.returncode == 0
                    and archive.is_file()
                    and archive.stat().st_size > 0
                )
                archive.chmod(0o600)
                record["archive_sha256"] = sha(archive)
                record["config_digest"] = saved_config(archive)
                argv = isolated() + [
                    "--mount",
                    f"type=bind,src={archive},dst=/scan/image.tar,readonly",
                    "--mount",
                    f"type=bind,src={cache},dst=/cache",
                    SCANNER,
                    "image",
                    "--cache-dir",
                    "/cache",
                    "--input",
                    "/scan/image.tar",
                    "--scanners",
                    "vuln",
                    "--severity",
                    "HIGH,CRITICAL",
                    "--exit-code",
                    "1",
                    "--timeout",
                    "5m",
                    "--format",
                    "json",
                ]
                scanned = command(argv)
                record["exit_code"] = scanned.returncode
                report = output / (name + ".json")
                report.write_bytes(scanned.stdout)
                (output / (name + ".log")).write_bytes(scanned.stderr)
                record["report_sha256"] = sha(report)
                document = json.loads(scanned.stdout)
                require(document["Metadata"]["ImageID"] == record["config_digest"])
                require(
                    document["SchemaVersion"] == 2
                    and document["Trivy"]["Version"] == "0.76.1"
                )
                results = document["Results"]
                require(isinstance(results, list) and len(results) > 0)
                findings = []
                for result in results:
                    require(
                        isinstance(result, dict) and isinstance(result["Target"], str)
                    )
                    vulnerabilities = result.get("Vulnerabilities")
                    if vulnerabilities is None:
                        vulnerabilities = []
                    require(isinstance(vulnerabilities, list))
                    for finding in vulnerabilities:
                        require(
                            isinstance(finding, dict)
                            and isinstance(finding["Severity"], str)
                        )
                        if finding["Severity"] in {"HIGH", "CRITICAL"}:
                            findings.append(finding)
                record["qualifying_findings"] = len(findings)
                record["database"] = db_metadata(cache)
                record["ok"] = version_ok and scanned.returncode == 0 and not findings
            except (
                ValueError,
                OSError,
                KeyError,
                TypeError,
                tarfile.TarError,
                subprocess.SubprocessError,
            ) as error:
                record["error"] = type(error).__name__
            finally:
                archive.unlink(missing_ok=True)
                record["seconds"] = round(time.monotonic() - started, 3)
                save_json(output / "status.json", evidence)
        metadata_path = cache / "db/metadata.json"
        if metadata_path.is_file():
            (output / "database.json").write_bytes(metadata_path.read_bytes())
    evidence["ok"] = version_ok and all(
        item["ok"] for item in evidence["targets"].values()
    )
    save_json(output / "status.json", evidence)
    return 0 if evidence["ok"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    for name in sorted(TARGETS):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    return run_scans(args.output, {name: getattr(args, name) for name in TARGETS})


if __name__ == "__main__":
    raise SystemExit(main())
