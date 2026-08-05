#!/usr/bin/env python3
"""Restore user-confirmed provider supportedTypes across published manifests."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "provider-type-policy.json"
MANIFESTS = (ROOT / "manifest.json", ROOT / "vf" / "manifest.json")
OVERRIDES = ROOT / "provider-overrides.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bump_patch(value: object) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def normalize_types(values: object) -> list[str]:
    allowed = {"movie", "tv", "anime"}
    result: list[str] = []
    for value in values if isinstance(values, list) else []:
        item = str(value).strip().casefold()
        if item in allowed and item not in result:
            result.append(item)
    return result


def update_manifest(path: Path, policy: dict[str, dict], *, require_all: bool) -> list[str]:
    data = load(path)
    rows = {
        str(row.get("id") or "").casefold(): row
        for row in data.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    missing = sorted(set(policy) - set(rows)) if require_all else []
    if missing:
        raise RuntimeError(f"{path}: policy providers missing: {missing}")

    changed: list[str] = []
    for provider_id, expected in policy.items():
        row = rows.get(provider_id)
        if row is None:
            continue
        desired_types = normalize_types(expected.get("supportedTypes"))
        if not desired_types:
            raise RuntimeError(f"{provider_id}: empty supportedTypes policy")
        desired_description = expected.get("description")
        dirty = False
        if normalize_types(row.get("supportedTypes")) != desired_types:
            row["supportedTypes"] = desired_types
            dirty = True
        if isinstance(desired_description, str) and row.get("description") != desired_description:
            row["description"] = desired_description
            dirty = True
        if dirty:
            row["version"] = bump_patch(row.get("version"))
            changed.append(provider_id)

    write(path, data)
    return changed


def update_overrides(policy: dict[str, dict]) -> list[str]:
    data = load(OVERRIDES)
    patches = data.setdefault("provider_patches", {})
    changed: list[str] = []
    for provider_id, expected in policy.items():
        patch = patches.get(provider_id)
        if not isinstance(patch, dict):
            continue
        desired_types = normalize_types(expected.get("supportedTypes"))
        if normalize_types(patch.get("published_types")) != desired_types:
            patch["published_types"] = desired_types
            changed.append(provider_id)
        options = patch.get("patch_script_options")
        if isinstance(options, dict):
            for config in options.values():
                if isinstance(config, dict) and "types" in config:
                    config["types"] = desired_types
    write(OVERRIDES, data)
    return changed


def validate(policy: dict[str, dict]) -> None:
    for path in MANIFESTS:
        data = load(path)
        rows = {
            str(row.get("id") or "").casefold(): row
            for row in data.get("scrapers") or []
            if isinstance(row, dict) and str(row.get("id") or "").strip()
        }
        for provider_id, expected in policy.items():
            if provider_id not in rows:
                if path.name == "manifest.json" and path.parent == ROOT:
                    raise RuntimeError(f"{path}: missing {provider_id}")
                continue
            actual = normalize_types(rows[provider_id].get("supportedTypes"))
            desired = normalize_types(expected.get("supportedTypes"))
            if actual != desired:
                raise RuntimeError(f"{path}:{provider_id}: {actual} != {desired}")


def main() -> int:
    policy_data = load(POLICY)
    policy = {
        str(provider_id).casefold(): config
        for provider_id, config in (policy_data.get("providers") or {}).items()
        if isinstance(config, dict)
    }
    main_changed = update_manifest(MANIFESTS[0], policy, require_all=True)
    vf_changed = update_manifest(MANIFESTS[1], policy, require_all=False)
    overrides_changed = update_overrides(policy)
    validate(policy)
    print("provider type policy restored")
    print("main changed:", ", ".join(main_changed) or "none")
    print("vf changed:", ", ".join(vf_changed) or "none")
    print("override types changed:", ", ".join(overrides_changed) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
