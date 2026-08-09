---
name: capcut-srt-generator
description: Generates .srt subtitle files from CapCut (剪映) draft projects by reading their draft_content.json and converting the subtitle/text track into standard SRT format. Use this whenever the user wants to export, extract, or convert subtitles/captions from a CapCut project, mentions a CapCut draft folder path (e.g. containing draft_content.json, or paths like ".../CapCut/User Data/Projects/com.lveditor.draft/..."), or asks to batch-generate SRT files for multiple CapCut projects at once. Also trigger on phrases like "剪映字幕导出", "CapCut 生成字幕", "把草稿转成srt", even if the user doesn't say "SRT" explicitly but clearly wants the on-screen captions as a subtitle file.
---

# CapCut Draft → SRT Generator

Converts the subtitle text track inside a CapCut (剪映) draft project into a
standard `.srt` file, using the bundled script `scripts/capcut_to_srt.py`.

## Why a script instead of parsing JSON by hand

`draft_content.json` is a large (often several MB), deeply nested JSON file.
Always use the bundled script rather than reading/parsing the file manually —
it already handles the material/segment lookup, time conversion, and text
fallback logic correctly and will be much faster and more reliable than doing
this ad hoc.

## How CapCut drafts store subtitles

- Each draft project is a folder containing `draft_content.json`.
- Inside it, `tracks` has one or more entries with `type: "text"`; each
  `segment` in that track has a `material_id` and a `target_timerange`
  (`start` / `duration`, in **microseconds**).
- The actual text for each segment lives in `materials.texts`, matched by
  `id == segment.material_id`, and only entries with `type: "subtitle"` are
  captions (as opposed to other on-screen text objects).
- Each text material has two possible sources of text:
  - `content` — a JSON string with a `text` field, reflecting what the user
    sees/edited in CapCut (may differ from the raw ASR output if the user
    corrected typos, etc.)
  - `recognize_text` — the raw speech-recognition output.
  - Prefer `content`'s text; fall back to `recognize_text` only if `content`
    is missing or has no text.

## Prerequisite: python3

The script requires `python3` (standard library only, no extra packages) on
whatever machine is running this Claude Code session. Before the first run
in a conversation, check with `python3 --version`. If that fails:

- On macOS it's usually preinstalled — a missing `python3` there is unusual,
  double-check with `which python3` / `python --version` too before assuming
  it's absent.
- On Windows it's often not preinstalled. Don't just install it — installing
  software is a system change, so tell the user `python3` wasn't found and
  ask whether you should install it (e.g. via `winget install Python.Python.3`
  on Windows, `brew install python3` on macOS) before running that command.
  If they'd rather install it themselves, point them to https://python.org.

Once `python3 --version` succeeds, proceed normally — no need to re-check on
later runs within the same session.

## Usage

CapCut/剪映's install location differs between macOS and Windows (and users
can have it on a non-default drive), so the script never hardcodes a path.
Directories are resolved with this priority, for both input and output:

1. **Explicit CLI argument** — pass it directly for a one-off run.
2. **Saved config** — `~/.capcut-srt-generator/config.json`, written by
   `--set-default` (input) / `--set-output` (output). Once set, the user
   never has to pass paths again.
3. **Auto-detected default** (input directory only) — the script checks the
   known CapCut/JianyingPro install locations for the current OS (e.g.
   `~/Movies/CapCut/User Data/Projects/com.lveditor.draft` on macOS,
   `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft` on
   Windows) and uses the first one that exists. On Windows this also falls
   back to probing every other drive letter for the same relative layout
   (`<drive>:\Users\<name>\AppData\Local\CapCut\...` and a drive-root
   variant), since `%LOCALAPPDATA%` normally only covers the system drive
   but CapCut lets users relocate their draft storage to another drive.
4. Otherwise the script exits with an error telling the user to specify one.

**First-time setup for a user** (skip any step already satisfied):

```bash
python3 scripts/capcut_to_srt.py --show-config                # see what's already configured/detected
python3 scripts/capcut_to_srt.py --set-default "<drafts folder>"  # only if auto-detect didn't find it
python3 scripts/capcut_to_srt.py --set-output "<output folder>"   # optional, saves re-typing it every time
```

Run `--show-config` first when helping a user — it tells you immediately
whether auto-detect already found their CapCut folder, so you don't need to
ask them for a path that's already resolved.

**Normal conversion run:**

```bash
python3 scripts/capcut_to_srt.py ["<input_dir>"] ["<output_dir>"]
```

Both arguments are optional if already resolvable via saved config or
auto-detection; pass them explicitly to override for a single run without
changing the saved defaults.

**Merging short lines (`--min-chars`):** CapCut's auto-recognized subtitle
track is split at speech-recognition boundaries, not at readable line
lengths — a raw export often has many lines that are just 2-4 characters.
If the user wants more readable lines (or mentions something like "字幕太碎
了" / "一行太短" / a target line length), add `--min-chars N`:

```bash
python3 scripts/capcut_to_srt.py "<input_dir>" "<output_dir>" --min-chars 18
```

This glues consecutive lines together (keeping the first one's start time and
the last one's end time) until each line has at least N characters — 18 is a
reasonable general-purpose default for Chinese captions if the user doesn't
give a specific number. A gap larger than `--max-gap-ms` (default 500ms)
between two lines always starts a new one even if still short, since that
usually means a real pause/sentence break rather than mid-sentence ASR
chopping. This is off by default (`--min-chars 0`) so a plain run preserves
CapCut's original per-segment timing exactly.

The script prints one line per draft it processed:
- `[ok] <project>: N subtitles -> <path>` on success
- `[skip] <project>: no subtitle segments found` for drafts with no captions
  (e.g. projects that only have a plain video/audio track) — this is normal
  and not an error, just report it to the user in passing.
- `[skip] <path>: invalid JSON (...)` if a `draft_content.json` is corrupted.

After running, tell the user how many drafts were converted and where the
files landed. If they ask to preview, `head` a couple of entries from a
generated `.srt` rather than dumping the whole file.

## Notes / edge cases

- Timestamps are converted from microseconds to `HH:MM:SS,mmm` (standard SRT
  format).
- Entries are sorted by start time before numbering, in case segments in the
  JSON aren't already in chronological order.
- A draft folder can contain a stale `draft_content.json.bak` — the script
  only ever reads `draft_content.json`, never the `.bak` file.
- If a root directory is passed and it contains many unrelated large JSON
  files, the recursive search still only looks for files named exactly
  `draft_content.json`, so it's safe to point at a broad folder.
