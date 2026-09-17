#!/usr/bin/env python3
"""Certify current Provider v3 bytes with positive playable fixtures per semantic lane.

An enabled provider is useful only when each declared semantic lane can currently
produce identity-verified playable output. Catalogue reachability alone is never a
certificate.

Candidate fixtures are tried in this order:
1. the provider/lane's previously learned positive fixtures;
2. corpus fixtures explicitly associated with that provider;
3. the rotating recent corpus, deterministically ordered per provider.

The first positive fixture becomes the lane witness for the exact current bundle
SHA. Stream URLs, cookies, tokens and headers are deliberately never persisted.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rotating_corpus import (  # noqa: E402
    all_fixtures,
    canonical_lane,
    default_seed,
    rotated_candidates,
)

MANIFEST = ROOT / "manifest.json"
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
PROBE = ROOT / "scripts/nuvio_tv_probe_tmdb_ci.cjs"
REGISTRY = ROOT / "automation/provider-positive-fixtures.json"
DEFAULT_OUTPUT = ROOT / "automation/provider-playable-certification.json"
LANES = ("movie", "tv", "anime")


def load(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def semantic_types(row: dict[str, Any]) -> list[str]:
    values = row.get("canonicalSupportedTypes")
    if not isinstance(values, list) or not values:
        values = row.get("supportedTypes") or []
    out: list[str] = []
    for raw in values:
        value = canonical(raw)
        if value in LANES and value not in out:
            out.append(value)
    return out


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_index() -> dict[str, dict[str, Any]]:
    return {str(row.get("slug") or ""): dict(row) for row in all_fixtures() if str(row.get("slug") or "")}


def corpus_targets() -> dict[tuple[str, str], list[str]]:
    data = load(CORPUS, {}) or {}
    out: dict[tuple[str, str], list[str]] = {}
    for raw in data.get("fixtures") or []:
        if not isinstance(raw, dict) or not isinstance(raw.get("fixture"), dict):
            continue
        slug = str(raw.get("slug") or "").strip()
        if not slug:
            continue
        lane = canonical_lane(raw["fixture"])
        for provider in raw.get("providers") or []:
            key = (canonical(provider), lane)
            out.setdefault(key, [])
            if slug not in out[key]:
                out[key].append(slug)
    return out


def previous_positive_slugs(registry: dict[str, Any], provider: str, lane: str) -> list[str]:
    providers = registry.get("providers") if isinstance(registry, dict) else {}
    row = providers.get(provider) if isinstance(providers, dict) else None
    lanes = row.get("lanes") if isinstance(row, dict) else None
    lane_row = lanes.get(lane) if isinstance(lanes, dict) else None
    if not isinstance(lane_row, dict):
        return []
    values: list[str] = []
    primary = str(lane_row.get("fixtureSlug") or "").strip()
    if primary:
        values.append(primary)
    for raw in lane_row.get("knownPositiveFixtures") or []:
        value = str(raw or "").strip()
        if value and value not in values:
            values.append(value)
    return values


def candidate_fixtures(
    provider: str,
    lane: str,
    *,
    registry: dict[str, Any],
    fixtures: dict[str, dict[str, Any]],
    targets: dict[tuple[str, str], list[str]],
    seed: str,
    limit: int,
) -> list[dict[str, Any]]:
    slugs: list[str] = []
    for slug in previous_positive_slugs(registry, provider, lane):
        if slug in fixtures and canonical_lane(fixtures[slug]) == lane and slug not in slugs:
            slugs.append(slug)
    for slug in targets.get((provider, lane), []):
        if slug in fixtures and canonical_lane(fixtures[slug]) == lane and slug not in slugs:
            slugs.append(slug)
    for row in rotated_candidates(lane, seed=seed, provider=provider):
        slug = str(row.get("slug") or "")
        if slug and slug not in slugs:
            slugs.append(slug)
    return [fixtures[slug] for slug in slugs[: max(1, limit)] if slug in fixtures]


def parse_probe(stdout: str) -> dict[str, Any] | None:
    for raw in reversed(stdout.splitlines()):
        raw = raw.strip()
        if not raw.startswith("{"):
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def probe_fixture(bundle: Path, fixture: dict[str, Any], timeout: int) -> dict[str, Any]:
    clean_fixture = {key: value for key, value in fixture.items() if key not in {"slug", "lane"}}
    command = [
        "node",
        str(PROBE),
        str(bundle),
        json.dumps(clean_fixture, ensure_ascii=False, separators=(",", ":")),
        "{}",
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "positive": False,
            "raw": 0,
            "playable": 0,
            "verified": 0,
            "contradictions": 0,
            "debugStage": "timeout",
            "durationMs": round((time.monotonic() - started) * 1000),
        }

    payload = parse_probe(completed.stdout)
    if payload is None:
        return {
            "status": "probe_error",
            "positive": False,
            "raw": 0,
            "playable": 0,
            "verified": 0,
            "contradictions": 0,
            "debugStage": "invalid_probe_output",
            "durationMs": round((time.monotonic() - started) * 1000),
        }

    raw_count = int(payload.get("raw_stream_count") or 0)
    playable = int(payload.get("playable_stream_count") or 0)
    verified = int(payload.get("content_verified_count") or payload.get("identity_verified_count") or 0)
    contradictions = int(payload.get("identity_contradiction_count") or 0)
    runtime_error = bool(payload.get("runtime_error"))
    debug = payload.get("debug") if isinstance(payload.get("debug"), dict) else {}
    stage = str(debug.get("stage") or "")
    positive = playable > 0 and verified > 0 and contradictions == 0 and not runtime_error
    status = "playable_verified" if positive else (
        "wrong_content" if contradictions else
        "runtime_error" if runtime_error else
        "returned_unplayable" if raw_count else
        "no_streams"
    )
    return {
        "status": status,
        "positive": positive,
        "raw": raw_count,
        "playable": playable,
        "verified": verified,
        "contradictions": contradictions,
        "debugStage": stage or status,
        "durationMs": int(payload.get("duration_ms") or round((time.monotonic() - started) * 1000)),
    }


def certify_provider(
    row: dict[str, Any],
    *,
    registry: dict[str, Any],
    fixtures: dict[str, dict[str, Any]],
    targets: dict[tuple[str, str], list[str]],
    seed: str,
    limit: int,
    timeout: int,
) -> dict[str, Any]:
    provider = canonical(row.get("id"))
    filename = str(row.get("filename") or "").strip()
    bundle = (ROOT / filename).resolve()
    required = semantic_types(row)
    result: dict[str, Any] = {
        "providerId": provider,
        "enabled": row.get("enabled") is not False,
        "filename": filename,
        "bundleSha256": sha256_file(bundle) if filename and bundle.is_file() else None,
        "requiredTypes": required,
        "certifiedTypes": [],
        "missingTypes": [],
        "lanes": {},
        "certified": False,
    }
    if not filename or not bundle.is_file():
        result["missingTypes"] = required
        result["failure"] = "bundle_missing"
        return result

    certified: list[str] = []
    for lane in required:
        attempts: list[dict[str, Any]] = []
        witness: dict[str, Any] | None = None
        candidates = candidate_fixtures(
            provider,
            lane,
            registry=registry,
            fixtures=fixtures,
            targets=targets,
            seed=seed,
            limit=limit,
        )
        for fixture in candidates:
            probe = probe_fixture(bundle, fixture, timeout)
            attempts.append({
                "fixtureSlug": str(fixture.get("slug") or ""),
                "status": probe["status"],
                "debugStage": probe["debugStage"],
                "raw": probe["raw"],
                "playable": probe["playable"],
                "verified": probe["verified"],
                "contradictions": probe["contradictions"],
                "durationMs": probe["durationMs"],
            })
            if probe["positive"]:
                witness = {
                    "fixtureSlug": str(fixture.get("slug") or ""),
                    "fixture": {key: value for key, value in fixture.items() if key not in {"lane"}},
                    "status": "playable_verified",
                    "playable": probe["playable"],
                    "verified": probe["verified"],
                }
                certified.append(lane)
                break
        result["lanes"][lane] = {
            "state": "certified" if witness else "uncertified",
            "fixtureSlug": witness.get("fixtureSlug") if witness else None,
            "fixture": witness.get("fixture") if witness else None,
            "attemptCount": len(attempts),
            "attempts": attempts,
        }

    missing = [lane for lane in required if lane not in certified]
    result["certifiedTypes"] = certified
    result["missingTypes"] = missing
    result["certified"] = bool(required) and not missing
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--candidate-limit", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=35)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", default=None)
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--require-active", action="store_true")
    args = parser.parse_args()

    manifest = load(args.manifest.resolve(), {}) or {}
    registry = load(args.registry.resolve(), {}) or {}
    fixtures = fixture_index()
    targets = corpus_targets()
    seed = str(args.seed if args.seed is not None else default_seed())
    rows = [
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
        and canonical(row.get("id"))
        and (args.include_disabled or row.get("enabled") is not False)
    ]

    results: list[dict[str, Any]] = []
    workers = max(1, min(int(args.workers), 16))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                certify_provider,
                row,
                registry=registry,
                fixtures=fixtures,
                targets=targets,
                seed=seed,
                limit=max(1, int(args.candidate_limit)),
                timeout=max(15, min(int(args.timeout), 90)),
            ): canonical(row.get("id"))
            for row in rows
        }
        for future in concurrent.futures.as_completed(futures):
            provider = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                results.append({
                    "providerId": provider,
                    "enabled": True,
                    "requiredTypes": [],
                    "certifiedTypes": [],
                    "missingTypes": [],
                    "lanes": {},
                    "certified": False,
                    "failure": type(exc).__name__,
                })

    results.sort(key=lambda row: str(row.get("providerId") or ""))
    active = [row for row in results if row.get("enabled")]
    certified = [row for row in active if row.get("certified")]
    payload = {
        "schemaVersion": 1,
        "authority": "exact-bundle-playable-lane-certification-v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "manifestVersion": manifest.get("version"),
        "seed": seed,
        "candidateLimit": max(1, int(args.candidate_limit)),
        "providerCount": len(results),
        "activeProviderCount": len(active),
        "certifiedActiveProviderCount": len(certified),
        "uncertifiedActiveProviderCount": len(active) - len(certified),
        "providers": results,
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_PLAYABLE_CERTIFICATION "
        f"providers={len(results)} active={len(active)} certified={len(certified)} "
        f"uncertified={len(active) - len(certified)}"
    )
    for row in active:
        if not row.get("certified"):
            print(
                "FIELD_PROVIDER_PLAYABLE_UNCERTIFIED "
                f"provider={row.get('providerId')} missing={','.join(row.get('missingTypes') or []) or 'unknown'}"
            )
    if args.require_active and len(certified) != len(active):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
