#!/usr/bin/env python3
"""Retest -> Brain: content-addressed, privacy-safe diagnostic reasons, not proof."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[a-f0-9]{40}$")
REASONS = {
    "insufficient_identity_metadata", "duration_incomplete_hls",
    "duration_unavailable", "fixture_duration_mismatch",
    "provider_tmdb_route_mismatch", "wrong_season_episode", "wrong_episode",
    "forbidden_title_alias", "media_filename_title_mismatch",
    "strong_title_mismatch", "expected_title_alias", "season_episode_match",
    "episode_match", "provider_tmdb_direct_route",
}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def bounded(value: object) -> int:
    return min(10000, max(0, value)) if type(value) is int else 0


def current_sha256(root: Path, provider: str) -> str:
    for relative in ("manifest.json", "vf/manifest.json"):
        path = root / relative
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for row in manifest.get("scrapers") or []:
            if not isinstance(row, dict) or cid(row.get("id")) != provider:
                continue
            if row.get("enabled") is not True:
                continue
            source = (path.parent / str(row.get("filename") or "")).resolve()
            try:
                parts = source.relative_to(root.resolve()).parts
            except ValueError:
                raise ValueError("provider path escapes repository") from None
            if not parts or parts[0] != "providers" or not source.is_file():
                raise ValueError("active provider JS must exist inside providers/")
            return hashlib.sha256(source.read_bytes()).hexdigest()
    return ""


def export(report: dict[str, Any], census: dict[str, Any], *,
           root: Path, sha: str, run: str) -> dict[str, Any]:
    if not SHA40.fullmatch(sha) or not run.isdigit():
        raise ValueError("Retest source SHA/run missing")
    if census.get("triggerSha") != sha or census.get("runId") != run + "-retest":
        raise ValueError("current census receipt does not match executed Retest")
    selected = [cid(x) for x in report.get("selected_providers") or []]
    if (report.get("resolved_scope") != "explicit" or not selected
            or len(selected) > 8 or len(set(selected)) != len(selected)):
        raise ValueError("only bounded explicit Retest can produce Brain observation")
    census_rows = {
        cid(x.get("provider")): x for x in census.get("providers") or []
        if isinstance(x, dict)
    }
    rows = []
    for raw in report.get("rows") or []:
        if not isinstance(raw, dict):
            continue
        provider = cid(raw.get("provider_id"))
        if provider not in selected or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,90}", provider):
            continue
        current = census_rows.get(provider) or {}
        if current.get("testedThisRun") is not True or current.get("status") == "DISABLED":
            continue
        digest = current_sha256(root, provider)
        if not digest:
            continue
        observed = raw.get("debug_identity_reasons") or []
        reasons = sorted({
            str(item.get(field) or "").strip().casefold()
            for item in observed[:16] if isinstance(item, dict)
            for field in ("identity_reason", "metadata_reason", "duration_reason")
            if str(item.get(field) or "").strip().casefold() in REASONS
        })
        fixture = raw.get("fixture") if isinstance(raw.get("fixture"), dict) else {}
        lane = str(raw.get("semantic_type") or "")
        lane = lane if lane in {"anime", "movie", "tv"} else ""
        status = str(raw.get("status") or "")
        stage = str(raw.get("debug_stage") or "")
        rows.append({
            "provider": provider, "providerArtifactSha256": digest,
            "lane": lane, "status": status[:48] if re.fullmatch(r"[a-z_]+", status) else "",
            "debugStage": stage[:64] if re.fullmatch(r"[a-z_]+", stage) else "",
            "fixture": {
                "mediaType": lane,
                "tmdbId": str(fixture.get("tmdbId") or "")[:12] if
                    str(fixture.get("tmdbId") or "").isdigit() else "",
                "season": bounded(fixture.get("season")),
                "episode": bounded(fixture.get("episode")),
            },
            "raw": bounded(raw.get("raw")), "playable": bounded(raw.get("playable")),
            "verified": bounded(raw.get("verified")),
            "identityReasons": reasons[:12], "proofAuthority": False,
            "publicationAuthority": False, "nativePlaybackAuthority": False,
        })
    return {
        "schemaVersion": 1, "authority": "current-retest-observation-only",
        "sourceNiakvioSha": sha, "sourceCensusRunId": run + "-retest",
        "providerCount": len(rows), "rows": rows[:8],
        "proofAuthority": False, "publicationAuthority": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    for arg in ("report", "census", "output"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    result = export(json.loads(args.report.read_text(encoding="utf-8")),
                    json.loads(args.census.read_text(encoding="utf-8")),
                    root=ROOT, sha=args.sha, run=args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("FIELD_PROVIDER_RETEST_BRAIN_EVIDENCE "
          f"providers={result['providerCount']} exact_bundle=true proof_authority=false")


if __name__ == "__main__":
    main()
