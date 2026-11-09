#!/usr/bin/env python3
"""Bounded B2 inventory and protected setup controls; no billing-counter API.

Only installed nightly entrypoints call this wrapper. backup.env is JSON,
never a systemd EnvironmentFile. Legacy quota field names request_remaining
and download_remaining_bytes carry LOCAL operation limits, not provider
remaining allowances. Caps are owner-attested setup controls, not API facts.
"""

import base64
import importlib.util
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location(
    "backup", Path(__file__).with_name("backup-snapshot.py")
)
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)
require = backup.require
ENDPOINT = "https://s3.eu-central-003.backblazeb2.com"
MAX_CALLS = 128
MAX_RESPONSE = 2_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("redirect prohibited")


class API:
    def __init__(
        self, request_budget=MAX_CALLS, download_budget=MAX_CALLS * MAX_RESPONSE
    ):
        # Ignore ambient proxies, credentials, netrc and alternate endpoints.
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )
        self.started = time.monotonic()
        self.calls = 0
        self.bytes = 0
        self.request_budget = request_budget
        self.download_budget = download_budget

    def call(self, base, operation, body, token):
        require(
            base == "https://api.backblazeb2.com"
            or re.fullmatch(r"https://api[0-9]{3}\.backblazeb2\.com", base)
        )
        require(
            operation
            in {
                "b2_authorize_account",
                "b2_list_buckets",
                "b2_list_file_versions",
                "b2_list_unfinished_large_files",
                "b2_list_parts",
            }
        )
        require(
            self.calls < min(MAX_CALLS, self.request_budget)
            and time.monotonic() - self.started < 120
        )
        # Charge a protocol allowance even for failed HTTP requests. No retries
        # or redirects occur beneath this counted native request boundary.
        require(self.bytes + 8192 < self.download_budget)
        self.bytes += 8192
        self.calls += 1
        req = urllib.request.Request(
            base + "/b2api/v4/" + operation,
            data=None
            if operation == "b2_authorize_account"
            else json.dumps(body).encode(),
            headers={"Authorization": token, "Content-Type": "application/json"},
        )
        with self.opener.open(
            req, timeout=min(10, max(1, 120 - (time.monotonic() - self.started)))
        ) as response:
            require(response.status == 200)
            chunks, size = [], 0
            while True:
                require(time.monotonic() - self.started < 120)
                remaining = self.download_budget - self.bytes
                require(remaining > 0)
                chunk = response.read1(min(65536, MAX_RESPONSE + 1 - size, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                self.bytes += len(chunk)
                require(size <= MAX_RESPONSE)
            data = b"".join(chunks)
        require(len(data) <= MAX_RESPONSE and time.monotonic() - self.started < 120)
        obj = backup.strict_json(data)
        require(type(obj) is dict)
        return obj


def integer(value):
    require(type(value) is int and 0 <= value <= 10**15)
    return value


def text(value):
    require(
        type(value) is str
        and 0 < len(value) <= 2048
        and "\n" not in value
        and "\r" not in value
    )
    return value


def controls(c):
    root = Path(c["_config_root"])
    a = backup.strict_json(
        backup.private_file(root / "backup-controls.json").read_bytes()
    )
    require(
        set(a)
        == {
            "format",
            "verified_at",
            "console_zero_caps",
            "daily_owner_checks",
            "exclusive_account_writes",
            "inventory_key_id_file",
            "inventory_key_file",
            "local_request_budget",
            "local_download_budget_bytes",
        }
    )
    require(
        a["format"] == 1
        and a["console_zero_caps"] is True
        and a["daily_owner_checks"] is True
        and a["exclusive_account_writes"] is True
    )
    # Setup attestation is deliberately separate from fresh measured inventory.
    require(600 <= time.time() - integer(a["verified_at"]) <= 31 * 86400)
    for key in ["inventory_key_id_file", "inventory_key_file"]:
        p = backup.contained(a[key], root)
        require(p == p.resolve())
        backup.private_file(p)
    require(1 <= integer(a["local_request_budget"]) <= 10000)
    require(
        c["max_stage_bytes"]
        <= integer(a["local_download_budget_bytes"])
        <= 4_000_000_000
    )
    return a


def inventory(c, a, api=None):
    if api is None:
        api = c.get("_inventory_api")
        if api is None:
            api = API(a["local_request_budget"], a["local_download_budget_bytes"])
            c["_inventory_api"] = api
        api.request_budget = min(api.request_budget, a["local_request_budget"])
        api.download_budget = min(api.download_budget, a["local_download_budget_bytes"])
    key = text(backup.private_file(a["inventory_key_id_file"]).read_text().strip())
    secret = text(backup.private_file(a["inventory_key_file"]).read_text().strip())
    auth = api.call(
        "https://api.backblazeb2.com",
        "b2_authorize_account",
        {},
        "Basic " + base64.b64encode((key + ":" + secret).encode()).decode(),
    )
    storage = auth["apiInfo"]["storageApi"]
    allowed = storage["allowed"]
    require(allowed.get("buckets") is None and allowed.get("namePrefix") is None)
    require(
        {"listBuckets", "listFiles", "readBucketRetentions"}
        <= set(allowed["capabilities"])
    )
    require(
        all(
            # The console's Read Only preset also delegates file downloads.
            # This cannot mutate files/buckets/keys. Our fixed API allowlist
            # never invokes b2_get_download_authorization, so inventory does
            # not exercise that extra capability. All mutations still reject.
            type(cap) is str
            and (cap.startswith(("read", "list")) or cap == "shareFiles")
            for cap in allowed["capabilities"]
        )
    )
    require(storage["s3ApiUrl"] == ENDPOINT)
    base, token, account = (
        text(storage["apiUrl"]),
        text(auth["authorizationToken"]),
        text(auth["accountId"]),
    )
    buckets = api.call(base, "b2_list_buckets", {"accountId": account}, token)[
        "buckets"
    ]
    require(type(buckets) is list and 1 <= len(buckets) <= 100)
    require(len({text(b["bucketId"]) for b in buckets}) == len(buckets))
    target = [b for b in buckets if b["bucketName"] == "Birja-backup"]
    require(len(target) == 1)
    target = target[0]
    writer_token = None
    require(target["bucketType"] == "allPrivate")
    lock = target["fileLockConfiguration"]
    require(
        lock["isClientAuthorizedToRead"] is True
        and lock["value"]["isFileLockEnabled"] is False
    )
    rules = target["lifecycleRules"]
    require(type(rules) is list and len(rules) == 1)
    rule = rules[0]
    require(
        rule["fileNamePrefix"] == ""
        and rule.get("daysFromHidingToDeleting") == 1
        and rule.get("daysFromUploadingToHiding") is None
        and rule.get("daysFromStartingToCancelingUnfinishedLargeFiles") is None
    )
    totals = {
        "visible_bytes": 0,
        "hidden_bytes": 0,
        "unfinished_bytes": 0,
        "other_bytes": 0,
    }
    for bucket in buckets:
        bid = text(bucket["bucketId"])
        cursor = None
        seen_cursors, seen_files = set(), set()
        prior_name = None
        while True:
            body = {"bucketId": bid, "maxFileCount": 1000}
            if cursor:
                body.update(startFileName=cursor[0], startFileId=cursor[1])
            page = api.call(base, "b2_list_file_versions", body, token)
            require(type(page["files"]) is list and len(page["files"]) <= 1000)
            for f in page["files"]:
                require(f["bucketId"] == bid and f["accountId"] == account)
                name, fid = text(f["fileName"]), text(f["fileId"])
                require(
                    fid not in seen_files and (prior_name is None or name >= prior_name)
                )
                seen_files.add(fid)
                first = name != prior_name
                prior_name = name
                action, size = f["action"], integer(f["contentLength"])
                require(action in {"upload", "hide", "start"})
                require(action == "upload" or size == 0)
                if action == "upload":
                    kind = (
                        "other_bytes"
                        if bid != target["bucketId"] or not name.startswith("prod/")
                        else ("visible_bytes" if first else "hidden_bytes")
                    )
                    totals[kind] += size
            nf, ni = page["nextFileName"], page["nextFileId"]
            require((nf is None) == (ni is None))
            if nf is None:
                break
            cursor = (text(nf), text(ni))
            require(cursor not in seen_cursors)
            seen_cursors.add(cursor)
        cursor, seen_cursors, unfinished = None, set(), set()
        while True:
            body = {"bucketId": bid, "maxFileCount": 100}
            if cursor:
                body["startFileId"] = cursor
            page = api.call(base, "b2_list_unfinished_large_files", body, token)
            require(type(page["files"]) is list and len(page["files"]) <= 100)
            for f in page["files"]:
                require(
                    f["bucketId"] == bid
                    and f["accountId"] == account
                    and f["action"] == "start"
                )
                fid = text(f["fileId"])
                # Native list_parts requires writeFiles. Never grant that to
                # all-account inventory: reuse only the existing Birja writer.
                # Unknown parts outside this repository block before upload.
                require(
                    bid == target["bucketId"]
                    and text(f["fileName"]).startswith("prod/")
                )
                if writer_token is None:
                    key = text(
                        backup.private_file(c["access_key_file"]).read_text().strip()
                    )
                    secret = text(
                        backup.private_file(c["secret_key_file"]).read_text().strip()
                    )
                    writer = api.call(
                        "https://api.backblazeb2.com",
                        "b2_authorize_account",
                        {},
                        "Basic "
                        + base64.b64encode((key + ":" + secret).encode()).decode(),
                    )
                    ws = writer["apiInfo"]["storageApi"]
                    wa = ws["allowed"]
                    require(
                        writer["accountId"] == account
                        and ws["apiUrl"] == base
                        and ws["s3ApiUrl"] == ENDPOINT
                    )
                    require(
                        wa["buckets"]
                        == [{"id": target["bucketId"], "name": "Birja-backup"}]
                        and wa["namePrefix"] in [None, "prod/"]
                        and "writeFiles" in wa["capabilities"]
                    )
                    writer_token = text(writer["authorizationToken"])
                require(fid not in unfinished)
                unfinished.add(fid)
                part_cursor, seen_parts = 1, set()
                while True:
                    parts = api.call(
                        base,
                        "b2_list_parts",
                        {
                            "fileId": fid,
                            "startPartNumber": part_cursor,
                            "maxPartCount": 1000,
                        },
                        writer_token,
                    )
                    require(
                        type(parts["parts"]) is list and len(parts["parts"]) <= 1000
                    )
                    for part in parts["parts"]:
                        number = integer(part["partNumber"])
                        require(
                            part["fileId"] == fid
                            and number >= part_cursor
                            and number not in seen_parts
                        )
                        seen_parts.add(number)
                        totals["unfinished_bytes"] += integer(part["contentLength"])
                    next_part = parts["nextPartNumber"]
                    if next_part is None:
                        break
                    require(integer(next_part) > part_cursor)
                    part_cursor = next_part
            cursor = page["nextFileId"]
            if cursor is None:
                break
            text(cursor)
            require(cursor not in seen_cursors)
            seen_cursors.add(cursor)
    return totals


def refresh(c):
    q = dict(c["quota"])
    if c["_synthetic"]:
        repo = Path(c["repository"])
        require(repo.is_dir() and not repo.is_symlink())
        files = list(repo.rglob("*"))
        require(len(files) <= 100000 and all(not p.is_symlink() for p in files))
        q.update(
            visible_bytes=sum(p.stat().st_size for p in files if p.is_file()),
            hidden_bytes=0,
            unfinished_bytes=0,
            other_bytes=0,
        )
    else:
        a = controls(c)
        q.update(inventory(c, a))
        # Existing schema names are retained for compatibility; these are local
        # limits. Provider bills/caps/download allowance are NOT API observations.
        q.update(
            storage_limit_bytes=10_000_000_000,
            upload_reserve_bytes=max(
                c["max_stage_bytes"] * 2, c["timeout_seconds"] * 1024 * 1024 * 2
            ),
            repack_reserve_bytes=c["max_stage_bytes"],
            download_remaining_bytes=a["local_download_budget_bytes"],
            request_remaining=a["local_request_budget"],
            request_reserve=1,
            free_controls_verified=True,
            dedicated_repository=True,
        )
    q["observed_at"] = int(time.time())
    require(
        sum(
            q[k]
            for k in [
                "visible_bytes",
                "hidden_bytes",
                "unfinished_bytes",
                "other_bytes",
                "upload_reserve_bytes",
                "repack_reserve_bytes",
            ]
        )
        <= q["storage_limit_bytes"]
    )
    return q


def main(args):
    try:
        c = backup.load_config(args)
        job = backup.Job(c)
        job.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        backup.private_dir(job.state)
        with job.lock() as lock:
            backup.atomic(
                job.state / "last-attempt.json",
                {"ok": False, "step": "quota-preflight", "utc": backup.utc()},
            )
            c["quota"] = refresh(c)
            path = Path(args[1]) if args else Path("/etc/birja/backup.env")
            backup.atomic(path, {k: v for k, v in c.items() if not k.startswith("_")})
            previous = os.environ.get("BIRJA_BACKUP_LOCK_FD")
            os.environ["BIRJA_BACKUP_LOCK_FD"] = str(lock.fileno())
            try:
                return backup.main(["backup", *args], config=c)
            finally:
                if previous is None:
                    os.environ.pop("BIRJA_BACKUP_LOCK_FD", None)
                else:
                    os.environ["BIRJA_BACKUP_LOCK_FD"] = previous
    except Exception:  # noqa: BLE001 - never disclose provider/private diagnostics
        print("quota_preflight=false")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
