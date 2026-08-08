#!/usr/bin/env python3
"""Publish evidence-backed platform compatibility into both Nuvio manifests.

The same positional QuickJS getStreams contract is used by current Nuvio Mobile
(Android/iOS) and Nuvio Desktop (Windows/macOS/Linux). For the finite VF movie
runtime diagnostic already captured in automation/mobile-vf-runtime.json, a
provider that produced no direct media is hidden from all full clients rather
than being exposed as a non-playable result. Providers with direct-media proof
remain available. Platform state is persisted to provider-overrides.json so
future deep publications preserve the decision.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "automation" / "mobile-vf-runtime.json"
CONTRACTS = ROOT / "automation" / "platform-runtime-contracts.json"
POLICY = ROOT / "automation" / "platform-runtime-policy.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"

BLOCK_TOKENS = ("android", "ios", "desktop")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in document.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def normalized_platforms(row: dict[str, Any]) -> list[str]:
    output: list[str] = []
    for value in row.get("disabledPlatforms") or []:
        item = str(value).strip().casefold()
        if item and item not in output:
            output.append(item)
    return output


def set_runtime_block(row: dict[str, Any], blocked: bool) -> bool:
    before = normalized_platforms(row)
    after = [value for value in before if value not in BLOCK_TOKENS]
    if blocked:
        after.extend(BLOCK_TOKENS)
    if before == after and row.get("disabledPlatforms") is not None:
        return False
    row["disabledPlatforms"] = after
    return True


def sync_vf(main_row: dict[str, Any], vf_row: dict[str, Any] | None) -> None:
    if vf_row is None:
        return
    filename = str(main_row.get("filename") or "")
    vf_row.clear()
    vf_row.update(json.loads(json.dumps(main_row)))
    if filename.startswith("providers/"):
        vf_row["filename"] = "../" + filename


def set_override(overrides: dict[str, Any], provider_id: str, blocked: bool) -> None:
    provider = overrides.setdefault("provider_patches", {}).setdefault(provider_id, {})
    manifest_overrides = provider.setdefault("manifest_overrides", {})
    current: list[str] = []
    for value in manifest_overrides.get("disabledPlatforms") or []:
        item = str(value).strip().casefold()
        if item and item not in current and item not in BLOCK_TOKENS:
            current.append(item)
    if blocked:
        current.extend(BLOCK_TOKENS)
    manifest_overrides["disabledPlatforms"] = current


def main() -> int:
    report = load(REPORT)
    contracts = load(CONTRACTS)
    main_doc = load(MAIN)
    vf_doc = load(VF)
    overrides = load(OVERRIDES)

    if str(report.get("release") or "") != str(main_doc.get("version") or ""):
        raise SystemExit("runtime evidence release does not match current manifest")

    clients = contracts.get("clients") or {}
    expected_clients = {"android", "ios", "windows", "macos", "linux"}
    if set(clients) != expected_clients:
        raise SystemExit(f"platform contract set mismatch: {sorted(clients)}")
    if any((clients[name] or {}).get("plugin_runtime") != "quickjs-positional-getStreams" for name in expected_clients):
        raise SystemExit("all full clients must use the same positional QuickJS contract")

    evidence = {
        str(row.get("id") or "").casefold(): row
        for row in report.get("providers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    proven = {
        provider_id
        for provider_id, row in evidence.items()
        if row.get("android_direct_movie_proof") is True
    }
    if not {"purstream", "goated"}.issubset(proven):
        raise SystemExit(f"required direct-media evidence missing: {sorted(proven)}")

    main_rows = rows(main_doc)
    vf_rows = rows(vf_doc)
    changed: list[str] = []
    blocked: list[str] = []

    for provider_id, row_evidence in sorted(evidence.items()):
        main_row = main_rows.get(provider_id)
        if main_row is None:
            continue
        should_block = row_evidence.get("android_direct_movie_proof") is not True
        if should_block:
            blocked.append(provider_id)
        if set_runtime_block(main_row, should_block):
            changed.append(provider_id)
        set_override(overrides, provider_id, should_block)
        sync_vf(main_row, vf_rows.get(provider_id))

    now = datetime.now(timezone.utc).isoformat()
    policy = {
        "schema_version": 2,
        "generated_at": now,
        "source_report": str(REPORT.relative_to(ROOT)),
        "source_release": main_doc.get("version"),
        "contract_file": str(CONTRACTS.relative_to(ROOT)),
        "client_platforms": sorted(expected_clients),
        "runtime_family_contract": "quickjs-positional-getStreams",
        "direct_media_proven": sorted(proven),
        "blocked_no_direct_media": sorted(blocked),
        "blocked_platform_tokens": list(BLOCK_TOKENS),
        "scope": "finite VF movie evidence applied to full-client platform visibility; unassessed providers remain unchanged",
        "changed_providers": sorted(set(changed)),
    }

    dump(MAIN, main_doc)
    dump(VF, vf_doc)
    dump(OVERRIDES, overrides)
    dump(POLICY, policy)
    print(json.dumps(policy, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
