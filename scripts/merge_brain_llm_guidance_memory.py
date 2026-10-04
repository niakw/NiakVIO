#!/usr/bin/env python3
"""Merge concurrent sanitized Brain Learning guidance without losing provider priors.

The persistent brain-learning/proposals ref is memory, not code authority. A later
Learning run may cover a different provider cohort than the previous publisher.
Carry forward prior-only guidance only when:
- both payloads use the same Brain-LLM revision,
- the previous NiakVIO source is an ancestor of the current source,
- provider materialization bytes did not drift between those sources.

Current rows are preferred on exact duplicate keys. Previous rows may coexist for
one provider when their executable experiment fingerprints differ; negative-memory
filtering still suppresses experiments already proven bad.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from import_external_brain_llm_guidance import canon, source_drift  # noqa: E402

SHA40 = re.compile(r"^[0-9a-f]{40}$")
FP64 = re.compile(r"^[0-9a-f]{64}$")
ROW_FIELDS = {
    "providerId",
    "failureClass",
    "targetLayer",
    "strategy",
    "profile",
    "confidence",
    "priorOnly",
    "experiment",
    "experimentFingerprint",
}
AUTHORITY_FLAGS = (
    "publicationAuthority",
    "directMutationAuthority",
    "proofAuthority",
    "rawMutationContentRetained",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"guidance payload must be an object: {path}")
    return value


def validate(payload: dict[str, Any], *, label: str) -> None:
    if int(payload.get("schemaVersion") or 0) != 2:
        raise ValueError(f"{label}: unsupported guidance schema")
    for flag in AUTHORITY_FLAGS:
        if payload.get(flag) is not False:
            raise ValueError(f"{label}: unsafe authority flag {flag}")
    source = str(payload.get("sourceSha") or "").strip().casefold()
    brain = str(payload.get("brainLlmSha") or "").strip().casefold()
    if not SHA40.fullmatch(source):
        raise ValueError(f"{label}: invalid sourceSha")
    if not SHA40.fullmatch(brain):
        raise ValueError(f"{label}: invalid brainLlmSha")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError(f"{label}: guidance rows missing")
    for raw in rows:
        if not isinstance(raw, dict) or set(raw) != ROW_FIELDS:
            raise ValueError(f"{label}: unexpected guidance row shape")
        provider = canon(raw.get("providerId"))
        fp = str(raw.get("experimentFingerprint") or "").strip().casefold()
        if (
            not provider
            or str(raw.get("targetLayer") or "").strip().casefold() != "provider"
            or raw.get("priorOnly") is not True
            or not FP64.fullmatch(fp)
            or not isinstance(raw.get("experiment"), dict)
        ):
            raise ValueError(f"{label}: unsafe guidance row for {provider or '<missing>'}")


def row_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        canon(row.get("providerId")),
        str(row.get("profile") or "").strip().casefold(),
        str(row.get("experimentFingerprint") or "").strip().casefold(),
    )


def merge(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate(previous, label="previous")
    validate(current, label="current")

    previous_source = str(previous["sourceSha"]).casefold()
    current_source = str(current["sourceSha"]).casefold()
    previous_brain = str(previous["brainLlmSha"]).casefold()
    current_brain = str(current["brainLlmSha"]).casefold()

    drifted_providers: set[str] = set()
    neutral_paths: list[str] = []
    carry_enabled = previous_brain == current_brain
    if carry_enabled and previous_source != current_source:
        neutral_paths, drifted_providers = source_drift(
            repo_root,
            previous_source,
            current_source,
        )

    merged_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    # Newest run wins exact duplicates.
    for raw in current.get("rows") or []:
        row = copy.deepcopy(raw)
        key = row_key(row)
        if key in seen:
            continue
        seen.add(key)
        merged_rows.append(row)

    carried = 0
    dropped_drift = 0
    dropped_brain = 0
    if carry_enabled:
        for raw in previous.get("rows") or []:
            provider = canon(raw.get("providerId"))
            if provider in drifted_providers:
                dropped_drift += 1
                continue
            row = copy.deepcopy(raw)
            key = row_key(row)
            if key in seen:
                continue
            seen.add(key)
            merged_rows.append(row)
            carried += 1
            if len(merged_rows) >= 128:
                break
    else:
        dropped_brain = len(previous.get("rows") or [])

    output = copy.deepcopy(current)
    output["rows"] = merged_rows[:128]
    output["providerCount"] = len({
        canon(row.get("providerId"))
        for row in output["rows"]
        if canon(row.get("providerId"))
    })

    stats = {
        "currentRows": len(current.get("rows") or []),
        "previousRows": len(previous.get("rows") or []),
        "mergedRows": len(output["rows"]),
        "providerCount": output["providerCount"],
        "carriedRows": carried,
        "droppedProviderDriftRows": dropped_drift,
        "droppedBrainRevisionRows": dropped_brain,
        "neutralDriftPathCount": len(neutral_paths),
        "driftedProviders": sorted(drifted_providers),
        "sourceSha": current_source,
        "brainLlmSha": current_brain,
    }
    validate(output, label="merged")
    return output, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    previous = load(args.previous)
    current = load(args.current)
    output, stats = merge(previous, current, repo_root=args.repo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "FIELD_BRAIN_GUIDANCE_MEMORY_MERGE "
        + " ".join(
            [
                f"current={stats['currentRows']}",
                f"previous={stats['previousRows']}",
                f"carried={stats['carriedRows']}",
                f"merged={stats['mergedRows']}",
                f"providers={stats['providerCount']}",
                f"provider_drift={stats['droppedProviderDriftRows']}",
                f"brain_revision_drop={stats['droppedBrainRevisionRows']}",
                f"neutral_drift={stats['neutralDriftPathCount']}",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
