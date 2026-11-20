#!/usr/bin/env python3
"""Persist only bounded, non-authoritative Brain native candidate experiments."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = re.compile(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")
PROVIDER = re.compile(r"[a-z][a-z0-9-]{1,79}")
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
ALLOWED_EXPERIMENT = "native-blocking-player-origin-priority"
ALLOWED_STRATEGY = "prioritize_native_blocking_player_origin_from_observed_outcome"


def load(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("ledger must be an object")
    return value


def canonical_fingerprint(row: dict) -> str:
    basis = {
        key: row[key]
        for key in (
            "experimentType", "providerId", "fixture", "requestType",
            "sourceNiakvioSha", "sourceRunId", "providerArtifactSha256",
            "officialClientSha", "runtimeScope", "preferredHosts",
            "deprioritizedHosts", "evidencePattern",
        )
    }
    return hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def sanitize(route: dict, brain_sha: str) -> dict | None:
    if not isinstance(route, dict):
        return None
    exp = route.get("candidateExperiment")
    if not isinstance(exp, dict):
        return None
    if (
        route.get("mode") != "deterministic_advisor"
        or route.get("targetLayer") != "core"
        or route.get("strategy") != ALLOWED_STRATEGY
        or exp.get("experimentType") != ALLOWED_EXPERIMENT
        or exp.get("runtimeScope") != "native-blocking-fetch"
        or exp.get("candidateOnly") is not True
        or exp.get("generatedByBrain") is not True
        or any(exp.get(key) is not False for key in (
            "proofAuthority", "publicationAuthority",
            "nativePlaybackAuthority", "providerMutationAuthority",
        ))
    ):
        raise ValueError("candidate experiment authority/route mismatch")
    provider = str(exp.get("providerId") or "").strip().lower()
    fixture = str(exp.get("fixture") or "").strip().lower()
    request_type = str(exp.get("requestType") or "").strip().lower()
    source_sha = str(exp.get("sourceNiakvioSha") or "").strip().lower()
    run_id = str(exp.get("sourceRunId") or "").strip()
    digest = str(exp.get("providerArtifactSha256") or "").strip().lower()
    client_sha = str(exp.get("officialClientSha") or "").strip().lower()
    preferred = [str(v or "").strip().lower() for v in (exp.get("preferredHosts") or [])]
    deprioritized = [str(v or "").strip().lower() for v in (exp.get("deprioritizedHosts") or [])]
    if (
        not PROVIDER.fullmatch(provider)
        or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", fixture)
        or request_type not in {"movie", "tv", "anime"}
        or not SHA40.fullmatch(source_sha)
        or not run_id.isdigit() or not (8 <= len(run_id) <= 20)
        or not SHA64.fullmatch(digest)
        or (client_sha and not SHA40.fullmatch(client_sha))
        or not SHA40.fullmatch(brain_sha)
        or not preferred or len(preferred) > 4 or len(deprioritized) > 4
        or any(not HOST.fullmatch(v) for v in preferred + deprioritized)
        or set(preferred) & set(deprioritized)
        or exp.get("evidencePattern") != "player-5xx-then-alternate-2xx-then-hls-2xx-near-budget-zero"
    ):
        raise ValueError("candidate experiment shape mismatch")
    row = {
        "schemaVersion": 1,
        "experimentType": ALLOWED_EXPERIMENT,
        "providerId": provider,
        "fixture": fixture,
        "requestType": request_type,
        "sourceNiakvioSha": source_sha,
        "sourceRunId": run_id,
        "providerArtifactSha256": digest,
        "officialClientSha": client_sha,
        "runtimeScope": "native-blocking-fetch",
        "preferredHosts": list(dict.fromkeys(preferred)),
        "deprioritizedHosts": list(dict.fromkeys(deprioritized)),
        "evidencePattern": exp["evidencePattern"],
        "candidateOnly": True,
        "generatedByBrain": True,
        "brainSha": brain_sha,
        "proofAuthority": False,
        "publicationAuthority": False,
        "nativePlaybackAuthority": False,
        "providerMutationAuthority": False,
    }
    fingerprint = canonical_fingerprint(row)
    if str(exp.get("experimentFingerprint") or "").lower() != fingerprint:
        raise ValueError("Brain experiment fingerprint mismatch")
    row["experimentFingerprint"] = fingerprint
    return row


def persist(route_path: Path, ledger_path: Path, brain_sha: str) -> dict:
    route_doc = load(route_path)
    incoming = [
        row for route in (route_doc.get("routes") or [])
        if (row := sanitize(route, brain_sha)) is not None
    ]
    ledger = load(ledger_path)
    rows = [
        row for row in (ledger.get("rows") or [])
        if isinstance(row, dict) and SHA64.fullmatch(
            str(row.get("experimentFingerprint") or "").lower())
    ]
    by_id = {str(row["experimentFingerprint"]): row for row in rows}
    verdict_keys = (
        "candidateAttempts", "lastCandidateRunId", "lastCandidateSourceSha",
        "lastCandidateJsSha256", "lastCandidateVerdict",
        "lastCandidateExecutionObserved", "lastCandidateExtractionNonEmpty",
        "lastCandidateTerminalReaderHealthy", "lastCandidateDecodedVideoObserved",
        "lastCandidateFrAudioObserved", "lastCandidateValidatedRepair",
    )
    for row in incoming:
        fingerprint = row["experimentFingerprint"]
        previous = by_id.get(fingerprint) or {}
        for key in verdict_keys:
            if key in previous:
                row[key] = previous[key]
        by_id[fingerprint] = row
    bounded = sorted(
        by_id.values(),
        key=lambda row: (int(row.get("sourceRunId") or 0),
                         str(row.get("experimentFingerprint") or "")),
    )[-64:]
    out = {
        "schemaVersion": 1,
        "authority": "candidate-only",
        "publicationAuthority": False,
        "providerMutationAuthority": False,
        "rows": bounded,
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--brain-sha", required=True)
    args = parser.parse_args()
    brain_sha = str(args.brain_sha).strip().lower()
    if not SHA40.fullmatch(brain_sha):
        raise ValueError("invalid Brain SHA")
    out = persist(args.route.resolve(), args.ledger.resolve(), brain_sha)
    print(
        "FIELD_BRAIN_NATIVE_CANDIDATE_EXPERIMENTS "
        f"rows={len(out['rows'])} authority=candidate-only publication=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
