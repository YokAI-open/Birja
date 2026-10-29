#!/usr/bin/env python3
"""Adapt a local upstream GSD install and expose its skills to Codex."""

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path


ADAPTER = """<project_codex_adapter>
Read `.codex/GSD-ADAPTER.md` for this repository's tool mappings and workflow
rules before performing this role. Resolve project paths from the repo root.
</project_codex_adapter>
"""


def write_if_changed(path: Path, content: str) -> None:
    if path.read_text() != content:
        path.write_text(content)


def sync(root: Path) -> None:
    config_dir = root / ".codex"
    config_path = config_dir / "config.toml"
    config = tomllib.loads(config_path.read_text())
    prefixes = set()
    for name, role in config.get("agents", {}).items():
        if name.startswith("gsd-") and isinstance(role, dict):
            source = Path(role.get("config_file", ""))
            if source.is_absolute():
                prefixes.add(str(source.parent.parent) + "/")

    # Only touch upstream GSD documents and role definitions, not user config.
    generated = list((config_dir / "skills").glob("gsd-*/SKILL.md"))
    generated += list((config_dir / "agents").glob("gsd-*.*"))
    generated += list((config_dir / "get-shit-done").rglob("*.md"))
    changes = {}
    for path in generated:
        original = path.read_text()
        content = original
        for prefix in sorted(prefixes, key=len, reverse=True):
            content = content.replace(prefix, ".codex/")
            content = content.replace(prefix.rstrip("/"), ".codex")
        if path.name == "SKILL.md":
            name = path.parent.name
            header = (
                "<codex_skill_adapter>\n"
                "Read `.codex/GSD-ADAPTER.md` before executing this skill.\n"
                f"Invoke as `${name}`; text after the invocation is "
                "`{{GSD_ARGS}}` (empty when omitted).\n"
                "Resolve all project paths from the repository root.\n"
                "</codex_skill_adapter>"
            )
            content, count = re.subn(
                r"<codex_skill_adapter>.*?</codex_skill_adapter>",
                lambda _: header,
                content,
                count=1,
                flags=re.S,
            )
            if count != 1:
                raise ValueError(f"Missing upstream Codex adapter: {path}")
        elif path.parent.name == "agents" and ADAPTER not in content:
            if path.suffix == ".toml":
                marker = "developer_instructions = '''\n"
                if marker not in content:
                    raise ValueError(f"Unsupported upstream agent format: {path}")
                content = content.replace(marker, marker + ADAPTER + "\n", 1)
            elif path.suffix == ".md":
                if content.startswith("---\n"):
                    end = content.index("\n---", 4) + len("\n---")
                    content = content[:end] + "\n\n" + ADAPTER + content[end:]
                else:
                    content = ADAPTER + "\n" + content
        if original != content:
            changes[str(path.relative_to(config_dir))] = (
                hashlib.sha256(original.encode()).hexdigest(),
                hashlib.sha256(content.encode()).hexdigest(),
            )
            path.write_text(content)

    config_text = config_path.read_text()
    for prefix in sorted(prefixes, key=len, reverse=True):
        config_text = config_text.replace(prefix + "agents/", "agents/")
    write_if_changed(config_path, config_text)

    hooks_path = config_dir / "hooks.json"
    if hooks_path.exists():
        hooks = json.loads(hooks_path.read_text())
        for group in hooks.get("SessionStart", []):
            for hook in group.get("hooks", []):
                if "gsd-check-update.js" in hook.get("command", ""):
                    hook["command"] = (
                        'node "$(git rev-parse --show-toplevel)/'
                        '.codex/hooks/gsd-check-update.js"'
                    )
        write_if_changed(hooks_path, json.dumps(hooks, indent=2) + "\n")

    discovery = root / ".agents" / "skills"
    discovery.mkdir(parents=True, exist_ok=True)
    for skill in sorted((config_dir / "skills").iterdir()):
        if not (skill / "SKILL.md").is_file():
            continue
        link = discovery / skill.name
        target = Path("../../.codex/skills") / skill.name
        if link.is_symlink() and link.readlink() == target:
            continue
        if link.exists() or link.is_symlink():
            raise ValueError(f"Refusing to replace an existing skill: {link}")
        link.symlink_to(target, target_is_directory=True)

    # These are deterministic install adaptations; maintain the upstream
    # baseline so its updater can still detect later user edits accurately.
    manifest_path = config_dir / "gsd-file-manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for relative, (before, after) in changes.items():
            # Only advance a pristine upstream baseline. Preserve evidence of
            # user edits so GSD's updater can still save those as local patches.
            if manifest.get("files", {}).get(relative) == before:
                manifest["files"][relative] = after
        write_if_changed(manifest_path, json.dumps(manifest, indent=2) + "\n")


def check(root: Path) -> tuple[int, int]:
    config_dir = root / ".codex"
    if not (config_dir / "GSD-ADAPTER.md").is_file():
        raise ValueError("Missing .codex/GSD-ADAPTER.md")
    count = 0
    gsd_count = 0
    for skill in sorted((config_dir / "skills").iterdir()):
        manifest = skill / "SKILL.md"
        if not manifest.is_file():
            continue
        text = manifest.read_text()
        name = re.search(r"^name:\s*([^\n]+)", text, re.M)
        if not text.startswith("---\n") or not name:
            raise ValueError(f"Invalid skill frontmatter: {manifest}")
        if name.group(1).strip("\"' ") != skill.name:
            raise ValueError(f"Skill name differs from folder: {manifest}")
        link = root / ".agents" / "skills" / skill.name
        if not link.is_symlink() or link.resolve() != skill.resolve():
            raise ValueError(f"Missing or incorrect discovery link: {link}")
        if skill.name.startswith("gsd-"):
            gsd_count += 1
            if ".codex/GSD-ADAPTER.md" not in text:
                raise ValueError(f"Missing project adapter reference: {manifest}")
        for block in re.findall(r"<execution_context>(.*?)</execution_context>", text, re.S):
            for reference in re.findall(r"^@([^\s]+)\s*$", block, re.M):
                if not (root / reference).is_file():
                    raise ValueError(f"Broken execution context in {manifest}: {reference}")
        count += 1
    if not gsd_count or not (config_dir / "skills/ui-ux-pro-max/scripts/search.py").is_file():
        raise ValueError("GSD and the project UI skill must both be installed")
    roles = 0
    config = tomllib.loads((config_dir / "config.toml").read_text())
    for name, role in config.get("agents", {}).items():
        if not name.startswith("gsd-") or not isinstance(role, dict):
            continue
        path = config_dir / role["config_file"]
        if not path.is_file():
            raise ValueError(f"Missing agent config: {path}")
        agent = tomllib.loads(path.read_text())
        if ADAPTER not in agent.get("developer_instructions", ""):
            raise ValueError(f"Missing project adapter in agent: {path}")
        roles += 1
    if not roles:
        raise ValueError("No GSD agent roles installed")
    return count, roles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without writing files")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if not args.check:
            sync(root)
        skills, roles = check(root)
    except (OSError, ValueError, KeyError) as error:
        print(f"Codex setup: {error}", file=sys.stderr)
        sys.exit(1)
    print(f"Codex setup valid: {skills} skills, {roles} GSD agent roles")


if __name__ == "__main__":
    main()
