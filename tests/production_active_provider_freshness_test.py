#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_production_freshness import (
    ProductionFreshnessAuthority,
    artifact_digest,
    exact_disabled_reactivation,
    declared_lanes,
    load,
)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--allow-proof-debt",
    action="store_true",
    help=(
        "Architecture/CI mode: keep exact current active bytes visible while their "
        "fresh FULL proof is being recomputed. This never grants FULL/proof authority."
    ),
)
args = parser.parse_args()

authority = ProductionFreshnessAuthority(ROOT)
workflow = (ROOT / ".github" / "workflows" / "github-actions-gate.yml").read_text(encoding="utf-8")
for dependency in (
    "PROVENANCE.json",
    "provider-v3-materialization.json",
    "automation/provider-v3-static-knowledge.json",
    "automation/provider-census-all-status-latest.json",
    "automation/provider-onboarding-pending-status-latest.json",
    "automation/provider-disabled-reactivation-ledger.json",
    "providers/**",
    "provider-bases/**",
    "vf/manifest.json",
):
    assert workflow.count(f'- "{dependency}"') >= 2, dependency

assert "production_active_provider_freshness_test.py --allow-proof-debt" in workflow

offline_seen = 0
reactivated_seen = 0
pending_seen = 0
proof_debt_seen = 0

for manifest_path, projection in (
    (ROOT / "manifest.json", "global"),
    (ROOT / "vf" / "manifest.json", "france"),
):
    manifest = load(manifest_path)
    active = [
        row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("enabled") is not False
    ]
    for row in active:
        provider = str(row.get("id") or "").strip().casefold().replace("_", "-")
        assert provider, (manifest_path, row)
        allowed, proof_authority = authority.authorize(row, projection)
        if not allowed:
            if not args.allow_proof_debt:
                raise AssertionError(
                    f"{manifest_path}: active {provider} lacks fresh FULL proof or "
                    f"exact-byte production exception proof ({proof_authority})"
                )
            assert proof_authority == "no-current-byte-production-proof", (
                manifest_path,
                provider,
                proof_authority,
            )
            assert declared_lanes(row), (manifest_path, provider, "missing-declared-lanes")
            assert artifact_digest(ROOT, row.get("filename")), (
                manifest_path,
                provider,
                "missing-current-provider-artifact",
            )
            proof_debt_seen += 1
            continue
        if proof_authority == "offline-contract-exact-byte":
            offline_seen += 1
        elif proof_authority == "disabled-recovery-exact-byte":
            reactivated_seen += 1
        elif proof_authority == "pending-full-exact-byte":
            pending_seen += 1

assert int(authority.all_scope_state.get("artifactHashSchemaVersion") or 0) >= 2, (
    "missing byte-bound all-scope freshness ledger"
)

# Offline proof scope is projection authority, not self-declared metadata.
with tempfile.TemporaryDirectory(prefix="niakvio-freshness-scope-") as tmp:
    root = Path(tmp)
    (root / "providers").mkdir()
    data = b"synthetic exact provider bytes"
    artifact = root / "providers" / "demo.js"
    artifact.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    proof = {
        "schemaVersion": 1,
        "scope": "global",
        "providerSha256": digest,
        "pendingSha256": digest,
        "minimizerFixedPoint": True,
        "nodeSyntax": "passed",
        "providerV3Contract": "passed",
        "directOriginSyntax": "passed",
        "networkValidation": "not_authoritative_in_github_waf_limited",
        "livePlaybackValidated": False,
        "fullOkClaimed": False,
    }
    provenance = {
        "providers": {
            "demo": {
                "activation_mode": "bulk_offline_contract_live_unverified",
                "check_mode": "bulk_offline_contract_live_unverified",
                "check_status": "live_unverified",
                "activation_eligible": True,
                "strict_activation_eligible": False,
                "runtime_evidence_eligible": False,
                "activation_blockers": ["live_native_validation_pending"],
                "sha256": digest,
                "bulk_offline_activation_proof": proof,
            }
        }
    }
    (root / "PROVENANCE.json").write_text(json.dumps(provenance), encoding="utf-8")
    synthetic = ProductionFreshnessAuthority(root)
    global_row = {"id": "demo", "canonicalSupportedTypes": ["movie"], "filename": "providers/demo.js"}
    allowed, proof_authority = synthetic.authorize(global_row, "global")
    assert allowed and proof_authority == "offline-contract-exact-byte", proof_authority
    france_row = {"id": "demo", "canonicalSupportedTypes": ["movie"], "filename": "../providers/demo.js"}
    allowed, proof_authority = synthetic.authorize(france_row, "france")
    assert not allowed and proof_authority == "no-current-byte-production-proof", proof_authority
    allowed, proof_authority = synthetic.authorize(global_row, "unknown")
    assert not allowed and proof_authority == "invalid-projection-scope", proof_authority

    # Fresh exact-byte census proof can reauthorize lifecycle-retained bytes
    # without forcing a Brain run whose only valid action would be abstention.
    (root / "automation").mkdir(exist_ok=True)
    ledger = {
        "schemaVersion": 1,
        "authority": "provider-disabled-reactivation-ledger-v1",
        "providers": {
            "demo": {
                "proofAuthority": "current-census-exact-byte-terminal-v1",
                "proofStatus": "terminal_identity_verified",
                "sourceKind": "current-bytes-census",
                "sourceRunId": "42",
                "sourceSha": "a" * 40,
                "providerArtifactSha256": digest,
                "declaredLanes": ["movie"],
                "verifiedLanes": ["movie"],
                "testedThisRun": True,
                "verifiedRowCount": 1,
                "identityContradictionCount": 0,
                "wrongContent": False,
                "repairRequired": False,
                "directMutationAuthority": False,
                "routeAuthorityVerified": True,
            }
        },
    }
    (root / "automation/provider-disabled-reactivation-ledger.json").write_text(
        json.dumps(ledger), encoding="utf-8"
    )
    census_reactivated = ProductionFreshnessAuthority(root)
    allowed, proof_authority = census_reactivated.authorize(global_row, "global")
    assert allowed and proof_authority == "disabled-recovery-exact-byte", proof_authority
    ledger["providers"]["demo"]["providerArtifactSha256"] = "0" * 64
    (root / "automation/provider-disabled-reactivation-ledger.json").write_text(
        json.dumps(ledger), encoding="utf-8"
    )
    assert not exact_disabled_reactivation(
        ledger["providers"]["demo"], {"movie"}, digest
    ), "drifted current-census reactivation proof was accepted"

print(
    "Production active providers require shared byte-bound all-scope FULL OK or exact-byte "
    "activation authority; "
    f"mode={'architecture-proof-debt' if args.allow_proof_debt else 'strict-production'} "
    f"offline_live_unverified_checks={offline_seen} "
    f"reactivation_checks={reactivated_seen} pending_checks={pending_seen} "
    f"proof_debt_checks={proof_debt_seen}"
)
