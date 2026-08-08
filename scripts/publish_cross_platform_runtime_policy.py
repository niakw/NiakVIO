#!/usr/bin/env python3
"""Publish conservative cross-platform compatibility decisions.

Only conclusive runtime failures from the fresh platform matrix can add a
platform block. Zero streams is inconclusive and never creates a block. The
legacy 5.20.27 Android blocks that were based only on missing proof are removed
when fresh evidence remains inconclusive. Existing blocks not managed by this
policy are preserved.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation" / "platform-runtime-matrix.json"
CONTRACTS = ROOT / "automation" / "platform-runtime-contracts.json"
POLICY = ROOT / "automation" / "platform-runtime-policy.json"
LEGACY_POLICY = ROOT / "automation" / "mobile-vf-runtime-policy.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
PROFILE_TOKEN = {"android": "android", "ios": "ios", "desktop": "desktop"}


def load(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in document.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def platforms(row: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for value in row.get("disabledPlatforms") or []:
        item = str(value).strip().casefold()
        if item and item not in result:
            result.append(item)
    return result


def set_token(row: dict[str, Any], token: str, blocked: bool) -> bool:
    before = platforms(row)
    after = [value for value in before if value != token]
    if blocked:
        after.append(token)
    if before == after and row.get("disabledPlatforms") is not None:
        return False
    row["disabledPlatforms"] = after
    return True


def set_override_token(overrides: dict[str, Any], provider_id: str, token: str, blocked: bool) -> None:
    patch = overrides.setdefault("provider_patches", {}).setdefault(provider_id, {})
    manifest_overrides = patch.setdefault("manifest_overrides", {})
    current: list[str] = []
    for value in manifest_overrides.get("disabledPlatforms") or []:
        item = str(value).strip().casefold()
        if item and item != token and item not in current:
            current.append(item)
    if blocked:
        current.append(token)
    manifest_overrides["disabledPlatforms"] = current


def sync_vf(main_row: dict[str, Any], vf_row: dict[str, Any] | None) -> None:
    if vf_row is None:
        return
    filename = str(main_row.get("filename") or "")
    vf_row.clear()
    vf_row.update(deepcopy(main_row))
    if filename.startswith("providers/"):
        vf_row["filename"] = "../" + filename


def main() -> int:
    matrix = load(MATRIX)
    contracts = load(CONTRACTS)
    main_doc = load(MAIN)
    vf_doc = load(VF)
    overrides = load(OVERRIDES)
    if not all(isinstance(value, dict) for value in (matrix, contracts, main_doc, vf_doc, overrides)):
        raise SystemExit("missing or malformed platform publication input")
    if str(matrix.get("release") or "") != str(main_doc.get("version") or ""):
        raise SystemExit("platform matrix must be generated from the exact current release")
    if matrix.get("manifest") != "manifest.json":
        raise SystemExit("platform matrix must probe the general manifest")

    clients = contracts.get("clients") or {}
    expected = {"android", "ios", "windows", "macos", "linux"}
    if set(clients) != expected:
        raise SystemExit(f"platform contract mismatch: {sorted(clients)}")
    if any((clients[name] or {}).get("plugin_runtime") != "quickjs-positional-getStreams" for name in expected):
        raise SystemExit("unexpected Nuvio plugin runtime contract")

    legacy = load(LEGACY_POLICY, {}) or {}
    previous = load(POLICY, {}) or {}
    previous_managed: dict[str, set[str]] = {}
    for provider_id in legacy.get("android_disabled_no_direct_movie_proof") or []:
        previous_managed.setdefault(str(provider_id).casefold(), set()).add("android")
    for provider_id, tokens in (previous.get("managed_platform_tokens_by_provider") or {}).items():
        previous_managed.setdefault(str(provider_id).casefold(), set()).update(
            str(token).casefold() for token in tokens if str(token).strip()
        )

    main_rows = rows(main_doc)
    vf_rows = rows(vf_doc)
    managed: dict[str, list[str]] = {}
    classifications: dict[str, dict[str, str]] = {}
    changed: set[str] = set()

    for evidence in matrix.get("providers") or []:
        if not isinstance(evidence, dict):
            continue
        provider_id = str(evidence.get("id") or "").casefold()
        row = main_rows.get(provider_id)
        if not provider_id or row is None:
            continue
        profile_rows = evidence.get("profiles") or {}
        classifications[provider_id] = {}
        for profile, token in PROFILE_TOKEN.items():
            result = profile_rows.get(profile) or {}
            classification = str(result.get("classification") or "inconclusive")
            classifications[provider_id][profile] = classification
            was_managed = token in previous_managed.get(provider_id, set())
            currently_blocked = token in platforms(row)

            if classification in {"conclusive_non_playable", "conclusive_runtime_error"}:
                desired = True
                policy_manages = True
            elif classification == "compatible_direct":
                desired = False if was_managed else currently_blocked
                policy_manages = False
            else:
                # Inconclusive evidence cannot create or remove a previously
                # conclusive cross-platform block. The one exception is the
                # legacy Android no-proof policy, whose basis was deliberately
                # weaker and is retired by this release.
                legacy_weak = token == "android" and provider_id in {
                    str(value).casefold() for value in legacy.get("android_disabled_no_direct_movie_proof") or []
                } and token not in {
                    str(value).casefold()
                    for value in (previous.get("managed_platform_tokens_by_provider") or {}).get(provider_id, [])
                }
                desired = False if legacy_weak else currently_blocked
                policy_manages = was_managed and not legacy_weak

            if set_token(row, token, desired):
                changed.add(provider_id)
            set_override_token(overrides, provider_id, token, desired)
            if policy_manages and desired:
                managed.setdefault(provider_id, []).append(token)

        sync_vf(row, vf_rows.get(provider_id))

    policy = {
        "schema_version": 3,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_matrix": str(MATRIX.relative_to(ROOT)),
        "source_release": matrix.get("release"),
        "contract_file": str(CONTRACTS.relative_to(ROOT)),
        "runtime_profiles": list(PROFILE_TOKEN),
        "desktop_platforms": ["windows", "macos", "linux"],
        "decision_rule": "block only conclusive non-playable/runtime failure; zero-stream is inconclusive",
        "managed_platform_tokens_by_provider": {key: sorted(set(value)) for key, value in sorted(managed.items())},
        "classifications": classifications,
        "changed_providers": sorted(changed),
        "legacy_android_no_proof_policy_retired": True,
    }
    dump(MAIN, main_doc)
    dump(VF, vf_doc)
    dump(OVERRIDES, overrides)
    dump(POLICY, policy)
    print(json.dumps(policy, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
