#!/usr/bin/env python3
"""Independent synthetic PG18 fixture; never imports application test fixtures."""
import importlib.util
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("recovery", ROOT / "deploy/verify-restore.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def smoke():
    dc = r.compose()
    try:
        r.call(dc + ["up", "-d", "--wait"], timeout=120)
        r.check_running(dc)
        assert r.sql(dc, "SHOW server_version;", "birja_ops_test").startswith(b"18.6")
        print("isolated_pg18=true")
    finally:
        r.call(dc + ["down", "-v", "--remove-orphans"], timeout=60)


if __name__ == "__main__":
    os.umask(0o077)
    if sys.argv[1:] != ["--smoke"]:
        raise SystemExit("unsupported test selection")
    smoke()
