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


def safe_repair_family(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    key = str(value.get("key") or "").strip().casefold()
    if not FP64.fullmatch(key):
        return {}
    allowed = {
        "version": max(1, int(value.get("version") or 1)),
        "key": key,
        "failure": canon(value.get("failure"))[:96],
        "status": canon(value.get("status"))[:64],
        "archetype": str(value.get("archetype") or "")[:240],
        "mediaTypes": [canon(x)[:48] for x in (value.get("mediaTypes") or [])[:8] if canon(x)],
        "signals": [canon(x)[:96] for x in (value.get("signals") or [])[:24] if canon(x)],
        "stages": [canon(x)[:96] for x in (value.get("stages") or [])[:16] if canon(x)],
        "mutationSurfaces": [canon(x)[:64] for x in (value.get("mutationSurfaces") or [])[:8] if canon(x)],
    }
    return allowed


def safe_coverage_summary(value: Any) -> dict[str, Any]:
    """Retain only bounded causal completeness metrics from a sandbox result."""
    if not isinstance(value, dict):
        return {}
    coverage = value.get("variantCoverage")
    if not isinstance(coverage, dict):
        coverage = {}

    def non_negative_int(raw: Any, limit: int = 100000) -> int:
        try:
            return max(0, min(int(raw or 0), limit))
        except (TypeError, ValueError):
            return 0

    def heights(raw: Any) -> list[int]:
        out: set[int] = set()
        if isinstance(raw, list):
            for value in raw[:24]:
                try:
                    height = int(value or 0)
                except (TypeError, ValueError):
                    continue
                if 144 <= height <= 4320:
                    out.add(height)
        return sorted(out)

    states = sorted({
        canon(item)[:80]
        for item in (coverage.get("fanoutStates") or [])[:16]
        if canon(item)
    })
    result = {
        "streamsReturned": non_negative_int(value.get("streamsReturned")),
        "streamsPlayable": non_negative_int(value.get("streamsPlayable")),
        "identityContradictions": non_negative_int(value.get("identityContradictions"), 1000),
        "qualityHeights": heights(coverage.get("qualityHeights")),
        "announcedQualityHeights": heights(coverage.get("announcedQualityHeights")),
        "maxPlayableHeight": non_negative_int(coverage.get("maxPlayableHeight"), 4320),
        "announcedPlayerCandidates": non_negative_int(coverage.get("announcedPlayerCandidates"), 10000),
        "announcedVariantCandidates": non_negative_int(coverage.get("announcedVariantCandidates"), 10000),
        "exploredPlayerRequests": non_negative_int(coverage.get("exploredPlayerRequests"), 10000),
        "reachableHostCount": min(256, len([
            item for item in (coverage.get("reachableHosts") or [])[:256]
            if str(item or "").strip()
        ])),
        "fanoutStates": states,
    }
    return result


def safe_coverage_delta(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, int]:
    keys = (
        "streamsReturned",
        "streamsPlayable",
        "identityContradictions",
        "maxPlayableHeight",
        "announcedPlayerCandidates",
        "announcedVariantCandidates",
        "exploredPlayerRequests",
        "reachableHostCount",
    )
    out = {
        key: int(candidate.get(key) or 0) - int(baseline.get(key) or 0)
        for key in keys
    }
    out["qualityHeightCount"] = (
        len(candidate.get("qualityHeights") or [])
        - len(baseline.get("qualityHeights") or [])
    )
    return out


def safe_mutation_summary(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    for raw in value[:8]:
        if not isinstance(raw, dict):
            continue
        row = {
            "scope": str(raw.get("scope") or "")[:40],
            "operation": str(raw.get("operation") or "")[:40],
        }
        family = str(raw.get("family") or "")[:80]
        if family:
            row["family"] = family
        path = str(raw.get("path") or "")[:160]
        if path:
            row["path"] = path
        if row["scope"]:
            out.append(row)
    return out


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
        if result.get("executionObserved") is False:
            # Portfolio reservations that were skipped after an earlier winner,
            # or candidates that never reached executable provider bytes, are
            # not sandbox outcomes and must not become negative memory.
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
        summary = safe_mutation_summary(result.get("mutationSummary"))
        if summary:
            row["lastMutationSummary"] = summary
        repair_family = safe_repair_family(result.get("repairFamily"))
        if repair_family:
            row["repairFamily"] = repair_family
        mechanism_family = canon(result.get("mechanismFamily"))[:160]
        if mechanism_family:
            row["mechanismFamily"] = mechanism_family

        baseline_coverage = safe_coverage_summary(result.get("baseline"))
        candidate_coverage = safe_coverage_summary(result.get("candidate"))
        if baseline_coverage:
            row["lastBaselineCoverage"] = baseline_coverage
        if candidate_coverage:
            row["lastCandidateCoverage"] = candidate_coverage
        if baseline_coverage and candidate_coverage:
            row["lastCoverageDelta"] = safe_coverage_delta(
                baseline_coverage,
                candidate_coverage,
            )

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

    validated: dict[tuple[str, str], dict[str, Any]] = {}
    for row in entries:
        if int(row.get("successes") or 0) <= 0:
            continue
        family = safe_repair_family(row.get("repairFamily"))
        mechanism = canon(row.get("mechanismFamily"))[:160]
        if not family or not mechanism:
            continue
        key = (family["key"], mechanism)
        aggregate = validated.get(key)
        if aggregate is None:
            aggregate = {
                "repairFamily": family,
                "mechanismFamily": mechanism,
                "successCount": 0,
                "failureCount": 0,
                "providers": [],
                "source": "sandbox-validated-force-memory",
                "proofAuthority": False,
                "autoApply": False,
            }
            validated[key] = aggregate
        aggregate["successCount"] += int(row.get("successes") or 0)
        aggregate["failureCount"] += int(row.get("failures") or 0)
        provider = canon(row.get("providerId"))
        if provider and provider not in aggregate["providers"]:
            aggregate["providers"].append(provider)

    validated_families = sorted(
        validated.values(),
        key=lambda row: (
            -int(row.get("successCount") or 0),
            int(row.get("failureCount") or 0),
            str((row.get("repairFamily") or {}).get("archetype") or ""),
            str(row.get("mechanismFamily") or ""),
        ),
    )[:1000]

    return {
        "schemaVersion": 2,
        "entries": entries,
        "validatedFamilies": validated_families,
        "validatedFamilyCount": len(validated_families),
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
