from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("team_ram_durham_plugin", ROOT / "__init__.py")
PLUGIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLUGIN)


class FakeContext:
    def __init__(self, interactive=True):
        self.skills = {}
        self.commands = {}
        self.tools = {}
        self.messages = []
        self.interactive = interactive

    def register_skill(self, name, path, **kwargs):
        assert path.is_file(), path
        self.skills[name] = path

    def register_command(self, name, handler, **kwargs):
        self.commands[name] = handler

    def register_tool(self, **kwargs):
        self.tools[kwargs['name']] = kwargs

    def inject_message(self, content, role='user'):
        if not self.interactive:
            return False
        self.messages.append((content, role))
        return True


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.ctx = FakeContext()
        PLUGIN.register(self.ctx)

    def test_registration_avoids_unprefixed_collisions_and_uses_skill_files(self):
        self.assertEqual(len(self.ctx.commands), 26)
        self.assertNotIn('brooks', self.ctx.commands)
        self.assertIn('ram-brooks', self.ctx.commands)
        self.assertIn('durham-qa-reviewer', self.ctx.commands)
        self.assertIn('ram-context7', self.ctx.skills)
        self.assertIn('durham-context7', self.ctx.skills)
        self.assertNotEqual(self.ctx.skills['ram-context7'], self.ctx.skills['durham-context7'])
        self.assertNotIn('ram-figma-create-new-file', self.ctx.skills)

    def test_command_queues_exact_task_in_active_session_once(self):
        task = 'Review file names; $(echo literal) stays a task string'
        result = self.ctx.commands['ram-pike'](task)
        self.assertIsNone(result)
        self.assertEqual(len(self.ctx.messages), 1)
        message, role = self.ctx.messages[0]
        self.assertEqual(role, 'user')
        self.assertIn(task, message)
        self.assertIn('allura-system', message)
        self.assertIn('per-role tool sandbox', message)
        self.assertIn('HERMES ADAPTER', message)

    def test_missing_task_does_not_start_work(self):
        self.assertIn('Usage: /ram-woz', self.ctx.commands['ram-woz']('   '))
        self.assertEqual(self.ctx.messages, [])

    def test_gateway_fallback_does_not_claim_execution(self):
        ctx = FakeContext(interactive=False)
        PLUGIN.register(ctx)
        result = ctx.commands['durham']('Write the approved brand copy')
        self.assertIn('Task not started', result)
        self.assertIn('allura_team', result)
        self.assertIn("team='durham'", result)
        self.assertEqual(ctx.messages, [])

    def test_tool_guidance_keeps_distinct_tenants_and_model_inheritance(self):
        for team, tenant in [('ram', 'allura-system'), ('durham', 'allura-team-durham')]:
            with self.subTest(team=team):
                result = json.loads(PLUGIN.team_tool({'team': team, 'task': 'plan'}))
                self.assertEqual(result['status'], 'guidance_loaded')
                self.assertFalse(result['execution_started'])
                self.assertEqual(result['group_id'], tenant)
                self.assertEqual(result['model'], 'inherit')
                self.assertIn('ADAPTIVE WORKFLOW', result['instructions'])
                self.assertIn('never\nfall back', result['instructions'])

    def test_invalid_input_cannot_read_arbitrary_files(self):
        for args in [None, {'team': []}, {'team': '../../'}, {'team': 'ram', 'role': '../../README'}, {'team': 'ram', 'task': 123}]:
            result = json.loads(PLUGIN.team_tool(args))
            self.assertEqual(result['status'], 'error')
            self.assertFalse(result['execution_started'])
        with self.assertRaises(ValueError):
            PLUGIN._read('../README.md')

    def test_missing_role_or_policy_fails_closed(self):
        with patch.object(PLUGIN, '_read', side_effect=FileNotFoundError('missing bundle')):
            self.assertEqual(json.loads(PLUGIN.team_tool({'team': 'ram'}))['status'], 'error')
            self.assertIn('Task not started', self.ctx.commands['ram']('work'))
        self.assertEqual(self.ctx.messages, [])

    def test_every_role_loads_from_current_bundle(self):
        for team, config in PLUGIN.TEAMS.items():
            for role in config['roles']:
                with self.subTest(team=team, role=role):
                    result = json.loads(PLUGIN.team_tool({'team': team, 'role': role}))
                    self.assertEqual(result['status'], 'guidance_loaded')
                    self.assertEqual(result['role'], role)


if __name__ == '__main__':
    unittest.main()
