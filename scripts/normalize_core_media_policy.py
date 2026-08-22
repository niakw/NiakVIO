#!/usr/bin/env python3
"""Enforce Core-wide media identity/presentation policy.

Provider configuration may describe domains/capabilities and generic compatibility
options. It must not carry a Purstream-only media identity/presentation repair:
those rules belong to the shared Core/runtime capability layer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
FORBIDDEN_PURSTREAM_PREFIX = "scripts/provider_patches/purstream_"
POLICY_NOTE = (
    "Content identity, stream facts and final presentation are Core-wide; "
    "do not add provider-specific media repair hooks."
)


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must be an object")
    return value


def normalize(value: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    changed: list[str] = []
    providers = value.get("provider_patches")
    if not isinstance(providers, dict):
        raise ValueError("provider_patches must be an object")
    row = providers.get("purstream")
    if not isinstance(row, dict):
        raise ValueError("provider_patches.purstream must be an object")

    scripts = row.get("patch_scripts") or []
    if not isinstance(scripts, list):
        raise ValueError("provider_patches.purstream.patch_scripts must be an array")
    filtered = [
        str(path) for path in scripts
        if not str(path).startswith(FORBIDDEN_PURSTREAM_PREFIX)
    ]
    if filtered != scripts:
        row["patch_scripts"] = filtered
        changed.append("provider_patches.purstream.patch_scripts")

    options = row.get("patch_script_options") or {}
    if not isinstance(options, dict):
        raise ValueError("provider_patches.purstream.patch_script_options must be an object")
    filtered_options = {
        str(path): config
        for path, config in options.items()
        if not str(path).startswith(FORBIDDEN_PURSTREAM_PREFIX)
    }
    if filtered_options != options:
        row["patch_script_options"] = filtered_options
        changed.append("provider_patches.purstream.patch_script_options")

    notes = [str(note) for note in (row.get("notes") or [])]
    if POLICY_NOTE not in notes:
        notes.append(POLICY_NOTE)
        row["notes"] = notes
        changed.append("provider_patches.purstream.notes")

    return value, changed


def assert_policy(value: dict[str, Any]) -> None:
    row = value["provider_patches"]["purstream"]
    scripts = [str(path) for path in (row.get("patch_scripts") or [])]
    options = [str(path) for path in (row.get("patch_script_options") or {})]
    forbidden = [path for path in scripts + options if path.startswith(FORBIDDEN_PURSTREAM_PREFIX)]
    if forbidden:
        raise ValueError("provider-specific Purstream media repair remains active: " + ", ".join(sorted(forbidden)))

    runtime = ROOT / "scripts/provider_patches/runtime_capability_media_safety_v4.py"
    presentation = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
    if not runtime.is_file() or not presentation.is_file():
        raise ValueError("shared Core media safety/presentation implementation is missing")
    runtime_text = runtime.read_text(encoding="utf-8")
    presentation_text = presentation.read_text(encoding="utf-8")
    if "field-safety-v5-native-identity-collisions-all-rows" not in runtime_text:
        raise ValueError("shared runtime identity safety revision is not current")
    if "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" not in presentation_text:
        raise ValueError("shared stream presentation wrapper is missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")

    value = load()
    normalized, changed = normalize(value)
    assert_policy(normalized)

    if args.check:
        if changed:
            raise SystemExit("core media policy normalization required: " + ", ".join(changed))
    elif args.apply and changed:
        OVERRIDES.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "FIELD_CORE_MEDIA_POLICY "
        f"provider_specific_purstream_repairs=0 changed={len(changed)} "
        "identity=global_runtime presentation=global_core"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
