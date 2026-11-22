#!/usr/bin/env python3
"""Offline negative contracts; these are not browser execution receipts."""

import copy
import hashlib
import html
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).with_name("portfolio-ui-evidence.py")
EXPECTED_WIDTHS = (320, 375, 768, 1024, 1280, 1440)
PHASE14_POLICY = (
    '<meta http-equiv="Content-Security-Policy" content="'
    "default-src 'none'; style-src 'unsafe-inline'; font-src data:; "
    "img-src data:; base-uri 'none'; form-action 'none'\">"
)
EXPECTED_STATES = (
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


def expected_paths(width, state):
    stem = f"phase13-{state}-{width}"
    return {
        "html": stem + ".html",
        "png": stem + ".png",
        "trace": stem + ".trace.json",
        **({"reflow_png": stem + ".reflow.png"} if width >= 768 else {}),
    }


def required_names():
    return {"index.html"} | {
        name
        for width in EXPECTED_WIDTHS
        for state in EXPECTED_STATES
        for name in expected_paths(width, state).values()
    }


class EvidenceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("portfolio_ui_evidence", PATH)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def sample(self):
        return self.module.contract_example()

    def test_valid_complete_packet(self):
        self.module.validate_manifest(self.sample())

    def test_source_drift_refused(self):
        value = self.sample()
        with self.assertRaises(ValueError):
            self.module.validate_manifest(
                value, source={"frontend/src/App.tsx": "b" * 64}
            )

    def test_browser_version_and_width_refused(self):
        for field, replacement in [
            ("browser_version", ""),
            ("browser", "unknown"),
            ("width", 321),
        ]:
            value = self.sample()
            value["captures"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module.validate_manifest(value)

    def test_missing_duplicate_and_cross_owner_capture_refused(self):
        for operation in ("missing", "duplicate", "owner"):
            value = self.sample()
            if operation == "missing":
                value["captures"].pop()
            elif operation == "duplicate":
                value["captures"].append(copy.deepcopy(value["captures"][0]))
            else:
                value["captures"][1]["scope"] = "b" * 64
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.module.validate_manifest(value)

    def test_cannot_inherit_native_zoom_or_owner_approval(self):
        for field in ("native_200_percent_verified", "owner_accepted"):
            value = self.sample()
            value[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module.validate_manifest(value)

    def test_malformed_hash_and_render_input_mismatch_refused(self):
        for operation in ("hash", "render"):
            value = self.sample()
            value["captures"][0]["render_inputs_sha256"] = (
                "x" if operation == "hash" else "b" * 64
            )
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.module.validate_manifest(value)

    def packet(self, directory):
        """Offline schema fixture, independently enumerated; never a browser receipt."""
        value = self.sample()
        for capture in value["captures"]:
            width, state = capture["width"], capture["state"]
            capture["artifacts"] = expected_paths(width, state)
            metadata = {
                "phase": 13,
                "state": state,
                "width": width,
                "browser": "chromium",
                "version": "1.2.3",
                "scope": capture["scope"],
                "source": value["git_commit"],
                "synthetic": True,
                "native_200_percent_verified": False,
                "artifacts": expected_paths(width, state),
                "trace": [{"path": "/synthetic", "start": 1, "duration": 2}],
            }
            text = (
                '<!doctype html><meta name="birja-evidence" content="'
                + html.escape(json.dumps(metadata), quote=True)
                + '">'
            )
            for kind, name in expected_paths(width, state).items():
                (directory / name).write_text(
                    text
                    if kind == "html"
                    else json.dumps(metadata["trace"])
                    if kind == "trace"
                    else "offline-image-specimen"
                )
        (directory / "index.html").write_text(
            "<!doctype html>Offline contract specimen"
        )
        value["artifacts"] = {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for name in required_names()
        }
        self.write_manifest(directory, value)
        return value

    def write_manifest(self, directory, value):
        (directory / "manifest.json").write_text(json.dumps(value))

    def test_independent_required_matrix_and_complete_packet_control(self):
        self.assertEqual(len(required_names()), 265)
        self.assertEqual(
            {(c["width"], c["state"]) for c in self.sample()["captures"]},
            {(w, s) for w in EXPECTED_WIDTHS for s in EXPECTED_STATES},
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            value = self.packet(directory)
            self.module.validate_manifest(value)
            self.module.verify_artifacts(directory, value["artifacts"])

    def test_coherent_artifact_omission_cannot_qualify_metadata_only_evidence(self):
        for missing in (
            "phase13-unknown-1280.html",
            "phase13-unknown-1280.png",
            "phase13-unknown-1280.reflow.png",
            "phase13-unknown-1280.trace.json",
            "index.html",
        ):
            with (
                self.subTest(missing=missing),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                value = self.packet(directory)
                (directory / missing).unlink()
                del value["artifacts"][missing]
                for capture in value["captures"]:
                    capture["artifacts"] = {
                        k: n for k, n in capture["artifacts"].items() if n != missing
                    }
                # Coherently rewrite all remaining declarations and their hashes.
                for capture in value["captures"]:
                    page = (
                        directory
                        / expected_paths(capture["width"], capture["state"])["html"]
                    )
                    if page.exists():
                        text = page.read_text()
                        start = text.index('content="') + len('content="')
                        metadata = json.loads(html.unescape(text[start:-2]))
                        metadata["artifacts"] = capture["artifacts"]
                        page.write_text(
                            text[:start]
                            + html.escape(json.dumps(metadata), quote=True)
                            + '">'
                        )
                        value["artifacts"][page.name] = hashlib.sha256(
                            page.read_bytes()
                        ).hexdigest()
                value["render_inputs_sha256"] = self.module.input_digest(
                    value["source_sha256"]
                )
                self.write_manifest(directory, value)
                with self.assertRaises(ValueError):
                    self.module.verify_artifacts(directory, value["artifacts"])

    def test_extra_missing_tampered_symlink_traversal_and_manifest_refused(self):
        for operation in (
            "extra",
            "missing",
            "tampered",
            "symlink",
            "manifest-symlink",
            "manifest-missing",
            "traversal",
            "index-only",
        ):
            with (
                self.subTest(operation=operation),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                value = self.packet(directory)
                path = directory / "phase13-overview-320.html"
                if operation == "extra":
                    (directory / "extra.html").write_text("unexpected")
                elif operation == "tampered":
                    path.write_text("tampered")
                elif operation == "index-only":
                    value["artifacts"] = {
                        "index.html": value["artifacts"]["index.html"]
                    }
                    self.write_manifest(directory, value)
                elif operation == "traversal":
                    value["artifacts"]["../unsafe.html"] = "a" * 64
                    self.write_manifest(directory, value)
                else:
                    target = (
                        directory / "manifest.json"
                        if operation.startswith("manifest")
                        else path
                    )
                    target.unlink()
                    if "symlink" in operation:
                        target.symlink_to(PATH)
                with self.assertRaises(ValueError):
                    self.module.verify_artifacts(directory, value["artifacts"])

    def test_capture_paths_and_embedded_metadata_must_correspond(self):
        for operation in ("capture-path", "html-state", "trace-body"):
            with (
                self.subTest(operation=operation),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                value = self.packet(directory)
                if operation == "capture-path":
                    value["captures"][0]["artifacts"]["html"] = "phase13-cap-1440.html"
                else:
                    path = directory / (
                        "phase13-overview-320.html"
                        if operation == "html-state"
                        else "phase13-overview-320.trace.json"
                    )
                    text = path.read_text()
                    path.write_text(
                        text.replace("overview", "unknown")
                        if operation == "html-state"
                        else "[]"
                    )
                    value["artifacts"][path.name] = hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest()
                self.write_manifest(directory, value)
                with self.assertRaises(ValueError):
                    self.module.verify_artifacts(directory, value["artifacts"])

    def test_active_html_credentials_and_external_resources_refused(self):
        for content in (
            "<script>x</script>",
            "<form>x</form>",
            '<img src="https://bad.invalid/x">',
            "bj_access=secret",
        ):
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.module.validate_html(content)

    def test_render_inventory_includes_fonts_configuration_and_backend(self):
        sources = self.module.source_snapshot()
        for path in (
            "frontend/src/App.tsx",
            "frontend/index.html",
            "frontend/package-lock.json",
            "frontend/vite.config.ts",
            "frontend/tsconfig.app.json",
            "frontend/node_modules/@fontsource-variable/inter/index.css",
            "backend/app/services/portfolios.py",
            "frontend/e2e/portfolio-strategies.spec.ts",
            "deploy/tests/portfolio-ui-evidence.py",
        ):
            self.assertIn(path, sources)
        self.assertTrue(any(name.endswith(".woff2") for name in sources))


# This matrix is intentionally independent of production inventory helpers.
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


def phase14_paths(width, state):
    stem = f"phase14-{state}-{width}"
    return {
        "html": stem + ".html",
        "png": stem + ".png",
        "trace": stem + ".trace.json",
        **({"reflow_png": stem + ".reflow.png"} if width >= 768 else {}),
    }


def phase14_names():
    return {"index.html"} | {
        name
        for width in EXPECTED_WIDTHS
        for state in PHASE14_STATES
        for name in phase14_paths(width, state).values()
    }


class Phase14EvidenceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("phase14_ui_evidence", PATH)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def sample(self):
        return self.module.contract_example(14)

    def test_linked_render_roots_children_and_ancestors_refuse_before_read(self):
        from unittest.mock import patch

        original = self.module.source_snapshot()
        for linked in (
            "frontend/src",
            "frontend/src/linked",
            "frontend/public",
            "frontend",
            "frontend/node_modules/@fontsource-variable/inter",
            "frontend/node_modules/@fontsource-variable/inter/files/linked",
            "frontend/vite.config.ts",
        ):
            with (
                self.subTest(linked=linked),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary) / "checkout"
                for name in original:
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("ordinary controlled render input")
                target = root / linked
                outside = Path(temporary) / "controlled-target"
                if target.is_file():
                    outside.write_text("controlled config")
                    target.unlink()
                else:
                    import shutil

                    if target.exists():
                        shutil.move(str(target), str(outside))
                    else:
                        outside.mkdir()
                        (outside / "render.tsx").write_text("controlled render")
                target.symlink_to(outside, target_is_directory=outside.is_dir())
                with patch.object(self.module, "ROOT", root):
                    for _ in range(2):
                        with self.assertRaises(ValueError):
                            self.module.source_snapshot()
                        if outside.is_dir():
                            (outside / "render.tsx").write_text(
                                "changed controlled render"
                            )
                        else:
                            outside.write_text("changed controlled config")

    def test_ordinary_render_target_mutation_changes_inventory(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in self.module.source_snapshot():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("ordinary input")
            with patch.object(self.module, "ROOT", root):
                before = self.module.source_snapshot()
                target = root / "frontend/src/ordinary.tsx"
                target.write_text("ordinary first")
                first = self.module.source_snapshot()
                target.write_text("ordinary second")
                self.assertNotEqual(before, first)
                self.assertNotEqual(first, self.module.source_snapshot())
            alias = Path(temporary).with_name(Path(temporary).name + "-controlled-link")
            try:
                alias.symlink_to(root, target_is_directory=True)
                with (
                    patch.object(self.module, "ROOT", alias),
                    self.assertRaises(ValueError),
                ):
                    self.module.source_snapshot()
            finally:
                alias.unlink(missing_ok=True)

    def test_static_svg_and_early_owned_policy_only(self):
        policy = (
            '<meta http-equiv="Content-Security-Policy" content="'
            "default-src 'none'; style-src 'unsafe-inline'; font-src data:; "
            "img-src data:; base-uri 'none'; form-action 'none'\">"
        )
        icon = '<svg viewBox="0 0 24 24"><path d="M1 1L2 2"></path><circle cx="2" cy="2" r="1"/></svg>'
        positive = (
            "<!doctype html><html><head>"
            + policy
            + "</head><body>"
            + icon
            + "</body></html>"
        )
        self.module.validate_html(positive, phase=14)
        for content in (
            positive.replace(policy, ""),
            positive.replace("default-src 'none'", "default-src 'self'"),
            positive.replace(policy, policy + policy),
            positive.replace(policy, "").replace("<body>", "<body>" + policy),
            positive.replace(policy, "<style>p {color: black}</style>" + policy),
            positive.replace("<html>", '<html style="color: black">'),
            positive.replace("<head>", '<head style="color: black">'),
            positive.replace(policy, "").replace("</head>", "</head>" + policy),
            positive.replace(
                icon, '<svg><animate attributeName="opacity" values="0;1"/></svg>'
            ),
            positive.replace(
                icon, '<svg><set attributeName="visibility" to="hidden"/></svg>'
            ),
            positive.replace(
                icon, "<svg><foreignObject><p>ordinary text</p></foreignObject></svg>"
            ),
        ):
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.module.validate_html(content, phase=14)
        self.module.validate_html("<!doctype html><p>Phase 13 compatibility</p>")

    def test_coherent_index_and_capture_policy_mutations_refuse(self):
        for name in ("index.html", "phase14-collapsed-320.html"):
            for mutation in ("missing", "weakened", "duplicate", "unsupported-svg"):
                with (
                    self.subTest(name=name, mutation=mutation),
                    tempfile.TemporaryDirectory() as temporary,
                ):
                    directory = Path(temporary)
                    value = self.packet(directory)
                    target = directory / name
                    content = target.read_text()
                    if mutation == "missing":
                        content = content.replace(PHASE14_POLICY, "")
                    elif mutation == "weakened":
                        content = content.replace(
                            "default-src 'none'", "default-src 'self'"
                        )
                    elif mutation == "duplicate":
                        content = content.replace(PHASE14_POLICY, PHASE14_POLICY * 2)
                    else:
                        content += (
                            '<svg><animate attributeName="opacity" values="0;1"/></svg>'
                        )
                    target.write_text(content)
                    self.checksum(directory, value, name)
                    with self.assertRaises(ValueError):
                        self.module.verify_artifacts(directory, value["artifacts"], 14)

    def test_every_prepolicy_event_has_a_trusted_structural_prefix(self):
        prefixes = (
            "<!doctype html>",
            '<!doctype html><meta charset="utf-8">',
            '<!doctype html>\n<html lang="en"><head>',
            "<!doctype html>\t\n\f\r <html><head>",
        )
        for prefix in prefixes:
            self.module.validate_html(
                prefix + PHASE14_POLICY + "<p>ordinary</p>", phase=14
            )
        unsupported = (
            "</html>",
            "</body>",
            "</head>",
            "\u00a0",
            "\u2003",
            "\v",
            "\ufeff",
            "&#160;",
            "&nbsp;",
            "&#32;",
            "<!-- ordinary -->",
            "<?ordinary text?>",
            "<!doctype other>",
            "<![CDATA[ordinary]]>",
            "<html/>",
            "<head/>",
            '<meta charset="utf-8"/>',
        )
        for name in ("index.html", "phase14-collapsed-320.html"):
            for token in unsupported:
                with (
                    self.subTest(name=name, token=token),
                    tempfile.TemporaryDirectory() as temporary,
                ):
                    directory = Path(temporary)
                    value = self.packet(directory)
                    target = directory / name
                    content = target.read_text()
                    if name != "index.html":
                        content = content.replace(
                            "<!doctype html>", '<!doctype html><html lang="en"><head>'
                        )
                    target.write_text(
                        content.replace(PHASE14_POLICY, token + PHASE14_POLICY)
                    )
                    self.checksum(directory, value, name)
                    with self.assertRaises(ValueError):
                        self.module.verify_artifacts(directory, value["artifacts"], 14)
        self.module.validate_html(
            "<!doctype html><!-- legacy -->\u00a0<p>Phase 13 compatibility</p>"
        )

    def screenshot(self, width):
        import struct
        import zlib

        def chunk(kind, data):
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data))
            )

        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\0" + bytes(width * 3)))
            + chunk(b"IEND", b"")
        )

    def packet(self, directory):
        """Offline specimen, never represented as a real capture receipt."""
        value = self.sample()
        for capture in value["captures"]:
            width, state = capture["width"], capture["state"]
            paths = phase14_paths(width, state)
            capture["artifacts"] = paths
            metadata = {
                "phase": 14,
                "state": state,
                "width": width,
                "browser": "chromium",
                "version": "1.2.3",
                "scope": capture["scope"],
                "source": value["git_commit"],
                "synthetic": True,
                "native_200_percent_verified": False,
                "owner_accepted": False,
                "artifacts": paths,
                "layout": capture["layout"],
                "trace": [{"path": "/synthetic", "start": 1, "duration": 2}],
            }
            content = (
                "<!doctype html>"
                + PHASE14_POLICY
                + '<meta name="birja-evidence" content="'
                + html.escape(json.dumps(metadata), quote=True)
                + '">'
            )
            for kind, name in paths.items():
                target = directory / name
                if kind == "html":
                    target.write_text(content)
                elif kind == "trace":
                    target.write_text(json.dumps(metadata["trace"]))
                else:
                    target.write_bytes(
                        self.screenshot(width // 2 if kind == "reflow_png" else width)
                    )
        (directory / "index.html").write_text(
            "<!doctype html>" + PHASE14_POLICY + "<p>Offline test specimen</p>"
        )
        value["artifacts"] = {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for name in phase14_names()
        }
        self.write(directory, value)
        return value

    def write(self, directory, value):
        (directory / "manifest.json").write_text(json.dumps(value))

    def checksum(self, directory, value, name):
        value["artifacts"][name] = hashlib.sha256(
            (directory / name).read_bytes()
        ).hexdigest()
        self.write(directory, value)

    def test_independent_phase14_complete_positive_and_phase13_remains_distinct(self):
        self.assertEqual(len(phase14_names()), 419)
        value = self.sample()
        self.assertEqual(value["phase"], 14)
        self.assertEqual(value["artifacts"].keys(), phase14_names())
        self.assertEqual(
            {(c["width"], c["state"]) for c in value["captures"]},
            {(w, s) for w in EXPECTED_WIDTHS for s in PHASE14_STATES},
        )
        self.module.validate_manifest(value, phase=14)
        with self.assertRaises(ValueError):
            self.module.validate_manifest(value, phase=13)
        self.module.validate_manifest(self.module.contract_example(), phase=13)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            complete = self.packet(directory)
            self.module.verify_artifacts(directory, complete["artifacts"], 14)

    def test_cannot_inherit_owner_native_zoom_or_another_family(self):
        for field, replacement in (
            ("owner_accepted", True),
            ("native_200_percent_verified", True),
            ("phase", 13),
            ("phase", 15),
            ("synthetic", False),
        ):
            value = self.sample()
            value[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module.validate_manifest(value, phase=14)

    def test_coherent_required_omissions_refuse_even_with_forged_remaining_hashes(self):
        for missing in (
            "index.html",
            *phase14_paths(1280, "restored-unknown").values(),
        ):
            with (
                self.subTest(missing=missing),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                value = self.packet(directory)
                (directory / missing).unlink()
                del value["artifacts"][missing]
                for capture in value["captures"]:
                    capture["artifacts"] = {
                        k: v for k, v in capture["artifacts"].items() if v != missing
                    }
                self.write(directory, value)
                with self.assertRaises(ValueError):
                    self.module.verify_artifacts(directory, value["artifacts"], 14)

    def test_matrix_owner_duplicates_paths_and_layout_are_authoritative(self):
        for operation in (
            "missing",
            "duplicate",
            "owner",
            "paths",
            "layout",
            "narrow-layout",
        ):
            value = self.sample()
            if operation == "missing":
                value["captures"].pop()
            elif operation == "duplicate":
                value["captures"][1] = copy.deepcopy(value["captures"][0])
            elif operation == "owner":
                value["captures"][1]["scope"] = "b" * 64
            elif operation == "paths":
                value["captures"][0]["artifacts"]["html"] = "phase14-empty-1440.html"
            elif operation == "layout":
                value["captures"][0]["layout"]["no_horizontal_overflow"] = False
            else:
                next(c for c in value["captures"] if c["width"] >= 768)["layout"].pop(
                    "reflow"
                )
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.module.validate_manifest(value, phase=14)

    def test_coherent_wrong_metadata_trace_and_screenshot_dimensions_refuse(self):
        for operation in ("state", "layout", "trace", "png", "owner-flag"):
            with (
                self.subTest(operation=operation),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                value = self.packet(directory)
                paths = phase14_paths(320, "collapsed")
                if operation in ("state", "layout", "owner-flag"):
                    path = directory / paths["html"]
                    metadata = self.module.capture_metadata(path.read_text())
                    if operation == "state":
                        metadata["state"] = "empty"
                    elif operation == "layout":
                        metadata["layout"]["action_count"] = 99
                    else:
                        metadata["owner_accepted"] = True
                    path.write_text(
                        '<meta name="birja-evidence" content="'
                        + html.escape(json.dumps(metadata), quote=True)
                        + '">'
                    )
                    self.checksum(directory, value, path.name)
                elif operation == "trace":
                    (directory / paths["trace"]).write_text("[]")
                    self.checksum(directory, value, paths["trace"])
                else:
                    (directory / paths["png"]).write_bytes(self.screenshot(321))
                    self.checksum(directory, value, paths["png"])
                with self.assertRaises(ValueError):
                    self.module.verify_artifacts(directory, value["artifacts"], 14)

    def test_active_handlers_refresh_escaped_schemes_and_private_content_refuse(self):
        for content in (
            '<img onerror="alert(1)" src=x>',
            '<meta http-equiv=refresh content="0;url=/">',
            "<a href=java&#115;cript:alert(1)>x</a>",
            '<svg><a xlink:href="//bad.invalid/x">x</a></svg>',
            "<object data=/secret>",
            "<script src=/local.js></script>",
            "<form action=/api/>",
            "bj_refresh=private",
            '<img srcset="one.png 1x, https://bad.invalid/x 2x">',
        ):
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.module.validate_html(content)

    def test_source_changes_and_uncommitted_capture_inputs_refuse(self):
        from unittest.mock import patch

        value = self.sample()
        with self.assertRaises(ValueError):
            self.module.validate_manifest(
                value, phase=14, source={"frontend/src/App.tsx": "b" * 64}
            )
        for outputs in (
            [b"frontend/src/App.tsx\0", b"frontend/src/App.tsx\n"],
            [b"other.ts\0"],
        ):
            with (
                patch.object(
                    self.module.subprocess, "check_output", side_effect=outputs
                ),
                self.assertRaises(ValueError),
            ):
                self.module.require_committed_inputs(value["source_sha256"])

    def test_packet_zip_inventory_and_bytes_cannot_diverge(self):
        import zipfile

        for operation in ("positive", "missing", "duplicate", "extra", "tampered"):
            with (
                self.subTest(operation=operation),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary) / "review"
                directory.mkdir()
                self.packet(directory)
                archive = directory.with_suffix(".zip")
                with zipfile.ZipFile(archive, "w") as bundle:
                    for path in directory.iterdir():
                        if operation == "missing" and path.name == "index.html":
                            continue
                        bundle.writestr(
                            path.name,
                            b"tampered"
                            if operation == "tampered" and path.name == "index.html"
                            else path.read_bytes(),
                        )
                    if operation == "duplicate":
                        bundle.writestr("index.html", b"fake duplicate")
                    if operation == "extra":
                        bundle.writestr("../extra.html", b"fake traversal")
                if operation == "positive":
                    self.module.verify_zip(directory, 14)
                else:
                    with self.assertRaises(ValueError):
                        self.module.verify_zip(directory, 14)

    def test_complete_packager_positive_is_read_only_and_preserves_owner_pending(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            captured = root / "capture"
            captured.mkdir()
            value = self.packet(captured)
            destination = root / "review"
            with patch.object(
                self.module, "source_snapshot", return_value=value["source_sha256"]
            ):
                self.module.package(
                    captured,
                    destination,
                    value["source_sha256"],
                    value["git_commit"],
                    14,
                )
            self.module.verify_zip(destination, 14)
            manifest = json.loads((destination / "manifest.json").read_text())
            self.assertIs(manifest["owner_accepted"], False)
            self.assertIs(manifest["native_200_percent_verified"], False)
            self.assertEqual(len(manifest["artifacts"]), 419)
            self.assertEqual(destination.stat().st_mode & 0o777, 0o500)
            destination.chmod(0o700)


if __name__ == "__main__":
    unittest.main(verbosity=2)
