#!/usr/bin/env python3
"""Inspect one provider's exact production publication convergence.

Read-only diagnostic used by release/Repair operators. It compares the active
manifest row, current artifact bytes, materialization ledger and provenance
proof hashes without granting any publication authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def canon(value: object) -> str:
    return str(value or "").strip().casefold()


def find_manifest_row(provider_id: str) -> tuple[str, dict[str, Any]] | tuple[None, None]:
    for label, path in (("global", ROOT / "manifest.json"), ("france", ROOT / "vf" / "manifest.json")):
        doc = load(path, {})
        for row in doc.get("scrapers") or []:
            if isinstance(row, dict) and canon(row.get("id")) == provider_id:
                return label, row
    return None, None


def resolve_artifact(filename: object) -> Path | None:
    raw = str(filename or "").strip().replace("\\", "/")
    if raw.startswith("../"):
        raw = raw[3:]
    if not raw:
        return None
    path = (ROOT / raw).resolve()
    if ROOT.resolve() not in path.parents or not path.is_file():
        return None
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("provider")
    args = ap.parse_args()
    provider_id = canon(args.provider)

    scope, row = find_manifest_row(provider_id)
    provenance = load(ROOT / "PROVENANCE.json", {})
    prov = (provenance.get("providers") or {}).get(provider_id)
    material = load(ROOT / "provider-v3-materialization.json", {})
    material_row = next(
        (
            x for x in material.get("providers") or []
            if isinstance(x, dict) and canon(x.get("provider")) == provider_id
        ),
        None,
    )

    artifact = resolve_artifact(row.get("filename") if isinstance(row, dict) else "")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest() if artifact else None

    prov = prov if isinstance(prov, dict) else {}
    final_min = prov.get("final_minimizer") if isinstance(prov.get("final_minimizer"), dict) else {}
    final_fixed = prov.get("final_fixed_point") if isinstance(prov.get("final_fixed_point"), dict) else {}
    proof = (
        prov.get("bulk_offline_activation_proof")
        if isinstance(prov.get("bulk_offline_activation_proof"), dict)
        else {}
    )

    result = {
        "provider": provider_id,
        "scope": scope,
        "manifest": {
            "id": row.get("id") if isinstance(row, dict) else None,
            "enabled": row.get("enabled") if isinstance(row, dict) else None,
            "version": row.get("version") if isinstance(row, dict) else None,
            "filename": row.get("filename") if isinstance(row, dict) else None,
            "supportedTypes": row.get("supportedTypes") if isinstance(row, dict) else None,
        },
        "artifact": {
            "exists": artifact is not None,
            "sha256": digest,
            "bytes": artifact.stat().st_size if artifact else None,
        },
        "materialization": {
            "file": material_row.get("file") if isinstance(material_row, dict) else None,
            "sha256": material_row.get("sha256") if isinstance(material_row, dict) else None,
            "minimizer": material_row.get("minimizer") if isinstance(material_row, dict) else None,
        },
        "provenance": {
            "activation_mode": prov.get("activation_mode"),
            "check_mode": prov.get("check_mode"),
            "check_status": prov.get("check_status"),
            "published_filename": prov.get("published_filename"),
            "sha256": prov.get("sha256"),
            "patched_sha256": prov.get("patched_sha256"),
            "final_minimizer": {
                "sha256": final_min.get("sha256"),
                "production_enabled": final_min.get("production_enabled"),
                "one_physical_line": final_min.get("one_physical_line"),
                "schema_version": final_min.get("schema_version"),
            },
            "final_fixed_point": {
                "sha256": final_fixed.get("sha256"),
                "verified": final_fixed.get("verified"),
                "one_physical_line": final_fixed.get("one_physical_line"),
            },
            "offline_proof": {
                "providerSha256": proof.get("providerSha256"),
                "pendingSha256": proof.get("pendingSha256"),
                "livePlaybackValidated": proof.get("livePlaybackValidated"),
                "fullOkClaimed": proof.get("fullOkClaimed"),
                "scope": proof.get("scope"),
            },
        },
    }
    result["convergence"] = {
        "manifest_matches_materialization": bool(
            isinstance(material_row, dict)
            and str(row.get("filename") if isinstance(row, dict) else "").lstrip("../")
            == str(material_row.get("file") or "")
        ),
        "artifact_matches_materialization": bool(
            digest and isinstance(material_row, dict)
            and digest == str(material_row.get("sha256") or "").casefold()
        ),
        "artifact_matches_final_minimizer": bool(
            digest and digest == str(final_min.get("sha256") or "").casefold()
        ),
        "artifact_matches_fixed_point": bool(
            digest and digest == str(final_fixed.get("sha256") or "").casefold()
        ),
        "artifact_matches_offline_proof": bool(
            digest and digest == str(proof.get("providerSha256") or "").casefold()
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
