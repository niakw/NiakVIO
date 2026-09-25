#!/usr/bin/env python3
"""Persist exact Brain-LLM Force candidate outcomes.

Memory identity is provider + mutation fingerprint + exact mutation-context
fingerprint. This prevents replaying the same candidate on unchanged provider
bytes while allowing a structurally identical idea to be reconsidered after the
provider's actual mutation surface changes.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

FP64 = re.compile(r"^[0-9a-f]{64}$")


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def merge(memory: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    rows = [
        dict(row)
        for row in memory.get("entries") or []
        if isinstance(row, dict)
    ]
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            canon(row.get("providerId")),
            str(row.get("mutationFingerprint") or "").strip().casefold(),
            str(row.get("mutationContextFingerprint") or "").strip().casefold(),
        )
        if key[0] and FP64.fullmatch(key[1]) and FP64.fullmatch(key[2]):
            by_key[key] = row

    current_sha = str(evaluation.get("currentSha") or "").strip().casefold()
    source_sha = str(evaluation.get("sourceNiakvioSha") or "").strip().casefold()
    brain_sha = str(evaluation.get("sourceBrainLlmSha") or "").strip().casefold()

    for result in evaluation.get("rows") or []:
        if not isinstance(result, dict):
            continue
        provider = canon(result.get("provider"))
        mutation_fp = str(result.get("mutationFingerprint") or "").strip().casefold()
        context_fp = str(result.get("mutationContextFingerprint") or "").strip().casefold()
        if not provider or not FP64.fullmatch(mutation_fp) or not FP64.fullmatch(context_fp):
            continue
        key = (provider, mutation_fp, context_fp)
        row = by_key.get(key)
        if row is None:
            row = {
                "providerId": provider,
                "mutationFingerprint": mutation_fp,
                "mutationContextFingerprint": context_fp,
                "failures": 0,
                "consecutiveFailures": 0,
                "successes": 0,
            }
            by_key[key] = row

        accepted = result.get("accepted") is True
        if accepted:
            row["successes"] = int(row.get("successes") or 0) + 1
            row["consecutiveFailures"] = 0
            row["lastOutcome"] = "accepted"
        else:
            row["failures"] = int(row.get("failures") or 0) + 1
            row["consecutiveFailures"] = int(row.get("consecutiveFailures") or 0) + 1
            row["lastOutcome"] = "rejected"
        row["lastReason"] = str(result.get("reason") or "")[:240]
        row["lastCurrentSha"] = current_sha
        row["sourceNiakvioSha"] = source_sha
        row["sourceBrainLlmSha"] = brain_sha

    entries = sorted(
        by_key.values(),
        key=lambda row: (
            -int(row.get("consecutiveFailures") or 0),
            -int(row.get("failures") or 0),
            -int(row.get("successes") or 0),
            str(row.get("providerId") or ""),
            str(row.get("mutationFingerprint") or ""),
            str(row.get("mutationContextFingerprint") or ""),
        ),
    )[:2000]

    return {
        "schemaVersion": 1,
        "entries": entries,
        "publicationAuthority": False,
        "proofAuthority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    args = parser.parse_args()

    memory = load(args.memory, {"schemaVersion": 1, "entries": []})
    evaluation = load(args.evaluation, {})
    if not isinstance(memory, dict) or not isinstance(evaluation, dict):
        raise SystemExit("Force memory/evaluation must be JSON objects")

    output = merge(memory, evaluation)
    args.memory.parent.mkdir(parents=True, exist_ok=True)
    args.memory.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "FIELD_BRAIN_LLM_FORCE_MEMORY "
        f"entries={len(output['entries'])} "
        f"observed={len([r for r in evaluation.get('rows') or [] if isinstance(r,dict)])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
