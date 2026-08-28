#!/usr/bin/env python3
"""Enforce Core-wide media identity/presentation/branding/security policy.

Provider-specific media repair is intentionally excluded from this normalizer.
Identity, stream facts, presentation, branding, platform compatibility and security
are repository-wide Core concerns. Provider rows may still describe capability or
official-domain discovery, but they must not own private copies of those Core layers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from normalize_provider_branding_pipeline import assert_contract as assert_branding_pipeline_contract
from normalize_provider_branding_pipeline import normalize as normalize_branding_pipeline
from normalize_stream_presentation_v12 import assert_contract as assert_stream_presentation_contract
from normalize_stream_presentation_v12 import normalize as normalize_stream_presentation

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.json"
PROVIDER_BRANDING = ROOT / "assets/providers/emojis.json"
DESKTOP_COMPAT = ROOT / "scripts/publish_desktop_runtime_compat.py"
APPLY_OVERRIDES = ROOT / "scripts/apply_provider_overrides.py"
GLOBAL_SECURITY_HOOK = "scripts/provider_patches/global_provider_security_hardening_v1.py"
GLOBAL_BRANDING_HOOK = "scripts/provider_patches/global_provider_branding_v1.py"
ALLOWED_SHARED_PURSTREAM_SCRIPTS = {
    "scripts/provider_patches/native_sync_fetch_target_order_minified_v5.py",
    "scripts/provider_patches/native_sync_fetch_target_order_v1.py",
    "scripts/provider_patches/runtime_capability_media_safety_v4.py",
}
POLICY_NOTE = (
    "Purstream has no provider-specific repair hooks; content identity, stream facts, "
    "presentation and platform compatibility are handled by shared Core/capability layers."
)
# Desktop compatibility is domain-agnostic. Provider URLs/domains remain provider-owned.
FORBIDDEN_DESKTOP_DOMAIN_RUNTIME = ("domainFailover", "rewriteHost", "orderedSuffixes")

def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must be an object")
    return value


def _normalize_global_tail(value: dict[str, Any], changed: list[str]) -> None:
    playback = value.get("playback_integrity_policy")
    if not isinstance(playback, dict):
        raise ValueError("playback_integrity_policy must be an object")
    hooks = playback.get("global_discovery_hooks") or []
    if not isinstance(hooks, list):
        raise ValueError("playback_integrity_policy.global_discovery_hooks must be an array")
    # Security remains the last configurable playback hook. Provider branding is
    # deliberately excluded here and is applied by the controlled Core pipeline
    # *after* global_stream_presentation, so original stream facts remain readable.
    controlled = {GLOBAL_SECURITY_HOOK, GLOBAL_BRANDING_HOOK}
    normalized = [str(path) for path in hooks if str(path).strip() and str(path) not in controlled]
    normalized.append(GLOBAL_SECURITY_HOOK)
    if normalized != hooks:
        playback["global_discovery_hooks"] = normalized
        changed.append("playback_integrity_policy.global_discovery_hooks:security_tail")



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
    filtered = [str(path) for path in scripts if str(path) in ALLOWED_SHARED_PURSTREAM_SCRIPTS]
    if filtered != scripts:
        row["patch_scripts"] = filtered
        changed.append("provider_patches.purstream.patch_scripts")

    options = row.get("patch_script_options") or {}
    if not isinstance(options, dict):
        raise ValueError("provider_patches.purstream.patch_script_options must be an object")
    filtered_options = {
        str(path): config
        for path, config in options.items()
        if str(path) in ALLOWED_SHARED_PURSTREAM_SCRIPTS
    }
    if filtered_options != options:
        row["patch_script_options"] = filtered_options
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

    _normalize_global_tail(value, changed)
    return value, changed


def normalize_source_files(*, apply: bool) -> list[str]:
    changed: list[str] = []
    apply_source = APPLY_OVERRIDES.read_text(encoding="utf-8")
    normalized_apply, branding_changes = normalize_branding_pipeline(apply_source)
    assert_branding_pipeline_contract(normalized_apply)
    if branding_changes:
        changed.extend(f"scripts/apply_provider_overrides.py:{item}" for item in branding_changes)
        if apply:
            APPLY_OVERRIDES.write_text(normalized_apply, encoding="utf-8")

    presentation_changes = normalize_stream_presentation(apply=apply)
    changed.extend(f"stream_presentation:{item}" for item in presentation_changes)
    return changed


def _assert_branding_inventory() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    branding = json.loads(PROVIDER_BRANDING.read_text(encoding="utf-8"))
    if branding.get("policy") != "committed-provider-default-emoji":
        raise ValueError("provider branding policy must be committed-provider-default-emoji")
    rows = branding.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("provider branding providers must be an object")
    manifest_ids = {
        str(row.get("id") or "").strip().casefold()
        for row in (manifest.get("scrapers") or [])
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    branding_ids = {str(value).strip().casefold() for value in rows}
    missing = sorted(manifest_ids - branding_ids)
    if missing:
        raise ValueError(
            "provider branding coverage mismatch: "
            f"missing={','.join(missing)}"
        )
    for provider_id, row in rows.items():
        if not isinstance(row, dict):
            raise ValueError(f"provider branding row must be an object: {provider_id}")
        if not str(row.get("name") or "").strip() or not str(row.get("emoji") or "").strip():
            raise ValueError(f"provider branding row requires clean name + emoji: {provider_id}")


def _assert_branding_pipeline_order() -> None:
    source = APPLY_OVERRIDES.read_text(encoding="utf-8")
    assert_branding_pipeline_contract(source)
    presentation = source.find('"scope": "global_stream_presentation"')
    branding = source.find('"scope": "global_provider_branding"')
    final_return = source.find("    if text == original_text:", branding)
    if presentation < 0 or branding < 0 or final_return < 0 or not (presentation < branding < final_return):
        raise ValueError("provider branding must execute after stream presentation and before final return")


def assert_policy(value: dict[str, Any]) -> None:
    row = value["provider_patches"]["purstream"]
    scripts = {str(path) for path in (row.get("patch_scripts") or [])}
    options = {str(path) for path in (row.get("patch_script_options") or {})}
    forbidden = sorted((scripts | options) - ALLOWED_SHARED_PURSTREAM_SCRIPTS)
    if forbidden:
        raise ValueError("provider-specific media repair/configuration remains active: " + ", ".join(forbidden))


    runtime = ROOT / "scripts/provider_patches/runtime_capability_media_safety_v4.py"
    presentation = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
    security = ROOT / GLOBAL_SECURITY_HOOK
    branding = ROOT / GLOBAL_BRANDING_HOOK
    if not runtime.is_file() or not presentation.is_file() or not security.is_file() or not branding.is_file():
        raise ValueError("shared Core media/branding/security implementation is missing")
    runtime_text = runtime.read_text(encoding="utf-8")
    presentation_text = presentation.read_text(encoding="utf-8")
    security_text = security.read_text(encoding="utf-8")
    branding_text = branding.read_text(encoding="utf-8")
    if "field-safety-v5-native-identity-collisions-all-rows" not in runtime_text:
        raise ValueError("shared runtime identity safety revision is not current")
    if "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" not in presentation_text:
        raise ValueError("shared stream presentation wrapper is missing")
    assert_stream_presentation_contract()
    if "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1" not in security_text:
        raise ValueError("shared provider security Core hook is missing")
    if "NUVIO_GLOBAL_PROVIDER_BRANDING_V1" not in branding_text:
        raise ValueError("shared provider branding Core hook is missing")
    _assert_branding_inventory()
    _assert_branding_pipeline_order()

    playback = value.get("playback_integrity_policy") or {}
    hooks = [str(path) for path in (playback.get("global_discovery_hooks") or [])]
    if hooks.count(GLOBAL_SECURITY_HOOK) != 1:
        raise ValueError("global provider security hook must be present exactly once")
    if GLOBAL_BRANDING_HOOK in hooks:
        raise ValueError("provider branding must not run before stream presentation as a playback hook")
    if not hooks or hooks[-1] != GLOBAL_SECURITY_HOOK:
        raise ValueError("global configurable Core tail must end with provider security")

    desktop_text = (ROOT / "scripts/provider_patches/desktop_runtime_compat_v1.py").read_text(encoding="utf-8")
    forbidden_desktop = [token for token in FORBIDDEN_DESKTOP_DOMAIN_RUNTIME if token in desktop_text]
    if forbidden_desktop:
        raise ValueError(
            "Desktop runtime compatibility must not rewrite provider domains: "
            + ", ".join(forbidden_desktop)
        )


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

    assert_policy(normalized)

    pending = list(changed) + ([] if args.apply else source_changes)
    if args.check and pending:
        raise SystemExit("core media policy normalization required: " + ", ".join(pending))

    print(
        "FIELD_CORE_MEDIA_POLICY "
        f"provider_specific_media_repairs=0 changed={len(changed) + len(source_changes)} "
        "identity=global_runtime presentation=global_core_v12 branding=post_presentation_global_core "
        "compatibility=shared security=global_core"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
