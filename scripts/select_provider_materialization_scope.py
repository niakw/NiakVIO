#!/usr/bin/env python3
"""Select the minimum Provider v3 rematerialization scope for current-byte census."""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

GLOBAL_PROVIDER_PREFIXES = ("provider-bases/",)
GLOBAL_PROVIDER_INPUTS = {
    "scripts/provider_base_store.py",
    "scripts/apply_provider_overrides.py",
    "scripts/materialize_provider_v3_all.py",
    "scripts/materialize_provider_v3_one.py",
    "scripts/provider_patch_blocks.py",
    "scripts/provider_engine_normalizer.py",
    "scripts/provider_byte_stability.py",
}
PROVIDER_MAP_FILES = {
    "provider-overrides.json": ("provider_patches", "provider_capabilities"),
    "provider-hubs.json": ("providers",),
    "automation/provider-v3-static-knowledge.json": ("providers",),
}
PROVIDER_LIST_FILES = {
    "manifest.json": ("scrapers", "id"),
}
NEUTRAL_PREFIXES = (".github/", "tests/")
NEUTRAL_FILES = {
    "PROVIDER_CENSUS_STATUS.md",
    "MEMORY.md",
    "automation/provider-census-status.json",
    "automation/provider-census-proof-history.json",
    "automation/provider-authority-status.json",
    "automation/provider-repair-batch-plan-latest.json",
}


def norm(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def git_text(ref: str, path: str) -> str:
    if not ref:
        return ""
    completed = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else ""


def load_json_text(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def git_json(ref: str, path: str) -> dict[str, Any]:
    return load_json_text(git_text(ref, path))


def current_json(path: str) -> dict[str, Any]:
    try:
        return load_json_text((ROOT / path).read_text(encoding="utf-8"))
    except OSError:
        return {}


def changed_provider_keys(
    before: dict[str, Any],
    after: dict[str, Any],
    sections: tuple[str, ...],
) -> set[str]:
    providers: set[str] = set()
    for section in sections:
        old = before.get(section) if isinstance(before.get(section), dict) else {}
        new = after.get(section) if isinstance(after.get(section), dict) else {}
        for key in set(old) | set(new):
            if old.get(key) != new.get(key):
                provider = norm(key)
                if provider:
                    providers.add(provider)
    return providers


def changed_provider_rows(
    before: dict[str, Any],
    after: dict[str, Any],
    section: str,
    id_key: str,
) -> set[str]:
    def rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        raw = payload.get(section) if isinstance(payload.get(section), list) else []
        return {
            norm(row.get(id_key)): row
            for row in raw
            if isinstance(row, dict) and norm(row.get(id_key))
        }

    old = rows(before)
    new = rows(after)
    return {
        provider
        for provider in set(old) | set(new)
        if old.get(provider) != new.get(provider)
    }


def unscoped_override_change(before: dict[str, Any], after: dict[str, Any]) -> bool:
    scoped = {"provider_patches", "provider_capabilities"}
    return any(
        key not in scoped and before.get(key) != after.get(key)
        for key in set(before) | set(after)
    )


def transitively_imported_shared_patch_owners(
    path: str,
    before_overrides: dict[str, Any],
    after_overrides: dict[str, Any],
) -> set[str]:
    """Identify one-hop source-import owners of shared family Lego.

    A shared Core file with no statically attributable registered import still
    expands to ALL providers. Only a literal Python import in a registered
    provider script is accepted as proof of a narrower family blast radius.
    """
    if not path.startswith("scripts/provider_patches/") or not path.endswith(".py"):
        return set()
    # Global cross-provider identity/presentation patches have an independent
    # materializer owner and cannot be narrowed by unrelated wrapper imports.
    module = Path(path).stem
    if module.startswith(("global_", "core_")):
        return set()
    target_root = (ROOT / "scripts/provider_patches").resolve()
    owners: set[str] = set()
    checked: dict[str, bool] = {}
    for payload in (before_overrides, after_overrides):
        patches = payload.get("provider_patches")
        if not isinstance(patches, dict):
            continue
        for provider, row in patches.items():
            if not isinstance(row, dict):
                continue
            scripts: list[str] = []
            for key in ("provider_lego_scripts", "patch_scripts"):
                value = row.get(key)
                if isinstance(value, str):
                    scripts.append(value)
                elif isinstance(value, list):
                    scripts.extend(str(item) for item in value if isinstance(item, str))
            for script in scripts:
                if not script.startswith("scripts/provider_patches/") or ".." in Path(script).parts:
                    continue
                if script == path:
                    continue
                if script not in checked:
                    source = (ROOT / script).resolve()
                    if not source.is_relative_to(target_root) or not source.is_file():
                        checked[script] = False
                    else:
                        try:
                            tree = ast.parse(source.read_text(encoding="utf-8"))
                        except (OSError, UnicodeError, SyntaxError):
                            checked[script] = False
                        else:
                            checked[script] = any(
                                isinstance(node, ast.ImportFrom)
                                and (node.module or "").split(".")[-1] == module
                                or isinstance(node, ast.Import)
                                and any(alias.name.split(".")[-1] == module for alias in node.names)
                                for node in ast.walk(tree)
                            )
                if checked[script]:
                    item = norm(provider)
                    if item:
                        owners.add(item)
    return owners


def patch_script_owners(
    path: str,
    before_overrides: dict[str, Any],
    after_overrides: dict[str, Any],
) -> set[str]:
    owners: set[str] = set()
    for payload in (before_overrides, after_overrides):
        patches = payload.get("provider_patches")
        if not isinstance(patches, dict):
            continue
        for provider, row in patches.items():
            if not isinstance(row, dict):
                continue
            scripts: list[str] = []
            for key in ("provider_lego_scripts", "patch_scripts"):
                raw = row.get(key)
                if isinstance(raw, str):
                    scripts.append(raw)
                elif isinstance(raw, list):
                    scripts.extend(str(value) for value in raw)
            if path in scripts:
                provider_id = norm(provider)
                if provider_id:
                    owners.add(provider_id)
    return owners


def classify(
    changed_paths: list[str],
    before_docs: dict[str, dict[str, Any]],
    after_docs: dict[str, dict[str, Any]],
) -> tuple[str, list[str], list[str]]:
    providers: set[str] = set()
    reasons: list[str] = []

    for path in changed_paths:
        if any(path.startswith(prefix) for prefix in GLOBAL_PROVIDER_PREFIXES):
            return "all", [], [*reasons, f"global-prefix:{path}"]
        if path in GLOBAL_PROVIDER_INPUTS:
            return "all", [], [*reasons, f"global:{path}"]

        if path in PROVIDER_MAP_FILES:
            sections = PROVIDER_MAP_FILES[path]
            before = before_docs.get(path, {})
            after = after_docs.get(path, {})
            if path == "provider-overrides.json" and unscoped_override_change(before, after):
                return "all", [], [*reasons, f"global-map:{path}"]
            changed = changed_provider_keys(before, after, sections)
            providers.update(changed)
            if changed:
                reasons.append(f"providers:{path}:{','.join(sorted(changed))}")
            continue

        if path in PROVIDER_LIST_FILES:
            section, id_key = PROVIDER_LIST_FILES[path]
            changed = changed_provider_rows(
                before_docs.get(path, {}),
                after_docs.get(path, {}),
                section,
                id_key,
            )
            providers.update(changed)
            if changed:
                reasons.append(f"providers:{path}:{','.join(sorted(changed))}")
            continue

        if path.startswith("scripts/provider_patches/") and path.endswith(".py"):
            before_overrides = before_docs.get("provider-overrides.json", {})
            after_overrides = after_docs.get("provider-overrides.json", {})
            owners = patch_script_owners(path, before_overrides, after_overrides)
            if not owners:
                owners = transitively_imported_shared_patch_owners(path, before_overrides, after_overrides)
            if not owners:
                return "all", [], [*reasons, f"unowned-patch:{path}"]
            providers.update(owners)
            reasons.append(f"patch:{path}:{','.join(sorted(owners))}")
            continue

        if path in NEUTRAL_FILES or path.startswith(NEUTRAL_PREFIXES):
            continue

    return ("providers" if providers else "none"), sorted(providers), reasons


def changed_paths(base: str, head: str, *, committed_only: bool = False) -> list[str]:
    paths: set[str] = set()
    commands = [["git", "diff", "--name-only", base, head]]
    if not committed_only:
        commands.extend([
            ["git", "diff", "--name-only"],
            ["git", "diff", "--name-only", "--cached"],
        ])
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            continue
        paths.update(
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip()
        )
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--committed-only",
        action="store_true",
        help="Compare only the exact base/head commits; ignore sandbox/index working-tree drift.",
    )
    args = parser.parse_args()

    base = str(args.base or "").strip()
    if not base or set(base) == {"0"}:
        completed = subprocess.run(
            ["git", "rev-parse", f"{args.head}^"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        base = completed.stdout.strip() if completed.returncode == 0 else ""
    if not base:
        raise SystemExit("provider materialization scope requires a base revision")

    paths = changed_paths(base, args.head, committed_only=args.committed_only)
    tracked = set(PROVIDER_MAP_FILES) | set(PROVIDER_LIST_FILES)
    before_docs = {path: git_json(base, path) for path in tracked}
    after_docs = {
        path: (
            git_json(args.head, path)
            if args.committed_only
            else current_json(path)
        )
        for path in tracked
    }
    mode, providers, reasons = classify(paths, before_docs, after_docs)

    payload = {
        "schemaVersion": 1,
        "base": base,
        "head": args.head,
        "mode": mode,
        "providers": providers,
        "changedPaths": paths,
        "reasons": reasons,
        "committedOnly": bool(args.committed_only),
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print("FIELD_PROVIDER_MATERIALIZATION_SCOPE " + json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
