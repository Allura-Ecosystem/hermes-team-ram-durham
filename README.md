# Team RAM + Team Durham for Hermes

A native Hermes Agent plugin that brings the Team RAM and Team Durham agent
teams into Hermes as slash commands, bundled skills, and Allura Brain memory
wiring.

## Install

```bash
hermes plugins install Allura-Ecosystem/hermes-team-ram-durham
hermes plugins enable team-ram-durham
```

## What it provides

- **24 personas as slash commands** — `/brooks`, `/woz`, `/scout`, `/jobs`,
  `/pike`, `/fowler`, `/bellard`, `/carmack`, `/knuth`, `/hightower`,
  `/bahari`, plus the 13 Team Durham personas. Each injects the canonical role
  card as the governing instruction.
- **222 bundled skills** — all Team RAM and Team Durham `SKILL.md` files,
  loaded as `plugin:team-ram-durham-<skill>`.
- **Allura Brain wiring** — the role cards carry the
  `allura-brain__memory_search` / `memory_add` protocol, and a
  `post_tool_call` hook logs tool usage for the audit trail.

## Layout

```
team-ram-durham/
├── plugin.yaml          # manifest (v2)
├── __init__.py          # register(ctx) — personas + skills + hook
├── agents/
│   ├── ram/             # 11 Team RAM role cards
│   └── durham/          # 13 Team Durham role cards
└── skills/              # 222 bundled SKILL.md files
```

## Source

- Team RAM: https://github.com/Allura-Ecosystem/allura-team-ram
- Team Durham: https://github.com/Allura-Ecosystem/allura-plugins
