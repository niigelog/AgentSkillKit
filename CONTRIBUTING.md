# Contributing

Thanks for considering a contribution. This repo is a Claude Code plugin
marketplace — a collection of plugins, each bundling one or more skills.

## Adding a new skill to an existing plugin

If the skill fits an existing plugin's theme (e.g. another CapCut-related
tool belongs in `capcut-toolkit`), add it under that plugin:

```
plugins/<plugin-name>/skills/<new-skill-name>/
├── SKILL.md
├── README.md      (optional but recommended — human-facing usage doc)
└── scripts/        (optional — bundled scripts, if the skill needs them)
```

Bump the plugin's `version` in its `.claude-plugin/plugin.json` — users
won't pick up the change otherwise, since Claude Code treats an unchanged
version as "nothing to update."

## Adding a new plugin

If the skill doesn't fit any existing plugin's theme, create a new one:

1. `plugins/<new-plugin-name>/.claude-plugin/plugin.json` — see an existing
   plugin for the shape (`name`, `description`, `version`, `author`).
2. `plugins/<new-plugin-name>/skills/<skill-name>/SKILL.md` and its
   resources.
3. Add an entry to `.claude-plugin/marketplace.json`'s `plugins` array:
   `{"name": "...", "source": "./plugins/<new-plugin-name>", "description": "..."}`.

## Writing the SKILL.md

- `description` in the frontmatter is what triggers the skill — Claude
  matches it against what the user is asking for, so be specific about when
  to use it, and list a few phrasings a real user might type (including
  Chinese phrasings, if relevant to that skill's domain). Skills tend to
  under-trigger, so lean toward being explicit rather than vague.
- The body is written for Claude, not for a human reader — explain the
  *why* behind non-obvious steps, don't pad it with things Claude can
  already infer.
- Keep secrets, personal file paths, and machine-specific assumptions out
  of committed skills — anything environment-specific (like install
  locations) should be auto-detected or configurable, not hardcoded.
- If the skill needs a runtime dependency (Python, ffmpeg, etc.), document
  a check-and-ask-before-installing flow rather than assuming it's present
  or silently installing it — see `capcut-srt-generator`'s SKILL.md for an
  example.

## Before opening a PR

- Test the skill for real — run it against a real (or realistic sample)
  input and confirm the output is correct, not just that the script runs
  without crashing.
- Make sure `.claude-plugin/marketplace.json` and every `plugin.json` are
  still valid JSON.
- If you're using the [skill-creator skill](https://github.com/anthropics/skills)
  workflow to draft and iterate, its `quick_validate.py` script is a decent
  sanity check before opening a PR.
