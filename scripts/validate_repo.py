#!/usr/bin/env python3
"""Sanity-check the marketplace/plugin/skill structure of this repo.

Checks (no external dependencies — stdlib only, mirrors this repo's own
"don't require extra packages" convention):
  - .claude-plugin/marketplace.json is valid JSON with required fields, and
    every listed plugin's `source` path exists.
  - Every plugins/*/.claude-plugin/plugin.json is valid JSON with required
    fields.
  - Every SKILL.md has YAML-ish frontmatter with non-empty `name` and
    `description` fields.

This intentionally does NOT depend on PyYAML: SKILL.md frontmatter in this
repo only ever has simple flat `key: value` lines, so a hand-rolled parser
keeps this script runnable anywhere with just `python3`.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    frontmatter = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def check_marketplace(errors: list[str]) -> None:
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    if not path.is_file():
        fail(errors, f"missing {path.relative_to(REPO_ROOT)}")
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(errors, f"{path.relative_to(REPO_ROOT)}: invalid JSON ({exc})")
        return

    for field in ("name", "owner", "plugins"):
        if field not in data:
            fail(errors, f"{path.relative_to(REPO_ROOT)}: missing required field '{field}'")

    for entry in data.get("plugins", []):
        name = entry.get("name", "<unnamed>")
        if "source" not in entry:
            fail(errors, f"marketplace plugin '{name}': missing 'source'")
            continue
        source = entry["source"]
        if source.startswith("./") or source.startswith("../"):
            plugin_dir = (REPO_ROOT / source).resolve()
            if not plugin_dir.is_dir():
                fail(errors, f"marketplace plugin '{name}': source path does not exist: {source}")


def check_plugins(errors: list[str]) -> None:
    plugins_dir = REPO_ROOT / "plugins"
    if not plugins_dir.is_dir():
        return

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            fail(errors, f"{plugin_dir.name}: missing .claude-plugin/plugin.json")
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(errors, f"{manifest.relative_to(REPO_ROOT)}: invalid JSON ({exc})")
            continue
        for field in ("name", "description"):
            if not data.get(field):
                fail(errors, f"{manifest.relative_to(REPO_ROOT)}: missing required field '{field}'")


def check_skills(errors: list[str]) -> None:
    for skill_md in sorted(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md")):
        frontmatter = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        for field in ("name", "description"):
            if not frontmatter.get(field):
                fail(errors, f"{skill_md.relative_to(REPO_ROOT)}: missing/empty '{field}' in frontmatter")


def main() -> int:
    errors: list[str] = []
    check_marketplace(errors)
    check_plugins(errors)
    check_skills(errors)

    if errors:
        print(f"Found {len(errors)} problem(s):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("All good: marketplace.json, plugin.json(s), and SKILL.md(s) look valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
