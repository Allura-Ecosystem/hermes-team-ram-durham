# Team RAM + Team Durham for Hermes

Native Hermes plugin **1.2.0**: 17 public role definitions and 87 namespaced
skills, using the active conversation's model, context and tools. Two entry
workflows bring the total to 89 registered skills. RAM has ten public personas
and ten public skills; Durham has seven specialist roles and 77 skills.

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
skill_view(name="team-ram-durham:ram-allura-menu")
skill_view(name="team-ram-durham:durham-brand-strategy")
```

Registered plugin skills are opt-in `skill_view` resources, not automatically
created slash commands. Load only 1–3 relevant skills. Both teams' copies are
kept separate, including skills with the same name.

## What changed in 1.2.0

- Refreshed immutable public sources to Team RAM `0.6.1-persona.20261018` and
  Durham `0.4.2-persona.20261018`.
- Exported RAM's ten public skill directories and ten individually allowlisted
  agent files. Retired internal skills and roles are no longer registered.
- Reduced Durham's roster to its seven current public role definitions.
- Registered the compact canonical RAM menu as
  `team-ram-durham:ram-allura-menu`. On activation or menu/help/MH requests, the
  active agent displays it in chat and recommends the next applicable step.
  These menu choices route to skills; they do not create new slash commands.
- Retained native Hermes skill-file registration, conversation command injection,
  and separate team tenant scopes. The memory provider remains a separate plugin.

The refresh uses committed source objects only; local source edits are excluded.
No live-model latency, cost or quality improvement has been measured.

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

The upgrade is maintained on the
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

## Setup and Doctor in Hermes

Choose **Setup** or **Doctor** from the chat menu. The adapter supplies the
absolute installed path to `python3 .../scripts/doctor.py` for the host shell.
From the installed plugin directory, the same read-only check is:

```bash
python3 scripts/doctor.py
```

This Hermes command replaces the canonical skills' Bun/source-checkout diagnostic.
It checks the manifest version format, declared roles, entry workflows, registration
adapter, RAM public skill surface, source lock digest and all recorded resource
hashes. It works without Git, source repositories, Bun, network or credentials.
A failing check exits nonzero. It never installs or repairs anything. If the
host lacks a shell or Python, the agent reports that limitation and shows the
command. Brain remains separately unverified without a scoped live tool receipt.
Recorded hashes prove local consistency, not remote authenticity or live runtime
health. Setup explains any missing capability using this same diagnostic.

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
install, alter runtime configuration, or write to Allura Brain. Only the current
public RAM skill surface and individual public agent files are selected; retired
internal roles and skill directories are not copied.

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
