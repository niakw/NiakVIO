#!/usr/bin/env python3
"""Disable active providers only from fresh exact-byte wrong-content proof.

This is lifecycle safety, not provider Repair. A current provider is moved toward
disabled-retained only when the canonical current-byte census observed an
identity/content contradiction against the exact same provider bytes and the
provider execution/domain authority has not changed since that census.

A stale negative result must never disable a newer provider generation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from reactivate_disabled_from_current_census import (
    EligibilityError,
    canon,
    canonical_json,
    census_inputs,
    current_provider_authority,
    current_source,
    declared_lanes,
    dump,
    git_bytes,
    load,
    require_ancestor,
    sha256,
    status_row,
    tested_provider_authority,
    tested_source_row,
)

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "automation/provider-active-wrong-content-disable-latest.json"
DISABLE_REASON = "auto_off_current_wrong_content"
PROOF_AUTHORITY = "current-census-exact-byte-wrong-content-v1"


def active_repo_path(filename: object) -> str:
    value = str(filename or "").strip().replace("\\", "/")
    while value.startswith("../"):
        value = value[3:]
    if not value.startswith("providers/") or ".." in Path(value).parts:
        raise EligibilityError(f"active provider path is not repository-safe: {filename!r}")
    return value


def raw_identity_contradictions(raw: dict[str, Any], provider: str) -> list[dict[str, Any]]:
    rows = [
        item
        for item in raw.get("rows") or []
        if isinstance(item, dict) and canon(item.get("provider_id")) == provider
    ]
    return [
        item
        for item in rows
        if str(item.get("status") or "") == "wrong_content"
        or int(item.get("contradictions") or 0) > 0
        or item.get("identity_safe") is False
    ]


def validate_candidate(root: Path, provider: str) -> dict[str, Any]:
    provider = canon(provider)
    status, summary, raw = census_inputs(root)
    trigger_sha = str(status.get("triggerSha") or "").strip().casefold()
    run_id = str(status.get("runId") or "").strip()
    require_ancestor(root, trigger_sha)

    row_status = status_row(status, provider)
    if row_status.get("testedThisRun") is not True:
        raise EligibilityError(f"{provider}: wrong-content evidence was not tested this run")
    wrong = {canon(value) for value in summary.get("wrongContentProviders") or [] if canon(value)}
    if provider not in wrong:
        raise EligibilityError(f"{provider}: provider is not in current-run wrong-content set")
    contradictions = raw_identity_contradictions(raw, provider)
    if not contradictions:
        raise EligibilityError(f"{provider}: raw current census contains no identity contradiction")

    scope, row, _doc = current_source(root, provider)
    if row.get("enabled") is False:
        raise EligibilityError(f"{provider}: provider is already disabled")
    declared = declared_lanes(row)
    if not declared:
        raise EligibilityError(f"{provider}: active provider has no declared lanes")

    tested_row = tested_source_row(root, trigger_sha, scope, provider)
    if tested_row.get("enabled") is False:
        raise EligibilityError(f"{provider}: tested provider was not active")
    if declared_lanes(tested_row) != declared:
        raise EligibilityError(f"{provider}: declared lanes drifted since wrong-content census")

    current_path = active_repo_path(row.get("filename"))
    tested_path = active_repo_path(tested_row.get("filename"))
    current_asset = root / current_path
    if not current_asset.is_file():
        raise EligibilityError(f"{provider}: current active provider bytes are missing")
    current_digest = sha256(current_asset.read_bytes())
    tested_digest = sha256(git_bytes(root, trigger_sha, tested_path))
    if current_digest != tested_digest:
        raise EligibilityError(
            f"{provider}: active bytes changed since wrong-content census "
            f"tested={tested_digest[:16]} current={current_digest[:16]}"
        )

    patch, registry, _overrides, _hubs = current_provider_authority(root, provider)
    tested_patch, tested_registry = tested_provider_authority(root, trigger_sha, provider)
    if canonical_json(patch) != canonical_json(tested_patch):
        raise EligibilityError(f"{provider}: provider execution authority changed since wrong-content census")
    if canonical_json(registry) != canonical_json(tested_registry):
        raise EligibilityError(f"{provider}: provider hub/domain authority changed since wrong-content census")

    lanes = sorted({
        canon(item.get("semantic_type"))
        for item in contradictions
        if canon(item.get("semantic_type")) in {"movie", "tv", "anime"}
    })
    return {
        "provider": provider,
        "scope": scope,
        "proofAuthority": PROOF_AUTHORITY,
        "sourceKind": "current-bytes-census",
        "sourceRunId": run_id,
        "sourceSha": trigger_sha,
        "providerArtifactSha256": current_digest,
        "declaredLanes": sorted(declared),
        "contradictoryLanes": lanes,
        "identityContradictionCount": len(contradictions),
        "wrongContent": True,
        "testedThisRun": True,
        "disableReason": DISABLE_REASON,
        "repairRequired": True,
        "directProviderMutationAuthority": False,
    }


def _catalog_row(catalog: dict[str, Any], provider: str) -> dict[str, Any]:
    matches = []
    for entry in catalog.get("providers") or []:
        if not isinstance(entry, dict):
            continue
        scraper = entry.get("scraper") if isinstance(entry.get("scraper"), dict) else {}
        if canon(entry.get("canonicalId") or scraper.get("id")) == provider:
            matches.append(scraper)
    if len(matches) != 1:
        raise EligibilityError(f"{provider}: expected one provider_catalog row, got {len(matches)}")
    return matches[0]


def apply_proofs(root: Path, proofs: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = load(root / "manifest.json", {"scrapers": []})
    catalog = load(root / "provider_catalog.json", {"providers": []})
    overrides = load(root / "provider-overrides.json", {"provider_patches": {}})
    hubs = load(root / "provider-hubs.json", {"providers": {}})
    patches = overrides.setdefault("provider_patches", {})
    registries = hubs.setdefault("providers", {})
    applied: list[str] = []

    for proof in proofs:
        provider = canon(proof.get("provider"))
        scope = str(proof.get("scope") or "")
        if scope == "global":
            matches = [
                row for row in manifest.get("scrapers") or []
                if isinstance(row, dict) and canon(row.get("id")) == provider
            ]
            if len(matches) != 1:
                raise EligibilityError(f"{provider}: expected one Global manifest row")
            row = matches[0]
        elif scope == "france":
            row = _catalog_row(catalog, provider)
        else:
            raise EligibilityError(f"{provider}: unsupported projection scope {scope!r}")

        if row.get("enabled") is False:
            continue
        row["enabled"] = False
        row["disabledReason"] = DISABLE_REASON

        patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
        manifest_overrides = (
            patch.get("manifest_overrides")
            if isinstance(patch.get("manifest_overrides"), dict)
            else {}
        )
        manifest_overrides["enabled"] = False
        patch["manifest_overrides"] = manifest_overrides
        patch["route_data_state"] = "off"
        patch["activation_eligible"] = False
        patch.pop("manual_off_reason", None)
        patch["wrong_content_disable_proof"] = dict(proof)
        patches[provider] = patch

        registry = registries.get(provider) if isinstance(registries.get(provider), dict) else {}
        registry["manifest_status"] = "Désactivé"
        registry["activation_eligible"] = False
        registry.pop("manual_off_reason", None)
        registries[provider] = registry
        applied.append(provider)

    dump(root / "manifest.json", manifest)
    dump(root / "provider_catalog.json", catalog)
    dump(root / "provider-overrides.json", overrides)
    dump(root / "provider-hubs.json", hubs)
    return {"applied": sorted(applied), "proofs": proofs}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()

    _status, summary, _raw = census_inputs(ROOT)
    candidates = sorted({
        canon(value)
        for value in (args.provider or summary.get("wrongContentProviders") or [])
        if canon(value)
    })
    proofs: list[dict[str, Any]] = []
    blocked: list[dict[str, str]] = []
    for provider in candidates:
        try:
            proofs.append(validate_candidate(ROOT, provider))
        except EligibilityError as exc:
            blocked.append({"provider": provider, "reason": str(exc)})

    result = {
        "schemaVersion": 1,
        "authority": PROOF_AUTHORITY,
        "eligible": [proof["provider"] for proof in proofs],
        "blocked": blocked,
        "applied": [],
    }
    if args.apply and proofs:
        applied = apply_proofs(ROOT, proofs)
        result["applied"] = applied["applied"]
    dump(LATEST, result)
    print(
        "FIELD_ACTIVE_WRONG_CONTENT_LIFECYCLE "
        f"eligible={len(proofs)} applied={len(result['applied'])} blocked={len(blocked)} "
        f"providers={','.join(result['applied'] or result['eligible']) or '-'}"
    )
    if args.provider and not proofs:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
