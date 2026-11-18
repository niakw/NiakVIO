#!/usr/bin/env python3
"""Shared production activation authority for current provider bytes.

This module is deliberately proof-oriented. A provider is allowed to remain
active only when its exact current artifact is covered by one of the production
freshness authorities accepted by NiakVIO:
- fresh all-scope FULL OK replay;
- exact-byte disabled recovery proof, from either residential recovery or a fresh
  canonical current-byte census that required no provider mutation;
- exact-byte offline activation contract (live still unverified);
- exact pending onboarding FULL replay bound to the promoted bytes.

Status labels, domain authority and Repair eligibility are not substitutes for
these byte-bound production proofs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

OFFLINE_MODE = "bulk_offline_contract_live_unverified"
OFFLINE_BLOCKER = "live_native_validation_pending"


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def proof_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        canon(row.get("provider")): row
        for row in state.get("providers") or []
        if isinstance(row, dict) and canon(row.get("provider"))
    }


def declared_lanes(row: dict[str, Any]) -> set[str]:
    return {
        str(value).strip().lower()
        for value in row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
        if str(value).strip()
    }


def fresh_full(evidence: dict[str, Any] | None, declared: set[str], digest: str) -> bool:
    if not isinstance(evidence, dict):
        return False
    verified = {
        str(value).strip().lower()
        for value in evidence.get("currentVerifiedLanes") or []
        if str(value).strip()
    }
    return (
        evidence.get("status") == "FULL OK"
        and evidence.get("testedThisRun") is True
        and bool(declared)
        and declared <= verified
        and evidence.get("repairEligible") is not True
        and bool(digest)
        and str(evidence.get("providerArtifactSha256") or "").strip().casefold() == digest
    )


def exact_disabled_reactivation(
    proof: dict[str, Any] | None,
    declared: set[str],
    digest: str,
) -> bool:
    if not isinstance(proof, dict) or not digest:
        return False
    verified = {
        str(value).strip().lower()
        for value in proof.get("verifiedLanes") or []
        if str(value).strip()
    }
    proof_declared = {
        str(value).strip().lower()
        for value in proof.get("declaredLanes") or []
        if str(value).strip()
    }
    common = (
        proof.get("proofStatus") == "terminal_identity_verified"
        and proof.get("repairRequired") is False
        and proof.get("directMutationAuthority") is False
        and bool(declared)
        and proof_declared == declared
        and declared <= verified
        and str(proof.get("providerArtifactSha256") or "").strip().casefold() == digest
    )
    if not common:
        return False
    authority = proof.get("proofAuthority")
    if authority == "disabled-recovery-exact-byte-residential-v1":
        return (
            proof.get("brainAbstained") is True
            and int(proof.get("streamsPlayable") or 0) >= len(declared)
            and int(proof.get("payloadVerifiedStreams") or 0) >= len(declared)
            and int(proof.get("identityVerifiedStreams") or 0) >= len(declared)
        )
    if authority == "current-census-exact-byte-terminal-v1":
        return (
            proof.get("sourceKind") == "current-bytes-census"
            and proof.get("testedThisRun") is True
            and int(proof.get("verifiedRowCount") or 0) >= len(declared)
            and int(proof.get("identityContradictionCount") or 0) == 0
            and proof.get("wrongContent") is False
            and proof.get("routeAuthorityVerified") is True
        )
    return False


def artifact_digest(root: Path, filename: object) -> str:
    relative = str(filename or "").strip().replace("\\", "/")
    if relative.startswith("../"):
        relative = relative[3:]
    if not relative.startswith("providers/"):
        return ""
    artifact = (root / relative).resolve()
    providers_root = (root / "providers").resolve()
    if not artifact.is_file() or providers_root not in artifact.parents:
        return ""
    return hashlib.sha256(artifact.read_bytes()).hexdigest()


def exact_offline_contract(prov: dict[str, Any], digest: str, expected_scope: str) -> bool:
    if not isinstance(prov, dict) or not digest:
        return False
    proof = prov.get("bulk_offline_activation_proof")
    if not isinstance(proof, dict):
        return False
    blockers = [str(value) for value in prov.get("activation_blockers") or []]
    recorded = str(prov.get("sha256") or "").strip().casefold()
    return (
        prov.get("activation_mode") == OFFLINE_MODE
        and prov.get("check_mode") == OFFLINE_MODE
        and prov.get("check_status") == "live_unverified"
        and prov.get("activation_eligible") is True
        and prov.get("strict_activation_eligible") is False
        and prov.get("runtime_evidence_eligible") is False
        and blockers == [OFFLINE_BLOCKER]
        and (len(recorded) != 64 or recorded == digest)
        and proof.get("schemaVersion") == 1
        and proof.get("scope") == expected_scope
        and str(proof.get("providerSha256") or "").casefold() == digest
        and str(proof.get("pendingSha256") or "").casefold() == digest
        and proof.get("minimizerFixedPoint") is True
        and proof.get("nodeSyntax") == "passed"
        and proof.get("providerV3Contract") == "passed"
        and proof.get("directOriginSyntax") == "passed"
        and proof.get("networkValidation") == "not_authoritative_in_github_waf_limited"
        and proof.get("livePlaybackValidated") is False
        and proof.get("fullOkClaimed") is False
    )


class ProductionFreshnessAuthority:
    def __init__(self, root: Path, *, all_scope_status: Path | None = None):
        self.root = root
        self.all_scope_state = load(
            all_scope_status
            if all_scope_status is not None
            else root / "automation/provider-census-all-status-latest.json"
        )
        self.pending_state = load(root / "automation/provider-onboarding-pending-status-latest.json")
        self.all_scope = proof_map(self.all_scope_state)
        self.pending = proof_map(self.pending_state)
        reactivation = load(root / "automation/provider-disabled-reactivation-ledger.json")
        rows = reactivation.get("providers") if isinstance(reactivation.get("providers"), dict) else {}
        self.reactivation = {canon(key): value for key, value in rows.items() if isinstance(value, dict)}
        provenance = load(root / "PROVENANCE.json")
        prov_rows = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}
        self.provenance = {canon(key): value for key, value in prov_rows.items() if isinstance(value, dict)}

    def authorize(self, row: dict[str, Any], projection: str) -> tuple[bool, str]:
        provider = canon(row.get("id"))
        declared = declared_lanes(row)
        digest = artifact_digest(self.root, row.get("filename"))
        if (
            int(self.all_scope_state.get("artifactHashSchemaVersion") or 0) >= 2
            and fresh_full(self.all_scope.get(provider), declared, digest)
        ):
            return True, "all-scope-full-exact-byte"

        if exact_disabled_reactivation(self.reactivation.get(provider), declared, digest):
            return True, "disabled-recovery-exact-byte"

        prov = self.provenance.get(provider) or {}
        if projection not in {"global", "france"}:
            return False, "invalid-projection-scope"
        expected_scope = projection
        if exact_offline_contract(prov, digest, expected_scope):
            return True, "offline-contract-exact-byte"

        evidence = self.pending.get(provider)
        activation = prov.get("bulk_activation_proof") if isinstance(prov.get("bulk_activation_proof"), dict) else {}
        if fresh_full(evidence, declared, digest):
            pending_ok = (
                prov.get("activation_mode") == "bulk_census_full_ok"
                and str(activation.get("runId") or "") == str(self.pending_state.get("runId") or "")
                and str(activation.get("triggerSha") or "") == str(self.pending_state.get("triggerSha") or "")
                and activation.get("proofSource") == "onboarding-pending-status"
                and digest
                and digest == str(activation.get("providerSha256") or "").casefold()
                and (
                    len(str(prov.get("sha256") or "").strip()) != 64
                    or digest == str(prov.get("sha256") or "").strip().casefold()
                )
            )
            if pending_ok:
                return True, "pending-full-exact-byte"

        return False, "no-current-byte-production-proof"


__all__ = [
    "OFFLINE_MODE",
    "OFFLINE_BLOCKER",
    "ProductionFreshnessAuthority",
    "artifact_digest",
    "canon",
    "declared_lanes",
    "exact_disabled_reactivation",
    "exact_offline_contract",
    "fresh_full",
    "load",
    "proof_map",
]
