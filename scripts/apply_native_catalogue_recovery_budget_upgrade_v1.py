#!/usr/bin/env python3
"""Attach the native catalogue recovery budget patch wherever the global fallback exists."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
MARKER = "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2"
PATCH = "scripts/provider_patches/native_catalogue_recovery_budget_v1.py"
FINAL_SAFETY = "scripts/provider_patches/runtime_capability_media_safety_v4.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    manifest = load(MANIFEST)
    config = load(OVERRIDES)
    provider_patches = config.setdefault("provider_patches", {})
    targets: list[str] = []
    changed = 0
    for entry in manifest.get("scrapers", []):
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        filename = str(entry.get("filename") or "")
        source = ROOT / filename
        if not provider_id or not filename.startswith("providers/") or not source.is_file():
            continue
        if MARKER not in source.read_text(encoding="utf-8", errors="ignore"):
            continue
        targets.append(provider_id)
        row = provider_patches.setdefault(provider_id, {})
        scripts = row.setdefault("patch_scripts", [])
        if not isinstance(scripts, list):
            raise ValueError(f"provider_patches.{provider_id}.patch_scripts must be an array")
        original = list(scripts)
        scripts = [script for script in scripts if script != PATCH]
        # Keep runtime media safety as the final output guard when present.
        if FINAL_SAFETY in scripts:
            index = scripts.index(FINAL_SAFETY)
            scripts.insert(index, PATCH)
        else:
            scripts.append(PATCH)
        if scripts != original:
            row["patch_scripts"] = scripts
            changed += 1
    config["native_catalogue_recovery_budget"] = {
        "version": 1,
        "scope": "providers_with_global_catalogue_alias_recovery",
        "native_max_search_requests": 2,
        "native_max_candidate_pages": 2,
        "native_soft_budget_ms": 12000,
        "desktop_behavior": "unchanged_broad_recovery",
        "reason": "native_host_fetch_is_synchronous_and_not_reliably_abortable_from_js",
        "targets": sorted(set(targets)),
    }
    dump(OVERRIDES, config)
    print(f"native catalogue recovery budget configured: targets={len(set(targets))} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
