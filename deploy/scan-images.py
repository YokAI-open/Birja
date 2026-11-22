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
ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXCEPTION = {
    "issue": "https://github.com/YokAI-open/Birja/issues/35",
    "advisory": "GHSA-fc5q-39xc-vjpf",
    "cve": "CVE-2026-112366",
    "expires": "2026-12-17T00:00:00+00:00",
    "dockerfile_sha256": "94dbef7eba9db0e2ec652c286cc562eeec294666e29e5ac3e031af8a03d8a148",
    "package_path": "usr/local/lib/node_modules/npm/node_modules/tinyglobby/node_modules/picomatch/package.json",
}


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


def accepted_finding(name, result, finding, *, now=None, dockerfile=None):
    """Accept only the owner's exact unresolved tooling advisory, not a CVE class."""
    if not (
        name == "node"
        and result.get("Target") == "Node.js"
        and result.get("Class") == "lang-pkgs"
        and result.get("Type") == "node-pkg"
        and finding.get("Severity") == "HIGH"
        and finding.get("VulnerabilityID") == IMAGE_EXCEPTION["cve"]
        and finding.get("VendorIDs") == [IMAGE_EXCEPTION["advisory"]]
        and finding.get("PkgName") == "picomatch"
        and finding.get("PkgID") == "picomatch@4.0.4"
        and finding.get("InstalledVersion") == "4.0.4"
        and finding.get("PkgPath") == IMAGE_EXCEPTION["package_path"]
    ):
        return False
    now = datetime.datetime.now(datetime.UTC) if now is None else now
    source = (ROOT / "frontend/Dockerfile").read_bytes() if dockerfile is None else dockerfile
    return (
        isinstance(now, datetime.datetime)
        and now.tzinfo is not None
        and now < datetime.datetime.fromisoformat(IMAGE_EXCEPTION["expires"])
        and hashlib.sha256(source).hexdigest() == IMAGE_EXCEPTION["dockerfile_sha256"]
    )


def classify_findings(name, results, *, now=None, dockerfile=None):
    """Retain all HIGH/CRITICAL rows; identify accepted risk separately."""
    require(isinstance(results, list) and len(results) > 0)
    findings, accepted = [], []
    for result in results:
        require(isinstance(result, dict) and isinstance(result["Target"], str))
        vulnerabilities = result.get("Vulnerabilities")
        if vulnerabilities is None:
            vulnerabilities = []
        require(isinstance(vulnerabilities, list))
        for finding in vulnerabilities:
            require(isinstance(finding, dict) and finding.get("Severity") in {
                "UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"
            })
            if finding["Severity"] in {"HIGH", "CRITICAL"}:
                findings.append(finding)
                if accepted_finding(name, result, finding, now=now, dockerfile=dockerfile):
                    accepted.append(finding)
    return findings, accepted


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
        "--user",
        f"{os.geteuid()}:{os.getegid()}",
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
    require(set(targets) == TARGETS)
    resolved = [ref for ref in targets.values() if ref]
    require(len(set(resolved)) == len(resolved))
    require(
        all(
            (ref == "" and name in {"runtime", "builder", "node"})
            or re.fullmatch(r"(?:[a-z0-9./:_-]+@)?sha256:[0-9a-f]{64}", ref)
            for name, ref in targets.items()
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
                if targets[name] == "":
                    record["error"] = "identity-resolution-failed"
                    resolution_log = output / (name + "-resolve.log")
                    if resolution_log.is_file():
                        record["identity_resolution_log_sha256"] = sha(resolution_log)
                    continue
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
                findings, accepted = classify_findings(name, document["Results"])
                record["qualifying_findings"] = len(findings)
                record["accepted_findings"] = len(accepted)
                record["blocking_findings"] = len(findings) - len(accepted)
                record["risk_status"] = "accepted-risk" if accepted else "no-exception-used"
                if accepted:
                    record["accepted_risk"] = {
                        **IMAGE_EXCEPTION,
                        "findings": accepted,
                    }
                # Trivy's findings exit is accepted only with complete valid
                # evidence; operational errors and inconsistent exits still fail.
                require(scanned.returncode == (1 if findings else 0))
                record["database"] = db_metadata(cache)
                record["ok"] = version_ok and record["blocking_findings"] == 0
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
