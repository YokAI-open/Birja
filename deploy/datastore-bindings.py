#!/usr/bin/env python3
"""Fixed protected existing-volume bindings for retained production orchestration."""

import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CONFIG = Path("/etc/birja/datastore-bindings.json")
OVERLAY = Path("/var/lib/birja/ops/datastore-volumes.json")
LOCK = Path("/var/lock/birja-deploy.lock")
ENV = {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8"}
LOGICAL = {"pgdata", "redisdata"}

PROBES = {
    "pgdata": """for p in /selected/18 /selected/18/docker /selected/18/docker/global /selected/18/docker/PG_VERSION /selected/18/docker/global/pg_control; do test ! -L "$p"; done
test -f /selected/18/docker/PG_VERSION
test "$(cat /selected/18/docker/PG_VERSION)" = 18
test -s /selected/18/docker/global/pg_control
test "$(stat -c '%u:%g' /selected/18/docker)" = 70:70
test "$(stat -c '%u:%g' /selected/18/docker/global/pg_control)" = 70:70
""",
    "redisdata": """test ! -L /selected/appendonlydir
test ! -L /selected/appendonlydir/appendonly.aof.manifest
test -s /selected/appendonlydir/appendonly.aof.manifest
test "$(stat -c '%u:%g' /selected/appendonlydir)" = 65532:65532
test "$(stat -c '%u:%g' /selected/appendonlydir/appendonly.aof.manifest)" = 65532:65532
awk 'NF != 6 || $1 != "file" || $3 != "seq" || $5 != "type" || $2 !~ /^[A-Za-z0-9_.-]+$/ || $2 == "." || $2 == ".." || ($6 != "b" && $6 != "i") {exit 1} END {if (NR == 0) exit 1}' /selected/appendonlydir/appendonly.aof.manifest
while read -r kind file seq number type role; do
 test ! -L "/selected/appendonlydir/$file"
 test -f "/selected/appendonlydir/$file"
 test "$(stat -c '%u:%g' "/selected/appendonlydir/$file")" = 65532:65532
 if test "$role" = b; then test -s "/selected/appendonlydir/$file"; fi
done < /selected/appendonlydir/appendonly.aof.manifest
""",
}


def require(ok):
    if not ok:
        raise ValueError("datastore binding guard")


def command(argv):
    result = subprocess.run(argv, env=ENV, capture_output=True, check=False, timeout=45)
    require(result.returncode == 0)
    return result.stdout


def protected(path, *, directory=False, mode=None):
    require(path.is_absolute() and path == path.resolve())
    for parent in path.parents:
        entry = parent.lstat()
        require(stat.S_ISDIR(entry.st_mode) and entry.st_uid == 0)
        require(
            not entry.st_mode & 0o022
            or (parent == Path("/tmp") and entry.st_mode & stat.S_ISVTX)
        )
    entry = path.lstat()
    require(entry.st_uid == 0)
    require(stat.S_ISDIR(entry.st_mode) if directory else stat.S_ISREG(entry.st_mode))
    require(not entry.st_mode & 0o022)
    if mode is not None:
        require(stat.S_IMODE(entry.st_mode) == mode)


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value)
        value[key] = item
    return value


def read_bindings():
    protected(CONFIG, mode=0o600)
    require(CONFIG.stat().st_size <= 8192)
    binding = json.loads(CONFIG.read_text(), object_pairs_hook=unique_object)
    require(set(binding) == {"format", "project", "volumes"})
    require(type(binding["format"]) is int and binding["format"] == 1)
    require(binding["project"] == "birja-prod" and set(binding["volumes"]) == LOGICAL)
    names = []
    for pair in binding["volumes"].values():
        require(set(pair) == {"original", "candidate"})
        for volume in pair.values():
            require(set(volume) == {"name", "created_at", "driver", "scope"})
            require(
                type(volume["name"]) is str
                and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", volume["name"])
            )
            require(
                type(volume["created_at"]) is str
                and re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+(?:Z|[+-][0-9]{2}:[0-9]{2})",
                    volume["created_at"],
                )
            )
            require(volume["driver"] == volume["scope"] == "local")
            names.append(volume["name"])
    require(len(names) == len(set(names)) == 4)
    return binding


def inspect_volumes(binding):
    expected = {
        v["name"]: v for pair in binding["volumes"].values() for v in pair.values()
    }
    rows = json.loads(
        command(["/usr/bin/docker", "volume", "inspect", *sorted(expected)])
    )
    require(type(rows) is list and len(rows) == 4)
    require({row["Name"] for row in rows} == set(expected))
    for row in rows:
        value = expected[row["Name"]]
        require(
            row["CreatedAt"] == value["created_at"]
            and row["Driver"] == row["Scope"] == "local"
        )
        require(row.get("Options") in (None, {}))
    return {row["Name"]: row for row in rows}


def images():
    source = (HERE.parent / "docker-compose.prod.yml").read_text()
    return {
        service: re.search(
            r"^  " + service + r":\n.*?^    image: (\S+)$",
            source,
            re.MULTILINE | re.DOTALL,
        )[1]
        for service in ["postgres", "redis"]
    }


def check_data(binding, volumes):
    image = images()["postgres"]
    require(re.fullmatch(r"cgr\.dev/chainguard/postgres@sha256:[0-9a-f]{64}", image))
    for logical in sorted(LOGICAL):
        name = binding["volumes"][logical]["candidate"]["name"]
        # A volume mount can implicitly create a deleted source. A bind mount
        # of the inspected local driver's existing data directory cannot.
        data = Path(volumes[name]["Mountpoint"])
        require(data.is_absolute() and data == data.resolve() and data.is_dir())
        require(data.name == "_data" and data.parent.name == name)
        protected(data.parent, directory=True)
        command(
            [
                "/usr/bin/docker",
                "run",
                "--rm",
                "--pull",
                "never",
                "--network",
                "none",
                "--read-only",
                "--mount",
                f"type=bind,source={data},target=/selected,readonly",
                "--entrypoint",
                "sh",
                image,
                "-ec",
                PROBES[logical],
            ]
        )
    inspect_volumes(binding)


def overlay_value(binding):
    return {
        "volumes": {
            logical: {
                "external": True,
                "name": binding["volumes"][logical]["candidate"]["name"],
            }
            for logical in sorted(LOGICAL)
        }
    }


def write_overlay(binding):
    protected(OVERLAY.parent, directory=True)
    expected = overlay_value(binding)
    require(not OVERLAY.is_symlink())
    if OVERLAY.exists():
        protected(OVERLAY, mode=0o600)
        require(OVERLAY.stat().st_size <= 8192)
        require(
            json.loads(OVERLAY.read_text(), object_pairs_hook=unique_object) == expected
        )
        return
    temporary = OVERLAY.with_suffix(".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(json.dumps(expected, sort_keys=True) + "\n")
        os.replace(temporary, OVERLAY)
    finally:
        temporary.unlink(missing_ok=True)


def check_running(binding):
    projection = '{"Id":{{json .Id}},"Image":{{json .Image}},"Platform":{{json .Platform}},"State":{"Running":{{json .State.Running}}},"Config":{"User":{{json .Config.User}},"Labels":{{json .Config.Labels}}},"HostConfig":{"PortBindings":{{json .HostConfig.PortBindings}},"Privileged":{{json .HostConfig.Privileged}}},"Mounts":{{json .Mounts}},"NetworkSettings":{"Networks":{{json .NetworkSettings.Networks}}}}'
    for service, logical, destination, user in [
        ("postgres", "pgdata", "/var/lib/postgresql", "70:70"),
        ("redis", "redisdata", "/data", "65532"),
    ]:
        ids = (
            command(
                [
                    "/usr/bin/docker",
                    "ps",
                    "-aq",
                    "--no-trunc",
                    "--filter",
                    "label=com.docker.compose.project=birja-prod",
                    "--filter",
                    "label=com.docker.compose.service=" + service,
                ]
            )
            .decode()
            .split()
        )
        require(len(ids) == 1)
        row = json.loads(
            command(["/usr/bin/docker", "inspect", ids[0], "--format", projection])
        )
        labels = row["Config"]["Labels"]
        require(
            labels["com.docker.compose.project"] == "birja-prod"
            and labels["com.docker.compose.service"] == service
        )
        require(row["Id"] == ids[0] and row["State"]["Running"] is True)
        approved = json.loads(
            command(
                [
                    "/usr/bin/docker",
                    "image",
                    "inspect",
                    images()[service],
                    "--platform",
                    "linux/amd64",
                ]
            )
        )
        require(
            len(approved) == 1
            and approved[0]["Os"] == "linux"
            and approved[0]["Architecture"] == "amd64"
        )
        require(row["Image"] == approved[0]["Id"] and row["Platform"] == "linux")
        require(
            row["Config"]["User"] == user and row["HostConfig"]["Privileged"] is False
        )
        require(not row["HostConfig"].get("PortBindings"))
        mounts = row["Mounts"]
        volumes = [m for m in mounts if m["Type"] == "volume"]
        require(
            len(volumes) == 1
            and volumes[0]["Name"] == binding["volumes"][logical]["candidate"]["name"]
        )
        require(volumes[0]["Destination"] == destination and volumes[0]["RW"] is True)
        require(len([m for m in mounts if m["Destination"] == destination]) == 1)
        binds = [m for m in mounts if m["Type"] != "volume"]
        expected = (
            {
                "/run/birja/db-server": "/etc/birja/db-tls/server",
                "/run/birja/db-hba": str(HERE / "db"),
            }
            if service == "postgres"
            else {}
        )
        require(len(binds) == len(expected))
        require({m["Destination"] for m in binds} == set(expected))
        require(
            all(
                m["Type"] == "bind"
                and m["Source"] == expected[m["Destination"]]
                and m["RW"] is False
                for m in binds
            )
        )
        require(set(row["NetworkSettings"]["Networks"]) == {"birja-prod_data"})
    network = json.loads(
        command(["/usr/bin/docker", "network", "inspect", "birja-prod_data"])
    )
    require(len(network) == 1 and network[0]["Internal"] is True)


def operation_lock(inherited=None):
    require(os.geteuid() == 0)
    fd = inherited if inherited is not None else os.environ.get("BIRJA_BACKUP_LOCK_FD")
    require(fd is not None)
    spec = importlib.util.spec_from_file_location(
        "binding_lock", HERE / "backup-snapshot.py"
    )
    backup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backup)
    return backup.acquire_operation_lock(LOCK, fd)


def main(args=None, inherited=None):
    args = sys.argv[1:] if args is None else args
    require(args in [["--check-volumes"], ["--write-overlay"], ["--check-running"]])
    with operation_lock(inherited):
        binding = read_bindings()
        volumes = inspect_volumes(binding)
        if args == ["--write-overlay"]:
            write_overlay(binding)
        elif args == ["--check-volumes"]:
            check_data(binding, volumes)
        else:
            check_running(binding)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError):
        print("datastore_bindings_failed=true diagnostics=redacted", file=sys.stderr)
        raise SystemExit(1) from None
