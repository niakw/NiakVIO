#!/usr/bin/env python3
"""Convert NiakVIO-Brain-LLM output into a bounded production Brain advisor hint.

The LLM is never proof or publication authority. Raw diagnoses, evidence,
mutations and tests are intentionally discarded here. Only an allowlisted
provider-local strategy/profile hint can cross into the deterministic planner.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

STRATEGY_TO_PROFILE = {
    "provider-owned-origin-header-and-domain-replay": "provider_origin_failover_v1",
    "search-detail-player-terminal-traversal": "proven_route_terminal_traversal_v1",
    "terminal-media-extractor-with-playback-validation": "chain_terminal_extractor_v1",
    "same-provider-candidate-program-replay": "retained_candidate_replay_v1",
    "proven-request-program-and-terminal-extraction": "player_media_extractor_v1",
    "discover-api-from-current-page-and-bundles": "search_contract_inference_v1",
}
ALLOWED_PROFILES = frozenset(STRATEGY_TO_PROFILE.values())
PROVIDER_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,159}$")


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def safe_sha(value: object) -> str:
    raw = str(value or "").strip().casefold()
    return raw if re.fullmatch(r"[0-9a-f]{40}", raw) else ""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def sanitize(
    rows: list[dict[str, Any]],
    *,
    source_sha: str,
    brain_llm_sha: str,
    min_confidence: float,
) -> dict[str, Any]:
    source_sha = safe_sha(source_sha)
    brain_llm_sha = safe_sha(brain_llm_sha)
    if not source_sha or not brain_llm_sha:
        raise ValueError("source and Brain-LLM SHAs must be exact 40-hex commits")

    guidance: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if row.get("ok") is not True:
            continue
        provider = canon(row.get("provider"))
        if not provider or not PROVIDER_ID.fullmatch(provider):
            continue
        proposal = row.get("proposal")
        if not isinstance(proposal, dict):
            continue
        if canon(proposal.get("provider_id")) != provider:
            continue
        strategy = canon(proposal.get("strategy"))
        target_layer = canon(proposal.get("target_layer"))
        try:
            confidence = max(0.0, min(1.0, float(proposal.get("confidence") or 0.0)))
        except (TypeError, ValueError):
            confidence = 0.0
        abstain = proposal.get("abstain") is True
        profile = STRATEGY_TO_PROFILE.get(strategy, "")
        if (
            abstain
            or target_layer != "provider"
            or confidence < min_confidence
            or profile not in ALLOWED_PROFILES
        ):
            continue
        failure = canon(row.get("failure_class"))
        key = (provider, profile)
        if key in seen:
            continue
        seen.add(key)
        guidance.append({
            "providerId": provider,
            "failureClass": failure,
            "targetLayer": "provider",
            "strategy": strategy,
            "profile": profile,
            "confidence": round(confidence, 6),
            "priorOnly": True,
        })

    return {
        "schemaVersion": 1,
        "sourceSha": source_sha,
        "brainLlmSha": brain_llm_sha,
        "publicationAuthority": False,
        "directMutationAuthority": False,
        "proofAuthority": False,
        "rawMutationContentRetained": False,
        "minConfidence": min_confidence,
        "providerCount": len({row["providerId"] for row in guidance}),
        "rows": guidance,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--brain-llm-sha", required=True)
    ap.add_argument("--min-confidence", type=float, default=0.80)
    args = ap.parse_args()
    if not 0.0 <= args.min_confidence <= 1.0:
        raise SystemExit("--min-confidence must be between 0 and 1")
    report = sanitize(
        load_jsonl(args.input),
        source_sha=args.source_sha,
        brain_llm_sha=args.brain_llm_sha,
        min_confidence=args.min_confidence,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_LLM_GUIDANCE "
        f"providers={report['providerCount']} rows={len(report['rows'])} "
        f"brain_llm_sha={report['brainLlmSha'][:12]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
