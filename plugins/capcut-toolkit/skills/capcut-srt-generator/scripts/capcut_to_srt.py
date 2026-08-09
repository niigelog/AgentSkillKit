#!/usr/bin/env python3
"""Convert CapCut draft subtitle tracks into .srt files.

Usage:
    python3 capcut_to_srt.py [input_dir] [output_dir]
    python3 capcut_to_srt.py --set-default <input_dir>
    python3 capcut_to_srt.py --set-output <output_dir>
    python3 capcut_to_srt.py --show-config

<input_dir> may be:
  - a single CapCut draft project folder (contains draft_content.json directly), or
  - a root folder containing many draft project folders (searched recursively).

For every draft_content.json found, all "subtitle" segments on the text track(s)
are collected, sorted by start time, and written to <output_dir>/<project>.srt.
The project name is the name of the folder that directly contains draft_content.json.

Directory resolution (for both input_dir and output_dir), in priority order:
  1. Explicit CLI argument
  2. Saved config (see --set-default / --set-output, stored in
     ~/.capcut-srt-generator/config.json)
  3. For input_dir only: auto-detected CapCut/JianyingPro install location for
     the current OS (first one that exists on disk).
  4. Otherwise: error, asking the user to specify one.
"""

import argparse
import json
import platform
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".capcut-srt-generator" / "config.json"


def known_default_input_dirs() -> list[Path]:
    """Known default install locations for CapCut / JianyingPro (剪映), by OS."""
    home = Path.home()
    system = platform.system()

    if system == "Darwin":
        return [
            home / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
            home / "Movies" / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft",
        ]
    if system == "Windows":
        import os
        import string

        app_names = ["CapCut", "JianyingPro"]
        local_appdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        candidates = [
            local_appdata / name / "User Data" / "Projects" / "com.lveditor.draft" for name in app_names
        ]

        # %LOCALAPPDATA% is normally on the system drive regardless of where the
        # app itself is installed, so the above covers most machines. But CapCut
        # lets users move their draft storage location in its own settings, and
        # some users relocate their whole profile — so as a fallback, also probe
        # every other drive letter for the same relative layout (cheap: just an
        # is_dir() check per candidate, no directory walking).
        username = Path(os.environ.get("USERPROFILE", str(home))).name
        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:/")
            if not drive.is_dir():
                continue
            for name in app_names:
                candidates.append(
                    drive / "Users" / username / "AppData" / "Local" / name
                    / "User Data" / "Projects" / "com.lveditor.draft"
                )
                # Portable/relocated installs sometimes keep everything at the drive root.
                candidates.append(drive / name / "User Data" / "Projects" / "com.lveditor.draft")

        # Dedup while preserving order (e.g. C: appears both explicitly and via the loop).
        return list(dict.fromkeys(candidates))
    # Other platforms (Linux, etc.) have no known standard install location.
    return []


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(updates: dict) -> None:
    config = load_config()
    config.update(updates)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def resolve_input_dir(cli_value: str | None) -> tuple[Path | None, str]:
    """Returns (path, source) where source explains where the path came from."""
    if cli_value:
        return Path(cli_value).expanduser(), "command-line argument"

    config = load_config()
    if config.get("input_dir"):
        return Path(config["input_dir"]).expanduser(), f"saved config ({CONFIG_PATH})"

    for candidate in known_default_input_dirs():
        if candidate.is_dir():
            return candidate, f"auto-detected default for {platform.system()}"

    return None, ""


def resolve_output_dir(cli_value: str | None) -> tuple[Path | None, str]:
    if cli_value:
        return Path(cli_value).expanduser(), "command-line argument"

    config = load_config()
    if config.get("output_dir"):
        return Path(config["output_dir"]).expanduser(), f"saved config ({CONFIG_PATH})"

    return None, ""


def format_srt_time(microseconds: int) -> str:
    total_ms = microseconds // 1000
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def extract_text(material: dict) -> str:
    """Prefer the user-edited text in `content`, fall back to `recognize_text`."""
    raw_content = material.get("content")
    if raw_content:
        try:
            parsed = json.loads(raw_content)
            text = parsed.get("text", "").strip()
            if text:
                return text
        except (json.JSONDecodeError, AttributeError):
            pass
    return (material.get("recognize_text") or "").strip()


def collect_subtitle_entries(draft_content: dict) -> list[tuple[int, int, str]]:
    materials_by_id = {
        m["id"]: m
        for m in draft_content.get("materials", {}).get("texts", [])
        if m.get("type") == "subtitle"
    }

    entries = []
    for track in draft_content.get("tracks", []):
        if track.get("type") != "text":
            continue
        for segment in track.get("segments", []):
            material = materials_by_id.get(segment.get("material_id"))
            if material is None:
                continue
            timerange = segment.get("target_timerange") or {}
            start = timerange.get("start")
            duration = timerange.get("duration")
            if start is None or duration is None:
                continue
            text = extract_text(material)
            if not text:
                continue
            entries.append((start, start + duration, text))

    entries.sort(key=lambda e: e[0])
    return entries


def merge_short_entries(
    entries: list[tuple[int, int, str]], min_chars: int, max_gap_us: int
) -> list[tuple[int, int, str]]:
    """Merge consecutive entries so each line has at least `min_chars` characters.

    CapCut's auto-recognized subtitle track is split at speech-recognition word
    boundaries, not at readable line lengths, so many entries end up being only
    a couple of characters long. This glues consecutive entries together
    (keeping the first entry's start time and the last one's end time) until
    the combined text reaches `min_chars`. A gap larger than `max_gap_us`
    between two entries is treated as a natural pause and always starts a new
    line, even if the current one is still short, so unrelated sentences don't
    get glued together just because both are short.
    """
    if min_chars <= 0 or not entries:
        return entries

    merged: list[tuple[int, int, str]] = []
    group_start, group_end, group_text = entries[0]

    for start, end, text in entries[1:]:
        gap = start - group_end
        if len(group_text) >= min_chars or gap > max_gap_us:
            merged.append((group_start, group_end, group_text))
            group_start, group_end, group_text = start, end, text
        else:
            group_end = end
            group_text += text

    merged.append((group_start, group_end, group_text))
    return merged


def write_srt(entries: list[tuple[int, int, str]], out_path: Path) -> None:
    lines = []
    for idx, (start, end, text) in enumerate(entries, start=1):
        lines.append(str(idx))
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        lines.append(text)
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def find_draft_content_files(input_dir: Path) -> list[Path]:
    direct = input_dir / "draft_content.json"
    if direct.is_file():
        return [direct]
    return sorted(input_dir.rglob("draft_content.json"))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_dir", nargs="?", help="CapCut draft project folder, or a root folder containing many")
    parser.add_argument("output_dir", nargs="?", help="Folder to write generated .srt files into")
    parser.add_argument("--set-default", metavar="PATH", help="Save PATH as the default input directory and exit")
    parser.add_argument("--set-output", metavar="PATH", help="Save PATH as the default output directory and exit")
    parser.add_argument("--show-config", action="store_true", help="Print the resolved config/defaults and exit")
    parser.add_argument(
        "--min-chars",
        type=int,
        default=0,
        help="Merge consecutive short lines until each has at least this many characters "
        "(0 = disabled, keep CapCut's original per-segment lines; try 18 for readable lines)",
    )
    parser.add_argument(
        "--max-gap-ms",
        type=int,
        default=500,
        help="When merging (--min-chars), a gap larger than this between two lines always "
        "starts a new line even if the current one is still short (default: 500ms)",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.set_default:
        path = Path(args.set_default).expanduser()
        if not path.is_dir():
            print(f"Warning: {path} does not exist yet, saving anyway.", file=sys.stderr)
        save_config({"input_dir": str(path)})
        print(f"Saved default input directory: {path}")
        return 0

    if args.set_output:
        path = Path(args.set_output).expanduser()
        save_config({"output_dir": str(path)})
        print(f"Saved default output directory: {path}")
        return 0

    if args.show_config:
        config = load_config()
        print(f"Config file: {CONFIG_PATH}")
        print(f"Saved input_dir: {config.get('input_dir', '(none)')}")
        print(f"Saved output_dir: {config.get('output_dir', '(none)')}")
        all_candidates = known_default_input_dirs()
        found = [c for c in all_candidates if c.is_dir()]
        print(f"Auto-detection scanned {len(all_candidates)} known location(s) for this OS:")
        if found:
            for candidate in found:
                print(f"  - {candidate} [exists]")
        else:
            print("  (none found)")
        return 0

    input_dir, input_source = resolve_input_dir(args.input_dir)
    if input_dir is None:
        print(
            "Could not determine an input directory. Pass one explicitly, or run:\n"
            "  python3 capcut_to_srt.py --set-default \"<your CapCut drafts folder>\"",
            file=sys.stderr,
        )
        return 1

    output_dir, output_source = resolve_output_dir(args.output_dir)
    if output_dir is None:
        print(
            "Could not determine an output directory. Pass one explicitly, or run:\n"
            "  python3 capcut_to_srt.py --set-output \"<folder for generated .srt files>\"",
            file=sys.stderr,
        )
        return 1

    print(f"Using input directory ({input_source}): {input_dir}")
    print(f"Using output directory ({output_source}): {output_dir}")

    if not input_dir.is_dir():
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1

    draft_files = find_draft_content_files(input_dir)
    if not draft_files:
        print(f"No draft_content.json found under: {input_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    for draft_file in draft_files:
        project_name = draft_file.parent.name
        try:
            draft_content = json.loads(draft_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[skip] {draft_file}: invalid JSON ({exc})", file=sys.stderr)
            continue

        entries = collect_subtitle_entries(draft_content)
        if not entries:
            print(f"[skip] {project_name}: no subtitle segments found")
            continue

        if args.min_chars > 0:
            entries = merge_short_entries(entries, args.min_chars, args.max_gap_ms * 1000)

        out_path = output_dir / f"{project_name}.srt"
        write_srt(entries, out_path)
        print(f"[ok] {project_name}: {len(entries)} subtitles -> {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
