"""Regression tests for the immutable public-source exporter (no network)."""
import importlib.util
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/sync_sources.py'
spec = importlib.util.spec_from_file_location('source_sync', SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
REMOTE = 'https://github.com/Allura-Ecosystem/allura-team-ram.git'

def run(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args]).decode().strip()

def commit(repo):
    run(repo, 'add', '.')
    run(repo, '-c', 'user.name=Source sync test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
    return run(repo, 'rev-parse', 'HEAD')

def make_source(tmp_path):
    repo = tmp_path / 'source'
    repo.mkdir()
    run(repo, 'init', '-q')
    run(repo, 'remote', 'add', 'origin', REMOTE)
    (repo / 'package.json').write_text(json.dumps({'version': '0.5.0', 'files': ['agents/**', '.opencode/skills/**']}))
    (repo / 'agents').mkdir()
    (repo / 'agents/brooks.md').write_text('# Brooks\nmodel: inherit\n')
    for name in ('review', 'figma-create-new-file'):
        skill = repo / '.opencode/skills' / name
        skill.mkdir(parents=True)
        disabled = 'disable-model-invocation: true\n' if name == 'figma-create-new-file' else ''
        (skill / 'SKILL.md').write_text(f'---\nname: {name}\n{disabled}---\n')
    (repo / '.opencode/skills/review/evidence.txt').write_text('public evidence')
    locks = {'schemaVersion': 1, 'sources': {'ram': {'repository': REMOTE, 'version': '0.5.0', 'commit': commit(repo), 'mappings': [{'source': 'agents', 'destination': 'agents/ram'}, {'source': '.opencode/skills', 'destination': 'skills/ram'}], 'exclude': ['.opencode/skills/figma-create-new-file']}}}
    return (repo, locks)

class SourceSyncTests(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='source-sync-test-')
        self.addCleanup(temporary.cleanup)
        self.tmp_path = Path(temporary.name)
        self.source = make_source(self.tmp_path)

    def test_dirty_worktree_is_ignored_and_assets_are_namespaced(self):
        repo, locks = self.source
        original = sync.build_bundle(locks, {'ram': repo})
        (repo / '.opencode/skills/review/SKILL.md').write_text('DIRTY replacement')
        (repo / '.opencode/skills/review/untracked.txt').write_text('not exported')
        (repo / 'package.json').write_text('invalid dirty package')
        self.assertEqual(sync.build_bundle(locks, {'ram': repo}), original)
        self.assertEqual(original['skills/ram/review/evidence.txt'][0], b'public evidence')
        self.assertFalse(any(('figma-create-new-file' in name for name in original)))
        provenance = json.loads(original[sync.PROVENANCE][0])
        receipt = provenance['files']['skills/ram/review/evidence.txt']
        self.assertEqual(receipt['commit'], locks['sources']['ram']['commit'])
        self.assertEqual(receipt['sourcePath'], '.opencode/skills/review/evidence.txt')
        self.assertEqual(len(receipt['sha256']), 64)

    def test_check_detects_tampering_and_sync_preserves_unowned_files(self):
        repo, locks = self.source
        outputs = sync.build_bundle(locks, {'ram': repo})
        target = self.tmp_path / 'bundle'
        target.mkdir()
        (target / '__init__.py').write_text('owned by runtime maintainer')
        (target / 'skills').mkdir()
        (target / 'skills/old-flat.md').write_text('old bundle')
        sync.write_bundle(target, outputs)
        self.assertEqual(sync.check_bundle(target, outputs), [])
        self.assertFalse((target / 'skills/old-flat.md').exists())
        (target / 'skills/ram/review/evidence.txt').write_text('tampered')
        self.assertIn('generated file differs: skills/ram/review/evidence.txt', sync.check_bundle(target, outputs))
        self.assertEqual((target / '__init__.py').read_text(), 'owned by runtime maintainer')

    def test_internal_file_symlink_is_materialized_with_provenance(self):
        repo, locks = self.source
        (repo / '.opencode/skills/review/linked.txt').symlink_to('evidence.txt')
        locks['sources']['ram']['commit'] = commit(repo)
        outputs = sync.build_bundle(locks, {'ram': repo})
        self.assertEqual(outputs['skills/ram/review/linked.txt'][0], b'public evidence')
        receipt = json.loads(outputs[sync.PROVENANCE][0])['files']['skills/ram/review/linked.txt']
        self.assertEqual(receipt['resolvedSourcePath'], '.opencode/skills/review/evidence.txt')

    def test_symlink_escape_fails_before_export(self):
        repo, locks = self.source
        (repo / 'private.txt').write_text('not public')
        (repo / '.opencode/skills/review/escape.txt').symlink_to('../../../private.txt')
        locks['sources']['ram']['commit'] = commit(repo)
        with self.assertRaisesRegex(ValueError, 'escapes public allowlist'):
            sync.build_bundle(locks, {'ram': repo})

    def test_unexpected_output_symlink_is_rejected_without_following_it(self):
        repo, locks = self.source
        outputs = sync.build_bundle(locks, {'ram': repo})
        target = self.tmp_path / 'bundle'
        sync.write_bundle(target, outputs)
        path = target / 'skills/ram/review/evidence.txt'
        path.unlink()
        path.symlink_to(repo / '.opencode/skills/review/evidence.txt')
        self.assertIn('missing or unsafe generated file: skills/ram/review/evidence.txt', sync.check_bundle(target, outputs))

    def test_wrong_origin_and_abbreviated_pin_are_rejected(self):
        repo, locks = self.source
        run(repo, 'remote', 'set-url', 'origin', 'https://example.invalid/other.git')
        with self.assertRaisesRegex(ValueError, 'origin mismatch'):
            sync.build_bundle(locks, {'ram': repo})
        locks['sources']['ram']['commit'] = '123abcd'
        with self.assertRaisesRegex(ValueError, 'full Git object ID'):
            sync.build_bundle(locks, {'ram': repo})

    def test_private_asset_in_public_directory_is_rejected(self):
        repo, locks = self.source
        (repo / '.opencode/skills/review/.env').write_text('synthetic test placeholder')
        locks['sources']['ram']['commit'] = commit(repo)
        with self.assertRaisesRegex(ValueError, 'private/runtime asset'):
            sync.build_bundle(locks, {'ram': repo})
if __name__ == '__main__':
    unittest.main()
