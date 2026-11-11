#!/usr/bin/env python3
"""Private, stdlib-only isolated recovery tooling."""

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
COMPOSE_SHA = "6e3a5c1b02d07c785cc69327c0656424af307da7719ed51781ab0d6c5fe3bc9c"
BOOT = "birja_ops_bootstrap"
CLONE = "birja_restore_test"
RESTIC_SHA = "20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639"
# Config identity is distinct from registry and engine identities. Docker's
# classic store exposes the config ID; containerd exposes the manifest ID.
IMAGE_ID = "sha256:91c89cf7f1f18cc4d96fcb5b9e2438108569c1dfcd5aa7286f9cad7d75742ed4"
INDEX_DIGEST = "sha256:f131db66371391e404c80cef7dd40f31b1b54eb264a6cb032925d9a3859f93f4"
PLATFORM_DIGEST = (
    "sha256:4401cf2919e749cd77b634a72e4a677c1a1afc12baddb21faf28df326162472e"
)
REGISTRY_REF = "cgr.dev/chainguard/postgres@" + INDEX_DIGEST
RECOVERY_IMAGE = "birja-recovery-postgres:verified-" + IMAGE_ID[7:]
IMAGE_PROVENANCE = ["images/registry-index.json", "images/platform-manifest.json"]
CORE = [
    "deploy/backup.sh",
    "deploy/backup-status.sh",
    "deploy/backup-snapshot.py",
    "deploy/backup-quota.py",
    "deploy/backup-manifest.sql",
    "deploy/restore-check.sh",
    "deploy/verify-restore.py",
    "deploy/recovery-bundle.sh",
    "docker-compose.ops-test.yml",
]
UNITS = ["deploy/systemd/birja-backup.service", "deploy/systemd/birja-backup.timer"]
PROVENANCE = {
    "SHA256SUMS": "fb520966ee01d2a3d4219c66762c66efa56300833b6f639f36082b7462f91cb8",
    "SHA256SUMS.asc": "649f3a48d322c3d7a457ef58e2dc4c5094b1f823192cdbac3f092ea23e194d9a",
    "gpg-key-alex.asc": "e4f09134173fdd60ece4454d30e38459d172f3ea9a97b32a37324b4f0515a289",
}


def require(value):
    if not value:
        raise ValueError("recovery guard")


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def private(path, directory=False):
    p = Path(path)
    require(p.is_absolute() and p == p.resolve())
    for component in [p, *p.parents]:
        require(not component.is_symlink())
    s = p.stat()
    require(s.st_uid == os.geteuid() and s.st_mode & 0o077 == 0)
    require(stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
    return p


def synthetic_path(path, exists=True):
    p = Path(path)
    require(p.is_absolute() and p == p.resolve())
    require(
        len(p.parts) >= 4
        and p.parts[1] == "tmp"
        and p.parts[2].startswith("birja-backup-test-")
    )
    private(Path(*p.parts[:3]), True)
    for component in [p, *list(p.parents)[:-1]]:
        require(not component.is_symlink())
        if component.exists() and component != Path("/tmp"):
            st = component.stat()
            require(st.st_uid == os.geteuid() and st.st_mode & 0o022 == 0)
    return private(p) if exists else p


def runtime():
    require(
        platform.system() == "Linux"
        and platform.machine() == "x86_64"
        and sys.version_info >= (3, 11)
    )
    commands = {
        "bash": ["bash", "--version"],
        "python3": ["python3", "--version"],
        "docker": ["docker", "--version"],
        "compose": ["docker", "compose", "version"],
        "tar": ["tar", "--version"],
        "flock": ["flock", "--version"],
        "realpath": ["realpath", "--version"],
        "sha256sum": ["sha256sum", "--version"],
        "install": ["install", "--version"],
        "systemd": ["systemctl", "--version"],
    }
    versions = {k: call(v).decode().splitlines()[0] for k, v in commands.items()}
    require(
        "GNU bash, version 5." in versions["bash"]
        and re.search(r"Compose version v[25]\.", versions["compose"])
    )
    require(Path("/etc/ssl/certs/ca-certificates.crt").is_file())
    return {
        "versions": versions,
        "platform": "linux/amd64",
        "ca_store": "/etc/ssl/certs/ca-certificates.crt",
        "backend": "S3 HTTPS; no jq/uv/app dependency",
    }


def tar_members(tar):
    members = tar.getmembers()
    names = [m.name for m in members]
    require(len(names) == len(set(names)))
    for m in members:
        require(m.isfile() and 0 <= m.size <= 1_000_000_000)
        require(
            m.name
            and not m.name.startswith("/")
            and all(x not in {"", ".", ".."} for x in m.name.split("/"))
        )
        require(m.mode & 0o022 == 0 and m.uid == 0 and m.gid == 0)
    return set(names)


def sha_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def verify_image_provenance(index_bytes, manifest_bytes, config_bytes):
    require(sha_bytes(index_bytes) == INDEX_DIGEST)
    require(sha_bytes(manifest_bytes) == PLATFORM_DIGEST)
    require(sha_bytes(config_bytes) == IMAGE_ID)
    index, manifest, config = map(
        json.loads, [index_bytes, manifest_bytes, config_bytes]
    )
    selected = [
        m
        for m in index["manifests"]
        if m.get("platform", {}).get("os") == "linux"
        and m.get("platform", {}).get("architecture") == "amd64"
    ]
    require(len(selected) == 1)
    require(
        selected[0]["digest"] == PLATFORM_DIGEST
        and selected[0]["size"] == len(manifest_bytes)
    )
    require(
        manifest["config"]["digest"] == IMAGE_ID
        and manifest["config"]["size"] == len(config_bytes)
    )
    require(config["os"] == "linux" and config["architecture"] == "amd64")


def verified_blob(image, descriptor):
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", descriptor["digest"]))
    name = "blobs/sha256/" + descriptor["digest"][7:]
    member = image.getmember(name)
    require(member.isfile() and member.size == descriptor["size"])
    require(
        "sha256:" + hashlib.file_digest(image.extractfile(member), "sha256").hexdigest()
        == descriptor["digest"]
    )
    return name


def verify_saved_roots(image, saved_index, index_bytes):
    # Docker29 may retain the selected platform's attestation sibling. Accept
    # only the optional sibling authenticated by our exact pinned registry
    # index, then authenticate every manifest/config/payload byte it references.
    source = json.loads(index_bytes)["manifests"]
    attestations = [
        d
        for d in source
        if d.get("annotations", {}).get("vnd.docker.reference.type")
        == "attestation-manifest"
        and d.get("annotations", {}).get("vnd.docker.reference.digest")
        == PLATFORM_DIGEST
        and d.get("platform") == {"os": "unknown", "architecture": "unknown"}
    ]
    require(len(attestations) <= 1)
    trusted = {d["digest"]: d for d in source if d["digest"] == PLATFORM_DIGEST}
    trusted.update({d["digest"]: d for d in attestations})
    roots = saved_index["manifests"]
    digests = [d["digest"] for d in roots]
    require(PLATFORM_DIGEST in digests and len(digests) == len(set(digests)))
    require(set(digests) <= set(trusted))
    extra_blobs = set()
    for descriptor in roots:
        approved = trusted[descriptor["digest"]]
        require(
            descriptor["size"] == approved["size"]
            and descriptor.get("mediaType") == approved.get("mediaType")
        )
        require(
            not descriptor.get("platform")
            or descriptor["platform"] == approved["platform"]
        )
        if descriptor["digest"] == PLATFORM_DIGEST:
            continue
        require(
            descriptor.get("annotations", {}).get("io.containerd.manifest.subject")
            == PLATFORM_DIGEST
        )
        name = verified_blob(image, approved)
        extra_blobs.add(name)
        attestation = json.load(image.extractfile(name))
        extra_blobs.add(verified_blob(image, attestation["config"]))
        for layer in attestation["layers"]:
            require(layer["mediaType"] == "application/vnd.in-toto+json")
            extra_blobs.add(verified_blob(image, layer))
    return extra_blobs


def verify_saved_image(fileobj, index_bytes, manifest_bytes):
    # Inspect the Docker-save manifest and actual config bytes without loading.
    # Both classic .json paths and OCI blob paths are supported explicitly.
    with tarfile.open(fileobj=fileobj, mode="r:") as image:
        names = image.getnames()
        require(len(names) == len(set(names)))
        for member in image:
            require(member.isfile() or member.isdir())
            require(
                not member.name.startswith("/") and ".." not in Path(member.name).parts
            )
        manifest = json.load(image.extractfile("manifest.json"))
        require(len(manifest) == 1)
        require(not manifest[0].get("RepoTags"))
        config_name = manifest[0]["Config"]
        require(config_name in {IMAGE_ID[7:] + ".json", "blobs/sha256/" + IMAGE_ID[7:]})
        config_bytes = image.extractfile(config_name).read()
        verify_image_provenance(index_bytes, manifest_bytes, config_bytes)
        # OCI imports use this manifest as their engine identity. Authenticate
        # its bytes and layers too, rather than trusting a mutable local tag.
        blob = "blobs/sha256/" + PLATFORM_DIGEST[7:]
        if blob in names:
            require(image.extractfile(blob).read() == manifest_bytes)
            doc = json.loads(manifest_bytes)
            require(
                manifest[0]["Layers"]
                == ["blobs/sha256/" + layer["digest"][7:] for layer in doc["layers"]]
            )
            saved_index = json.load(image.extractfile("index.json"))
            allowed_blobs = {blob, config_name, *manifest[0]["Layers"]}
            allowed_blobs.update(verify_saved_roots(image, saved_index, index_bytes))
            require(
                {name for name in names if name.startswith("blobs/sha256/")}
                == allowed_blobs
            )
            for layer in doc["layers"]:
                name = "blobs/sha256/" + layer["digest"][7:]
                member = image.getmember(name)
                require(member.size == layer["size"])
                require(
                    "sha256:"
                    + hashlib.file_digest(
                        image.extractfile(member), "sha256"
                    ).hexdigest()
                    == layer["digest"]
                )
        else:
            config = json.loads(config_bytes)
            require(
                {m.name for m in image.getmembers() if m.isfile()}
                == {"manifest.json", config_name, *manifest[0]["Layers"]}
            )
            require(len(manifest[0]["Layers"]) == len(config["rootfs"]["diff_ids"]))
            for name, expected in zip(
                manifest[0]["Layers"], config["rootfs"]["diff_ids"], strict=True
            ):
                require(
                    "sha256:"
                    + hashlib.file_digest(image.extractfile(name), "sha256").hexdigest()
                    == expected
                )


def image_inspect(ref):
    rows = json.loads(
        call(["docker", "image", "inspect", ref, "--platform", "linux/amd64"])
    )
    require(len(rows) == 1)
    row = rows[0]
    # A registry pull can retain the multi-platform index as engine ID.
    # Cold import binds only the authenticated platform/config identities.
    identities = {IMAGE_ID, PLATFORM_DIGEST}
    if ref == REGISTRY_REF:
        identities.add(INDEX_DIGEST)
    require(row["Id"] in identities)
    require(row["Os"] == "linux" and row["Architecture"] == "amd64")
    return row["Id"]


def bind_recovery_image():
    # Only identities authenticated from the archive graph may be selected.
    # No registry reference, RepoDigest, floating tag or pull is consulted.
    for identity in [IMAGE_ID, PLATFORM_DIGEST]:
        try:
            engine_id = image_inspect(identity)
        except ValueError:
            continue
        require(engine_id == identity)
        call(["docker", "image", "tag", engine_id, RECOVERY_IMAGE])
        require(loaded_recovery_image() == engine_id)
        return engine_id
    raise ValueError("verified imported recovery image missing")


def loaded_recovery_image():
    return image_inspect(RECOVERY_IMAGE)


def registry_manifests():
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError("registry redirect rejected")

    opener = urllib.request.build_opener(NoRedirect)

    def fetch(url, headers=None):
        require(url.startswith("https://cgr.dev/"))
        request = urllib.request.Request(url, headers=headers or {})
        with opener.open(request, timeout=30) as response:
            require(response.geturl() == url and response.status == 200)
            data = response.read(2_000_001)
        require(len(data) <= 2_000_000)
        return data

    token = json.loads(
        fetch(
            "https://cgr.dev/token?service=cgr.dev&scope=repository%3Achainguard%2Fpostgres%3Apull"
        )
    )["token"]
    require(isinstance(token, str) and 0 < len(token) <= 100_000 and "\n" not in token and "\r" not in token)
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.manifest.v1+json",
    }
    base = "https://cgr.dev/v2/chainguard/postgres/manifests/"
    index, manifest = (
        fetch(base + d, headers) for d in [INDEX_DIGEST, PLATFORM_DIGEST]
    )
    require(sha_bytes(index) == INDEX_DIGEST and sha_bytes(manifest) == PLATFORM_DIGEST)
    return index, manifest


def bundle_verify(archive, sha, required_profile=None):
    p = (
        synthetic_path(archive)
        if str(archive).startswith("/tmp/")
        else private(archive)
    )
    require(re.fullmatch(r"[0-9a-f]{64}", sha) and digest(p) == sha)
    with tarfile.open(p, "r:") as t:
        names = tar_members(t)
        require({"INVENTORY.json", "SHA256SUMS"} <= names)
        inventory = json.load(t.extractfile("INVENTORY.json"))
        allowed = set(
            CORE
            + [
                "tools/restic",
                "images/postgres.tar",
                "provenance/verified.json",
                "INVENTORY.json",
                "SHA256SUMS",
            ]
            + IMAGE_PROVENANCE
            + ["provenance/" + n for n in PROVENANCE]
        )
        require(inventory["units"] == UNITS)
        allowed.update(inventory["units"])
        require(
            names == allowed
            and inventory["files"] == sorted(allowed - {"SHA256SUMS", "INVENTORY.json"})
        )
        require(
            inventory["image_id"] == IMAGE_ID
            and inventory["registry_index_digest"] == INDEX_DIGEST
            and inventory["platform_manifest_digest"] == PLATFORM_DIGEST
            and inventory["registry_reference"] == REGISTRY_REF
            and inventory["restic_sha256"] == RESTIC_SHA
        )
        sums = t.extractfile("SHA256SUMS").read().decode().splitlines()
        expected = {}
        for line in sums:
            h, name = line.split("  ")
            require(re.fullmatch(r"[0-9a-f]{64}", h) and name not in expected)
            expected[name] = h
        require(set(expected) == names - {"SHA256SUMS"})
        for name, h in expected.items():
            require(hashlib.file_digest(t.extractfile(name), "sha256").hexdigest() == h)
        verify_contract_inventory(inventory, expected)
        require(expected["tools/restic"] == RESTIC_SHA)
        require(expected["docker-compose.ops-test.yml"] == COMPOSE_SHA)
        require(all(expected["provenance/" + n] == h for n, h in PROVENANCE.items()))
        proof = json.load(t.extractfile("provenance/verified.json"))
        require(
            proof
            == {
                "fingerprint": "CF8F18F2844575973F79D4E191A6868BD3F7A907",
                "binary_sha256": RESTIC_SHA,
                "compressed_sha256": "f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c",
                "signature": "GOODSIG VALIDSIG; verified 2026-11-02; official restic 0.19.1 linux amd64",
            }
        )
        verify_saved_image(
            t.extractfile("images/postgres.tar"),
            t.extractfile(IMAGE_PROVENANCE[0]).read(),
            t.extractfile(IMAGE_PROVENANCE[1]).read(),
        )
        if required_profile is not None:
            require(
                required_profile == "deploy-recovery-v2"
                and inventory.get("recovery_profile") == required_profile
            )
    runtime()
    return inventory


CONTRACT_PAYLOAD = [
    "deploy/backup-manifest.sql", "deploy/backup-snapshot.py", "deploy/verify-restore.py"
]


def verify_contract_inventory(inventory, expected):
    """Old immutable artifacts remain readable; successor metadata is exact."""
    if "schema_contract" in inventory:
        require(inventory["schema_contract"] == {
            "revisions": list(recovery_contract().SUPPORTED_REVISIONS),
            "payload_sha256": {name: expected[name] for name in CONTRACT_PAYLOAD},
        })


def bundle_package(output, units=False):
    output = synthetic_path(output, False)
    require(not output.exists())
    versions = runtime()
    tools = Path("/tmp/birja-test-tools/restic-0.19.1")
    require(digest(tools / "restic") == RESTIC_SHA)
    require(all(digest(tools / n) == h for n, h in PROVENANCE.items()))
    image_inspect(REGISTRY_REF)
    index_bytes, manifest_bytes = registry_manifests()
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        stage = Path(tmp)
        files = CORE + UNITS
        for name in files:
            src = HERE.parent / name
            require(src.is_file() and not src.is_symlink())
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copyfile(src, dest)
        for directory in ["tools", "images", "provenance"]:
            (stage / directory).mkdir(mode=0o700)
        shutil.copyfile(tools / "restic", stage / "tools/restic")
        for n in PROVENANCE:
            shutil.copyfile(tools / n, stage / "provenance" / n)
        (stage / "provenance/verified.json").write_text(
            json.dumps(
                {
                    "fingerprint": "CF8F18F2844575973F79D4E191A6868BD3F7A907",
                    "binary_sha256": RESTIC_SHA,
                    "compressed_sha256": "f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c",
                    "signature": "GOODSIG VALIDSIG; verified 2026-11-02; official restic 0.19.1 linux amd64",
                },
                sort_keys=True,
            )
        )
        with (stage / "images/postgres.tar").open("wb") as f:
            run = subprocess.run(
                ["docker", "image", "save", "--platform", "linux/amd64", REGISTRY_REF],
                check=False,
                stdout=f,
                stderr=subprocess.DEVNULL,
                env=ENV,
                timeout=120,
            )
            require(run.returncode == 0)
        for name, data in zip(
            IMAGE_PROVENANCE, [index_bytes, manifest_bytes], strict=True
        ):
            (stage / name).write_bytes(data)
        with (stage / "images/postgres.tar").open("rb") as saved:
            verify_saved_image(saved, index_bytes, manifest_bytes)
        files = sorted(
            p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()
        )
        inventory = {
            "format": 1,
            "recovery_profile": "deploy-recovery-v2",
            "files": files,
            "units": UNITS,
            "image_id": IMAGE_ID,
            "registry_reference": REGISTRY_REF,
            "registry_index_digest": INDEX_DIGEST,
            "platform_manifest_digest": PLATFORM_DIGEST,
            "restic_sha256": RESTIC_SHA,
            "runtime": versions,
            "schema_contract": {
                "revisions": list(recovery_contract().SUPPORTED_REVISIONS),
                "payload_sha256": {name: digest(stage / name) for name in CONTRACT_PAYLOAD},
            },
        }
        (stage / "INVENTORY.json").write_text(json.dumps(inventory, sort_keys=True))
        files.append("INVENTORY.json")
        (stage / "SHA256SUMS").write_text(
            "".join(digest(stage / n) + "  " + n + "\n" for n in sorted(files))
        )
        files.append("SHA256SUMS")
        with tarfile.open(output, "w", format=tarfile.USTAR_FORMAT) as t:
            for name in sorted(files):
                p = stage / name
                info = tarfile.TarInfo(name)
                info.size = p.stat().st_size
                info.mode = (
                    0o700 if name.endswith(".sh") or name == "tools/restic" else 0o600
                )
                with p.open("rb") as f:
                    t.addfile(info, f)
    output.chmod(0o600)
    sha = digest(output)
    record = output.with_suffix(output.suffix + ".sha256")
    require(not record.exists())
    record.write_text(sha + "\n")
    record.chmod(0o600)
    print("archive_sha256=" + sha)


def bundle_install(archive, sha, synthetic_root=None, required_profile=None):
    if synthetic_root:
        root = synthetic_path(synthetic_root, False)
        require(root.name == "host")
    else:
        require(os.geteuid() == 0)
        root = Path("/")
    bundle_verify(archive, sha, required_profile)
    base = root / "var/lib/birja/recovery"
    releases = base / "releases"
    if base.exists():
        private(base, True)
    releases.mkdir(parents=True, exist_ok=True, mode=0o700)
    release = releases / sha
    require(not release.exists())
    with tempfile.TemporaryDirectory(prefix=".install-", dir=releases) as tmp:
        stage = Path(tmp)
        with tarfile.open(archive, "r:") as t:
            for member in t:
                dest = stage / member.name
                dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with dest.open("xb") as out, t.extractfile(member) as source:
                    shutil.copyfileobj(source, out)
                dest.chmod(member.mode)
        # Verification precedes image load and every executable invocation.
        with (stage / "images/postgres.tar").open("rb") as f:
            result = subprocess.run(
                ["docker", "image", "load"],
                check=False,
                stdin=f,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=ENV,
                timeout=120,
            )
            require(result.returncode == 0)
        engine_id = bind_recovery_image()
        print(
            "recovery_image="
            + RECOVERY_IMAGE
            + " engine_image_id="
            + engine_id
            + " config_digest="
            + IMAGE_ID
            + " platform=linux/amd64 pull_fallback=false"
        )
        os.rename(stage, release)
        # TemporaryDirectory tolerates its renamed staging directory.
    bindir = root / "usr/local/sbin"
    bindir.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, script in [
        ("birja-backup", "backup.sh"),
        ("birja-backup-status", "backup-status.sh"),
        ("birja-restore-check", "restore-check.sh"),
    ]:
        p = bindir / name
        content = (
            '#!/bin/bash\nset -Eeuo pipefail\numask 077\nexec /bin/bash "'
            + str(base / "current/deploy" / script)
            + '" "$@"\n'
        )
        if name == "birja-backup":
            content = (
                '#!/bin/bash\nset -Eeuo pipefail\numask 077\nexec /usr/bin/python3 "'
                + str(base / "current/deploy/backup-quota.py")
                + '" "$@"\n'
            )
        temp = bindir / ("." + name + ".tmp")
        require(not temp.exists() and not temp.is_symlink())
        temp.write_text(content)
        temp.chmod(0o700)
        os.replace(temp, p)
    link = base / ".current.tmp"
    require(not link.exists() and not link.is_symlink())
    link.symlink_to(release)
    os.replace(link, base / "current")
    print("installed=true archive_sha256=" + sha)


def bundle(args):
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["package", "verify", "install"])
    p.add_argument("--archive")
    p.add_argument("--sha")
    p.add_argument("--output")
    p.add_argument("--synthetic-root")
    p.add_argument("--include-units", action="store_true")
    p.add_argument("--require-profile", choices=["deploy-recovery-v2"])
    a = p.parse_args(args)
    if a.mode == "package":
        require(a.output and not a.archive and not a.sha and not a.synthetic_root)
        require(not a.require_profile)
        bundle_package(a.output, a.include_units)
    else:
        require(a.archive and a.sha and not a.output and not a.include_units)
        if a.mode == "verify":
            require(not a.synthetic_root)
            bundle_verify(a.archive, a.sha, a.require_profile)
            print("bundle_verified=true")
        else:
            bundle_install(a.archive, a.sha, a.synthetic_root, a.require_profile)


def backup_module():
    spec = importlib.util.spec_from_file_location(
        "backup_private", HERE / "backup-snapshot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compose(project="birja-ops-test"):
    require(project in {"birja-ops-test", "birja-restore-check"})
    path = HERE.parent / "docker-compose.ops-test.yml"
    require(digest(path) == COMPOSE_SHA)
    return [
        "/usr/bin/docker",
        "compose",
        "--env-file",
        "/dev/null",
        "-p",
        project,
        "-f",
        str(path),
    ]


ENV = {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8"}


def call(argv, data=None, timeout=120):
    r = subprocess.run(
        argv, check=False, input=data, capture_output=True, env=ENV, timeout=timeout
    )
    require(r.returncode == 0)
    return r.stdout


def sql(dc, query, db=CLONE):
    require(db in {CLONE, "birja_source_test", "birja_ops_test"})
    return call(
        dc
        + [
            "exec",
            "-T",
            "postgres",
            "psql",
            "-XqAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "birja_migrator" if db == CLONE else BOOT,
            "-d",
            db,
        ],
        query.encode(),
    )


def recovery_config(dc):
    config = json.loads(call(dc + ["config", "--format", "json"]))
    require(set(config["services"]) == {"postgres"} and not config.get("volumes"))
    s = config["services"]["postgres"]
    require(not s.get("ports") and not s.get("volumes") and not s.get("privileged"))
    require(s["image"] == RECOVERY_IMAGE and s["pull_policy"] == "never")
    require(
        len(config["networks"]) == 1
        and all(n.get("internal") is True for n in config["networks"].values())
    )
    return s


def start_recovery(dc):
    recovery_config(dc)
    loaded_recovery_image()
    call(dc + ["up", "-d", "--wait", "--pull", "never"])


def check_running(dc):
    s = recovery_config(dc)
    engine_id = loaded_recovery_image()
    ids = call(dc + ["ps", "-q", "postgres"]).decode().split()
    require(len(ids) == 1)
    inspected = json.loads(call(["/usr/bin/docker", "inspect", ids[0]]))[0]
    require(inspected["Image"] == engine_id)
    require(inspected["Platform"] == "linux")
    require(image_inspect(inspected["Image"]) == engine_id)
    print(
        "recovery_running_image_id="
        + engine_id
        + " config_digest="
        + IMAGE_ID
        + " resolved_image="
        + s["image"]
        + " platform=linux/amd64 pull_policy=never"
    )
    require(not inspected["HostConfig"]["Privileged"])
    require(
        not inspected["HostConfig"].get("Binds")
        and not inspected["HostConfig"].get("PortBindings")
    )
    mounts = inspected["Mounts"]
    require(
        not mounts
        and inspected["HostConfig"]["Tmpfs"]
        == {"/var/lib/postgresql": "size=268435456,uid=70,gid=70,mode=0750"}
    )
    networks = inspected["NetworkSettings"]["Networks"]
    require(len(networks) == 1)
    network = json.loads(
        call(["/usr/bin/docker", "network", "inspect", next(iter(networks))])
    )[0]
    require(network["Internal"] is True)


def recovery_contract():
    spec = importlib.util.spec_from_file_location("recovery_contract", HERE / "backup-snapshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical(dc, db=CLONE):
    contract = recovery_contract()
    revision = sql(dc, "SELECT version_num FROM alembic_version ORDER BY version_num;", db).decode().strip()
    return json.loads(
        sql(
            dc,
            "SET TIME ZONE 'UTC';\n" + contract.schema_guard_sql(revision) + contract.manifest_sql(revision),
            db,
        )
    )


def verify(dc, manifest):
    contract = recovery_contract()
    contract.validate_manifest(manifest)
    actual = canonical(dc)
    contract.validate_manifest(actual)
    require(
        all(
            actual[k] == manifest[k]
            for k in ["tables", "financial", "revision", "schema"]
        )
    )
    require(
        all(
            actual["financial"][k] == 0
            for k in ["negative_cash", "fractional_cents", "negative_holdings"]
        )
    )
    # Compare complete constraint/index definitions against the reviewed schema
    # captured independently by fixture tests; additionally require core invariants.
    constraints = sql(
        dc,
        "SELECT count(*) FROM pg_constraint WHERE connamespace='public'::regnamespace AND contype='f' AND convalidated;",
    ).strip()
    stock = manifest["revision"] in ("0009", "0010", "0011")
    require(constraints == (b"40" if manifest["revision"] == "0011" else b"10" if stock else b"8"))
    if manifest["revision"] == "0011":
        require(actual["identity_state"] == manifest["identity_state"])
    require(
        sql(
            dc,
            "SELECT count(*) FROM pg_index WHERE indrelid IN (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace) AND (NOT indisvalid OR NOT indisready);",
        ).strip()
        == b"0"
    )
    expected = (
        "pk_trades" if manifest["revision"] == "0007" else "ix_trades_user_created_id"
    )
    require(sql(dc, f"SELECT to_regclass('{expected}') IS NOT NULL;").strip() == b"t")
    names = {c[1] for c in actual["schema"]["constraints"]}
    require(
        {
            "ck_accounts_cash_cents",
            "ck_accounts_cash_non_negative",
            "ck_holdings_quantity_non_negative",
            "uq_holdings_user_coin",
            "uq_trades_user_idempotency_key",
        }
        <= names
    )
    # Check identity progression without consuming sequence values. MVCC sequence
    # state need not equal the source; every future generated id must be safe.
    identities = contract.identity_tables(manifest["revision"])
    for table in identities:
        sequence = f"{table}_id_seq"
        require(
            sql(
                dc,
                f"SELECT pg_get_serial_sequence('public.{table}','id')='public.{sequence}' "
                f"AND (CASE WHEN is_called THEN last_value+1 ELSE last_value END) "
                f"> coalesce((SELECT max(id) FROM {table}),0) FROM {sequence};",
            ).strip()
            == b"t"
        )
    print("equality=true invariants=true identities=true")


@contextlib.contextmanager
def restored(dc, dump):
    created = False
    try:
        call(dc + ["exec", "-T", "postgres", "pg_restore", "--list"], dump)
        require(
            sql(
                dc,
                f"SELECT NOT EXISTS(SELECT FROM pg_database WHERE datname='{CLONE}');",
                "birja_ops_test",
            ).strip()
            == b"t"
        )
        sql(
            dc,
            "DO $$BEGIN IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_migrator') THEN CREATE ROLE birja_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION; END IF; END$$;",
            "birja_ops_test",
        )
        require(
            sql(
                dc,
                "SELECT NOT (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls) FROM pg_roles WHERE rolname='birja_migrator';",
                "birja_ops_test",
            ).strip()
            == b"t"
        )
        sql(
            dc,
            f"CREATE DATABASE {CLONE} OWNER birja_migrator TEMPLATE template0;",
            "birja_ops_test",
        )
        created = True
        call(
            dc
            + [
                "exec",
                "-T",
                "postgres",
                "pg_restore",
                "-U",
                "birja_migrator",
                "-d",
                CLONE,
                "--no-owner",
                "--no-acl",
                "--role=birja_migrator",
                "--exit-on-error",
                "--single-transaction",
            ],
            dump,
        )
        yield
    finally:
        if created:
            sql(dc, f"DROP DATABASE {CLONE} WITH (FORCE);", "birja_ops_test")


def restore(args):
    # No operational env override is accepted, including ambient Compose options.
    require(
        not any(
            k in os.environ
            for k in [
                "COMPOSE_FILE",
                "COMPOSE_PROJECT_NAME",
                "DOCKER_HOST",
                "DATABASE_URL",
                "PGUSER",
                "PGDATABASE",
                "PGHOST",
                "APP_DIR",
            ]
        )
    )
    parser = argparse.ArgumentParser(allow_abbrev=False)
    require(
        len([x.split("=", 1)[0] for x in args if x.startswith("--")])
        == len({x.split("=", 1)[0] for x in args if x.startswith("--")})
    )
    parser.add_argument("--isolated-clone", action="store_true")
    parser.add_argument("--synthetic")
    parser.add_argument("--approved-clone", action="store_true")
    parser.add_argument("--snapshot", required=True)
    a = parser.parse_args(args)
    require(re.fullmatch(r"[0-9a-f]{64}", a.snapshot))
    require(bool(a.synthetic) != a.approved_clone)
    b = backup_module()
    c = b.load_config(["--synthetic", a.synthetic] if a.synthetic else [])
    if a.synthetic:
        require(c["db_user"] == BOOT and c["db_name"] == "birja_source_test")
    require(not a.isolated_clone or a.synthetic)
    dc = compose(
        "birja-ops-test"
        if a.synthetic and not a.isolated_clone
        else "birja-restore-check"
    )
    job = b.Job(c)
    job.state.mkdir(mode=0o700, parents=True, exist_ok=True)
    b.private_dir(job.state)
    with job.lock() as lock:
        owns_server = False
        started = int(time.time())
        attempt = {
            "format": 1,
            "run_id": os.urandom(16).hex(),
            "snapshot_id": a.snapshot,
            "ok": False,
            "started_epoch": started,
            "started_utc": b.utc(started),
        }
        b.atomic(job.state / "restore-last-attempt.json", attempt)
        previous_signals = {}

        def interrupted(signum, frame):
            raise InterruptedError("restore interrupted")

        for signum in [signal.SIGTERM, signal.SIGINT]:
            previous_signals[signum] = signal.signal(signum, interrupted)
        try:
            binding = b.recovery_binding(c)
            job.refresh_quota(lock)
            if a.approved_clone or a.isolated_clone:
                require(not call(dc + ["ps", "-q"]).strip())
                owns_server = True
                start_recovery(dc)
            check_running(dc)
            snapshots = json.loads(job.restic("snapshots", a.snapshot))
            require(job.check_scope(snapshots) == [a.snapshot])
            with tempfile.TemporaryDirectory(prefix="restore-", dir=job.state) as tmp:
                target = Path(tmp)
                job.restic("restore", a.snapshot, "--target", str(target), "--verify")
                require(
                    {p.name for p in target.iterdir()}
                    == {"database.dump", "manifest.json", "recovery.tar"}
                )
                for p in target.iterdir():
                    require(
                        p.is_file()
                        and not p.is_symlink()
                        and p.stat().st_size <= c["max_stage_bytes"]
                    )
                manifest = json.loads((target / "manifest.json").read_text())
                require(digest(target / "database.dump") == manifest["archive_sha256"])
                with restored(dc, (target / "database.dump").read_bytes()):
                    verify(dc, manifest)
                attempt.update(
                    binding,
                    source_release=manifest["release"],
                    source_revision=manifest["revision"],
                    manifest_sha256=digest(target / "manifest.json"),
                    dump_sha256=digest(target / "database.dump"),
                    recovery_sha256=digest(target / "recovery.tar"),
                )
                if "source_binding" in manifest:
                    require(
                        manifest["source_binding"] == binding
                        and manifest["recovery_sha256"] == attempt["recovery_sha256"]
                    )
            if owns_server:
                call(dc + ["down", "-v", "--remove-orphans"], timeout=60)
                require(not call(dc + ["ps", "-q"]).strip())
                owns_server = False
            require(binding == b.recovery_binding(c))
            completed = int(time.time())
            attempt.update(
                ok=True, completed_epoch=completed, completed_utc=b.utc(completed)
            )
            b.atomic(job.state / "restore-last-success.json", attempt)
            b.atomic(job.state / "restore-last-attempt.json", attempt)
        except BaseException:
            completed = int(time.time())
            attempt.update(
                ok=False, completed_epoch=completed, completed_utc=b.utc(completed)
            )
            b.atomic(job.state / "restore-last-attempt.json", attempt)
            raise
        finally:
            try:
                if owns_server:
                    call(dc + ["down", "-v", "--remove-orphans"], timeout=60)
            finally:
                for signum, handler in previous_signals.items():
                    signal.signal(signum, handler)


def main():
    os.umask(0o077)
    try:
        require(len(sys.argv) > 1)
        if sys.argv[1] == "restore":
            restore(sys.argv[2:])
        elif sys.argv[1] == "bundle":
            bundle(sys.argv[2:])
        else:
            raise ValueError("mode")
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError):
        print("recovery=false step=guard-or-verification", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
