# Team RAM + Team Durham for Hermes

Use engineering and brand specialists in your current Hermes conversation.

This native plugin loads RAM and Durham role guidance, task skills, and the shared Allura chat menu. The active host supplies the model, context, tools, and permissions. Choose RAM for software delivery or Durham for brand strategy, copy, and production.

Version `1.3.1` bundles 17 public role definitions and 90 registered skills: ten RAM skills, 77 Durham skills, one shared Cowork menu, and two entry workflows. These are available definitions, not counts of running agents.

## Install

This checkout declares version `1.3.1`. Its immutable source pins are recorded
in `source-locks.json`; check the reviewed checkout version before installing.

Clone `main` and review its commit and files first:

```bash
git clone --branch main --single-branch \
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

## Memory and authority

This is a standalone team plugin, separate from the Allura Brain memory provider.
It neither changes `memory.provider` nor configures credentials or MCP servers.
Memory operations preserve the authenticated project/task scope. RAM's
`allura-system` and Durham's `allura-team-durham` are default hints requiring
confirmation by the active project and credentials. Loading a Council role does
not change the parent's validated group_id or authorization receipt. The guidance
tool returns `default_group_id` and `scope_status: inherit_authenticated_task`;
it does not assert tenant authorization. Never infer a tenant from a persona
or fall back to an unrelated provider tenant.
If the configured Brain cannot serve the team/project scope, report degraded
local-only context and continue safe work. Persona names do not change the
authenticated principal. Semantic promotion and external shipping retain human
approval gates.

An active Brain write hold must be honored. If an ordinary episodic outcome is
unexpectedly stored as semantic or attributed to `auto-curator` without requested
human-governed promotion, the guidance requires stopping further writes and
reporting the receipt for investigation. This instruction does not repair or
enforce backend promotion behavior. No live memory write is required to activate
a lead or run the package doctor.

Canonical role cards contain foreign-runtime examples. The Hermes adapter maps
their resources to this bundle and requires actual host schemas. Personas and
skills are instructions, **not enforced per-role tool sandboxes**. Read-only
reviewers must report findings; where enforced isolation is required, use a
host-supported restricted context or report the missing capability.

## Setup and Doctor in Hermes

Choose **More**, then **Setup** or **Doctor** from the chat menu. The adapter supplies the
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

`source-locks.json` pins RAM, Durham, and the Allura Cowork menu source. `agents/`, `skills/` and
`policies/` are generated; edit team behavior in its canonical repository.
`SOURCE_PROVENANCE.json` records each exported path, source blob and SHA-256.

```bash
python3 scripts/sync_sources.py --check
python3 scripts/sync_sources.py --sync
```

Default local checkout paths come from each source's `defaultDirectory` in
`source-locks.json`. Use `--ram-source /path/to/repo`,
`--durham-source /path/to/repo`, and `--cowork-source /path/to/repo` to override them.
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

## Chat menu

Brooks and Kotler activation shows the selected lead's documented **Commands**
menu from its full role card. The adapter loads `ram-allura-menu` for Brooks or
`durham-source-command-quick-commands` for Kotler. Shared Allura choices remain
under **More**, or serve as the default when no lead is selected:

| Choice | Purpose |
|---|---|
| Next steps | Recommend the next useful action |
| Help with a prompt | Turn an idea into a usable request |
| Council | Examine one decision with actual available specialists |
| Work | Carry out the authorized task |
| Loop | Work, check, and improve within an agreed limit |
| Validate | Compare results with criteria and evidence |
| More | Find additional installed workflows, Setup, or Doctor |

The selected lead keeps its voice, reasoning and task context through follow-ups
and compaction until the user switches. Activation includes a brief greeting,
evidence-based continuity, an honest reflection and a recommended next action.
Recalled lessons cite a fresh scoped Brain receipt's memory ID and date; current
judgment and unavailable or unrelated recall are identified explicitly. Startup
chatter is not written to memory. Clear tasks proceed directly without repeating
the activation ceremony.

Direct address is a conversational selection instruction. It does not register
bare `Brooks` or `Kotler` commands or prove that a host dispatched a role. Use the
registered `/ram` and `/durham` CLI commands or the `allura_team` tool as described
above. The bundled `cowork-allura-menu` skill is exported from an
immutable Allura Cowork source pin and needs no extra plugin installation.
Prompt help and bounded improvement loops work in the active conversation.
Council depends on the host's actual delegation capability; loading multiple
personas with `allura_team` does not execute independent specialists. Missing
delegation yields an explicit limitation and a proposed Council brief.

## Release history

<details>
<summary>Menu and source refreshes</summary>

### Version 1.3.1

- Refreshed immutable sources to RAM `0.6.3`, Durham `0.4.5`, and Cowork `0.4.1`.
- Aligned the native adapter and entry workflows with persistent Brooks/Kotler
  ownership, their own role menus, and shared choices under More.
- Required honest continuity and reflections with memory ID/date evidence for
  recalled lessons, while preserving ordinary follow-up voice and task context.
- Added guidance to honor a Brain write hold and stop further writes after an
  unexpected semantic/auto-curator outcome. Backend investigation remains separate.
- Retained the existing guidance tool and CLI queue behavior, host model,
  permissions, memory provider, credentials, and command registrations.

### Version 1.3.0

- Added the common seven-choice chat interaction from Allura Cowork 0.4.0.
- Updated RAM 0.6.2 and Durham 0.4.3 owning menu sources, preserving their public
  skill counts and domain routes under More.
- Made Council's real delegation dependency and bounded loop stopping rules
  explicit in native guidance. The adapter itself remains guidance loading.

### Previous refresh: 1.2.0

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


</details>
