"""Team RAM and Durham guidance in the active Hermes conversation.

No subprocess workers, model overrides, memory-provider registration, or hidden
network calls. Persona guidance does not change the host's tool permissions.
"""
from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PLUGIN_NAME = "team-ram-durham"
TEAMS = {
    "ram": {
        "chair": "brooks",
        "group_id": "allura-system",
        "roles": ("brooks", "woz", "jobs", "scout", "pike", "fowler", "bellard", "carmack", "knuth", "hightower"),
        "policy": "policies/ram/adaptive-workflow.md",
    },
    "durham": {
        "chair": "brand-orchestrator",
        "group_id": "allura-team-durham",
        "roles": ("brand-orchestrator", "brand-strategist", "copywriter", "visual-director", "data-analyst", "qa-reviewer", "brand-kit-builder"),
        "policy": "policies/durham/governance/adaptive-workflow.md",
    },
}


def _read(relative: str) -> str:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Plugin reference escapes its package")
    return path.read_text(encoding="utf-8")


def _body(text: str) -> str:
    if text.startswith("---\n"):
        _, separator, remainder = text[4:].partition("\n---\n")
        if separator:
            return remainder.strip()
    return text.strip()


def _adapter(team: str) -> str:
    menu = (
        'On RAM activation or explicit menu/help/MH requests, load '
        'skill_view(name="team-ram-durham:ram-allura-menu"), show the canonical '
        'menu in chat, and recommend the next applicable step for the task. '
        'Menu entries are skill routes, not Hermes slash commands. '
        'Do not repeat the menu during ordinary work.\n'
        'Hermes Setup and Doctor override the canonical Bun/source-checkout '
        'diagnostic command: run this read-only installed-bundle check with the '
        'host shell tool: python3 '
        + shlex.quote(str(ROOT / 'scripts' / 'doctor.py')) + '. '
        'It needs no Bun, source checkout, network, configuration or credentials. '
        'If shell/Python is unavailable, report diagnosis unavailable and show '
        'the command; never claim it ran. Setup uses the same check and explains '
        'any missing capability; it does not install or edit configuration. '
        'Report Brain separately: unverified unless an exposed governed tool '
        'returns a scoped receipt.\n'
        if team == "ram" else ""
    )
    tenant = TEAMS[team]["group_id"]
    return f"""HERMES ADAPTER — active conversation, no new worker
Use this selected persona as task guidance, subordinate to the host's system,
developer, repository and direct user instructions. Host instructions and actual
Hermes tool schemas override foreign-runtime examples in the source role card.
Continue with the current configured model and permissions; do not change models,
spawn a worker, or install anything merely to activate a persona. Loading guidance
is not execution. Delegate only independent work when the user/runtime permits it.
Choose quick, standard, or sensitive routing from the adaptive workflow; keep one
accountable owner and reuse valid context for the same task, project, tenant,
workspace revision and authority. Refresh affected dependencies when these change.
Load local context first, then relevant Brain context through configured Hermes
MCP tools if available. Every memory operation must explicitly use {tenant}; never
fall back to a provider's default tenant or borrow another project's recall.
Use the authenticated host principal; a persona name grants no new permissions.
If Brain cannot serve this scope, report degraded local-only context and continue
safe work. Never claim a memory read/write, delegation, or validation without a
real receipt. Semantic promotion and external shipping retain human approval gates.
Use 1–3 relevant bundled skills through skill_view with names
{PLUGIN_NAME}:{team}-<skill>. These are read-only plugin resources, not agent
executors. Source paths for this team are under {ROOT / 'skills' / team};
role cards under {ROOT / 'agents' / team}; shared policy references under
{ROOT / 'policies' / team}. Resolve foreign .opencode/skills references against
the bundled skills; resolve Durham governance/contracts references under policies.
Use actual available tools rather than copied Claude/Codex/OpenCode tool names.
Respect read-only reviewer roles: report findings and let a producer fix them.
This plugin does not enforce a per-role tool sandbox; any task requiring enforced
isolation must use a host-supported restricted context, or report that limitation.
{menu}Finish authorized work with artifact paths, meaningful checks and limitations.
Persist one concise substantive outcome only if a governed Brain write succeeds.
"""


def _guidance(team: str, role: str, task: str) -> dict[str, Any]:
    if team not in TEAMS:
        raise ValueError("team must be ram or durham")
    config = TEAMS[team]
    selected = role or str(config["chair"])
    if selected not in config["roles"]:
        raise ValueError(f"Unknown {team} role: {selected}")
    card = _body(_read(f"agents/{team}/{selected}.md"))
    policy = _read(str(config["policy"]))
    return {
        "status": "guidance_loaded",
        "execution_started": False,
        "team": team,
        "role": selected,
        "group_id": config["group_id"],
        "model": "inherit",
        "task": task,
        "instructions": f"{_adapter(team)}\nADAPTIVE WORKFLOW\n{policy}\nSELECTED ROLE\n{card}",
        "entry_skill": f"{PLUGIN_NAME}:{team}",
    }


def team_tool(args: dict[str, Any], **kwargs: Any) -> str:
    """Load bounded guidance; performs no task, model, process or memory I/O."""
    del kwargs
    try:
        if not isinstance(args, dict):
            raise ValueError("arguments must be an object")
        team, role, task = args.get("team"), args.get("role", ""), args.get("task", "")
        if not all(isinstance(value, str) for value in (team, role, task)):
            raise ValueError("team, role and task must be strings")
        return json.dumps(_guidance(team, role, task))
    except (OSError, ValueError) as error:
        return json.dumps({"status": "error", "execution_started": False, "error": str(error)})


def _command(ctx: Any, team: str, role: str, command: str):
    def handler(raw_args: str, **kwargs: Any) -> str | None:
        del kwargs
        task = raw_args.strip()
        if not task:
            roles = ", ".join(str(item) for item in TEAMS[team]["roles"])
            return f"Usage: /{command} <task>\n{team.upper()} roles: {roles}"
        try:
            guidance = _guidance(team, role, task)
        except (OSError, ValueError) as error:
            return f"Task not started: {error}"
        prompt = (
            f"User selected {team}/{guidance['role']} for this task:\n{task}\n\n"
            f"{guidance['instructions']}"
        )
        inject = getattr(ctx, "inject_message", None)
        if callable(inject) and inject(prompt, role="user"):
            return None  # Hermes queues the turn; do not print a fake result.
        return (
            "Task not started: this Hermes surface cannot queue a plugin command. "
            f"Send a normal message asking the active agent to use allura_team "
            f"with team={team!r}, role={guidance['role']!r}, task={task!r}. "
            "It will continue in the current conversation."
        )
    return handler


def register(ctx: Any) -> None:
    ctx.register_tool(
        name="allura_team",
        toolset="allura_teams",
        schema={
            "name": "allura_team",
            "description": "Load Team RAM coding or Team Durham brand role and adaptive workflow for execution in this conversation. Use when asked to work with either team. Returns guidance, not a completed task; keeps the host model and permissions. RAM roles: " + ", ".join(TEAMS["ram"]["roles"]) + ". Durham roles: " + ", ".join(TEAMS["durham"]["roles"]),
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {"type": "string", "enum": ["ram", "durham"]},
                    "role": {"type": "string", "description": "Optional role; defaults to this team's chair."},
                    "task": {"type": "string", "description": "The user's bounded task, if known."},
                },
                "required": ["team"],
                "additionalProperties": False,
            },
        },
        handler=team_tool,
        description="Team RAM and Durham role guidance",
    )
    for team, config in TEAMS.items():
        ctx.register_skill(team, ROOT / "workflows" / team / "SKILL.md")
        for path in sorted((ROOT / "skills" / team).glob("*/SKILL.md")):
            # Hermes reads the supplied path as a FILE, not a skill directory.
            ctx.register_skill(f"{team}-{path.parent.name}", path)
        ctx.register_command(team, _command(ctx, team, str(config["chair"]), team), description=f"Work with Team {team.upper()} in this conversation", args_hint="<task>")
        for role in config["roles"]:
            name = f"{team}-{role}"
            ctx.register_command(name, _command(ctx, team, role, name), description=f"Use {team}/{role} in this conversation", args_hint="<task>")
