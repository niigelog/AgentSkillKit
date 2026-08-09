# AgentSkillKit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A personal, open-source collection of [Claude Code](https://claude.com/claude-code)
skills and plugins — built for my own workflows, shared as a Claude Code
plugin marketplace so anyone can install and use them.

## Install

Add this repo as a plugin marketplace, then install whichever plugin you want:

```bash
/plugin marketplace add niigelog/AgentSkillKit
/plugin install capcut-toolkit@agent-skill-kit
```

## Plugins

| Plugin | Skills inside | What it's for |
|---|---|---|
| [`capcut-toolkit`](plugins/capcut-toolkit) | [`capcut-srt-generator`](plugins/capcut-toolkit/skills/capcut-srt-generator) | Working with CapCut (剪映) draft projects — currently: export subtitle tracks to `.srt`. |

Each skill's `SKILL.md` is what Claude reads to decide when/how to use it;
each skill also has a human-facing `README.md` for people browsing the repo.
Longer written tutorials live in [`docs/`](docs).

## Repository structure

```
AgentSkillKit/
├── .claude-plugin/
│   └── marketplace.json        # marketplace catalog — lists all plugins in this repo
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json     # plugin manifest
│       └── skills/
│           └── <skill-name>/
│               ├── SKILL.md    # AI-facing: when/how Claude should use this skill
│               ├── README.md   # human-facing: what it is, how to run it manually
│               └── scripts/    # bundled scripts the skill calls
├── docs/                       # longer-form tutorials / write-ups
└── LICENSE
```

A **plugin** can bundle multiple related **skills** (plus, optionally,
commands/agents/hooks — not used here yet). Group skills into the same
plugin when they share a theme (e.g. all CapCut-related tools live under
`capcut-toolkit`); give something its own plugin when it's unrelated to the
existing ones.

## Contributing

Want to add a skill or improve an existing one? See
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, adapt it.
