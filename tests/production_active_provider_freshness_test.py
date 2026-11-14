#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFLINE_MODE = "bulk_offline_contract_live_unverified"
OFFLINE_BLOCKER = "live_native_validation_pending"


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def proof_map(state: dict) -> dict[str, dict]:
    return {
        canon(row.get("provider")): row
        for row in state.get("providers") or []
        if isinstance(row, dict) and canon(row.get("provider"))
    }


def fresh_full(evidence: dict | None, declared: set[str], digest: str) -> bool:
    if not isinstance(evidence, dict):
        return False
    verified = {str(x).strip().lower() for x in evidence.get("currentVerifiedLanes") or [] if str(x).strip()}
    return (
        evidence.get("status") == "FULL OK"
        and evidence.get("testedThisRun") is True
        and bool(declared)
        and declared <= verified
        and evidence.get("repairEligible") is not True
        and bool(digest)
        and str(evidence.get("providerArtifactSha256") or "").strip().casefold() == digest
    )


def exact_disabled_reactivation(proof: dict | None, declared: set[str], digest: str) -> bool:
    if not isinstance(proof, dict) or not digest:
        return False
    verified = {str(x).strip().lower() for x in proof.get("verifiedLanes") or [] if str(x).strip()}
    proof_declared = {str(x).strip().lower() for x in proof.get("declaredLanes") or [] if str(x).strip()}
    return (
        proof.get("proofAuthority") == "disabled-recovery-exact-byte-residential-v1"
        and proof.get("proofStatus") == "terminal_identity_verified"
        and proof.get("brainAbstained") is True
        and proof.get("repairRequired") is False
        and proof.get("directMutationAuthority") is False
        and bool(declared)
        and proof_declared == declared
        and declared <= verified
        and int(proof.get("streamsPlayable") or 0) >= len(declared)
        and int(proof.get("payloadVerifiedStreams") or 0) >= len(declared)
        and int(proof.get("identityVerifiedStreams") or 0) >= len(declared)
        and str(proof.get("providerArtifactSha256") or "").strip().casefold() == digest
    )


def artifact_digest(filename: str) -> str:
    relative = str(filename or "").strip().replace("\\", "/")
    if relative.startswith("../"):
        relative = relative[3:]
    if not relative.startswith("providers/"):
        return ""
    artifact = ROOT / relative
    return hashlib.sha256(artifact.read_bytes()).hexdigest() if artifact.is_file() else ""


def exact_offline_contract(prov: dict, digest: str, expected_scope: str) -> bool:
    if not isinstance(prov, dict) or not digest:
        return False
    proof = prov.get("bulk_offline_activation_proof")
    if not isinstance(proof, dict):
        return False
    blockers = [str(x) for x in prov.get("activation_blockers") or []]
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


canonical = load(ROOT / "automation/provider-census-status.json")
all_scope = load(ROOT / "automation/provider-census-all-status-latest.json")
pending = load(ROOT / "automation/provider-onboarding-pending-status-latest.json")
canonical_proof = proof_map(canonical)
all_scope_proof = proof_map(all_scope)
pending_proof = proof_map(pending)
reactivation = load(ROOT / "automation/provider-disabled-reactivation-ledger.json")
reactivation_rows = reactivation.get("providers") if isinstance(reactivation.get("providers"), dict) else {}
reactivation_by_id = {canon(k): v for k, v in reactivation_rows.items() if isinstance(v, dict)}
provenance = load(ROOT / "PROVENANCE.json")
prov_rows = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}
prov_by_id = {canon(k): v for k, v in prov_rows.items() if isinstance(v, dict)}

offline_seen = 0
reactivated_seen = 0
for manifest_path, projection in (
    (ROOT / "manifest.json", "global"),
    (ROOT / "vf" / "manifest.json", "france"),
):
    manifest = load(manifest_path)
    active = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and row.get("enabled") is not False]
    for row in active:
        pid = canon(row.get("id"))
        assert pid, (manifest_path, row)
        declared = {
            str(x).strip().lower()
            for x in row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
            if str(x).strip()
        }
        digest = artifact_digest(str(row.get("filename") or ""))
        # Production freshness comes from the last complete all-scope replay,
        # byte-bound to the current artifact. Operational unresolved/targeted
        # censuses remain free to update Repair state without erasing this proof.
        if fresh_full(all_scope_proof.get(pid), declared, digest):
            continue

        if exact_disabled_reactivation(reactivation_by_id.get(pid), declared, digest):
            reactivated_seen += 1
            continue

        prov = prov_by_id.get(pid) or {}
        offline_scope = str((prov.get("bulk_offline_activation_proof") or {}).get("scope") or "")
        expected_offline_scope = "global" if projection == "global" else offline_scope
        if exact_offline_contract(prov, digest, expected_offline_scope):
            if projection == "global":
                assert offline_scope == "global", f"{pid}: France-only offline provider leaked into Global"
            offline_seen += 1
            continue

        evidence = pending_proof.get(pid)
        activation = prov.get("bulk_activation_proof") if isinstance(prov.get("bulk_activation_proof"), dict) else {}
        assert fresh_full(evidence, declared, digest), (
            f"{manifest_path}: active {pid} lacks fresh FULL proof or exact-byte offline-live-unverified contract proof"
        )
        assert prov.get("activation_mode") == "bulk_census_full_ok", f"{pid}: pending proof without completed bulk activation"
        assert str(activation.get("runId") or "") == str(pending.get("runId") or ""), f"{pid}: activation/pending run mismatch"
        assert str(activation.get("triggerSha") or "") == str(pending.get("triggerSha") or ""), f"{pid}: activation/pending SHA mismatch"
        assert activation.get("proofSource") == "onboarding-pending-status", f"{pid}: unsupported proof source"
        assert digest and digest == str(activation.get("providerSha256") or "").casefold(), (
            f"{pid}: active provider bytes differ from replayed pending bytes"
        )
        recorded = str(prov.get("sha256") or "").strip().casefold()
        if len(recorded) == 64:
            assert digest == recorded, f"{pid}: provenance hash mismatch"

assert int(all_scope.get("artifactHashSchemaVersion") or 0) >= 1, "missing byte-bound all-scope freshness ledger"
print(
    "Production active providers require byte-bound all-scope FULL OK evidence or exact-byte offline contract proof; "
    f"offline_live_unverified_checks={offline_seen} reactivation_checks={reactivated_seen}; neither is mislabeled as census FULL OK"
)
