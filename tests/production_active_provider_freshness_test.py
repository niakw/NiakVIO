#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_production_freshness import ProductionFreshnessAuthority, load

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
    "manifest-hub46.json",
    "native-hub46/manifest.json",
):
    assert workflow.count(f'- "{dependency}"') >= 2, dependency

offline_seen = 0
reactivated_seen = 0
pending_seen = 0

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
        assert allowed, (
            f"{manifest_path}: active {provider} lacks fresh FULL proof or "
            f"exact-byte production exception proof ({proof_authority})"
        )
        if proof_authority == "offline-contract-exact-byte":
            offline_seen += 1
        elif proof_authority == "disabled-recovery-exact-byte":
            reactivated_seen += 1
        elif proof_authority == "pending-full-exact-byte":
            pending_seen += 1

assert int(authority.all_scope_state.get("artifactHashSchemaVersion") or 0) >= 1, (
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

print(
    "Production active providers require shared byte-bound all-scope FULL OK or exact-byte "
    "activation authority; "
    f"offline_live_unverified_checks={offline_seen} "
    f"reactivation_checks={reactivated_seen} pending_checks={pending_seen}"
)
