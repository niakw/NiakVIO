#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from provider_v3_minimizer import minimize_text, validate_transform

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
MATERIALIZATION = ROOT / "provider-v3-materialization.json"
PROVENANCE = ROOT / "PROVENANCE.json"
MINIMIZER = ROOT / "scripts" / "provider_v3_minimizer.py"
MINIMIZER_PROOF_SCHEMA = 2


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canon(value: object) -> str:
    return str(value or "").strip().casefold()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def canonical_minimizer_proof(filename: str, digest: str) -> dict[str, Any]:
    """Build the exact proof expected by the authoritative final minimizer.

    Domain refresh may update a touched provider's content-addressed asset, but it
    must never merely transplant an old proof to the new SHA. Verify the current
    bytes are already a minimizer fixed point, then bind a fresh proof to those
    exact bytes and to the current minimizer tool.
    """
    path = (ROOT / filename).resolve()
    safe_roots = ((ROOT / "providers").resolve(), (ROOT / "provider-disabled").resolve())
    if not any(_relative_to(path, root) for root in safe_roots):
        raise SystemExit(f"unsafe provider publication path: {filename}")
    if not path.is_file():
        raise SystemExit(f"missing provider publication asset: {filename}")

    original = path.read_text(encoding="utf-8")
    actual_digest = sha256(original.encode("utf-8"))
    if actual_digest != digest:
        raise SystemExit(
            f"provider publication digest mismatch: {filename} materialization={digest} actual={actual_digest}"
        )

    result = minimize_text(original)
    validate_transform(original, result.text)
    if result.text != original:
        raise SystemExit(
            f"provider publication is not minimizer fixed-point before provenance sync: {filename}"
        )

    return {
        "schema_version": MINIMIZER_PROOF_SCHEMA,
        "tool": "scripts/provider_v3_minimizer.py",
        "tool_sha256": sha256(MINIMIZER.read_bytes()),
        "production_enabled": True,
        "terser_allowed": False,
        "saved_bytes": int(result.saved_bytes),
        "transformed_lines": int(result.transformed_lines),
        "skipped_reason": str(result.skipped_reason or ""),
        "sha256": digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changes", default="health-output/domain-site-changes.json")
    args = parser.parse_args()

    changes = load(ROOT / args.changes)
    selected = {canon(x) for x in changes.get("changed") or [] if canon(x)}
    manifest = load(MANIFEST)
    materialization = load(MATERIALIZATION)
    provenance = load(PROVENANCE)

    manifest_rows = {
        canon(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and canon(row.get("id"))
    }
    material_rows = {
        canon(row.get("provider")): row
        for row in materialization.get("providers") or []
        if isinstance(row, dict) and canon(row.get("provider"))
    }
    provenance_rows = provenance.get("providers")
    if not isinstance(provenance_rows, dict):
        raise SystemExit("PROVENANCE.json providers map required")

    changed = []
    proof_refreshed = []
    for provider_id in sorted(selected):
        manifest_row = manifest_rows.get(provider_id)
        material_row = material_rows.get(provider_id)
        provenance_row = provenance_rows.get(provider_id)
        if not all(isinstance(x, dict) for x in (manifest_row, material_row, provenance_row)):
            raise SystemExit(f"{provider_id}: incomplete publication provenance state")
        filename = str(manifest_row.get("filename") or "").strip()
        material_filename = str(material_row.get("file") or "").strip()
        digest = str(material_row.get("sha256") or "").strip().casefold()
        if not filename.startswith(("providers/", "provider-disabled/")) or len(digest) != 64:
            raise SystemExit(f"{provider_id}: invalid current publication identity")
        if material_filename and material_filename != filename:
            raise SystemExit(
                f"{provider_id}: manifest/materialization publication mismatch: "
                f"manifest={filename} materialization={material_filename}"
            )

        # DOMAIN_REFRESH_MINIMIZER_PROOF_V61: prove the newly addressed asset is
        # already final-minimizer fixed-point before updating any provenance.
        minimizer_proof = canonical_minimizer_proof(filename, digest)

        before = json.dumps(provenance_row, ensure_ascii=False, sort_keys=True)
        provenance_row["published_filename"] = filename
        provenance_row["sha256"] = digest
        if "patched_sha256" in provenance_row:
            provenance_row["patched_sha256"] = digest
        fixed = provenance_row.get("final_fixed_point")
        if isinstance(fixed, dict):
            fixed["sha256"] = digest
        if provenance_row.get("final_minimizer") != minimizer_proof:
            provenance_row["final_minimizer"] = minimizer_proof
            proof_refreshed.append(provider_id)
        if before != json.dumps(provenance_row, ensure_ascii=False, sort_keys=True):
            changed.append(provider_id)

    if changed:
        write(PROVENANCE, provenance)
    print(
        "FIELD_DOMAIN_REFRESH_PROVENANCE "
        f"scope={','.join(sorted(selected)) if selected else '-'} "
        f"changed={','.join(changed) if changed else '-'} "
        f"minimizer_proof={','.join(proof_refreshed) if proof_refreshed else '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
