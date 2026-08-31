#!/usr/bin/env python3
"""Record cross-platform compatibility evidence without projecting unsupported manifest fields.

NiakVIO keeps runtime compatibility evidence in automation/platform-runtime-policy.json.
The upstream disabledPlatforms metadata was imported during the historical one-shot
bootstrap, but it is not part of NiakVIO's provider manifest contract and must never
be written back into manifest.json, vf/manifest.json or provider-overrides.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation" / "platform-runtime-matrix.json"
CONTRACTS = ROOT / "automation" / "platform-runtime-contracts.json"
POLICY = ROOT / "automation" / "platform-runtime-policy.json"
MAIN = ROOT / "manifest.json"
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


def main() -> int:
    matrix = load(MATRIX)
    contracts = load(CONTRACTS)
    main_doc = load(MAIN)
    if not all(isinstance(value, dict) for value in (matrix, contracts, main_doc)):
        raise SystemExit("missing or malformed platform evidence input")
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

    main_rows = rows(main_doc)
    classifications: dict[str, dict[str, str]] = {}
    managed: dict[str, list[str]] = {}

    for evidence in matrix.get("providers") or []:
        if not isinstance(evidence, dict):
            continue
        provider_id = str(evidence.get("id") or "").casefold()
        if not provider_id or provider_id not in main_rows:
            continue
        profile_rows = evidence.get("profiles") or {}
        classifications[provider_id] = {}
        for profile, token in PROFILE_TOKEN.items():
            result = profile_rows.get(profile) or {}
            classification = str(result.get("classification") or "inconclusive")
            classifications[provider_id][profile] = classification
            if classification in {"conclusive_non_playable", "conclusive_runtime_error"}:
                managed.setdefault(provider_id, []).append(token)

    policy = {
        "schema_version": 4,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_matrix": str(MATRIX.relative_to(ROOT)),
        "source_release": matrix.get("release"),
        "contract_file": str(CONTRACTS.relative_to(ROOT)),
        "runtime_profiles": list(PROFILE_TOKEN),
        "desktop_platforms": ["windows", "macos", "linux"],
        "decision_rule": "record conclusive compatibility failures internally; never project disabledPlatforms into NiakVIO manifests",
        "manifest_projection": "none",
        "unsupported_manifest_fields": ["disabledPlatforms"],
        "managed_platform_tokens_by_provider": {
            key: sorted(set(value)) for key, value in sorted(managed.items())
        },
        "classifications": classifications,
        "changed_providers": [],
        "legacy_android_no_proof_policy_retired": True,
    }
    dump(POLICY, policy)
    print(json.dumps(policy, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
