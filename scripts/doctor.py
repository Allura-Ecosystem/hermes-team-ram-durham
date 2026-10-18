"""Read-only standalone bundle checks; Python stdlib only, no source checkout."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_RAM_SKILLS = {
    'allura-memory-skill', 'allura-menu', 'code-review', 'multi-search',
    'party-mode', 'roundtable', 'systematic-debugging-memory',
    'team-ram-cowork', 'team-ram-doctor', 'team-ram-setup',
}


def diagnose(root: Path) -> dict:
    findings = []

    def read(relative: str) -> bytes:
        path = root / relative
        if (Path(relative).is_absolute() or '..' in Path(relative).parts
                or not path.resolve().is_relative_to(root.resolve())
                or any(parent.is_symlink() for parent in (path, *path.parents)
                       if parent != root.parent)):
            raise ValueError(f'unsafe bundle path: {relative}')
        return path.read_bytes()

    version = None
    checked = 0
    try:
        manifest = read('plugin.yaml').decode()
        if not re.search(r'^name: team-ram-durham$', manifest, re.M):
            raise ValueError('unexpected plugin name')
        match = re.search(r'^version: "([0-9]+\.[0-9]+\.[0-9]+)"$', manifest, re.M)
        if not match:
            raise ValueError('missing or invalid manifest version')
        version = match.group(1)
        adapter = read('__init__.py').decode()
        tree = ast.parse(adapter)
        teams = next(ast.literal_eval(node.value) for node in tree.body
                     if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'TEAMS'
                             for target in node.targets))
        if set(teams) != {'ram', 'durham'}:
            raise ValueError('missing team declaration')
        if not any(isinstance(node, ast.FunctionDef) and node.name == 'register'
                   for node in tree.body):
            raise ValueError('missing plugin registration adapter')
        if "ROOT / 'scripts' / 'doctor.py'" not in adapter:
            raise ValueError('missing Hermes Setup/Doctor route')
        for team, config in teams.items():
            read(f'workflows/{team}/SKILL.md')
            read(config['policy'])
            expected_roles = {f'{role}.md' for role in config['roles']}
            if config['chair'] not in config['roles']:
                raise ValueError(f'{team} chair is not declared')
            if {path.name for path in (root / 'agents' / team).glob('*.md')} != expected_roles:
                raise ValueError(f'{team} role surface differs from declaration')
            for role in config['roles']:
                read(f'agents/{team}/{role}.md')
        if {p.parent.name for p in (root / 'skills/ram').glob('*/SKILL.md')} != PUBLIC_RAM_SKILLS:
            raise ValueError('RAM public skill surface differs')
        provenance = json.loads(read('SOURCE_PROVENANCE.json'))
        locks = json.loads(read('source-locks.json'))
        locks_hash = hashlib.sha256(json.dumps(locks, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if locks_hash != provenance['sourceLocksSha256']:
            raise ValueError('source locks differ from bundled provenance')
        files = provenance['files']
        if not files:
            raise ValueError('empty provenance file inventory')
        actual = {p.relative_to(root).as_posix() for directory in ('agents', 'skills', 'policies')
                  for p in (root / directory).rglob('*') if p.is_file() or p.is_symlink()}
        if actual != set(files):
            raise ValueError('generated file inventory differs from provenance')
        for relative, receipt in sorted(files.items()):
            if hashlib.sha256(read(relative)).hexdigest() != receipt['sha256']:
                findings.append(f'content hash differs: {relative}')
            checked += 1
    except (OSError, ValueError, KeyError, TypeError, SyntaxError, StopIteration) as error:
        findings.append(str(error) or 'missing adapter team declaration')
    return {'status': 'fail' if findings else 'pass', 'version': version,
            'files_checked': checked, 'findings': findings,
            'brain': 'unverified (local bundle check only)',
            'scope': 'installed bundle structure and recorded hashes; not remote authenticity or live runtime health'}


if __name__ == '__main__':
    result = diagnose(ROOT)
    print(json.dumps(result, indent=2))
    sys.exit(1 if result['status'] == 'fail' else 0)
