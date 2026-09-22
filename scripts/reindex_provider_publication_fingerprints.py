#!/usr/bin/env python3
"""Reindex Provider v3 publication fingerprints without rebuilding provider bytes."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from reapply_published_overrides import (  # noqa: E402
    PUBLICATION_CONTRACT_SCHEMA,
    provider_build_input_sha,
    provider_policy_sha,
    publication_contract_sha,
    resolve_runtime_base,
)

MANIFEST=ROOT/"manifest.json"
OVERRIDES=ROOT/"provider-overrides.json"
PROVENANCE=ROOT/"PROVENANCE.json"


def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(f"{path}: expected object")
    return value


def main() -> int:
    manifest=load(MANIFEST)
    config=load(OVERRIDES)
    provenance=load(PROVENANCE)
    rows=provenance.get("providers")
    if not isinstance(rows,dict):
        raise ValueError("PROVENANCE.providers must be an object")

    contract_sha=publication_contract_sha(config)
    checked=0
    byte_proof_before: dict[str,str]={}

    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry,dict):
            continue
        provider_id=str(entry.get("id") or "").strip().casefold()
        relative=str(entry.get("filename") or "").strip()
        if not provider_id or not relative.startswith("providers/"):
            continue
        path=(ROOT/relative).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        byte_proof_before[provider_id]=digest

        row=rows.get(provider_id)
        if not isinstance(row,dict):
            raise ValueError(f"{provider_id}: missing provenance row")
        if str(row.get("published_filename") or "") != relative:
            raise ValueError(f"{provider_id}: published reference drift before fingerprint reindex")
        if str(row.get("sha256") or "").casefold() != digest:
            raise ValueError(f"{provider_id}: published SHA drift before fingerprint reindex")

        _base_path,base_sha=resolve_runtime_base(provider_id,row,require=True)
        if not base_sha:
            raise ValueError(f"{provider_id}: missing runtime base SHA")
        policy_sha=provider_policy_sha(config,provider_id)
        row["provider_policy_sha256"]=policy_sha
        row["build_contract_schema"]=PUBLICATION_CONTRACT_SCHEMA
        row["build_input_sha256"]=provider_build_input_sha(
            provider_id,
            base_sha,
            contract_sha,
            policy_sha,
            row,
        )
        checked+=1

    provenance["provider_publication_contract"]={
        "schema_version":PUBLICATION_CONTRACT_SCHEMA,
        "sha256":contract_sha,
        "provider_count":checked,
        "mode":"provider_base_plus_deterministic_core_provider_local_policy",
    }
    PROVENANCE.write_text(
        json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8",
    )

    # Fingerprint migration is metadata-only. Re-read every published byte after
    # the write and prove the provider assets themselves did not move.
    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry,dict):
            continue
        provider_id=str(entry.get("id") or "").strip().casefold()
        relative=str(entry.get("filename") or "").strip()
        if provider_id not in byte_proof_before:
            continue
        digest=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
        if digest != byte_proof_before[provider_id]:
            raise AssertionError(f"{provider_id}: fingerprint reindex changed provider bytes")

    print(
        "FIELD_PROVIDER_PUBLICATION_FINGERPRINT_REINDEX "
        f"schema={PUBLICATION_CONTRACT_SCHEMA} providers={checked} bytes_changed=0"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
