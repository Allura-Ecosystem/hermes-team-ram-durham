"""Team RAM + Team Durham plugin for Hermes.

Registers:
- Team RAM personas (Brooks, Woz, Jobs, Scout, Pike, Fowler, Bellard, Carmack,
  Knuth, Hightower, Bahari) as slash commands.
- Team Durham personas (brand-orchestrator, brand-strategist, copywriter,
  visual-director, data-analyst, evidence-collector, qa-reviewer,
  reality-checker, scout-recon, workflow-architect, agentic-trust-architect,
  brand-kit-builder, openagent) as slash commands.
- All bundled SKILL.md files under skills/ as plugin skills.
- A post_tool_call hook that logs tool usage for the Allura audit trail.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).resolve().parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

# name -> (description, role-card path relative to plugin dir)
# Role cards are the canonical agent definitions; the slash command injects
# the card as a workflow instruction so the persona behaves faithfully.
TEAM_RAM_PERSONAS = {
    "brooks": ("Route work through Brooks, the system architect.", "agents/ram/brooks.md"),
    "woz": ("Route work through Woz, the primary builder.", "agents/ram/woz.md"),
    "jobs": ("Route work through Jobs, the intent gate and scope owner.", "agents/ram/jobs.md"),
    "scout": ("Route work through Scout, recon and discovery.", "agents/ram/scout.md"),
    "pike": ("Route work through Pike, the interface and simplicity gate.", "agents/ram/pike.md"),
    "fowler": ("Route work through Fowler, the maintainability gate.", "agents/ram/fowler.md"),
    "bellard": ("Route work through Bellard, performance and diagnostics.", "agents/ram/bellard.md"),
    "carmack": ("Route work through Carmack, performance and optimization.", "agents/ram/carmack.md"),
    "knuth": ("Route work through Knuth, the data architect.", "agents/ram/knuth.md"),
    "hightower": ("Route work through Hightower, DevOps.", "agents/ram/hightower.md"),
    "bahari": ("Route work through Bahari, the memory curator.", "agents/ram/bahari.md"),
}

TEAM_DURHAM_PERSONAS = {
    "brand-orchestrator": ("Route governed Team Durham brand production work.", "agents/durham/brand-orchestrator.md"),
    "brand-strategist": ("Route work through the brand strategist.", "agents/durham/brand-strategist.md"),
    "copywriter": ("Route work through the copywriter.", "agents/durham/copywriter.md"),
    "visual-director": ("Route work through the visual director.", "agents/durham/visual-director.md"),
    "data-analyst": ("Route work through the data analyst.", "agents/durham/data-analyst.md"),
    "evidence-collector": ("Route work through the evidence collector.", "agents/durham/evidence-collector.md"),
    "qa-reviewer": ("Route work through the QA reviewer.", "agents/durham/qa-reviewer.md"),
    "reality-checker": ("Route work through the reality checker.", "agents/durham/reality-checker.md"),
    "scout-recon": ("Route work through Durham scout-recon.", "agents/durham/scout-recon.md"),
    "workflow-architect": ("Route work through the workflow architect.", "agents/durham/workflow-architect.md"),
    "agentic-trust-architect": ("Route work through the agentic trust architect.", "agents/durham/agentic-trust-architect.md"),
    "brand-kit-builder": ("Route work through the brand kit builder.", "agents/durham/brand-kit-builder.md"),
    "openagent": ("Route work through the Durham openagent fallback.", "agents/durham/openagent.md"),
}

ALL_PERSONAS = {**TEAM_RAM_PERSONAS, **TEAM_DURHAM_PERSONAS}


def _load_role_card(rel_path: str) -> str:
    """Read a role card file, returning its text or a fallback message."""
    path = _PLUGIN_DIR / rel_path
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        logger.warning("team-ram-durham: could not read role card %s: %s", rel_path, error)
        return f"# {rel_path}\n\n(Role card not bundled in this plugin.)"


def _make_persona_handler(persona: str, role_card: str):
    """Return a slash-command handler that injects the role card."""
    def handler(raw_args: str, **kwargs) -> str:
        del kwargs
        card = _load_role_card(role_card)
        return json.dumps({
            "persona": persona,
            "instruction": (
                f"You are operating as the {persona} persona from Team RAM/Durham.\n"
                f"Adopt the role card below as your governing instructions.\n\n"
                f"User request: {raw_args}\n\n"
                f"--- ROLE CARD ---\n{card}"
            ),
        })
    return handler


def _register_skills(ctx) -> int:
    """Register every bundled SKILL.md as a plugin skill. Returns count."""
    count = 0
    if not _SKILLS_DIR.is_dir():
        return 0
    for skill_dir in sorted(_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        # ctx.register_skill(name, path) namespaces as plugin:skill
        try:
            ctx.register_skill(skill_dir.name, skill_dir)
            count += 1
        except Exception as error:  # noqa: BLE001 - one bad skill must not block the rest
            logger.warning("team-ram-durham: failed to register skill %s: %s", skill_dir.name, error)
    return count


def _on_post_tool_call(tool_name, args, result, task_id, **kwargs):
    """Log tool usage for the Allura audit trail."""
    del args, result, task_id, kwargs
    logger.debug("team-ram-durham: tool called: %s", tool_name)


def register(ctx):
    """Wire personas, skills, and hooks into Hermes."""
    # 1. Register every bundled skill.
    skill_count = _register_skills(ctx)
    logger.info("team-ram-durham: registered %d bundled skills", skill_count)

    # 2. Register each persona as a slash command.
    for persona, (description, role_card) in ALL_PERSONAS.items():
        ctx.register_command(
            persona,
            _make_persona_handler(persona, role_card),
            description=description,
        )

    # 3. Register a post_tool_call hook for audit logging.
    ctx.register_hook("post_tool_call", _on_post_tool_call)

    logger.info(
        "team-ram-durham: registered %d personas (%d RAM, %d Durham)",
        len(ALL_PERSONAS),
        len(TEAM_RAM_PERSONAS),
        len(TEAM_DURHAM_PERSONAS),
    )
