#!/usr/bin/env python3
"""Enforce Core-wide media identity/presentation policy.

Purstream remains a normal provider with its own official-domain discovery, but
it must not own any special repair, media identity, facts, presentation, or
platform compatibility hook. Those concerns belong to shared Core/capability
layers so every provider receives the same behavior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
DESKTOP_COMPAT = ROOT / "scripts/publish_desktop_runtime_compat.py"
POLICY_NOTE = (
    "Purstream has no provider-specific repair hooks; content identity, stream facts, "
    "presentation and platform compatibility are handled by shared Core/capability layers."
)

# Exact historical block that made Purstream a special Desktop compatibility
# target. The normalizer removes it once and --check prevents resurrection.
_PURSTREAM_DESKTOP_TARGET = '''    "purstream": {
        "normalize_missing_episodes": True,
        "domain_failover": {
            "host_prefixes": ["api.purstream", "purstream"],
            "suffixes": ["club", "mx", "ch", "ac", "cx", "art", "co", "me", "to", "store"],
        },
    },
'''


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
    if scripts:
        row["patch_scripts"] = []
        changed.append("provider_patches.purstream.patch_scripts")

    options = row.get("patch_script_options") or {}
    if not isinstance(options, dict):
        raise ValueError("provider_patches.purstream.patch_script_options must be an object")
    if options:
        row["patch_script_options"] = {}
        changed.append("provider_patches.purstream.patch_script_options")

    notes = [str(note) for note in (row.get("notes") or [])]
    notes = [
        note for note in notes
        if "purstream" not in note.casefold()
        or "official-address" in note.casefold()
        or "official" in note.casefold()
    ]
    if POLICY_NOTE not in notes:
        notes.append(POLICY_NOTE)
    if notes != row.get("notes"):
        row["notes"] = notes
        changed.append("provider_patches.purstream.notes")

    return value, changed


def normalize_source_files(*, apply: bool) -> list[str]:
    changed: list[str] = []
    source = DESKTOP_COMPAT.read_text(encoding="utf-8")
    if _PURSTREAM_DESKTOP_TARGET in source:
        changed.append("scripts/publish_desktop_runtime_compat.py:purstream_target")
        if apply:
            DESKTOP_COMPAT.write_text(source.replace(_PURSTREAM_DESKTOP_TARGET, ""), encoding="utf-8")
    return changed


def assert_policy(value: dict[str, Any]) -> None:
    row = value["provider_patches"]["purstream"]
    scripts = [str(path) for path in (row.get("patch_scripts") or [])]
    options = [str(path) for path in (row.get("patch_script_options") or {})]
    if scripts or options:
        raise ValueError(
            "Purstream-specific repair/configuration remains active: "
            + ", ".join(sorted(set(scripts + options)))
        )

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

    desktop_text = DESKTOP_COMPAT.read_text(encoding="utf-8")
    if _PURSTREAM_DESKTOP_TARGET in desktop_text:
        raise ValueError("Purstream remains a special Desktop compatibility target")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")

    value = load()
    normalized, changed = normalize(value)
    source_changes = normalize_source_files(apply=args.apply)

    if args.apply and changed:
        OVERRIDES.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Re-read source after --apply so the assertion proves the exact resulting tree.
    assert_policy(normalized)

    pending = list(changed) + ([] if args.apply else source_changes)
    if args.check and pending:
        raise SystemExit("core media policy normalization required: " + ", ".join(pending))

    print(
        "FIELD_CORE_MEDIA_POLICY "
        f"provider_specific_purstream_repairs=0 changed={len(changed) + len(source_changes)} "
        "identity=global_runtime presentation=global_core compatibility=shared"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
