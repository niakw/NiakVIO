#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")

def load(path: Path) -> dict:
    if not path.is_file():
        return {}
    value=json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value,dict) else {}

def proof_map(state: dict) -> dict[str, dict]:
    return {
        canon(row.get("provider")):row
        for row in state.get("providers") or []
        if isinstance(row,dict) and canon(row.get("provider"))
    }

def fresh_full(evidence: dict | None, declared: set[str]) -> bool:
    if not isinstance(evidence,dict):
        return False
    verified={str(x).strip().lower() for x in evidence.get("currentVerifiedLanes") or [] if str(x).strip()}
    return (
        evidence.get("status")=="FULL OK"
        and evidence.get("testedThisRun") is True
        and bool(declared)
        and declared <= verified
        and evidence.get("repairEligible") is not True
    )

canonical=load(ROOT/"automation/provider-census-status.json")
pending=load(ROOT/"automation/provider-onboarding-pending-status-latest.json")
canonical_proof=proof_map(canonical)
pending_proof=proof_map(pending)
provenance=load(ROOT/"PROVENANCE.json")
prov_rows=provenance.get("providers") if isinstance(provenance.get("providers"),dict) else {}
prov_by_id={canon(k):v for k,v in prov_rows.items() if isinstance(v,dict)}

for manifest_path in (ROOT/"manifest.json", ROOT/"vf"/"manifest.json"):
    manifest=load(manifest_path)
    active=[row for row in manifest.get("scrapers") or [] if isinstance(row,dict) and row.get("enabled") is not False]
    for row in active:
        pid=canon(row.get("id"))
        assert pid, (manifest_path,row)
        declared={str(x).strip().lower() for x in row.get("canonicalSupportedTypes") or row.get("supportedTypes") or [] if str(x).strip()}
        if fresh_full(canonical_proof.get(pid),declared):
            continue
        evidence=pending_proof.get(pid)
        prov=prov_by_id.get(pid) or {}
        activation=prov.get("bulk_activation_proof") if isinstance(prov.get("bulk_activation_proof"),dict) else {}
        filename=str(row.get("filename") or "")
        artifact=ROOT/filename
        digest=hashlib.sha256(artifact.read_bytes()).hexdigest() if artifact.is_file() else ""
        assert fresh_full(evidence,declared), f"{manifest_path}: active {pid} lacks fresh canonical/pending FULL proof"
        assert prov.get("activation_mode")=="bulk_census_full_ok", f"{pid}: pending proof without completed bulk activation"
        assert str(activation.get("runId") or "")==str(pending.get("runId") or ""), f"{pid}: activation/pending run mismatch"
        assert str(activation.get("triggerSha") or "")==str(pending.get("triggerSha") or ""), f"{pid}: activation/pending SHA mismatch"
        assert activation.get("proofSource")=="onboarding-pending-status", f"{pid}: unsupported proof source"
        assert digest and digest==str(activation.get("providerSha256") or "").casefold(), f"{pid}: active provider bytes differ from replayed pending bytes"
        recorded=str(prov.get("sha256") or "").strip().casefold()
        if len(recorded)==64:
            assert digest==recorded, f"{pid}: provenance hash mismatch"

print("Production active providers require fresh FULL OK evidence or exact byte-bound pending activation proof")
