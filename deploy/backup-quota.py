#!/usr/bin/env python3
"""Nightly preflight callable seam for the behavioral RED gate."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("backup", Path(__file__).with_name("backup-snapshot.py"))
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def refresh(c):
    return c["quota"]


def main(args):
    return backup.main(["backup", *args])
