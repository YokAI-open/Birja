#!/usr/bin/env python3
"""Capture actual Phase13/14 UI with explicit inert source-bound evidence families."""

import argparse
import hashlib
import html
import json
import math
import os
import re
import stat
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


def source_directory(path):
    """Open every ancestor without following links, including the render root."""
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.absolute().parts[1:]:
            child = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
        return descriptor
    except OSError as error:
        os.close(descriptor)
        raise ValueError("Unsafe render directory") from error


def source_files(path, recursive=False, optional=False):
    """Inspect links before exclusions/filtering; never traverse a linked target."""
    result = []

    def visit(descriptor, directory):
        for entry in sorted(os.scandir(descriptor), key=lambda item: item.name):
            mode = entry.stat(follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode):
                raise ValueError("Linked render input")
            current = directory / entry.name
            if stat.S_ISDIR(mode):
                if recursive and entry.name != "__pycache__":
                    child = os.open(
                        entry.name,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=descriptor,
                    )
                    try:
                        visit(child, current)
                    finally:
                        os.close(child)
            elif stat.S_ISREG(mode):
                result.append(current)
            else:
                raise ValueError("Unsupported render input")

    try:
        descriptor = source_directory(path)
    except ValueError as error:
        if optional and isinstance(error.__cause__, FileNotFoundError):
            return []
        raise
    try:
        visit(descriptor, path)
    except OSError as error:
        raise ValueError("Unsafe render traversal") from error
    finally:
        os.close(descriptor)
    return result


def source_bytes(path):
    descriptor = source_directory(path.parent)
    try:
        child = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        with os.fdopen(child, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError("Nonregular render input")
            return source.read()
    except OSError as error:
        raise ValueError("Unsafe render file") from error
    finally:
        os.close(descriptor)


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
            source_files(
                ROOT / name, recursive=True, optional=name == "frontend/public"
            )
        )
    paths.update(
        p
        for p in source_files(
            ROOT / "frontend/node_modules/@fontsource-variable/inter/files"
        )
        if p.suffix == ".woff2"
    )
    paths.update(
        p
        for p in source_files(ROOT / "frontend/node_modules/@fontsource-variable/inter")
        if p.suffix == ".css"
    )
    paths.update(
        p
        for p in source_files(ROOT / "frontend")
        if p.name.startswith("tsconfig") and p.suffix == ".json"
    )
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
    return {
        p.relative_to(ROOT).as_posix(): digest(source_bytes(p)) for p in sorted(paths)
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
    validate_html((directory / "index.html").read_text(), phase=phase)
    for capture in manifest["captures"]:
        paths = capture_artifacts(capture["width"], capture["state"], phase)
        content = (directory / paths["html"]).read_text()
        validate_html(content, phase=phase)
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


class TrustedPolicyPrefix:
    """Finite generated-prefix grammar, before the browser's effective policy."""

    def __init__(self):
        self.state = "initial"

    def accept(self, event, value="", attributes=()):
        attrs = dict(attributes)
        policy = (
            event == "start"
            and value == "meta"
            and any(
                key == "http-equiv"
                and (item or "").lower() == "content-security-policy"
                for key, item in attributes
            )
        )
        if self.state == "complete":
            if policy:
                raise ValueError("Duplicate project capture policy")
            return
        if event == "data" and all(character in "\t\n\f\r " for character in value):
            return
        if (
            event == "declaration"
            and self.state == "initial"
            and value.lower() == "doctype html"
        ):
            self.state = "doctype"
            return
        if event == "start":
            if policy and self.state in {
                "doctype",
                "head",
                "head-charset",
                "implicit-head",
            }:
                if (
                    len(attributes) != 2
                    or set(attrs) != {"http-equiv", "content"}
                    or not isinstance(attrs.get("content"), str)
                ):
                    raise ValueError("Malformed project capture policy")
                clauses = [
                    item.strip("\t\n\f\r ")
                    for item in attrs.get("content", "").split(";")
                ]
                directives = [
                    re.split(r"[\t\n\f\r ]+", item) for item in clauses if item
                ]
                required = {
                    "default-src": ["'none'"],
                    "style-src": ["'unsafe-inline'"],
                    "font-src": ["data:"],
                    "img-src": ["data:"],
                    "base-uri": ["'none'"],
                    "form-action": ["'none'"],
                }
                if (
                    len(directives) != len(required)
                    or {item[0]: item[1:] for item in directives} != required
                ):
                    raise ValueError("Altered project capture policy")
                self.state = "complete"
                return
            if (
                self.state == "doctype"
                and value == "html"
                and list(attributes) in ([], [("lang", "en")])
            ):
                self.state = "html"
                return
            if self.state == "html" and value == "head" and not attributes:
                self.state = "head"
                return
            if (
                self.state in {"doctype", "head"}
                and value == "meta"
                and len(attributes) == 1
                and set(attrs) == {"charset"}
                and (attrs["charset"] or "").lower() == "utf-8"
            ):
                self.state = (
                    "implicit-head" if self.state == "doctype" else "head-charset"
                )
                return
        raise ValueError("Unsupported event in trusted policy prefix")


class InertCaptureParser(HTMLParser):
    def __init__(self, phase=13):
        super().__init__(convert_charrefs=False)
        self.phase = phase
        self.svg_depth = 0
        self.prefix = TrustedPolicyPrefix() if phase == 14 else None

    def prefix_event(self, event, value="", attributes=()):
        if self.prefix is not None:
            self.prefix.accept(event, value, attributes)

    def handle_starttag(self, tag, attributes):
        self.prefix_event("start", tag, attributes)
        if tag == "svg":
            self.svg_depth += 1
        if (
            self.svg_depth and tag not in {"svg", "path", "circle", "line"}
        ) or ":" in tag:
            raise ValueError("Unsupported SVG vocabulary")
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

    def handle_endtag(self, tag):
        self.prefix_event("end", tag)
        if tag == "svg":
            self.svg_depth = max(0, self.svg_depth - 1)

    def handle_data(self, data):
        self.prefix_event("data", data)

    def handle_startendtag(self, tag, attributes):
        self.prefix_event("startend", tag, attributes)
        self.handle_starttag(tag, attributes)
        self.handle_endtag(tag)

    def handle_decl(self, declaration):
        self.prefix_event("declaration", declaration)

    def unknown_decl(self, declaration):
        self.prefix_event("unknown-declaration", declaration)

    def handle_comment(self, comment):
        self.prefix_event("comment", comment)

    def handle_pi(self, instruction):
        self.prefix_event("processing-instruction", instruction)

    def handle_entityref(self, name):
        self.prefix_event("entity", name)

    def handle_charref(self, name):
        self.prefix_event("character-reference", name)


def validate_html(content, phase=13):
    phase_states(phase)
    if re.search(r"bj_(?:access|refresh|csrf)\s*=", content, re.IGNORECASE):
        raise ValueError("Private capture")
    parser = InertCaptureParser(phase)
    parser.feed(content)
    parser.close()
    if phase == 14 and parser.prefix.state != "complete":
        raise ValueError("Missing project capture policy")


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
            validate_html(text, phase=phase)
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
