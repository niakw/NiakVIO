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
    version_is_strictly_above_floor,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"
MINIMIZER = ROOT / "scripts" / "provider_v3_minimizer.py"
SCHEMA_VERSION = 2


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
    """Return only executable rows; visible disabled rows are publication metadata."""
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    ids = [str(row.get("id") or "").strip().casefold() for row in rows]
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("current manifest provider ids must be unique and non-empty")

    active: list[dict[str, Any]] = []
    for row in rows:
        relative = str(row.get("filename") or "").strip()
        if row.get("enabled") is False:
            if relative.startswith("providers/"):
                raise ValueError(
                    f"disabled provider remains in active publication folder: {row.get('id')}"
                )
            continue
        if not relative.startswith("providers/"):
            raise ValueError(
                f"active provider is outside active publication folder: {row.get('id')}={relative}"
            )
        active.append(row)
    if not active:
        raise ValueError("current active provider scope is empty")
    return active


def _safe_provider_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if PROVIDERS.resolve() not in path.parents or not path.is_file():
        raise ValueError(f"missing or unsafe current provider asset: {relative}")
    return path


def _proof_metrics(
    current: object,
    *,
    tool_sha: str,
    digest: str,
    result: Any,
    bytes_changed: bool,
) -> tuple[int, int, str]:
    """Keep publication-transform metrics stable across fixed-point checks.

    On the transformation pass the metrics describe bytes actually removed. A
    second pass necessarily observes zero removable bytes, but that must not
    rewrite the historical proof for the exact same minimized asset/tool.
    """
    if bytes_changed:
        return (
            int(result.saved_bytes),
            int(result.transformed_lines),
            str(result.skipped_reason or ""),
        )
    if isinstance(current, dict):
        same_asset = (
            int(current.get("schema_version") or 0) == SCHEMA_VERSION
            and str(current.get("tool_sha256") or "").casefold() == tool_sha.casefold()
            and str(current.get("sha256") or "").casefold() == digest.casefold()
            and current.get("production_enabled") is True
            and current.get("terser_allowed") is False
        )
        if same_asset:
            return (
                int(current.get("saved_bytes") or 0),
                int(current.get("transformed_lines") or 0),
                str(current.get("skipped_reason") or ""),
            )
    return (
        int(result.saved_bytes),
        int(result.transformed_lines),
        str(result.skipped_reason or ""),
    )


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
    already_versioned = 0
    stale = False
    outputs: dict[Path, bytes] = {}
    active_rows = _provider_rows(manifest)
    provider_count = len(active_rows)

    for entry in active_rows:
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

        current_proof = row.get("final_minimizer")
        proof_saved, proof_lines, proof_skipped = _proof_metrics(
            current_proof,
            tool_sha=tool_sha,
            digest=digest,
            result=result,
            bytes_changed=bytes_changed,
        )
        proof = {
            "schema_version": SCHEMA_VERSION,
            "tool": "scripts/provider_v3_minimizer.py",
            "tool_sha256": tool_sha,
            "production_enabled": True,
            "terser_allowed": False,
            "saved_bytes": proof_saved,
            "transformed_lines": proof_lines,
            "skipped_reason": proof_skipped,
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
            current_version = str(entry.get("version") or "1.0.0")
            floor = floors.get(provider_id)
            # Reapply may already have changed the exact same provider in this
            # accepted transaction. If its version is already strictly above the
            # published floor, minimization changes the same generation and must
            # not invent a second cache bump.
            if floor and version_is_strictly_above_floor(current_version, floor):
                already_versioned += 1
            else:
                entry["version"] = bump_provider_version(current_version, floor)
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
            f"providers={provider_count} changed=0 saved_bytes=0 "
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
        f"providers={provider_count} changed={changed} saved_bytes={saved_total} "
        f"transformed_lines={transformed_total} skipped_templates={skipped_templates} "
        f"already_versioned={already_versioned} tool_sha={tool_sha[:16]} terser_allowed=false"
    )
    return {
        "changed": changed,
        "saved_bytes": saved_total,
        "transformed_lines": transformed_total,
        "skipped_templates": skipped_templates,
        "already_versioned": already_versioned,
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
