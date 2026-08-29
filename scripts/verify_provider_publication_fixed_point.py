#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Verify persisted proof that every published provider is a final Terser fixed point.

The expensive two-pass Terser proof is minted only by the publication finalizer
when provider bytes are actually rebuilt. Unchanged Core runs verify the exact
published SHA, proof metadata and publication contract without re-running Terser.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from provider_purification import TERSER_VERSION

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def main() -> int:
    manifest = load_object(MANIFEST)
    provenance = load_object(PROVENANCE)
    provenance_rows = provenance.get("providers")
    if not isinstance(provenance_rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")

    contract = provenance.get("provider_publication_contract")
    if not isinstance(contract, dict) or int(contract.get("schema_version") or 0) != 2:
        raise ValueError("missing current provider publication contract proof")
    if not str(contract.get("sha256") or "").strip():
        raise ValueError("provider publication contract SHA is missing")

    checked = 0
    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        relative = str(entry.get("filename") or "").strip()
        if not provider_id or not relative.startswith("providers/"):
            continue
        row = provenance_rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance")
        if str(row.get("published_filename") or "") != relative:
            raise ValueError(f"{provider_id}: provenance/public manifest reference mismatch")

        path = (ROOT / relative).resolve()
        try:
            path.relative_to(PROVIDERS.resolve())
        except ValueError as exc:
            raise ValueError(f"{provider_id}: unsafe published provider path") from exc
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != str(row.get("sha256") or "").casefold():
            raise ValueError(f"{provider_id}: published provider SHA drift")

        proof = row.get("final_fixed_point")
        if not isinstance(proof, dict):
            raise ValueError(f"{provider_id}: missing final fixed-point proof")
        if int(proof.get("schema_version") or 0) != 1:
            raise ValueError(f"{provider_id}: unsupported final fixed-point proof schema")
        if proof.get("verified") is not True:
            raise ValueError(f"{provider_id}: final fixed point is not verified")
        if proof.get("mangle") is not False:
            raise ValueError(f"{provider_id}: unexpected Terser mangle policy")
        if str(proof.get("tool") or "") != "terser":
            raise ValueError(f"{provider_id}: unexpected fixed-point tool")
        if str(proof.get("tool_version") or "") != TERSER_VERSION:
            raise ValueError(f"{provider_id}: stale fixed-point Terser version")
        if str(proof.get("sha256") or "").casefold() != digest:
            raise ValueError(f"{provider_id}: fixed-point proof SHA mismatch")
        if not str(row.get("build_input_sha256") or "").strip():
            raise ValueError(f"{provider_id}: missing publication input fingerprint")
        checked += 1

    if checked < 1:
        raise ValueError("no published provider was checked")
    if checked != len(provenance_rows):
        raise ValueError(
            f"manifest/provenance provider count mismatch: checked={checked} provenance={len(provenance_rows)}"
        )

    print(
        f"FIELD_FINAL_TERSER_FIXED_POINT providers={checked} "
        f"tool=terser version={TERSER_VERSION} mangle=false proof=persisted-sha"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
