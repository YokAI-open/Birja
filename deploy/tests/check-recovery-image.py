#!/usr/bin/env python3
"""Check the CI image store and public export with the unchanged recovery guard."""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "recovery", ROOT / "deploy/verify-restore.py"
)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def main():
    driver = json.loads(
        r.call(["/usr/bin/docker", "info", "--format", "{{json .DriverStatus}}"])
    )
    r.require(["driver-type", "io.containerd.snapshotter.v1"] in driver)
    with tempfile.TemporaryFile() as saved:
        subprocess.run(
            [
                "/usr/bin/docker",
                "image",
                "save",
                "--platform",
                "linux/amd64",
                r.REGISTRY_REF,
            ],
            stdout=saved,
            env=r.ENV,
            check=True,
            timeout=120,
        )
        saved.seek(0)
        index, manifest = r.registry_manifests()
        r.verify_saved_image(saved, index, manifest)
    print("recovery_image_store_containerd=true strict_saved_image_verified=true")


if __name__ == "__main__":
    main()
