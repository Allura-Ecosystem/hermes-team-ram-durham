from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from typing import Callable

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
        self.dispatched: list[tuple[str, dict]] = []

    def register_skill(self, name: str, path: Path) -> None:
        assert isinstance(path, Path)
        assert path.exists()
        self.skills[name] = path

    def register_command(self, name: str, handler, description: str = "", args_hint: str = "") -> None:
        del description, args_hint
        self.commands[name] = handler

    def register_hook(self, name: str, callback) -> None:
        self.hooks[name] = callback

    def dispatch_tool(self, name: str, args: dict) -> str:
        self.dispatched.append((name, args))
        return '{"status":"dispatched"}'


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

    def test_persona_command_dispatches_real_worker(self) -> None:
        result = self.ctx.commands["brooks"]("Design a bounded execution harness")
        self.assertEqual(result, '{"status":"dispatched"}')
        self.assertEqual(len(self.ctx.dispatched), 1)
        tool, args = self.ctx.dispatched[0]
        self.assertEqual(tool, "delegate_task")
        self.assertEqual(args["goal"], "Design a bounded execution harness")
        self.assertEqual(args["role"], "leaf")
        self.assertIn("ACTIVE PERSONA: brooks", args["context"])
        self.assertIn("CANONICAL ROLE CARD", args["context"])
        self.assertIn("https://mcp.faithmeats.org/mcp", args["context"])
        self.assertIn("Never use or suggest a LAN/private-IP service path", args["context"])

    def test_empty_persona_command_does_not_dispatch(self) -> None:
        result = self.ctx.commands["woz"]("   ")
        self.assertEqual(result, "Usage: /woz <task>")
        self.assertEqual(self.ctx.dispatched, [])


if __name__ == "__main__":
    unittest.main()
