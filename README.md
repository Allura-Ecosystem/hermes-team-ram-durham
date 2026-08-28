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
  `/bahari`, plus the 13 Team Durham personas. Each command launches an isolated
  Hermes worker through `delegate_task`, with the canonical role card and a
  Hermes-specific runtime adapter.
- **219 bundled skills** — the valid Team RAM and Team Durham `SKILL.md` files,
  loaded as `plugin:team-ram-durham-<skill>`.
- **Allura Brain adapter** — workers are instructed to use Hermes' configured
  `mcp_allura_brain_*` tools through `https://mcp.faithmeats.org/mcp`; LAN and
  private-IP service paths are forbidden.

## Layout

```
team-ram-durham/
├── plugin.yaml          # Hermes-compatible manifest
├── __init__.py          # register(ctx) — personas + skills + hook
├── agents/
│   ├── ram/             # 11 Team RAM role cards
│   └── durham/          # 13 Team Durham role cards
└── skills/              # 219 registered SKILL.md files
```

## Usage

```text
/brooks Design a bounded execution harness
/scout Map this repository and return evidence paths
/brand-orchestrator Create a governed brand-work plan
```

The command returns a dispatch acknowledgment immediately. The isolated worker's
result re-enters the conversation when it completes.

## Source

- Team RAM: https://github.com/Allura-Ecosystem/allura-team-ram
- Team Durham: https://github.com/Allura-Ecosystem/allura-plugins
