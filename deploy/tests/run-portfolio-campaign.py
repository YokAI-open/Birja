#!/usr/bin/env python3
"""One local qualification command with private, durable process receipts.

Status/resume only inspect the original invocation. They never start a replacement
qualification or adopt another process's PID. This is not a scheduler.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validation():
    path = ROOT / "deploy/tests/run-portfolio-validation.py"
    spec = importlib.util.spec_from_file_location("campaign_validation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def private_directory(path, *, create=False):
    path = Path(path)
    if (
        not path.is_absolute()
        or path != path.resolve()
        or path.parent != Path("/tmp")
        or not re.fullmatch(
            r"birja-(?:backup-test-[A-Za-z0-9_.-]+|phase14-campaign-[a-z0-9-]+)",
            path.name,
        )
    ):
        raise ValueError("exclusive synthetic receipt path required")
    if create:
        path.mkdir(mode=0o700)  # Existing means refuse, never resume by rerunning.
    if path.is_symlink() or not path.is_dir():
        raise ValueError("private receipt directory required")
    st = path.stat()
    if st.st_uid != os.geteuid() or st.st_mode & 0o077:
        raise ValueError("private receipt ownership/mode required")
    return path


def read_json(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("private receipt file required")
    st = path.stat()
    if st.st_uid != os.geteuid() or st.st_mode & 0o077:
        raise ValueError("private receipt file ownership/mode required")
    return json.loads(path.read_text())


def write_json(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def process_identity(pid, *, alive_only=True):
    if type(pid) is not int or pid <= 0:
        return None
    try:
        tail = Path(f"/proc/{int(pid)}/stat").read_text().rsplit(") ", 1)[1].split()
        return None if alive_only and tail[0] == "Z" else int(tail[19])
    except (OSError, ValueError, IndexError):
        return None


def source_snapshot(runner):
    result = runner.security_sources()
    # Include this NEW entrypoint before its first commit as well.
    name = "deploy/tests/run-portfolio-campaign.py"
    result[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    return result


def artifact_snapshot(runner, previous):
    """Only freeze a complete packaged archive, not a partially written tar."""
    archive = runner.ARCHIVE
    status_file = archive.parent / "status.json"
    if not status_file.exists():
        if previous is not None:
            raise ValueError("campaign archive/status disappeared")
        return None
    state = read_json(status_file)
    expected = state.get("archive_sha256")
    sources = runner.load("portfolio-sources")
    sources.verify_archive_binding(archive, expected)
    records = {}
    for path in sorted(archive.parent.glob("*-image-binding.json")):
        binding = read_json(path)
        inspected = subprocess.check_output(
            ["docker", "image", "inspect", binding["id"]],
            env=runner.environment(),
            timeout=30,
        )
        sources.verify_image(binding, json.loads(inspected))
        records[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    runner.load("portfolio-smoke").authenticate_campaign_images(archive, expected)
    result = {"archive_sha256": expected, "images": records}
    if previous is not None and (
        previous["archive_sha256"] != expected
        or any(records.get(name) != sha for name, sha in previous["images"].items())
    ):
        raise ValueError("campaign archive/image identity changed or disappeared")
    return result


def verify_integrity(runner, request, state):
    if source_snapshot(runner) != request["source_sha256"]:
        raise ValueError("frozen campaign source changed")
    if runner.preserved_archive() != request["preserved_archive_sha256"]:
        raise ValueError("preserved archive changed")
    return (
        artifact_snapshot(runner, state.get("artifacts"))
        if request["suite"] == "recovery"
        else None
    )


def verify_claim(directory, request, state):
    claim = read_json(directory / "claim.json")
    digest = hashlib.sha256((directory / "request.json").read_bytes()).hexdigest()
    if (
        claim.get("request_sha256") != digest
        or state.get("request_sha256") != digest
        or claim.get("run_id") != request["run_id"]
        or (claim.get("pid"), claim.get("start_ticks"))
        != (state.get("pid"), state.get("start_ticks"))
    ):
        raise ValueError("claimed launch request/original identity mismatch")


def inspect_status(directory):
    directory = private_directory(directory)
    request = read_json(directory / "request.json")
    state = read_json(directory / "status.json")
    if (
        request.get("format") != 1
        or state.get("format") != 1
        or request.get("suite") not in {"all-security", "recovery"}
        or state.get("suite") != request["suite"]
        or state.get("state")
        not in {
            "starting",
            "preflight",
            "running",
            "passed",
            "failed",
            "refused",
            "interrupted",
        }
        or not isinstance(request.get("run_id"), str)
        or not request["run_id"]
        or request["run_id"] != state.get("run_id")
    ):
        raise ValueError("campaign receipt identity mismatch")
    if (
        state["state"] == "passed"
        and (type(state.get("exit_code")) is not int or state["exit_code"] != 0)
        or state["state"] == "failed"
        and (type(state.get("exit_code")) is not int or state["exit_code"] == 0)
    ):
        raise ValueError("campaign receipt outcome mismatch")
    runner = validation()
    if "request_sha256" in state:
        verify_claim(directory, request, state)
    artifacts = verify_integrity(runner, request, state)
    if state["state"] in {"starting", "preflight", "running"}:
        if process_identity(state["pid"]) != state["start_ticks"]:
            raise ValueError(
                "original supervisor disappeared or PID reused; refusing restart"
            )
        child = state.get("child_pid")
        if child and process_identity(child) not in (None, state["child_start_ticks"]):
            raise ValueError("original child PID reused")
        preflight = state.get("preflight_pid")
        if preflight and process_identity(preflight) not in (
            None,
            state["preflight_start_ticks"],
        ):
            raise ValueError("original preflight PID reused")
    return {**state, "artifacts": artifacts}


def group_members(pid):
    """Only live members of this owned session/group; zombies do no work."""
    members = []
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            tail = path.read_text().rsplit(") ", 1)[1].split()
            if tail[0] != "Z" and int(tail[2]) == pid and int(tail[3]) == pid:
                members.append(int(path.parent.name))
        except (OSError, ValueError, IndexError):
            continue
    return members


def stop_child(child, ticks):
    if process_identity(child.pid) not in (None, ticks):
        raise ValueError("original phase PID reused; refusing signal")
    if group_members(child.pid):
        try:
            os.killpg(child.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 60
    while group_members(child.pid) and time.monotonic() < deadline:
        child.poll()
        time.sleep(0.05)
    if group_members(child.pid):
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    code = child.wait(timeout=5)
    deadline = time.monotonic() + 5
    while group_members(child.pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    if group_members(child.pid):
        raise ValueError("owned phase group cleanup incomplete")
    return code


class PreflightProcess:
    """A forked preflight preserves test injection without untracked subprocesses."""

    def __init__(self, pid):
        self.pid = pid
        self.returncode = None

    def poll(self):
        if self.returncode is None:
            observed, status = os.waitpid(self.pid, os.WNOHANG)
            if observed:
                self.returncode = os.waitstatus_to_exitcode(status)
        return self.returncode

    def wait(self, timeout=None):
        deadline = time.monotonic() + (timeout if timeout is not None else 60)
        while self.poll() is None:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired("owned-preflight", timeout)
            time.sleep(0.02)
        return self.returncode


def claim_request(directory, request):
    """O_EXCL is the irreversible consume boundary, including stale claims."""
    claim = {
        "format": 1,
        "run_id": request["run_id"],
        "pid": os.getpid(),
        "start_ticks": process_identity(os.getpid()),
        "request_sha256": hashlib.sha256(
            (directory / "request.json").read_bytes()
        ).hexdigest(),
    }
    fd = os.open(directory / "claim.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    with os.fdopen(fd, "w") as stream:
        json.dump(claim, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return claim


def start_preflight(directory, runner, request, state):
    """The child cannot begin work until its session identity is durable."""
    log = os.open(
        directory / "preflight.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
    )
    read_gate, write_gate = os.pipe()
    ready_read, ready_write = os.pipe()
    child = None
    try:
        pid = os.fork()
        if pid == 0:
            try:
                os.close(write_gate)
                os.close(ready_read)
                os.setsid()
                os.dup2(log, 1)
                os.dup2(log, 2)
                os.close(log)
                os.write(ready_write, b"1")
                os.close(ready_write)
                if os.read(read_gate, 1) != b"1":
                    os._exit(1)
                os.close(read_gate)
                cancelled = False

                def cancel(signum, frame):
                    # Throwing through subprocess.run would SIGKILL its direct
                    # child before shell/Compose finalizers can finish. Every
                    # descendant receives this group signal independently.
                    nonlocal cancelled
                    cancelled = True

                signal.signal(signal.SIGINT, cancel)
                signal.signal(signal.SIGTERM, cancel)
                result = runner.preflight(request["suite"])
                if cancelled:
                    raise KeyboardInterrupt
                write_json(directory / "preflight.json", result)
                sys.stdout.flush()
                sys.stderr.flush()
                os._exit(0)
            except BaseException as exc:  # noqa: BLE001 - owned preflight exit boundary
                print(type(exc).__name__, file=sys.stderr, flush=True)
                os._exit(1)
        child = PreflightProcess(pid)
        os.close(read_gate)
        os.close(ready_write)
        if os.read(ready_read, 1) != b"1":
            raise ValueError("preflight session did not initialize")
        ticks = process_identity(pid, alive_only=False)
        if ticks is None:
            raise ValueError("preflight identity unavailable before work")
        state.update(
            phase="preflight",
            preflight_pid=pid,
            preflight_start_ticks=ticks,
            preflight_log="preflight.log",
        )
        write_json(directory / "status.json", state)
        os.write(write_gate, b"1")
        return child
    except BaseException:
        if child is not None:
            stop_child(child, process_identity(child.pid, alive_only=False))
        raise
    finally:
        for fd in (log, write_gate, ready_read):
            os.close(fd)


def worker(directory, *, runner=None, command=None):
    """Internal worker; command injection is only for bounded stdlib tests."""
    directory = private_directory(directory)
    request = read_json(directory / "request.json")
    try:
        claim = claim_request(directory, request)
    except FileExistsError:
        return 1  # Never touch original status/logs, even if its process is gone.
    runner = validation() if runner is None else runner
    state = {
        "format": 1,
        "run_id": request["run_id"],
        "suite": request["suite"],
        "pid": os.getpid(),
        "start_ticks": process_identity(os.getpid()),
        "state": "preflight",
        "started_at": time.time(),
        "artifacts": None,
        "request_sha256": claim["request_sha256"],
    }
    started = time.monotonic()
    write_json(directory / "status.json", state)
    child = None
    interrupted = False
    recording_child = False

    def interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True
        if not recording_child:
            raise KeyboardInterrupt

    old_handlers = {
        sig: signal.signal(sig, interrupt) for sig in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        verify_claim(directory, request, state)
        verify_integrity(runner, request, state)
        # Tools, current fixture tail and finite source pins precede the long command.
        recording_child = True
        try:
            child = start_preflight(directory, runner, request, state)
        finally:
            recording_child = False
        if interrupted:
            raise KeyboardInterrupt
        while child.poll() is None:
            time.sleep(0.05)
        state["preflight_exit_code"] = child.returncode
        if group_members(child.pid):
            stop_child(child, state["preflight_start_ticks"])
            raise ValueError("preflight returned with outstanding descendants")
        if child.returncode != 0:
            raise ValueError("preflight failed; see private preflight log")
        read_json(directory / "preflight.json")
        child = None
        verify_claim(directory, request, state)
        verify_integrity(runner, request, state)
        argv = (
            command
            if command is not None
            else [
                sys.executable,
                str(ROOT / "deploy/tests/run-portfolio-validation.py"),
                "--suite",
                request["suite"],
            ]
        )
        fd = os.open(
            directory / "command.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        with os.fdopen(fd, "wb", buffering=0) as log:
            recording_child = True
            try:
                child = subprocess.Popen(
                    argv,
                    cwd=ROOT,
                    env=runner.environment(),
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                ticks = process_identity(child.pid, alive_only=False)
                if ticks is None:
                    child.wait()
                state.update(
                    state="running",
                    phase="command",
                    child_pid=child.pid,
                    child_start_ticks=ticks,
                    argv=argv,
                )
                write_json(directory / "status.json", state)
            finally:
                recording_child = False
            if interrupted:
                raise KeyboardInterrupt
            next_check = 0
            while child.poll() is None:
                if time.monotonic() >= next_check:
                    verify_claim(directory, request, state)
                    state["artifacts"] = verify_integrity(runner, request, state)
                    write_json(directory / "status.json", state)
                    next_check = time.monotonic() + 5
                time.sleep(0.2)
            verify_claim(directory, request, state)
            state["artifacts"] = verify_integrity(runner, request, state)
            if group_members(child.pid):
                stop_child(child, ticks)
                raise ValueError("long command returned with outstanding descendants")
            state["exit_code"] = child.returncode
            state["state"] = "passed" if child.returncode == 0 else "failed"
            state["cleanup"] = (
                "runner-finalizers-returned"
                if child.returncode == 0
                else "see-command-log"
            )
    except (Exception, KeyboardInterrupt) as exc:  # noqa: BLE001 - durable supervisor failure boundary
        # Repeated cancellation must not interrupt the bounded original-child
        # reaper and leave a false running receipt.
        for sig in old_handlers:
            signal.signal(sig, signal.SIG_IGN)
        if child is not None:
            try:
                ticks = (
                    state.get("preflight_start_ticks")
                    if state.get("phase") == "preflight"
                    else state.get("child_start_ticks")
                )
                state["exit_code"] = stop_child(child, ticks)
                state["cleanup"] = (
                    "preflight-group-reaped;long-command-not-started"
                    if state.get("phase") == "preflight"
                    else "command-group-reaped;see-command-log"
                )
            except Exception:  # noqa: BLE001 - report cleanup failure without false success
                state["cleanup"] = (
                    "owned-group-cleanup-incomplete;manual-inspection-required"
                )
        state["state"] = "interrupted" if interrupted else "refused"
        # Do not serialize raw exception text, arguments or private environment.
        state["error_type"] = type(exc).__name__
        if child is None:
            state["cleanup"] = "long-command-not-started"
    finally:
        state["finished_at"] = time.time()
        state["elapsed_seconds"] = round(time.monotonic() - started, 3)
        write_json(directory / "status.json", state)
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
    return 0 if state["state"] == "passed" else 1


def start(suite, directory):
    if suite not in {"all-security", "recovery"}:
        raise ValueError("explicit suite required")
    runner = validation()
    if suite == "recovery" and runner.ARCHIVE.parent.exists():
        raise ValueError(
            "new recovery campaign requires absent exclusive archive directory"
        )
    directory = private_directory(directory, create=True)
    request = {
        "format": 1,
        "run_id": uuid.uuid4().hex,
        "suite": suite,
        "source_sha256": source_snapshot(runner),
        "preserved_archive_sha256": runner.preserved_archive(),
    }
    write_json(directory / "request.json", request)
    (directory / "request.json").chmod(0o400)
    fd = os.open(
        directory / "supervisor.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
    )
    with os.fdopen(fd, "wb", buffering=0) as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                "--receipt-dir",
                str(directory),
            ],
            cwd=ROOT,
            env=runner.environment(),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    # The caller owns launch only; the detached supervisor owns the one command.
    for _ in range(100):
        if (directory / "status.json").exists():
            return inspect_status(directory)
        if process.poll() is not None:
            raise ValueError("supervisor failed before process receipt")
        time.sleep(0.05)
    raise ValueError(
        "supervisor startup receipt unavailable; inspect original, never restart"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--receipt-dir", required=True)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--suite", choices=["all-security", "recovery"])
    choice.add_argument("--status", action="store_true")
    choice.add_argument(
        "--resume", action="store_true", help="Inspect the original run; never rerun it"
    )
    choice.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        return worker(args.receipt_dir)
    state = (
        start(args.suite, args.receipt_dir)
        if args.suite
        else inspect_status(args.receipt_dir)
    )
    print(json.dumps(state, sort_keys=True))
    return 0 if state["state"] in {"preflight", "running", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
