"""Run the public doctor command from a standalone installation, without Git."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DoctorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='hermes installed doctor ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'plugin'
        self.root.mkdir()
        for directory in ('agents', 'skills', 'policies', 'workflows', 'scripts'):
            shutil.copytree(ROOT / directory, self.root / directory,
                            ignore=shutil.ignore_patterns('__pycache__'))
        for name in ('__init__.py', 'plugin.yaml', 'source-locks.json', 'SOURCE_PROVENANCE.json'):
            shutil.copy2(ROOT / name, self.root / name)

    def check(self, expected):
        result = subprocess.run([sys.executable, '-B', str(self.root / 'scripts/doctor.py')],
                                cwd=self.root.parent, text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_standalone_install_passes_without_source_checkout(self):
        result = self.check(0)
        self.assertEqual(result['status'], 'pass')
        self.assertGreater(result['files_checked'], 200)
        self.assertIn('unverified', result['brain'])
        self.assertFalse((self.root / '.git').exists())
        self.assertFalse((self.root / 'package.json').exists())

    def test_tampered_skill_fails(self):
        (self.root / 'skills/ram/allura-menu/SKILL.md').write_text('modified menu')
        self.assertIn('content hash differs', ' '.join(self.check(1)['findings']))

    def test_missing_role_fails(self):
        (self.root / 'agents/ram/brooks.md').unlink()
        self.assertIn('role surface differs', ' '.join(self.check(1)['findings']))

    def test_missing_entry_workflow_fails(self):
        (self.root / 'workflows/ram/SKILL.md').unlink()
        self.check(1)

    def test_unlisted_skill_fails(self):
        path = self.root / 'skills/ram/unlisted/SKILL.md'
        path.parent.mkdir()
        path.write_text('unexpected skill')
        self.assertIn('public skill surface differs', ' '.join(self.check(1)['findings']))

    def test_missing_adapter_fails(self):
        (self.root / '__init__.py').unlink()
        self.check(1)

    def test_source_lock_tampering_fails(self):
        path = self.root / 'source-locks.json'
        locks = json.loads(path.read_text())
        locks['sources']['ram']['commit'] = '0' * 40
        path.write_text(json.dumps(locks))
        self.assertIn('source locks differ', ' '.join(self.check(1)['findings']))

    def test_symlinked_resource_fails(self):
        path = self.root / 'agents/ram/brooks.md'
        path.unlink()
        path.symlink_to(ROOT / 'agents/ram/brooks.md')
        self.assertIn('unsafe bundle path', ' '.join(self.check(1)['findings']))


if __name__ == '__main__':
    unittest.main()
