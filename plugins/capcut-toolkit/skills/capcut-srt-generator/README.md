# capcut-srt-generator

Generates `.srt` subtitle files from CapCut (剪映) draft projects.

This file is the **human-facing** doc — for what Claude reads to decide when
and how to use this skill, see [SKILL.md](SKILL.md). For a full walkthrough
with examples, see the [tutorial](../../../../docs/capcut-srt-generator-tutorial.md).

## What it does

- Finds your CapCut drafts folder (auto-detected on macOS/Windows, or
  configurable)
- Reads the subtitle text track(s) out of `draft_content.json`
- Converts them into a standard `.srt` file, with correct timestamps
- Optionally merges short auto-recognized fragments into readable lines

## Quick start

Once installed, just describe what you want in the chat, e.g.:

> 帮我把 `<CapCut 草稿目录>` 这个剪映草稿导出成 SRT 字幕文件

Or run the script directly:

```bash
python3 scripts/capcut_to_srt.py "<input_dir>" "<output_dir>"
python3 scripts/capcut_to_srt.py "<input_dir>" "<output_dir>" --min-chars 18   # merge short lines
python3 scripts/capcut_to_srt.py --set-default "<input_dir>"                   # remember it
python3 scripts/capcut_to_srt.py --set-output "<output_dir>"
python3 scripts/capcut_to_srt.py --show-config
```

## Requirements

- Python 3 (standard library only, no extra packages)

## License

MIT — see the repository [LICENSE](../../../../LICENSE).
