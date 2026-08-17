#!/usr/bin/env python3
"""Migrate a legacy global audit quarantine to the narrow scoped model.

This utility is deliberately evidence-bound. A provider can be restored only if:
- its current published bundle is a legacy global audit quarantine;
- the historical audit contains at least one playable, identity-verified scope;
- the same historical audit contains a conclusive playable identity contradiction;
- a non-baseline candidate exists in both the historical and current validated
  staging artifacts with exactly the same SHA-256.

The candidate is therefore not rediscovered or repaired here. We only replace an
obsolete global quarantine with the current scoped quarantine wrapper around the
exact code that already earned historical strict proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
LEGACY_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rows(value: Any, *keys: str) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        for key in keys:
            selected = value.get(key)
            if isinstance(selected, list):
                return [row for row in selected if isinstance(row, dict)]
    return []


def candidate_for(stage: Path, provider_id: str) -> dict[str, Any]:
    registry = load(stage / "candidates.json")
    matches = []
    for row in rows(registry, "candidates", "providers"):
        canonical = str(row.get("canonical_id") or "").strip().casefold()
        source = str(row.get("source") or "").strip().casefold()
        if canonical != provider_id or source == "published-baseline":
            continue
        local_path = str(row.get("local_path") or "").strip()
        path = stage / local_path
        if not local_path or not path.is_file():
            continue
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        if metadata.get("enabled") is False:
            continue
        matches.append((int(row.get("source_priority") or 9999), row, path))
    if not matches:
        raise SystemExit(f"{provider_id}: no validated non-baseline candidate in {stage}")
    matches.sort(key=lambda item: (item[0], str(item[1].get("key") or "")))
    _priority, selected, path = matches[0]
    selected = dict(selected)
    selected["_resolved_path"] = str(path)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-stage", required=True)
    parser.add_argument("--evidence-stage", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--evidence-run-id", type=int, default=0)
    parser.add_argument("--current-run-id", type=int, default=0)
    args = parser.parse_args()

    # Reuse the production quarantine implementation so migration and future
    # publication have one definition of a scoped identity quarantine.
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import quarantine_catalogue_audit_failures as quarantine  # type: ignore

    current_stage = Path(args.current_stage).resolve()
    evidence_stage = Path(args.evidence_stage).resolve()
    audit = load(Path(args.audit).resolve())
    manifest = load(MANIFEST)
    provenance = load(PROVENANCE)
    if not isinstance(manifest, dict) or not isinstance(provenance, dict):
        raise SystemExit("manifest/provenance must be JSON objects")

    manifest_rows = {
        str(row.get("id") or "").strip().casefold(): row
        for row in rows(manifest, "scrapers")
        if str(row.get("id") or "").strip()
    }
    provenance_rows = provenance.setdefault("providers", {})
    if not isinstance(provenance_rows, dict):
        raise SystemExit("PROVENANCE.providers must be an object")

    audit_rows = rows(audit, "rows")
    migrated = []

    for requested in args.provider:
        provider_id = str(requested).strip().casefold()
        entry = manifest_rows.get(provider_id)
        if not isinstance(entry, dict):
            raise SystemExit(f"{provider_id}: missing from manifest")

        old_relative = str(entry.get("filename") or "").strip()
        old_path = ROOT / old_relative
        if not old_path.is_file():
            raise SystemExit(f"{provider_id}: missing published bundle {old_relative}")
        old_source = old_path.read_text(encoding="utf-8")
        if LEGACY_MARKER not in old_source or quarantine.SCOPED_MARKER in old_source:
            raise SystemExit(f"{provider_id}: current bundle is not a legacy global audit quarantine")

        evidence_rows = [
            row for row in audit_rows
            if str(row.get("provider_id") or "").strip().casefold() == provider_id
        ]
        positive = [
            row for row in evidence_rows
            if int(row.get("playable_stream_count") or 0) > 0
            and int(row.get("identity_verified_count") or 0) > 0
            and int(row.get("identity_contradiction_count") or 0) == 0
        ]
        contradictions = quarantine.conclusive_rows({"rows": evidence_rows}).get(provider_id, [])
        scopes = quarantine.derive_scopes(contradictions)
        if not positive:
            raise SystemExit(f"{provider_id}: historical audit has no playable identity-verified scope")
        if not contradictions or not scopes:
            raise SystemExit(f"{provider_id}: historical audit has no safely scoped contradiction")

        historical = candidate_for(evidence_stage, provider_id)
        current = candidate_for(current_stage, provider_id)
        historical_sha = str(historical.get("sha256") or "")
        current_sha = str(current.get("sha256") or "")
        if not historical_sha or historical_sha != current_sha:
            raise SystemExit(
                f"{provider_id}: candidate changed since strict proof: historical={historical_sha} current={current_sha}"
            )
        current_path = Path(str(current["_resolved_path"]))
        source_bytes = current_path.read_bytes()
        actual_sha = hashlib.sha256(source_bytes).hexdigest()
        if actual_sha != current_sha:
            raise SystemExit(f"{provider_id}: current candidate SHA mismatch")

        source = source_bytes.decode("utf-8")
        payload_text = quarantine.scoped_quarantine_source(source, provider_id, scopes)
        payload = payload_text.encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        new_relative = f"providers/{quarantine.safe_id(provider_id)}--nuvio-audit-quarantine--{digest[:16]}.js"
        new_path = ROOT / new_relative
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_bytes(payload)

        metadata = current.get("metadata") if isinstance(current.get("metadata"), dict) else {}
        # Keep curated release identity/version while restoring runtime metadata
        # from the exact validated upstream candidate.
        for key in (
            "name", "description", "author", "supportedTypes", "hasSettings",
            "formats", "logo", "contentLanguage", "limited",
            "disabledPlatforms", "supportsExternalPlayer",
        ):
            if key in metadata:
                entry[key] = metadata[key]
        entry["filename"] = new_relative
        remaining = quarantine._remaining_types(entry, scopes)
        if "supportedTypes" in entry:
            entry["supportedTypes"] = remaining
        entry["enabled"] = bool(remaining) if "supportedTypes" in entry else True
        entry["version"] = quarantine.bump_patch(entry.get("version"))

        prov = provenance_rows.setdefault(provider_id, {})
        if not isinstance(prov, dict):
            prov = {}
            provenance_rows[provider_id] = prov
        prov.update({
            "source": current.get("source") or prov.get("source") or "validated-stage",
            "selected_source": current.get("source") or prov.get("selected_source") or "validated-stage",
            "published_filename": new_relative,
            "sha256": digest,
            "patched_sha256": digest,
            "catalogue_audit_quarantine_scopes": scopes,
            "activation_mode": "catalogue_audit_scoped_quarantine",
            "legacy_quarantine_migration": {
                "historical_run_id": int(args.evidence_run_id or 0),
                "current_stage_run_id": int(args.current_run_id or 0),
                "validated_candidate_sha256": current_sha,
                "positive_fixtures": sorted({str(row.get("fixture") or "") for row in positive}),
                "contradictory_fixtures": sorted({str(row.get("fixture") or "") for row in contradictions}),
                "scopes": scopes,
            },
        })
        migrated.append({
            "provider": provider_id,
            "candidate_sha256": current_sha,
            "published_sha256": digest,
            "filename": new_relative,
            "scopes": scopes,
        })

    write(MANIFEST, manifest)
    write(PROVENANCE, provenance)
    print(json.dumps({"migrated": migrated}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
