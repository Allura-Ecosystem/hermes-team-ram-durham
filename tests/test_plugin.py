from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from typing import Callable
from unittest.mock import patch

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("team_ram_durham_plugin", PLUGIN_ROOT / "__init__.py")
assert SPEC and SPEC.loader
PLUGIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLUGIN)


class FakeContext:
    def __init__(self) -> None:
        self.skills: dict[str, Path] = {}
        self.commands: dict[str, Callable[[str], str]] = {}
        self.hooks: dict[str, object] = {}

    def register_skill(self, name: str, path: Path) -> None:
        assert isinstance(path, Path)
        assert path.exists()
        self.skills[name] = path

    def register_command(self, name: str, handler, description: str = "", args_hint: str = "") -> None:
        del description, args_hint
        self.commands[name] = handler

    def register_hook(self, name: str, callback) -> None:
        self.hooks[name] = callback

class PluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = FakeContext()
        PLUGIN.register(self.ctx)

    def test_registers_personas_skills_and_hook(self) -> None:
        self.assertEqual(len(self.ctx.commands), 24)
        self.assertIn("brooks", self.ctx.commands)
        self.assertIn("brand-orchestrator", self.ctx.commands)
        self.assertGreaterEqual(len(self.ctx.skills), 200)
        self.assertIn("post_tool_call", self.ctx.hooks)

    def test_persona_command_runs_real_worker(self) -> None:
        with patch.object(PLUGIN, "_run_persona_worker", return_value="worker result") as run:
            result = self.ctx.commands["brooks"]("Design a bounded execution harness")
        self.assertEqual(result, "worker result")
        persona, card, task = run.call_args.args
        self.assertEqual(persona, "brooks")
        self.assertEqual(task, "Design a bounded execution harness")
        self.assertIn("Brooks", card)

    def test_empty_persona_command_does_not_dispatch(self) -> None:
        result = self.ctx.commands["woz"]("   ")
        self.assertEqual(result, "Usage: /woz <task>")

    def test_worker_uses_safe_argv_and_extracts_final_response(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="startup noise\nsession_id: test-session\nWORKER_OK\n",
            stderr="",
        )
        with patch.object(PLUGIN.subprocess, "run", return_value=completed) as run:
            result = PLUGIN._run_persona_worker("brooks", "# Brooks role", "Plan it")
        self.assertEqual(result, "WORKER_OK")
        argv = run.call_args.args[0]
        self.assertEqual(argv[:3], ["hermes", "chat", "-Q"])
        self.assertIn("--max-turns", argv)
        prompt = argv[-1]
        self.assertIn("ACTIVE PERSONA: brooks", prompt)
        self.assertIn("USER TASK:\nPlan it", prompt)
        self.assertIn("https://mcp.faithmeats.org/mcp", prompt)
        self.assertIn("Never use or suggest a LAN/private-IP service path", prompt)
        self.assertNotIn("shell", run.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
