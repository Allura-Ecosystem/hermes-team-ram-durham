# Team RAM + Team Durham for Hermes

Native Hermes plugin **1.1.1**: 24 role definitions and 239 namespaced skills,
using the active conversation's model, context and tools. Two entry workflows
bring the total to 241 registered skills. Durham has 12 specialist roles plus
`openagent`, its compatibility fallback; RAM has 11 loadable personas.

## Use

In interactive Hermes CLI:

```text
/ram Map this repository and implement the agreed fix
/ram-woz Implement the approved change and validate it
/ram-pike Review the interface; report findings only
/durham Plan the brand work from our approved brief
/durham-copywriter Refine this copy against the locked strategy
```

`/ram` selects Brooks; `/durham` selects the brand orchestrator. Role commands use
`/ram-<role>` or `/durham-<role>`. They queue work in the current CLI conversation,
not an independent worker. Existing host permissions and approvals still apply.

For gateway/chat surfaces, send a normal message:

> Use `allura_team` with team `durham`, role `copywriter`, and task “Refine the
> approved homepage copy.” Continue with the result in this conversation.

The tool loads the selected role and adaptive workflow; it does not execute the
task or claim completion. The active model then performs the work using its
available tools. The installed Hermes SDK cannot queue gateway turns from plugin
slash commands, so those commands return **Task not started** with this fallback.
No subprocess or detached worker is started. The `allura_teams` toolset must be
available in the host's chosen tool configuration for model-facing tool use.

Skills are explicitly loaded with:

```text
skill_view(name="team-ram-durham:ram")
skill_view(name="team-ram-durham:durham")
skill_view(name="team-ram-durham:ram-context7")
skill_view(name="team-ram-durham:durham-brand-strategy")
```

Registered plugin skills are opt-in `skill_view` resources, not automatically
created slash commands. Load only 1–3 relevant skills. Both teams' copies are
kept separate, including skills with the same name.

## What changed from 1.0.2

- Removed a fresh `hermes chat` process for every persona command. Work retains
  the active conversation, configured model and context; no guessed model IDs.
- Updated role/skill bundles from pinned Team RAM 0.5.1 and Durham 0.4.1 sources.
- Added quick/standard/sensitive routing and reuse of context that still matches
  the task, project, tenant, revision and authority. Review remains risk-based.
- Fixed skill registration to provide `SKILL.md` files instead of directories.
- Replaced bare `/brooks`, `/woz`, `/copywriter`, etc. with prefixed commands to
  avoid collisions. For example `/brooks` becomes `/ram-brooks`.
- Removed the debug-only hook previously described as an Allura audit trail.
  This plugin makes no audit or memory-persistence claim without real receipts.

These changes remove process startup and unnecessary handoffs by design. No
live-model latency, cost or quality improvement has yet been measured.

## Memory and authority

This is a standalone team plugin, separate from the Allura Brain memory provider.
It neither changes `memory.provider` nor configures credentials or MCP servers.
RAM uses explicit `group_id: allura-system`; Durham uses
`group_id: allura-team-durham`. Never fall back to an unrelated provider tenant.
If the configured Brain cannot serve the team/project scope, report degraded
local-only context and continue safe work. Persona names do not change the
authenticated principal. Semantic promotion and external shipping retain human
approval gates.

Canonical role cards contain foreign-runtime examples. The Hermes adapter maps
their resources to this bundle and requires actual host schemas. Personas and
skills are instructions, **not enforced per-role tool sandboxes**. Read-only
reviewers must report findings; where enforced isolation is required, use a
host-supported restricted context or report the missing capability.

## Install

Version 1.1.1 is published on the
[`codex/adaptive-hermes-teams` branch](https://github.com/Allura-Ecosystem/hermes-team-ram-durham/tree/codex/adaptive-hermes-teams),
not the default branch. The GitHub shorthand installs the remote default branch
and must not be treated as an installation of this update.

Clone the upgrade branch and review its commit and files first:

```bash
git clone --branch codex/adaptive-hermes-teams --single-branch \
  https://github.com/Allura-Ecosystem/hermes-team-ram-durham.git \
  ./hermes-team-ram-durham
```

For that reviewed, committed local checkout, the current Hermes CLI accepts a
Git file URL. From its parent directory:

```bash
reviewed_checkout="$PWD/hermes-team-ram-durham"
hermes plugins install "file://$reviewed_checkout" --no-enable
hermes plugins enable team-ram-durham
```

The installer clones the local repository's committed HEAD; it does not include
uncommitted edits. A URL fragment selects a plugin subdirectory, not a branch.
Validate in a staging Hermes home first. Retain an existing installation as a
rollback copy before replacing it. Do not use `--force` on a modified installation
without reviewing and preserving those changes. Restart Hermes after replacing
plugin files.

## Canonical sources and updates

`source-locks.json` pins both standalone repositories. `agents/`, `skills/` and
`policies/` are generated; edit team behavior in its canonical repository.
`SOURCE_PROVENANCE.json` records each exported path, source blob and SHA-256.

```bash
python3 scripts/sync_sources.py --check
python3 scripts/sync_sources.py --sync
```

Default source checkouts are adjacent `../allura-team-ram` and `../team-durham`.
Use `--ram-source /path/to/repo --durham-source /path/to/repo` to override paths.
Only committed Git objects at the pins are read; dirty worktrees are ignored.
Origins, versions, export roots and links are validated. Sync does not fetch,
install, alter runtime configuration, or write to Allura Brain. The invocation-
disabled RAM Figma skill and Python cache files are excluded.

## Validate

```bash
python3 -m unittest discover -s tests -v
python3 scripts/sync_sources.py --check
```

Run `tests/test_native_hermes.py` with the Python interpreter from the actual
Hermes installation. It uses the real loader, tool registry, skill reader and
command injection API in an isolated temporary Hermes home. On an interpreter
without Hermes, those integration checks skip explicitly. Tests use no model
calls, network requests or credentials; they do not certify live model outcomes.

Official SDK reference: [Hermes plugin documentation](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/plugins/index.md).
