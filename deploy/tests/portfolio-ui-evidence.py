#!/usr/bin/env python3
"""Capture actual Phase13/14 UI with explicit inert source-bound evidence families."""

import argparse
import hashlib
import html
import json
import math
import os
import re
import struct
import subprocess
import tempfile
import zipfile
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WIDTHS = (320, 375, 768, 1024, 1280, 1440)
STATES = (
    "overview",
    "create-long-astral",
    "keyboard-error-focus",
    "unknown",
    "edit",
    "stale-draft",
    "switch",
    "incomplete",
    "failed-refresh",
    "cap",
    "empty",
    "error",
)
PHASE14_STATES = (
    "collapsed",
    "confirmation",
    "last-confirmation",
    "cancel",
    "confirmation-long",
    "uncertain-stock",
    "rename-conflict",
    "submitting",
    "consistency-refusal",
    "retry-waiting",
    "checking",
    "confirmed-overview",
    "discovery-error",
    "stale-unavailable",
    "unknown",
    "restored-unknown",
    "cross-tab",
    "stale-unresolved-order",
    "empty",
)


def phase_states(phase):
    if type(phase) is not int or phase not in (13, 14):
        raise ValueError("Unknown evidence family")
    return STATES if phase == 13 else PHASE14_STATES


HASH = re.compile(r"^[0-9a-f]{64}$")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def source_snapshot():
    paths = set()
    for name in (
        "frontend/src",
        "frontend/e2e",
        "frontend/public",
        "backend/app",
        "backend/alembic",
    ):
        paths.update(
            p
            for p in (ROOT / name).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        )
    paths.update(
        (ROOT / "frontend/node_modules/@fontsource-variable/inter/files").glob(
            "*.woff2"
        )
    )
    paths.update(
        (ROOT / "frontend/node_modules/@fontsource-variable/inter").glob("*.css")
    )
    paths.update((ROOT / "frontend").glob("tsconfig*.json"))
    for name in (
        "frontend/index.html",
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/vite.config.ts",
        "frontend/playwright.config.ts",
        "frontend/components.json",
        "frontend/Dockerfile",
        "backend/Dockerfile",
        "backend/uv.lock",
        "backend/pyproject.toml",
        "backend/alembic.ini",
        "frontend/.dockerignore",
        "backend/.dockerignore",
        "frontend/.nvmrc",
        "docker-compose.yml",
        "deploy/tests/run-stock-browser.py",
        "deploy/tests/portfolio-ui-evidence.py",
        "deploy/tests/test-portfolio-ui-evidence.py",
    ):
        paths.add(ROOT / name)
    if any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValueError("Unsafe render input")
    return {
        p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(paths)
    }


def input_digest(source):
    return digest(json.dumps(source, sort_keys=True, separators=(",", ":")).encode())


def capture_artifacts(width, state, phase=13):
    stem = f"phase{phase}-{state}-{width}"
    return {
        "html": stem + ".html",
        "png": stem + ".png",
        "trace": stem + ".trace.json",
        **({"reflow_png": stem + ".reflow.png"} if width >= 768 else {}),
    }


def required_artifacts(phase=13):
    """Source-owned inventory; a manifest cannot choose which proof to omit."""
    return {"index.html"} | {
        name
        for width in WIDTHS
        for state in phase_states(phase)
        for name in capture_artifacts(width, state, phase).values()
    }


def contract_example(phase=13):
    """Independent schema specimen for offline negative tests, never a receipt."""
    source = {"frontend/src/App.tsx": "a" * 64}
    return {
        "format": 1,
        "phase": phase,
        "synthetic": True,
        "source_sha256": source,
        "git_commit": "a" * 40,
        "render_inputs_sha256": input_digest(source),
        "native_200_percent_verified": False,
        "owner_accepted": False,
        "artifacts": {name: "a" * 64 for name in required_artifacts(phase)},
        "captures": [
            {
                "state": state,
                "width": width,
                "browser": "chromium",
                "browser_version": "1.2.3",
                "scope": "a" * 64,
                "artifacts": capture_artifacts(width, state, phase),
                "render_inputs_sha256": input_digest(source),
                **(
                    {
                        "layout": {
                            "viewport": width,
                            "action_count": 1,
                            "h1_count": 1,
                            "no_horizontal_overflow": True,
                            **(
                                {
                                    "reflow": {
                                        "viewport": width // 2,
                                        "action_count": 1,
                                        "h1_count": 1,
                                        "no_horizontal_overflow": True,
                                    }
                                }
                                if width >= 768
                                else {}
                            ),
                        }
                    }
                    if phase == 14
                    else {}
                ),
            }
            for width in WIDTHS
            for state in phase_states(phase)
        ],
    }


def validate_manifest(value, *, source=None, phase=13):
    phase_states(phase)
    if (
        not isinstance(value, dict)
        or type(value.get("format")) is not int
        or value.get("format") != 1
        or type(value.get("phase")) is not int
        or value.get("phase") != phase
        or not isinstance(value.get("git_commit"), str)
        or re.fullmatch(r"[0-9a-f]{40}", value["git_commit"]) is None
    ):
        raise ValueError("Unknown evidence format")
    if (
        value.get("synthetic") is not True
        or value.get("native_200_percent_verified") is not False
        or value.get("owner_accepted") is not False
    ):
        raise ValueError("Separate owner/native200 gates must remain pending")
    sources = value.get("source_sha256")
    if (
        not isinstance(sources, dict)
        or not sources
        or any(
            not isinstance(k, str)
            or k.startswith("/")
            or ".." in Path(k).parts
            or not isinstance(v, str)
            or not HASH.fullmatch(v)
            for k, v in sources.items()
        )
    ):
        raise ValueError("Malformed source hashes")
    if source is not None and sources != source:
        raise ValueError("Source drift")
    bound = input_digest(sources)
    if value.get("render_inputs_sha256") != bound:
        raise ValueError("Render input mismatch")
    artifacts = value.get("artifacts")
    if (
        not isinstance(artifacts, dict)
        or set(artifacts) != required_artifacts(phase)
        or any(
            not isinstance(checksum, str) or not HASH.fullmatch(checksum)
            for checksum in artifacts.values()
        )
    ):
        raise ValueError("Incomplete or unexpected artifact inventory")
    captures = value.get("captures")
    if not isinstance(captures, list) or len(captures) != len(WIDTHS) * len(
        phase_states(phase)
    ):
        raise ValueError("Incomplete capture matrix")
    found, scopes, browsers = set(), {}, set()
    for capture in captures:
        if not isinstance(capture, dict):
            raise ValueError("Malformed capture")
        width, state = capture.get("width"), capture.get("state")
        if (
            width not in WIDTHS
            or state not in phase_states(phase)
            or (width, state) in found
        ):
            raise ValueError("Unexpected or duplicate capture")
        if capture.get("artifacts") != capture_artifacts(width, state, phase):
            raise ValueError("Capture paths do not match its required state/width")
        found.add((width, state))
        if phase == 14:
            validate_layout(capture.get("layout"), width)
            if width >= 768:
                validate_layout(capture["layout"].get("reflow"), width // 2)
        scope = capture.get("scope")
        if (
            not isinstance(scope, str)
            or not HASH.fullmatch(scope)
            or scopes.setdefault(width, scope) != scope
        ):
            raise ValueError("Crossed owner capture")
        if (
            capture.get("browser") != "chromium"
            or not isinstance(capture.get("browser_version"), str)
            or not re.fullmatch(r"\d+(?:\.\d+){1,4}", capture["browser_version"])
        ):
            raise ValueError("Missing browser provenance")
        browsers.add((capture["browser"], capture["browser_version"]))
        if capture.get("render_inputs_sha256") != bound:
            raise ValueError("Stale render capture")
    if len(browsers) != 1:
        raise ValueError("Mixed browser provenance")


def verify_artifacts(directory, hashes, phase=13):
    expected_names = required_artifacts(phase)
    if not isinstance(hashes, dict) or set(hashes) != expected_names:
        raise ValueError("Incomplete or unexpected required artifacts")
    if (
        directory.is_symlink()
        or not directory.is_dir()
        or {p.name for p in directory.iterdir()} != expected_names | {"manifest.json"}
    ):
        raise ValueError("Missing or unexpected on-disk evidence")
    for name in expected_names | {"manifest.json"}:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Unsafe evidence member: " + name)
    manifest = json.loads((directory / "manifest.json").read_text())
    validate_manifest(manifest, phase=phase)
    if manifest["artifacts"] != hashes:
        raise ValueError("Manifest artifact map mismatch")
    for name, expected in hashes.items():
        if (
            not isinstance(expected, str)
            or not HASH.fullmatch(expected)
            or digest((directory / name).read_bytes()) != expected
        ):
            raise ValueError("Missing/unsafe/tampered artifact: " + name)
    validate_html((directory / "index.html").read_text())
    for capture in manifest["captures"]:
        paths = capture_artifacts(capture["width"], capture["state"], phase)
        content = (directory / paths["html"]).read_text()
        validate_html(content)
        metadata = capture_metadata(content)
        verify_capture_metadata(metadata, capture, manifest["git_commit"], phase)
        if phase == 14:
            verify_png(directory / paths["png"], capture["width"])
            if capture["width"] >= 768:
                verify_png(directory / paths["reflow_png"], capture["width"] // 2)
        if json.loads((directory / paths["trace"]).read_text()) != metadata.get(
            "trace"
        ):
            raise ValueError("Timing trace does not correspond to its capture")


def capture_metadata(content):
    matches = re.findall(r'<meta name="birja-evidence" content="([^"]+)">', content)
    if len(matches) != 1:
        raise ValueError("Missing or duplicate browser capture metadata")
    value = json.loads(html.unescape(matches[0]))
    if not isinstance(value, dict):
        raise ValueError("Malformed browser capture metadata")
    return value


def verify_capture_metadata(metadata, capture, commit, phase=13):
    expected = {
        "phase": phase,
        "state": capture["state"],
        "width": capture["width"],
        "source": commit,
        "synthetic": True,
        "native_200_percent_verified": False,
        "browser": capture["browser"],
        "version": capture["browser_version"],
        "scope": capture["scope"],
        "artifacts": capture_artifacts(capture["width"], capture["state"], phase),
    }
    if phase == 14:
        expected["owner_accepted"] = False
        if set(metadata) != set(expected) | {"trace", "layout"}:
            raise ValueError("Unexpected capture metadata")
    if any(
        metadata.get(key) != value for key, value in expected.items()
    ) or not isinstance(metadata.get("trace"), list):
        raise ValueError("Capture metadata/source/path correspondence mismatch")
    if phase == 14 and metadata.get("layout") != capture.get("layout"):
        raise ValueError("Layout capture correspondence mismatch")
    for event in metadata["trace"]:
        if (
            not isinstance(event, dict)
            or set(event) != {"path", "start", "duration"}
            or not isinstance(event["path"], str)
            or not event["path"].startswith("/")
            or "?" in event["path"]
            or "#" in event["path"]
            or any(
                type(event[k]) not in (int, float)
                or not math.isfinite(event[k])
                or event[k] < 0
                for k in ("start", "duration")
            )
        ):
            raise ValueError("Unsafe credential-free timing evidence")


class InertCaptureParser(HTMLParser):
    def handle_starttag(self, tag, attributes):
        if tag in {
            "script",
            "form",
            "iframe",
            "object",
            "embed",
            "base",
            "frame",
            "frameset",
            "portal",
            "link",
        }:
            raise ValueError("Active capture element")
        for key, value in attributes:
            if key.startswith("on"):
                raise ValueError("Active capture handler")
            if (
                tag == "meta"
                and key == "http-equiv"
                and (value or "").lower() == "refresh"
            ):
                raise ValueError("Active capture refresh")
            if key in {
                "src",
                "href",
                "xlink:href",
                "action",
                "formaction",
                "poster",
                "data",
                "srcset",
            }:
                normalized = re.sub(r"[\x00-\x20]+", "", value or "").lower()
                if normalized.startswith(
                    (
                        "http:",
                        "https:",
                        "//",
                        "javascript:",
                        "vbscript:",
                        "data:text/html",
                    )
                ) or re.search(r",(?:https?:|//)", normalized):
                    raise ValueError("External or active capture resource")


def validate_html(content):
    if re.search(r"bj_(?:access|refresh|csrf)\s*=", content, re.IGNORECASE):
        raise ValueError("Private capture")
    parser = InertCaptureParser(convert_charrefs=True)
    parser.feed(content)
    parser.close()


def validate_layout(layout, width):
    if (
        not isinstance(layout, dict)
        or layout.get("viewport") != width
        or layout.get("h1_count") != 1
        or layout.get("no_horizontal_overflow") is not True
        or type(layout.get("action_count")) is not int
        or layout["action_count"] < 0
    ):
        raise ValueError("Missing actual layout evidence")


def verify_png(path, width):
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Malformed screenshot")
    actual_width, height = struct.unpack(">II", data[16:24])
    if actual_width != width or height < 1 or height > 65535:
        raise ValueError("Screenshot does not match its viewport")


def package(captured, destination, source, commit, phase=13):
    if source_snapshot() != source:
        raise ValueError("Source changed during actual browser run")
    if (
        destination.exists()
        or destination.is_symlink()
        or destination.with_suffix(".zip").exists()
    ):
        raise ValueError("Review destination already exists; preserve old packets")
    destination.mkdir(mode=0o700)
    bound, captures = input_digest(source), []
    for width in WIDTHS:
        for state in phase_states(phase):
            stem = f"phase{phase}-{state}-{width}"
            text = (captured / (stem + ".html")).read_text()
            validate_html(text)
            metadata = capture_metadata(text)
            capture = {
                "state": state,
                "width": width,
                "browser": metadata["browser"],
                "browser_version": metadata["version"],
                "scope": metadata["scope"],
                "render_inputs_sha256": bound,
                "artifacts": capture_artifacts(width, state, phase),
                "layout": metadata.get("layout", {}),
            }
            verify_capture_metadata(metadata, capture, commit, phase)
            captures.append(capture)
            for suffix in (".html", ".png"):
                path = captured / (stem + suffix)
                if path.is_symlink() or not path.is_file():
                    raise ValueError("Missing actual browser artifact")
                (destination / path.name).write_bytes(path.read_bytes())
            if width >= 768:
                reflow = captured / (stem + ".reflow.png")
                if reflow.is_symlink() or not reflow.is_file():
                    raise ValueError("Missing actual narrow reflow screenshot")
                (destination / reflow.name).write_bytes(reflow.read_bytes())
            # Only allowlisted actual performance events, without request bodies,
            # headers, cookies, query strings, keys or private session storage.
            (destination / (stem + ".trace.json")).write_text(
                json.dumps(metadata["trace"], indent=2)
            )
    manifest = {
        "format": 1,
        "phase": phase,
        "synthetic": True,
        "git_commit": commit,
        "captured_at": datetime.now(UTC).isoformat(),
        "source_sha256": source,
        "render_inputs_sha256": bound,
        "native_200_percent_verified": False,
        "owner_accepted": False,
        "captures": captures,
    }
    links = "".join(
        f'<li><a href="phase{phase}-{state}-{width}.html">{state} at {width}px</a> · <a href="phase{phase}-{state}-{width}.png">screenshot</a></li>'
        for width in WIDTHS
        for state in phase_states(phase)
    )
    (destination / "index.html").write_text(
        f"""<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src data:; img-src data:; base-uri 'none'; form-action 'none'"><title>Phase{phase} UI review</title><h1>Phase{phase} synthetic UI review</h1><p>Actual rendered read-only application states. Source hashes, browser version and credential-free timing traces are in manifest.json. CSS and fonts are embedded. Owner UI acceptance and genuine desktop browser-menu 200% acceptance remain pending separately; viewport reflow is automated evidence only. Download and extract the entire ZIP, open this index, and use your browser Zoom menu.</p><ul>"""
        + links
        + "</ul>"
    )
    manifest["artifacts"] = {
        p.name: digest(p.read_bytes()) for p in sorted(destination.iterdir())
    }
    validate_manifest(manifest, source=source, phase=phase)
    (destination / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2)
    )
    verify_artifacts(destination, manifest["artifacts"], phase)
    archive = destination.with_suffix(".zip")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(destination.iterdir()):
            output.write(path, path.name)
            path.chmod(0o400)
    destination.chmod(0o500)
    print(
        json.dumps(
            {
                "review": str(archive),
                "sha256": digest(archive.read_bytes()),
                "render_inputs_sha256": bound,
                "captures": len(captures),
                "artifacts": len(manifest["artifacts"]),
                "native_200_percent_verified": False,
            },
            sort_keys=True,
        )
    )


def require_committed_inputs(source):
    tracked = set(
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    paths = [name for name in source if not name.startswith("frontend/node_modules/")]
    if any(name not in tracked for name in paths):
        raise ValueError("Commit render inputs before actual capture")
    if subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "--", *paths], cwd=ROOT
    ):
        raise ValueError("Commit render inputs before actual capture")


def verify_zip(directory, phase=13):
    archive = directory.with_suffix(".zip")
    if archive.is_symlink() or not archive.is_file():
        raise ValueError("Missing or unsafe review archive")
    expected = required_artifacts(phase) | {"manifest.json"}
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        if len(members) != len(expected) or {v.filename for v in members} != expected:
            raise ValueError("Incomplete or unexpected ZIP inventory")
        for member in members:
            if member.is_dir() or (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsafe archive member")
            if member.file_size != (directory / member.filename).stat().st_size:
                raise ValueError("Archive size differs from verified member")
            if bundle.read(member) != (directory / member.filename).read_bytes():
                raise ValueError("Archive differs from verified review directory")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        type=int,
        choices=(13, 14),
        default=13,
        help="Explicit independently inventoried evidence family",
    )
    parser.add_argument(
        "--output", type=Path, help="Exclusive new /tmp review directory"
    )
    parser.add_argument(
        "--verify",
        type=Path,
        help="Verify existing bundle directory against current render inputs",
    )
    args = parser.parse_args()
    os.umask(0o077)
    if args.verify:
        if args.output:
            parser.error("--verify does not create or replace output")
        value = json.loads((args.verify / "manifest.json").read_text())
        validate_manifest(value, source=source_snapshot(), phase=args.phase)
        verify_artifacts(args.verify, value["artifacts"], args.phase)
        verify_zip(args.verify, args.phase)
        print("CURRENT SOURCE AND ARTIFACTS VERIFIED")
        return
    destination = args.output or Path(f"/tmp/birja-phase{args.phase}-ui-review")
    family = f"birja-phase{args.phase}-ui-review"
    if (
        destination.parent != Path("/tmp")
        or not re.fullmatch(
            re.escape(family) + r"(?:-[a-zA-Z0-9_-]+)?", destination.name
        )
        or destination.is_symlink()
    ):
        raise ValueError("Expected an exclusive synthetic evidence destination")
    if destination.exists() or destination.with_suffix(".zip").exists():
        raise ValueError("Preserve existing evidence packets before recapture")
    source = source_snapshot()
    require_committed_inputs(source)
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    prefix = (
        "birja-phase14-ui-capture-"
        if args.phase == 14
        else "birja-phase12-ui-review-p13-"
    )
    captured = Path(tempfile.mkdtemp(prefix=prefix))
    captured.rmdir()
    selector = "Phase14 deletion capture" if args.phase == 14 else "Phase13"
    subprocess.run(
        [
            "python3",
            str(ROOT / "deploy/tests/run-stock-browser.py"),
            "--suite",
            "portfolios",
            "--grep",
            selector,
            "--review-dir",
            str(captured),
        ],
        cwd=ROOT,
        check=True,
    )
    package(captured, destination, source, commit, args.phase)
    verify_zip(destination, args.phase)


if __name__ == "__main__":
    main()
