#!/usr/bin/env python3
"""Finalize exact-byte minimizer authority for active France-only providers.

Global providers are finalized by finalize_provider_v3_minimizer.py. This script
covers the strict catalogue-owned {general:false,vf:true} cohort so the VF
projection, catalogue, physical provider bytes and PROVENANCE exact-byte proofs
cannot diverge before offline-proof rebind or release publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from provider_security_hardening import assert_hardened
from provider_v3_minimizer import PRODUCTION_ENABLED, TERSER_ALLOWED, minimize_text, validate_transform
from reapply_published_overrides import (
    bump_provider_version,
    load_provider_version_floors,
    published_name,
    validate_artifact,
    version_is_strictly_above_floor,
)

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_MANIFEST = ROOT / "manifest.json"
VF_MANIFEST = ROOT / "vf" / "manifest.json"
CATALOG = ROOT / "provider_catalog.json"
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"
MINIMIZER = ROOT / "scripts" / "provider_v3_minimizer.py"
SCHEMA_VERSION = 3


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canon(value: object) -> str:
    return str(value or "").strip().casefold()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tool_sha() -> str:
    return sha(MINIMIZER.read_bytes())


def safe_path(relative: str) -> Path:
    clean = str(relative or "").strip().replace("\\", "/")
    if not clean.startswith("providers/"):
        raise ValueError(f"France-only active provider outside providers/: {clean}")
    path = (ROOT / clean).resolve()
    if path.parent != PROVIDERS.resolve() or not path.is_file():
        raise ValueError(f"missing or unsafe France-only provider asset: {clean}")
    return path


def active_france_only(
    global_manifest: dict[str, Any],
    vf_manifest: dict[str, Any],
    catalog: dict[str, Any],
) -> list[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]]:
    global_ids = {
        canon(row.get("id"))
        for row in global_manifest.get("scrapers") or []
        if isinstance(row, dict) and canon(row.get("id"))
    }
    vf_rows = {
        canon(row.get("id")): row
        for row in vf_manifest.get("scrapers") or []
        if isinstance(row, dict) and canon(row.get("id"))
    }
    out: list[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    seen: set[str] = set()
    for record in catalog.get("providers") or []:
        if not isinstance(record, dict):
            continue
        scraper = record.get("scraper")
        projections = record.get("projections")
        if not isinstance(scraper, dict) or not isinstance(projections, dict):
            continue
        pid = canon(record.get("canonicalId") or scraper.get("id"))
        if not pid or pid in seen:
            if pid:
                raise ValueError(f"duplicate France-only catalogue identity: {pid}")
            continue
        if projections.get("general") is not False or projections.get("vf") is not True:
            continue
        if pid in global_ids:
            raise ValueError(f"{pid}: strict France-only identity leaked into Global")
        seen.add(pid)
        if scraper.get("enabled") is False:
            continue
        vf_row = vf_rows.get(pid)
        if not isinstance(vf_row, dict) or vf_row.get("enabled") is False:
            raise ValueError(f"{pid}: active France-only catalogue row lacks active VF projection")
        catalog_file = str(scraper.get("filename") or "").strip().replace("\\", "/")
        vf_file = str(vf_row.get("filename") or "").strip().replace("\\", "/")
        expected_vf = f"../{catalog_file}" if catalog_file.startswith("providers/") else catalog_file
        if vf_file != expected_vf:
            raise ValueError(
                f"{pid}: France-only catalogue/VF filename mismatch "
                f"catalogue={catalog_file} vf={vf_file}"
            )
        out.append((pid, record, scraper, vf_row))
    return out


def final_proof(*, digest: str, t_sha: str, result: Any, current: object, changed: bool) -> dict[str, Any]:
    saved = int(result.saved_bytes)
    lines = int(result.transformed_lines)
    skipped = str(result.skipped_reason or "")
    if not changed and isinstance(current, dict):
        same = (
            int(current.get("schema_version") or 0) == SCHEMA_VERSION
            and str(current.get("tool_sha256") or "").casefold() == t_sha.casefold()
            and str(current.get("sha256") or "").casefold() == digest.casefold()
            and current.get("production_enabled") is True
            and current.get("terser_allowed") is False
        )
        if same:
            saved = int(current.get("saved_bytes") or 0)
            lines = int(current.get("transformed_lines") or 0)
            skipped = str(current.get("skipped_reason") or "")
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "scripts/provider_v3_minimizer.py",
        "tool_sha256": t_sha,
        "production_enabled": True,
        "terser_allowed": False,
        "one_physical_line": True,
        "saved_bytes": saved,
        "transformed_lines": lines,
        "skipped_reason": skipped,
        "sha256": digest,
    }


def finalize(*, check: bool) -> dict[str, Any]:
    if not PRODUCTION_ENABLED or TERSER_ALLOWED:
        raise ValueError("NiakVIO minimizer production contract is not safe")

    global_manifest = load(GLOBAL_MANIFEST)
    vf_manifest = load(VF_MANIFEST)
    catalog = load(CATALOG)
    provenance = load(PROVENANCE)
    prov_rows = provenance.get("providers")
    if not isinstance(prov_rows, dict):
        raise ValueError("PROVENANCE.json providers map required")

    cohort = active_france_only(global_manifest, vf_manifest, catalog)
    floors = load_provider_version_floors()
    t_sha = tool_sha()
    stale = False
    changed_count = 0
    outputs: dict[Path, bytes] = {}

    for pid, _record, scraper, vf_row in cohort:
        relative = str(scraper.get("filename") or "").strip().replace("\\", "/")
        path = safe_path(relative)
        original_bytes = path.read_bytes()
        original = original_bytes.decode("utf-8", errors="strict")
        try:
            result = minimize_text(original)
            validate_transform(original, result.text)
        except Exception as exc:
            raise ValueError(f"{pid}: France-only final minimizer failed: {exc}") from exc
        assert_hardened(result.text)
        minimized = result.text.encode("utf-8")
        validate_artifact(minimized, pid)

        digest = sha(minimized)
        new_name = published_name(pid, path, digest, audit_quarantined=False)
        new_relative = f"providers/{new_name}"
        changed = minimized != original_bytes
        ref_changed = new_relative != relative
        if changed != ref_changed:
            raise ValueError(
                f"{pid}: France-only content-addressed drift changed={changed} ref_changed={ref_changed}"
            )

        prov = prov_rows.get(pid)
        if not isinstance(prov, dict):
            raise ValueError(f"{pid}: missing provenance row")
        proof = final_proof(
            digest=digest,
            t_sha=t_sha,
            result=result,
            current=prov.get("final_minimizer"),
            changed=changed,
        )
        fixed = {
            "schema_version": 1,
            "verified": True,
            "tool": "raw-bytes",
            "mangle": False,
            "one_physical_line": True,
            "sha256": digest,
        }

        next_version = str(scraper.get("version") or "1.0.0")
        if changed:
            floor = floors.get(pid)
            if not (floor and version_is_strictly_above_floor(next_version, floor)):
                next_version = bump_provider_version(next_version, floor)
            changed_count += 1
            outputs[ROOT / new_relative] = minimized

        expected_vf_file = f"../{new_relative}"
        updates = (
            str(scraper.get("filename") or "") != new_relative
            or str(vf_row.get("filename") or "") != expected_vf_file
            or str(scraper.get("version") or "") != next_version
            or str(vf_row.get("version") or "") != next_version
            or prov.get("final_minimizer") != proof
            or prov.get("final_fixed_point") != fixed
            or str(prov.get("published_filename") or "") != new_relative
            or str(prov.get("sha256") or "").casefold() != digest
        )
        if updates:
            stale = True
            scraper["filename"] = new_relative
            scraper["version"] = next_version
            vf_row["filename"] = expected_vf_file
            vf_row["version"] = next_version
            prov["published_filename"] = new_relative
            prov["sha256"] = digest
            if "patched_sha256" in prov:
                prov["patched_sha256"] = digest
            prov["final_minimizer"] = proof
            prov["final_fixed_point"] = fixed

    if check:
        if stale:
            raise SystemExit("France-only published providers are not minimizer fixed-point")
        print(
            "FIELD_FRANCE_ONLY_MINIMIZER_PUBLICATION "
            f"providers={len(cohort)} changed=0 fixed_point=true one_line=true terser_allowed=false"
        )
        return {"providerCount": len(cohort), "changed": 0}

    for destination, data in outputs.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    write(VF_MANIFEST, vf_manifest)
    write(CATALOG, catalog)
    write(PROVENANCE, provenance)
    print(
        "FIELD_FRANCE_ONLY_MINIMIZER_PUBLICATION "
        f"providers={len(cohort)} changed={changed_count} "
        "fixed_point=true one_line=true terser_allowed=false"
    )
    return {"providerCount": len(cohort), "changed": changed_count}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    finalize(check=bool(args.check))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
