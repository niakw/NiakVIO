#!/usr/bin/env python3
"""Bounded sanitized Retest learning ledger; no source URLs or proof authority."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

REASONS = {
    "insufficient_identity_metadata", "duration_incomplete_hls",
    "duration_unavailable", "fixture_duration_mismatch",
    "provider_tmdb_route_mismatch", "wrong_season_episode", "wrong_episode",
    "forbidden_title_alias", "media_filename_title_mismatch",
    "strong_title_mismatch", "expected_title_alias", "season_episode_match",
    "episode_match", "provider_tmdb_direct_route",
}
ID = re.compile(r"[a-z0-9][a-z0-9-]{0,90}")
SHA = re.compile(r"[0-9a-f]{64}")
RUN = re.compile(r"\d+-retest")
MAX_PER_PROVIDER = 10
MAX_PROVIDERS = 140


def sanitize(payload: dict[str, Any], row: dict[str, Any]) -> dict[str, Any] | None:
    if (
        payload.get("proofAuthority") is not False
        or payload.get("publicationAuthority") is not False
        or row.get("proofAuthority") is not False
        or row.get("publicationAuthority") is not False
        or row.get("nativePlaybackAuthority") is not False
    ):
        return None
    provider = str(row.get("provider") or "")
    digest = str(row.get("providerArtifactSha256") or "")
    run = str(payload.get("sourceCensusRunId") or "")
    source_sha = str(payload.get("sourceNiakvioSha") or "")
    if (
        not ID.fullmatch(provider) or not SHA.fullmatch(digest)
        or not RUN.fullmatch(run) or not re.fullmatch(r"[0-9a-f]{40}", source_sha)
    ):
        return None
    lane = str(row.get("lane") or "")
    if lane not in {"movie", "tv", "anime"}:
        return None
    fixture = row.get("fixture") or {}
    if not isinstance(fixture, dict):
        fixture = {}
    def count(x: Any) -> int:
        return min(10000, max(0, x)) if type(x) is int else 0
    def code(x: Any) -> str:
        s = str(x or "")
        return s if re.fullmatch(r"[a-z_]{0,64}", s) else ""
    return {
        "provider": provider,
        "providerArtifactSha256": digest,
        "sourceCensusRunId": run,
        "sourceNiakvioSha": source_sha,
        "lane": lane,
        "status": code(row.get("status")),
        "debugStage": code(row.get("debugStage")),
        "fixture": {
            "mediaType": lane,
            "tmdbId": str(fixture.get("tmdbId") or "")[:12] if str(fixture.get("tmdbId") or "").isdigit() else "",
            "season": count(fixture.get("season")),
            "episode": count(fixture.get("episode")),
        },
        "raw": count(row.get("raw")),
        "playable": count(row.get("playable")),
        "verified": count(row.get("verified")),
        "identityReasons": sorted({
            x for x in row.get("identityReasons") or []
            if isinstance(x, str) and x in REASONS
        })[:12],
        "proofAuthority": False,
        "publicationAuthority": False,
        "nativePlaybackAuthority": False,
    }


def merge(previous: dict[str, Any], latest: dict[str, Any]) -> dict[str, Any]:
    if latest.get("schemaVersion") != 1 or latest.get("authority") != "current-retest-observation-only":
        raise ValueError("invalid current Retest envelope")
    rows: list[dict[str, Any]] = []
    for item in previous.get("rows") or []:
        if not isinstance(item, dict):
            continue
        envelope = {
            "sourceCensusRunId": item.get("sourceCensusRunId"),
            "sourceNiakvioSha": item.get("sourceNiakvioSha"),
            "proofAuthority": False, "publicationAuthority": False,
        }
        safe = sanitize(envelope, item)
        if safe:
            rows.append(safe)
    for item in latest.get("rows") or []:
        if not isinstance(item, dict):
            continue
        safe = sanitize(latest, item)
        if safe:
            rows.append(safe)
    # Preserve newest first without letting repeated same-run replay consume memory.
    seen: set[tuple[str, str, str, str]] = set()
    per_provider: dict[str, int] = {}
    kept: list[dict[str, Any]] = []
    for row in reversed(rows):
        provider = row["provider"]
        fixture = row["fixture"]
        key = (
            provider, row["providerArtifactSha256"], row["sourceCensusRunId"],
            f"{row['lane']}:{fixture['tmdbId']}:{fixture['season']}:{fixture['episode']}",
        )
        if key in seen or per_provider.get(provider, 0) >= MAX_PER_PROVIDER:
            continue
        if provider not in per_provider and len(per_provider) >= MAX_PROVIDERS:
            continue
        seen.add(key)
        per_provider[provider] = per_provider.get(provider, 0) + 1
        kept.append(row)
    return {
        "schemaVersion": 1,
        "authority": "historical-exact-bundle-diagnostics-only",
        "providerCount": len(per_provider),
        "observationCount": len(kept),
        "rows": kept,
        "proofAuthority": False,
        "publicationAuthority": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    a = parser.parse_args()
    previous = json.loads(a.history.read_text("utf-8")) if a.history.is_file() else {}
    latest = json.loads(a.latest.read_text("utf-8"))
    result = merge(previous, latest)
    a.history.parent.mkdir(parents=True, exist_ok=True)
    a.history.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("FIELD_PROVIDER_RETEST_BRAIN_HISTORY "
          f"providers={result['providerCount']} observations={result['observationCount']} "
          "proof_authority=false")


if __name__ == "__main__":
    main()
