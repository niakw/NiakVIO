#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Enforce clean-v3 runtime repository dependency ownership.

Clean Provider v3 persists official sites/APIs as structured DATA. Historical
runtime repository-domain materializers are compatibility knowledge only and
must never be restored as executable provider patches.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
CORE_MEDIA_POLICY = ROOT / "scripts" / "normalize_core_media_policy.py"
LEGACY_PATCH = "scripts/provider_patches/runtime_repository_domain_materializer_v1.py"
REGISTRY_URLS = {
    "https://raw.githubusercontent.com/phisher98/TVVVV/refs/heads/main/domains.json",
    "https://raw.githubusercontent.com/sapariyaneel/nuvio-plugin/refs/heads/main/domains.json",
    "https://raw.githubusercontent.com/PirateZoro9/asura-providers/main/urls.json",
}
REQUIRED_SITE = ("cineby", "uhdmovies", "4khdhub", "zinkmovies", "goated")

def load() -> dict[str, Any]:
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must be an object")
    return value

def _valid_url(value: object) -> bool:
    return isinstance(value, str) and value.strip().startswith(("http://", "https://"))

def normalize(value: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    providers = value.get("provider_patches")
    if not isinstance(providers, dict):
        raise ValueError("provider_patches must be an object")
    changed: list[str] = []
    for provider_id, raw in providers.items():
        if not isinstance(raw, dict):
            continue
        scripts = raw.get("patch_scripts")
        if isinstance(scripts, list):
            clean = [str(path) for path in scripts if str(path).strip() and str(path) != LEGACY_PATCH]
            if clean != scripts:
                raw["patch_scripts"] = clean
                changed.append(f"provider_patches.{provider_id}.patch_scripts:remove_legacy_repository_materializer")
        options = raw.get("patch_script_options")
        if isinstance(options, dict) and LEGACY_PATCH in options:
            clean_options = dict(options)
            clean_options.pop(LEGACY_PATCH, None)
            raw["patch_script_options"] = clean_options
            changed.append(f"provider_patches.{provider_id}.patch_script_options:remove_legacy_repository_materializer")
        for field in ("replacements", "route_replacements", "runtime_domain_replacements"):
            mapping = raw.get(field)
            if not isinstance(mapping, dict):
                continue
            clean_mapping = {str(k): v for k, v in mapping.items() if str(k) not in REGISTRY_URLS}
            if clean_mapping != mapping:
                raw[field] = clean_mapping
                changed.append(f"provider_patches.{provider_id}.{field}:remove_repository_registry")
    return value, changed

def assert_contract(value: dict[str, Any]) -> None:
    providers = value.get("provider_patches")
    if not isinstance(providers, dict):
        raise ValueError("provider_patches must remain an object")
    if (ROOT / LEGACY_PATCH).exists():
        raise ValueError("legacy runtime repository domain materializer must remain absent in clean-v3")
    for provider_id, raw in providers.items():
        if not isinstance(raw, dict):
            continue
        scripts = [str(v) for v in raw.get("patch_scripts") or []]
        if LEGACY_PATCH in scripts:
            raise ValueError(f"{provider_id}: legacy runtime repository materializer still configured")
        options = raw.get("patch_script_options") or {}
        if isinstance(options, dict) and LEGACY_PATCH in options:
            raise ValueError(f"{provider_id}: legacy runtime repository materializer options remain")
    for provider_id in REQUIRED_SITE:
        row = providers.get(provider_id)
        if not isinstance(row, dict) or not _valid_url(row.get("official_site")):
            raise ValueError(f"{provider_id}: structured DATA requires persisted official_site")
    cineby = providers.get("cineby")
    if not isinstance(cineby, dict) or not _valid_url(cineby.get("official_api")):
        raise ValueError("cineby: structured DATA requires persisted official_api")
    source = CORE_MEDIA_POLICY.read_text(encoding="utf-8")
    for token in ("ZINK_REPOSITORY_DOMAIN_SOURCE", "_normalize_zink_domain_discovery"):
        if token in source:
            raise ValueError("Core media policy still owns provider address routing")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error("choose exactly one of --apply or --check")
    current = load()
    normalized, changed = normalize(current)
    assert_contract(normalized)
    if args.check and changed:
        raise SystemExit("runtime repository dependency normalization required: " + ", ".join(changed))
    if args.apply and changed:
        CONFIG.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_RUNTIME_REPOSITORY_DEPENDENCIES "
        f"changed={len(changed)} repository_runtime_fetches=0 "
        "legacy_materializer=absent address_owner=provider_data"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
