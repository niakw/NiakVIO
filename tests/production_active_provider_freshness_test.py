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


def fresh_full(evidence: dict | None, declared: set[str]) -> bool:
    if not isinstance(evidence, dict):
        return False
    verified = {str(x).strip().lower() for x in evidence.get("currentVerifiedLanes") or [] if str(x).strip()}
    return (
        evidence.get("status") == "FULL OK"
        and evidence.get("testedThisRun") is True
        and bool(declared)
        and declared <= verified
        and evidence.get("repairEligible") is not True
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
pending = load(ROOT / "automation/provider-onboarding-pending-status-latest.json")
canonical_proof = proof_map(canonical)
pending_proof = proof_map(pending)
provenance = load(ROOT / "PROVENANCE.json")
prov_rows = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}
prov_by_id = {canon(k): v for k, v in prov_rows.items() if isinstance(v, dict)}

offline_seen = 0
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
        if fresh_full(canonical_proof.get(pid), declared):
            continue

        prov = prov_by_id.get(pid) or {}
        digest = artifact_digest(str(row.get("filename") or ""))
        offline_scope = str((prov.get("bulk_offline_activation_proof") or {}).get("scope") or "")
        expected_offline_scope = "global" if projection == "global" else offline_scope
        if exact_offline_contract(prov, digest, expected_offline_scope):
            if projection == "global":
                assert offline_scope == "global", f"{pid}: France-only offline provider leaked into Global"
            offline_seen += 1
            continue

        evidence = pending_proof.get(pid)
        activation = prov.get("bulk_activation_proof") if isinstance(prov.get("bulk_activation_proof"), dict) else {}
        assert fresh_full(evidence, declared), (
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

print(
    "Production active providers require fresh FULL OK evidence or exact-byte offline contract proof; "
    f"offline_live_unverified_checks={offline_seen} and never count as FULL OK"
)
