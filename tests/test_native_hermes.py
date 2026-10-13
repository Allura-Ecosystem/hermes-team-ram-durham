"""Integration smoke tests against the installed Hermes SDK, without a model call.

Run with the Hermes virtualenv Python; ordinary Python skips if Hermes is absent.
The manager, context, tool registry, command dispatch and skill_view are real.
Only the application-owned CLI queue endpoint is represented by a small fixture.
An isolated Hermes home prevents reading the operator's config or credentials.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path
from queue import Queue
import tempfile
import unittest
from unittest.mock import patch

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SDK_AVAILABLE = importlib.util.find_spec("hermes_cli") is not None
RAM_ROLES = {
    "brooks", "woz", "jobs", "scout", "pike", "fowler", "bellard",
    "carmack", "knuth", "hightower", "bahari",
}
DURHAM_ROLES = {
    "brand-orchestrator", "brand-strategist", "copywriter", "visual-director",
    "data-analyst", "evidence-collector", "qa-reviewer", "reality-checker",
    "scout-recon", "workflow-architect", "agentic-trust-architect",
    "brand-kit-builder", "openagent",
}


class CliQueues:
    """The actual CLI supplies these queues; no SDK behavior is reimplemented."""

    def __init__(self, running: bool = False) -> None:
        self._agent_running = running
        self._pending_input: Queue[str] = Queue()
        self._interrupt_queue: Queue[str] = Queue()


@unittest.skipUnless(SDK_AVAILABLE, "Hermes SDK absent; run with Hermes venv Python")
class NativeHermesTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_home = tempfile.TemporaryDirectory(prefix="allura-hermes-sdk-test-")
        self.addCleanup(temporary_home.cleanup)
        self.enterContext(patch.dict(os.environ, {"HERMES_HOME": temporary_home.name}))
        Path(temporary_home.name, "config.yaml").write_text("{}\n", encoding="utf-8")

        self.sdk = importlib.import_module("hermes_cli.plugins")
        registry_module = importlib.import_module("tools.registry")
        self.registry = registry_module.ToolRegistry()
        self.enterContext(patch.object(registry_module, "registry", self.registry))
        self.manager = self.sdk.PluginManager()
        # Use the real loader on this checkout only, not user or bundled plugins.
        self.manager._discovered = True
        self.enterContext(patch.object(self.sdk, "_plugin_manager", self.manager))
        manifest = self.manager._parse_manifest(
            PLUGIN_ROOT / "plugin.yaml", PLUGIN_ROOT, "project", ""
        )
        self.assertIsNotNone(manifest, "Hermes could not parse plugin.yaml")
        # Registration and subsequent activation must not launch workers or I/O.
        for target in ("subprocess.run", "subprocess.Popen", "os.system",
                       "socket.create_connection", "socket.socket.connect"):
            self.enterContext(patch(target, side_effect=AssertionError(f"Unexpected execution: {target}")))
        self.manager._load_plugin(manifest)
        loaded = self.manager._plugins[manifest.key or manifest.name]
        self.assertIsNone(loaded.error, f"Real Hermes registration failed: {loaded.error}")
        self.assertTrue(loaded.enabled)
        self.manifest = manifest
        self.loaded = loaded

    def command(self, name: str):
        handler = self.sdk.get_plugin_command_handler(name)
        self.assertIsNotNone(handler, f"Native slash command missing: {name}")
        return handler

    def tool_result(self, **arguments):
        raw = self.registry.dispatch("allura_team", arguments)
        self.assertIsInstance(raw, str, "Hermes tools must return serializable JSON text")
        return json.loads(raw)

    def test_real_loader_registers_read_only_tool_without_audit_hooks(self) -> None:
        self.assertEqual(self.loaded.tools_registered, ["allura_team"])
        self.assertEqual(self.registry.get_toolset_for_tool("allura_team"), "allura_teams")
        self.assertFalse(self.manager.has_hook("post_tool_call"))
        self.assertEqual(self.loaded.hooks_registered, [])
        self.assertEqual(self.manifest.provides_hooks, [])

    def test_registry_exposes_schema_to_the_model_without_extra_tool_authority(self) -> None:
        schema = self.registry.get_schema("allura_team")
        self.assertEqual(schema["name"], "allura_team")
        parameters = schema["parameters"]
        self.assertEqual(parameters["required"], ["team"])
        self.assertEqual(parameters["properties"]["team"]["enum"], ["ram", "durham"])
        self.assertEqual(set(parameters["properties"]), {"team", "role", "task"})
        self.assertFalse(parameters["additionalProperties"])
        definitions = self.registry.get_definitions({"allura_team"})
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["function"]["name"], "allura_team")

    def test_registry_dispatch_defaults_to_chair_and_returns_guidance_only(self) -> None:
        cli = CliQueues()
        self.manager._cli_ref = cli
        for team, role, tenant in (("ram", "brooks", "allura-system"),
                                   ("durham", "brand-orchestrator", "allura-team-durham")):
            with self.subTest(team=team):
                result = self.tool_result(team=team, task="Assess the approved scope")
                self.assertEqual(result["status"], "guidance_loaded")
                self.assertIs(result["execution_started"], False)
                self.assertEqual(result["role"], role)
                self.assertEqual(result["group_id"], tenant)
                self.assertEqual(result["model"], "inherit")
                self.assertEqual(result["task"], "Assess the approved scope")
                self.assertEqual(result["entry_skill"], f"team-ram-durham:{team}")
                policy_path = (PLUGIN_ROOT / "policies" / team /
                               ("governance/adaptive-workflow.md" if team == "durham" else "adaptive-workflow.md"))
                self.assertIn(policy_path.read_text(encoding="utf-8"), result["instructions"])
                self.assertIn("SELECTED ROLE", result["instructions"])
                self.assertIn("not enforce a per-role tool sandbox", result["instructions"])
                self.assertTrue(cli._pending_input.empty())
                self.assertTrue(cli._interrupt_queue.empty())

    def test_every_canonical_role_dispatches_within_its_declared_team(self) -> None:
        for team, roles in (("ram", RAM_ROLES), ("durham", DURHAM_ROLES)):
            for role in sorted(roles):
                with self.subTest(team=team, role=role):
                    result = self.tool_result(team=team, role=role)
                    self.assertEqual(result["status"], "guidance_loaded")
                    self.assertEqual(result["role"], role)
                    self.assertEqual(result["team"], team)
                    self.assertIs(result["execution_started"], False)

    def test_registry_rejects_missing_unknown_cross_team_and_traversal_roles(self) -> None:
        invalid = [
            {}, {"team": "unknown"}, {"team": None},
            {"team": "ram", "role": "brand-orchestrator"},
            {"team": "durham", "role": "brooks"},
            {"team": "ram", "role": "../../secret"},
            {"team": "ram", "role": 7}, {"team": "ram", "task": None},
        ]
        for arguments in invalid:
            with self.subTest(arguments=arguments):
                result = self.tool_result(**arguments)
                self.assertEqual(result["status"], "error")
                self.assertIs(result["execution_started"], False)
                self.assertIn("error", result)
                self.assertNotIn("instructions", result)

    def test_native_command_names_do_not_claim_bare_personas(self) -> None:
        expected = {"ram", "durham"}
        expected.update(f"ram-{role}" for role in RAM_ROLES)
        expected.update(f"durham-{role}" for role in DURHAM_ROLES)
        self.assertEqual(set(self.manager._plugin_commands), expected)
        for bare_name in RAM_ROLES | DURHAM_ROLES:
            with self.subTest(bare_name=bare_name):
                self.assertIsNone(self.sdk.get_plugin_command_handler(bare_name))

    def test_idle_cli_queues_guidance_and_task_in_current_conversation(self) -> None:
        cli = CliQueues()
        self.manager._cli_ref = cli
        task = "Inspect the acceptance evidence for the small widget change"
        response = self.command("ram-brooks")(task)
        queued = cli._pending_input.get_nowait()
        self.assertIn(task, queued)
        self.assertIn("Brooks", queued)
        self.assertIn("quick", queued.lower())
        self.assertIn("sensitive", queued.lower())
        self.assertTrue(cli._interrupt_queue.empty())
        self.assertTrue(cli._pending_input.empty())
        self.assertNotIn("completed", str(response).lower())

    def test_running_cli_queues_interrupt_through_real_context(self) -> None:
        cli = CliQueues(running=True)
        self.manager._cli_ref = cli
        task = "Review these brand artifacts against approved strategy"
        self.command("durham-qa-reviewer")(task)
        queued = cli._interrupt_queue.get_nowait()
        self.assertIn(task, queued)
        self.assertIn("read-only", queued.lower())
        self.assertTrue(cli._pending_input.empty())
        self.assertTrue(cli._interrupt_queue.empty())

    def test_team_entry_commands_queue_their_default_chair(self) -> None:
        for command, marker in (("ram", "Brooks"), ("durham", "Kotler")):
            with self.subTest(command=command):
                cli = CliQueues()
                self.manager._cli_ref = cli
                self.command(command)("Handle this bounded team task")
                queued = cli._pending_input.get_nowait()
                self.assertIn(marker, queued)
                self.assertIn("Handle this bounded team task", queued)

    def test_empty_command_neither_queues_nor_claims_work_started(self) -> None:
        cli = CliQueues()
        self.manager._cli_ref = cli
        response = self.command("ram-woz")("   ")
        self.assertIn("usage", str(response).lower())
        self.assertTrue(cli._pending_input.empty())
        self.assertTrue(cli._interrupt_queue.empty())

    def test_gateway_reports_not_started_and_offers_the_guidance_tool(self) -> None:
        self.manager._cli_ref = None
        for name in ("ram", "durham", "ram-brooks", "durham-brand-orchestrator"):
            with self.subTest(command=name):
                response = str(self.command(name)("Review the current scope"))
                self.assertIn("not started", response.lower())
                self.assertIn("allura_team", response)
                self.assertNotIn("completed", response.lower())

    def test_every_registered_skill_is_a_real_file_and_skill_view_can_read_it(self) -> None:
        skill_view = importlib.import_module("tools.skills_tool").skill_view
        registered = self.manager._plugin_skills
        expected = {
            f"team-ram-durham:{team}-{path.parent.name}": path
            for team in ("ram", "durham")
            for path in (PLUGIN_ROOT / "skills" / team).glob("*/SKILL.md")
        }
        # Workflow entry points are separate from the canonical skill bundles.
        workflow_paths = {PLUGIN_ROOT / "workflows" / team / "SKILL.md" for team in ("ram", "durham")}
        self.assertGreater(len(expected), 100, "Canonical skill bundles are missing")
        self.assertTrue(set(expected) <= set(registered), "Qualified canonical skills missing")
        actual_paths = {item["path"] for item in registered.values()}
        self.assertTrue(workflow_paths <= actual_paths, "RAM/Durham entry workflows missing")
        for name, registration in registered.items():
            with self.subTest(skill=name):
                path = registration["path"]
                self.assertTrue(path.is_file(), f"register_skill requires SKILL.md, not directory: {path}")
                self.assertEqual(path.name, "SKILL.md")
                if name in expected:
                    self.assertEqual(path, expected[name])
                payload = json.loads(skill_view(name, preprocess=False))
                self.assertTrue(payload.get("success"), payload.get("error"))
                self.assertEqual(payload["name"], name)
                self.assertIn(path.read_text(encoding="utf-8"), payload["content"])


if __name__ == "__main__":
    unittest.main()
