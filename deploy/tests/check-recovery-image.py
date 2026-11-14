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
        existing = subprocess.run(
            ["/usr/bin/docker", "image", "inspect", r.RECOVERY_IMAGE],
            capture_output=True, env=r.ENV, check=False, timeout=30,
        )
        if existing.returncode == 0:
            # Authenticate an existing alias rather than silently repairing a
            # tag that points at an unrelated image.
            r.loaded_recovery_image()
        # A registry pull/verification alone does not create Compose's fixed
        # recovery alias on a fresh runner. Import only the authenticated export
        # and bind its exact config/platform identity before any recovery test.
        saved.seek(0)
        subprocess.run(
            ["/usr/bin/docker", "image", "load"],
            stdin=saved,
            stdout=subprocess.DEVNULL,
            env=r.ENV,
            check=True,
            timeout=120,
        )
        r.bind_recovery_image()
    print("recovery_image_store_containerd=true strict_saved_image_verified=true")


if __name__ == "__main__":
    main()
