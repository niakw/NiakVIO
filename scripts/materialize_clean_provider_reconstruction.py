#!/usr/bin/env python3
"""Materialize validated clean ProviderBase candidates as review-only proposal artifacts.

This script never publishes or edits the repository's live ProviderBase tree.
It rebuilds deterministic NiakVIO-owned base bytes from the structured clean
model plus the proposed durable overrides, then writes a proposed provenance
file and candidate base files under the requested output directory.

Canonical promotion remains responsible for turning a candidate into a verified
v2 ProviderBase after fresh pipeline proof.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from provider_base_store import (
    CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
    CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE,
    base_relative,
    build_base_from_seed,
    build_clean_provider_seed,
    canonical_id,
    sha256,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def candidate_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        canonical_id(str(row.get("canonical_id") or row.get("upstream_id") or "")): row
        for row in registry.get("candidates") or []
        if isinstance(row, dict)
        and canonical_id(str(row.get("canonical_id") or row.get("upstream_id") or ""))
    }


def lab_is_strictly_playable(row: dict[str, Any]) -> bool:
    lab = row.get("finalLab") if isinstance(row.get("finalLab"), dict) else {}
    if row.get("resolved") is not True or lab.get("status") != "playable":
        return False
    if lab.get("allReturnedStreams") is not True:
        return False
    clients = lab.get("clients") if isinstance(lab.get("clients"), dict) else {}
    if not clients:
        return False
    return all(
        isinstance(value, dict)
        and value.get("hiddenFailure") is False
        and value.get("probeCoverageComplete") is True
        and int(value.get("playableProbes") or 0) > 0
        for value in clients.values()
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--queue-summary", type=Path, required=True)
    parser.add_argument("--overrides", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, default=ROOT / "PROVENANCE.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--proposed-provenance", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    registry = load_json(args.stage.resolve())
    queue = load_json(args.queue_summary.resolve())
    provenance = load_json(args.provenance.resolve())
    rows = provenance.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")
    candidates = candidate_map(registry)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    proposed = copy.deepcopy(provenance)
    proposed_rows = proposed.setdefault("providers", {})
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    now = datetime.now(timezone.utc).isoformat()

    for result in queue.get("results") or []:
        if not isinstance(result, dict):
            continue
        provider_id = canonical_id(str(result.get("provider") or ""))
        if not provider_id:
            continue
        if not lab_is_strictly_playable(result):
            rejected.append({"provider": provider_id, "reason": "strict_lab_proof_missing"})
            continue

        candidate = candidates.get(provider_id)
        if not isinstance(candidate, dict):
            rejected.append({"provider": provider_id, "reason": "candidate_missing"})
            continue
        if candidate.get("provider_base_reconstruction_required") is not True:
            continue
        origin = str(candidate.get("candidate_code_origin") or "")
        if origin not in {
            "new-niakvio-clean-seed",
            "pending-niakvio-clean-reconstruction-v2",
        }:
            rejected.append({"provider": provider_id, "reason": "candidate_not_clean_owned"})
            continue
        if candidate.get("upstream_code_executed") is not False:
            raise ValueError(f"{provider_id}: upstream JS execution flag is not false")
        if candidate.get("legacy_provider_js_executed_for_reconstruction") is not False:
            raise ValueError(f"{provider_id}: legacy JS execution flag is not false")

        metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
        model = candidate.get("clean_provider_model") if isinstance(candidate.get("clean_provider_model"), dict) else {}
        seed = build_clean_provider_seed(
            provider_id,
            metadata,
            known_site=str(candidate.get("observed_upstream_site") or "").strip() or None,
            provider_model=model,
        )
        base_data, stripped = build_base_from_seed(
            provider_id,
            seed,
            overrides_path=args.overrides.resolve(),
        )
        digest = sha256(base_data)
        relative = base_relative(provider_id, digest)
        target = output_dir / Path(relative).name
        target.write_bytes(base_data)

        current = proposed_rows.get(provider_id)
        if not isinstance(current, dict):
            raise ValueError(f"{provider_id}: missing provenance row")
        if str(current.get("base_source") or "") != CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE:
            current.setdefault("legacy_base_filename_before_clean_candidate", current.get("base_filename"))
            current.setdefault("legacy_base_sha256_before_clean_candidate", current.get("base_sha256"))
            current.setdefault("legacy_base_source_before_clean_candidate", current.get("base_source"))
        current["base_filename"] = relative
        current["base_sha256"] = digest
        current["base_source"] = CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE
        current["clean_reconstruction_candidate"] = True
        current["clean_reconstruction_verified"] = False
        current["clean_reconstruction_required"] = True
        current["clean_reconstruction_authoring_version"] = CLEAN_RECONSTRUCTION_AUTHORING_VERSION
        current["clean_reconstruction_candidate_at"] = now
        current["clean_reconstruction_candidate_origin"] = origin
        current["clean_reconstruction_candidate_lab"] = "tv-desktop-mobile-complete-playable"
        current["legacy_provider_js_executed_for_reconstruction"] = False
        current["upstream_code_role"] = "knowledge-only"
        current["upstream_code_executed"] = False
        current["base_migration_stripped_generated_core"] = bool(stripped)
        accepted.append({
            "provider": provider_id,
            "base_filename": relative,
            "base_sha256": digest,
            "source": CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE,
        })

    store = proposed.setdefault("provider_base_store", {})
    if isinstance(store, dict):
        store.update({
            "schema_version": max(5, int(store.get("schema_version") or 0)),
            "clean_candidate_count_this_proposal": len(accepted),
            "clean_candidate_policy": "review-only-until-canonical-pipeline-proof",
            "clean_candidate_generated_at": now,
            "upstream_code_role": "knowledge-only",
            "upstream_code_executed": False,
        })

    write_json(args.proposed_provenance.resolve(), proposed)
    write_json(args.summary.resolve(), {
        "schemaVersion": 1,
        "generatedAt": now,
        "candidateCount": len(accepted),
        "providers": [row["provider"] for row in accepted],
        "candidates": accepted,
        "rejected": rejected,
        "policy": {
            "publicationAllowed": False,
            "productionWritesAllowed": False,
            "pullRequestOnly": True,
            "requiresHumanMerge": True,
            "canonicalPipelineProofRequired": True,
            "legacyOrUpstreamExecutableSeedAllowed": False,
        },
    })
    print(
        "FIELD_CLEAN_PROVIDER_PROPOSAL "
        f"candidates={len(accepted)} rejected={len(rejected)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
