#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply the NiakVIO-safe Provider v3 minimizer to published current bundles.

This is deliberately a publication transform, not a generic JavaScript minifier.
It delegates every byte decision to ``provider_v3_minimizer.py`` (Terser is
forbidden), then updates content-addressed provider filenames, provider versions
and provenance atomically in the workspace. Superseded provider files are left
for the authoritative prune step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from provider_security_hardening import assert_hardened
from provider_v3_minimizer import (
    EXPECTED_PROVIDER_COUNT,
    PRODUCTION_ENABLED,
    TERSER_ALLOWED,
    minimize_text,
    validate_transform,
)
from reapply_published_overrides import (
    bump_provider_version,
    load_provider_version_floors,
    published_name,
    validate_artifact,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"
MINIMIZER = ROOT / "scripts" / "provider_v3_minimizer.py"
SCHEMA_VERSION = 1


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path.relative_to(ROOT)}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tool_sha() -> str:
    return _sha(MINIMIZER.read_bytes())


def _provider_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    if len(rows) != EXPECTED_PROVIDER_COUNT:
        raise ValueError(
            f"expected {EXPECTED_PROVIDER_COUNT} current providers, got {len(rows)}"
        )
    ids = [str(row.get("id") or "").strip().casefold() for row in rows]
    if any(not value for value in ids) or len(set(ids)) != EXPECTED_PROVIDER_COUNT:
        raise ValueError("current manifest provider ids must be unique and non-empty")
    return rows


def _safe_provider_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if PROVIDERS.resolve() not in path.parents or not path.is_file():
        raise ValueError(f"missing or unsafe current provider asset: {relative}")
    return path


def finalize(*, check: bool) -> dict[str, Any]:
    if not PRODUCTION_ENABLED or TERSER_ALLOWED:
        raise ValueError("NiakVIO minimizer production contract is not safe")

    manifest = _load_json(MANIFEST)
    provenance = _load_json(PROVENANCE)
    provenance_rows = provenance.get("providers")
    if not isinstance(provenance_rows, dict):
        raise ValueError("PROVENANCE.json providers map required")

    floors = load_provider_version_floors()
    tool_sha = _tool_sha()
    changed = 0
    saved_total = 0
    transformed_total = 0
    skipped_templates = 0
    stale = False
    outputs: dict[Path, bytes] = {}

    for entry in _provider_rows(manifest):
        provider_id = str(entry.get("id") or "").strip().casefold()
        relative = str(entry.get("filename") or "").strip()
        path = _safe_provider_path(relative)
        original = path.read_text(encoding="utf-8")
        result = minimize_text(original)
        validate_transform(original, result.text)
        minimized = result.text.encode("utf-8")
        assert_hardened(result.text)
        validate_artifact(minimized, provider_id)

        digest = _sha(minimized)
        audit_quarantined = "--nuvio-audit-quarantine--" in path.name
        new_name = published_name(
            provider_id,
            path,
            digest,
            audit_quarantined=audit_quarantined,
        )
        new_relative = f"providers/{new_name}"
        row = provenance_rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")

        bytes_changed = minimized != original.encode("utf-8")
        ref_changed = relative != new_relative
        if bytes_changed != ref_changed:
            raise ValueError(
                f"{provider_id}: content-addressed filename drift bytes_changed={bytes_changed} "
                f"ref_changed={ref_changed}"
            )

        proof = {
            "schema_version": SCHEMA_VERSION,
            "tool": "scripts/provider_v3_minimizer.py",
            "tool_sha256": tool_sha,
            "production_enabled": True,
            "terser_allowed": False,
            "saved_bytes": int(result.saved_bytes),
            "transformed_lines": int(result.transformed_lines),
            "skipped_reason": str(result.skipped_reason or ""),
            "sha256": digest,
        }

        expected_stale = False
        if bytes_changed:
            changed += 1
            saved_total += int(result.saved_bytes)
            transformed_total += int(result.transformed_lines)
            if result.skipped_reason == "template_literal":
                skipped_templates += 1
            expected_stale = True
            entry["filename"] = new_relative
            entry["version"] = bump_provider_version(
                str(entry.get("version") or "1.0.0"),
                floors.get(provider_id),
            )
            row["published_filename"] = new_relative
            row["sha256"] = digest
            if "patched_sha256" in row:
                row["patched_sha256"] = digest
            fixed = row.get("final_fixed_point")
            if not isinstance(fixed, dict):
                fixed = {}
            fixed.update({
                "schema_version": 1,
                "verified": True,
                "tool": "raw-bytes",
                "mangle": False,
                "sha256": digest,
            })
            row["final_fixed_point"] = fixed
            row["final_minimizer"] = proof
            outputs[ROOT / new_relative] = minimized
        else:
            current_proof = row.get("final_minimizer")
            if current_proof != proof:
                expected_stale = True
                row["final_minimizer"] = proof
            if str(row.get("published_filename") or "") != relative:
                expected_stale = True
                row["published_filename"] = relative
            if str(row.get("sha256") or "").casefold() != digest:
                expected_stale = True
                row["sha256"] = digest
            fixed = row.get("final_fixed_point")
            if isinstance(fixed, dict) and str(fixed.get("sha256") or "").casefold() != digest:
                expected_stale = True
                fixed["sha256"] = digest

        if expected_stale:
            stale = True

    if check:
        current_manifest = _load_json(MANIFEST)
        current_provenance = _load_json(PROVENANCE)
        if current_manifest != manifest or current_provenance != provenance or stale:
            raise SystemExit("published providers are not NiakVIO minimizer fixed-point")
        print(
            "FIELD_PROVIDER_V3_MINIMIZER_PUBLICATION "
            f"providers={EXPECTED_PROVIDER_COUNT} changed=0 saved_bytes=0 "
            f"tool_sha={tool_sha[:16]} fixed_point=true terser_allowed=false"
        )
        return {"changed": 0, "saved_bytes": 0, "tool_sha256": tool_sha}

    for destination, data in outputs.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    _write_json(MANIFEST, manifest)
    _write_json(PROVENANCE, provenance)

    print(
        "FIELD_PROVIDER_V3_MINIMIZER_PUBLICATION "
        f"providers={EXPECTED_PROVIDER_COUNT} changed={changed} saved_bytes={saved_total} "
        f"transformed_lines={transformed_total} skipped_templates={skipped_templates} "
        f"tool_sha={tool_sha[:16]} terser_allowed=false"
    )
    return {
        "changed": changed,
        "saved_bytes": saved_total,
        "transformed_lines": transformed_total,
        "skipped_templates": skipped_templates,
        "tool_sha256": tool_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    finalize(check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
