#!/usr/bin/env python3
"""Generate Hermes prompt assets from pinned local Git objects; never fetch."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANAGED = ("agents", "skills", "policies")
PROVENANCE = "SOURCE_PROVENANCE.json"


def git(repo: Path, *args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True).stdout


def safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value or str(path) != value:
        raise ValueError(f"unsafe relative path: {value!r}")
    return value


def require_public_asset(path: str) -> None:
    parts = PurePosixPath(path).parts
    forbidden = {".git", "node_modules", "__pycache__", "clients", "sessions", "runtime-data", ".credentials"}
    if any(part in forbidden or part == ".env" or (part.startswith(".env.") and part not in {".env.example", ".env.template"}) for part in parts):
        raise ValueError(f"private/runtime asset in public source selection: {path}")
    if PurePosixPath(path).suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        raise ValueError(f"credential asset in public source selection: {path}")


def within(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def normalized_remote(value: str) -> str:
    return value.strip().removesuffix(".git").removeprefix("git+")


def load_tree(repo: Path, lock: dict) -> dict[str, tuple[str, str, bytes]]:
    commit = lock["commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("source commit must be a full Git object ID")
    origin = git(repo, "remote", "get-url", "origin").decode().strip()
    if normalized_remote(origin) != normalized_remote(lock["repository"]):
        raise ValueError(f"origin mismatch for {repo}: {origin}")
    resolved = git(repo, "rev-parse", f"{commit}^{{commit}}").decode().strip()
    if resolved != commit:
        raise ValueError("source pin does not resolve to the exact commit")
    entries = {}
    for record in git(repo, "ls-tree", "-rz", commit).split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        path = safe_path(name.decode())
        if kind == "blob":
            entries[path] = (mode, oid)
    # Read immutable blobs in one subprocess. Never inspect the source worktree.
    oids = sorted({oid for _, oid in entries.values()})
    raw = git(repo, "cat-file", "--batch", data=("\n".join(oids) + "\n").encode())
    blobs = {}
    offset = 0
    for oid in oids:
        end = raw.index(b"\n", offset)
        actual, kind, size = raw[offset:end].decode().split()
        if actual != oid or kind != "blob":
            raise ValueError("unexpected Git batch response")
        offset = end + 1
        length = int(size)
        blobs[oid] = raw[offset:offset + length]
        offset += length + 1
    tree = {path: (mode, oid, blobs[oid]) for path, (mode, oid) in entries.items()}
    package = json.loads(tree["package.json"][2])
    if package["version"] != lock["version"]:
        raise ValueError("pinned source package version differs from lock")
    return tree


def resolve_blob(path: str, tree: dict, allowed: list[str], excluded: list[str], seen=()):
    require_public_asset(path)
    if path in seen:
        raise ValueError(f"source symlink cycle: {path}")
    if not any(within(path, prefix) for prefix in allowed) or any(within(path, prefix) for prefix in excluded):
        raise ValueError(f"source symlink escapes public allowlist: {path}")
    if path not in tree:
        raise ValueError(f"missing source blob or unsupported directory symlink: {path}")
    mode, oid, content = tree[path]
    if mode == "120000":
        target = content.decode()
        if target.startswith("/") or "\\" in target:
            raise ValueError(f"source symlink escapes package: {path}")
        target = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
        safe_path(target)
        return resolve_blob(target, tree, allowed, excluded, (*seen, path))
    if mode not in ("100644", "100755"):
        raise ValueError(f"unsupported source mode: {mode}")
    return path, mode, oid, content


def build_bundle(locks: dict, repositories: dict[str, Path]) -> dict[str, tuple[bytes, int]]:
    if locks.get("schemaVersion") != 1:
        raise ValueError("unsupported source-lock schema")
    outputs = {}
    receipts = {}
    for namespace, lock in sorted(locks["sources"].items()):
        if namespace not in ("ram", "durham"):
            raise ValueError(f"unsupported namespace: {namespace}")
        mappings = lock["mappings"]
        allowed = [safe_path(item["source"]) for item in mappings]
        excluded = [safe_path(item) for item in lock.get("exclude", [])]
        tree = load_tree(repositories[namespace], lock)
        # The selected roots must also be declared public by the source package.
        public = json.loads(tree["package.json"][2])["files"]
        public_roots = [item.removesuffix("/**").rstrip("/") for item in public]
        for prefix in allowed:
            if not any(within(prefix, root) for root in public_roots):
                raise ValueError(f"source root is not public: {prefix}")
        for mapping in mappings:
            prefix = mapping["source"]
            destination = safe_path(mapping["destination"])
            if not any(within(destination, f"{root}/{namespace}") for root in MANAGED):
                raise ValueError(f"destination outside namespace: {destination}")
            selected = [path for path in tree if within(path, prefix) and not any(within(path, ex) for ex in excluded)]
            if not selected:
                raise ValueError(f"empty public source mapping: {prefix}")
            for source_path in sorted(selected):
                output = destination + source_path[len(prefix):]
                if output in outputs:
                    raise ValueError(f"duplicate destination: {output}")
                resolved, mode, oid, content = resolve_blob(source_path, tree, allowed, excluded)
                outputs[output] = (content, 0o755 if mode == "100755" else 0o644)
                receipts[output] = {
                    "source": namespace, "repository": lock["repository"],
                    "commit": lock["commit"], "sourcePath": source_path,
                    "resolvedSourcePath": resolved, "blob": oid,
                    "sha256": hashlib.sha256(content).hexdigest(), "mode": mode,
                }
    provenance = {"schemaVersion": 1, "generatedBy": "scripts/sync_sources.py",
                  "sourceLocksSha256": hashlib.sha256(json.dumps(locks, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                  "sources": {name: {key: item[key] for key in ("repository", "commit", "version")}
                              for name, item in sorted(locks["sources"].items())},
                  "files": receipts}
    outputs[PROVENANCE] = ((json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode(), 0o644)
    return outputs


def check_bundle(root: Path, outputs: dict) -> list[str]:
    errors = []
    actual = set()
    for directory in MANAGED:
        base = root / directory
        if base.is_symlink():
            errors.append(f"unexpected generated directory symlink: {directory}")
            continue
        for current, dirs, files in os.walk(base, followlinks=False):
            for name in list(dirs):
                path = Path(current) / name
                if path.is_symlink():
                    actual.add(path.relative_to(root).as_posix())
                    dirs.remove(name)
            actual.update((Path(current) / name).relative_to(root).as_posix() for name in files)
    if (root / PROVENANCE).exists() or (root / PROVENANCE).is_symlink():
        actual.add(PROVENANCE)
    for name in sorted(actual - outputs.keys()):
        errors.append(f"unexpected generated file: {name}")
    for name, (content, mode) in outputs.items():
        path = root / name
        if name not in actual or path.is_symlink() or not path.is_file():
            errors.append(f"missing or unsafe generated file: {name}")
        elif path.read_bytes() != content or (path.stat().st_mode & 0o777) != mode:
            errors.append(f"generated file differs: {name}")
    return errors


def write_bundle(root: Path, outputs: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".source-sync-", dir=root) as temp:
        stage = Path(temp)
        for name, (content, mode) in outputs.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(mode)
        # Replace only this generator's owned trees, after all reads succeeded.
        for name in (*MANAGED, PROVENANCE):
            target = root / name
            if target.is_symlink() or target.is_file():
                target.unlink()
            elif target.exists():
                shutil.rmtree(target)
            staged = stage / name
            if staged.exists():
                staged.rename(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--sync", action="store_true")
    parser.add_argument("--ram-source", type=Path)
    parser.add_argument("--durham-source", type=Path)
    args = parser.parse_args()
    locks = json.loads((ROOT / "source-locks.json").read_text())
    repos = {name: (getattr(args, f"{name}_source") or ROOT / lock["defaultDirectory"]).resolve()
             for name, lock in locks["sources"].items()}
    outputs = build_bundle(locks, repos)
    if args.sync:
        write_bundle(ROOT, outputs)
    errors = check_bundle(ROOT, outputs)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Source parity passed: {len(outputs) - 1} assets, {len(locks['sources'])} pinned sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
