#!/usr/bin/env python3
"""Import persistent sanitized Learning guidance into one current-Repair view.

The persistent brain-learning/proposals payload is a cross-run memory surface.
Before Fast Repair may use it, both the Node planner and the outer wave scheduler
must see the exact same current-byte-safe rows. This adapter:
- validates the non-authoritative persistent schema through brain_repair_runtime,
- removes providers whose materialized bytes drifted since sourceSha,
- removes exact failed advisor fingerprints from Repair negative memory,
- re-scopes the resulting payload to the current SHA only after those checks.

It never grants publication, mutation, or proof authority.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import brain_repair_runtime as brain  # noqa: E402
from import_external_brain_llm_guidance import (  # noqa: E402
    canon,
    filter_failed_guidance,
    source_drift,
)

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("persistent Learning guidance must be an object")
    return value


def normalize(
    value: dict[str, Any],
    *,
    current_sha: str,
    repo_root: Path,
    negative_memory: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current_sha = str(current_sha or "").strip().casefold()
    if not SHA40.fullmatch(current_sha):
        raise ValueError("invalid current SHA")
    for key in (
        "publicationAuthority",
        "directMutationAuthority",
        "proofAuthority",
        "rawMutationContentRetained",
    ):
        if value.get(key) is not False:
            raise ValueError(f"unsafe persistent Learning guidance flag: {key}")

    source_sha = str(value.get("sourceSha") or "").strip().casefold()
    if not SHA40.fullmatch(source_sha):
        raise ValueError("invalid persistent Learning sourceSha")

    neutral_paths: list[str] = []
    drifted_providers: set[str] = set()
    if source_sha != current_sha:
        neutral_paths, drifted_providers = source_drift(
            repo_root.resolve(),
            source_sha,
            current_sha,
        )

    rows = brain._validated_guidance_rows(
        value,
        current_sha=current_sha,
        require_exact_sha=False,
        guidance_kind="persistent-learning",
    )
    before_drift = len(rows)
    rows = [
        row for row in rows
        if canon(row.get("providerId")) not in drifted_providers
    ]
    dropped_drift = before_drift - len(rows)

    payload: dict[str, Any] = {
        "schemaVersion": 2,
        "sourceSha": current_sha,
        "sourcePersistentLearningSha": source_sha,
        "brainLlmSha": str(value.get("brainLlmSha") or "").strip().casefold(),
        "publicationAuthority": False,
        "directMutationAuthority": False,
        "proofAuthority": False,
        "rawMutationContentRetained": False,
        "persistentLearningPrior": True,
        "providerCount": len({canon(row.get("providerId")) for row in rows if canon(row.get("providerId"))}),
        "rows": rows,
    }
    failed_dropped = 0
    if isinstance(negative_memory, dict):
        payload, failed_dropped = filter_failed_guidance(payload, negative_memory)

    stats = {
        "sourceSha": source_sha,
        "currentSha": current_sha,
        "neutralDriftPathCount": len(neutral_paths),
        "driftedProviders": sorted(drifted_providers),
        "droppedProviderDriftRows": dropped_drift,
        "droppedFailedFingerprintRows": failed_dropped,
        "providerCount": int(payload.get("providerCount") or 0),
        "rowCount": len(payload.get("rows") or []),
    }
    return payload, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--negative-memory", type=Path)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()

    value = load(args.input)
    memory = load(args.negative_memory) if args.negative_memory and args.negative_memory.is_file() else {}
    payload, stats = normalize(
        value,
        current_sha=args.current_sha,
        repo_root=args.repo_root,
        negative_memory=memory,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "FIELD_PERSISTENT_BRAIN_LEARNING_GUIDANCE "
        f"providers={stats['providerCount']} rows={stats['rowCount']} "
        f"source={stats['sourceSha'][:12]} current={stats['currentSha'][:12]} "
        f"neutral_drift={stats['neutralDriftPathCount']} "
        f"provider_drift={len(stats['driftedProviders'])} "
        f"dropped_drift={stats['droppedProviderDriftRows']} "
        f"failed_fingerprints={stats['droppedFailedFingerprintRows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
