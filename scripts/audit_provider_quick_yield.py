#!/usr/bin/env python3
"""Fast report-only Provider v3 yield census with execution-gate diagnostics."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from rotating_corpus import default_seed, provider_census_candidates

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
CORPUS = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"
OUTPUT = ROOT / "provider-v3-quick-yield.json"
STATUS_FILE = ROOT / "automation" / "provider-census-status.json"
PROOF_HISTORY = ROOT / "automation" / "provider-census-proof-history.json"
WORKERS = max(1, min(int(os.environ.get("NIAKVIO_QUICK_YIELD_WORKERS", "12")), 20))
TIMEOUT = max(20, min(int(os.environ.get("NIAKVIO_QUICK_YIELD_TIMEOUT", "45")), 90))
MAX_SAMPLES = max(1, min(int(os.environ.get("NIAKVIO_QUICK_YIELD_MAX_SAMPLES", "4")), 8))
REPRESENTATIVE = {
    "movie": "interstellar",
    "tv": "breaking-bad-s01e01",
    "anime": "jujutsu-kaisen-s01e01",
}
TMDB_ERASED_HOST_RE = re.compile(r"^/+(?:api\.)?themoviedb\.org(?:/|$)", re.I)
TMDB_CORE_ROUTE_RE = re.compile(r"^/3/(?:movie|tv)(?:/|$)", re.I)
CHAIN_ROUTE_RE = re.compile(r"(?:/(?:watch|movie|tv|episode|episodes|ep|player|embed|links?|source|sources|server|servers|stream|streams|download|file|zfile|v)(?:/|$)|showid|episodestring|[?&](?:eid|lid)=)", re.I)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def semantic_types(row: dict[str, Any]) -> list[str]:
    values = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
    out: list[str] = []
    for value in values:
        item = str(value or "").strip().casefold()
        if item in REPRESENTATIVE and item not in out:
            out.append(item)
    return out


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


def _fixture_identity(fixture: dict[str, Any]) -> tuple[str, int, int, str]:
    def integer(value: object) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
    return (
        str(fixture.get("tmdbId") or fixture.get("id") or "").strip(),
        integer(fixture.get("season")),
        integer(fixture.get("episode")),
        str(fixture.get("mediaType") or fixture.get("category") or "").strip().casefold(),
    )


def _provider_fixture_priority(record: dict[str, Any], provider_id: str) -> int:
    raw = record.get("providerEvidencePriority")
    if not isinstance(raw, dict):
        return 0
    wanted = str(provider_id or "").strip().casefold()
    for key, value in raw.items():
        if str(key or "").strip().casefold() != wanted:
            continue
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
    return 0


def _history_lane(history: dict[str, Any], provider_id: str, media_type: str) -> dict[str, Any]:
    providers = history.get("providers") if isinstance(history.get("providers"), dict) else {}
    provider = providers.get(provider_id) if isinstance(providers.get(provider_id), dict) else {}
    lanes = provider.get("lanes") if isinstance(provider.get("lanes"), dict) else {}
    return lanes.get(media_type) if isinstance(lanes.get(media_type), dict) else {}


def _history_proof_fixtures(history: dict[str, Any], provider_id: str, media_type: str) -> list[dict[str, Any]]:
    lane = _history_lane(history, provider_id, media_type)
    out: list[dict[str, Any]] = []
    for row in lane.get("proofs") or []:
        if isinstance(row, dict) and isinstance(row.get("fixture"), dict):
            out.append(dict(row["fixture"]))
    return out


def _history_chain_fixtures(history: dict[str, Any], provider_id: str, media_type: str) -> list[dict[str, Any]]:
    lane = _history_lane(history, provider_id, media_type)
    out: list[dict[str, Any]] = []
    for row in lane.get("chainHits") or []:
        if isinstance(row, dict) and isinstance(row.get("fixture"), dict):
            out.append(dict(row["fixture"]))
    return out


def _history_miss_slugs(history: dict[str, Any], provider_id: str, media_type: str) -> set[str]:
    lane = _history_lane(history, provider_id, media_type)
    out: set[str] = set()
    for row in lane.get("misses") or []:
        if not isinstance(row, dict):
            continue
        fixture = row.get("fixture") if isinstance(row.get("fixture"), dict) else {}
        slug = str(fixture.get("slug") or "").strip()
        if slug:
            out.add(slug)
    return out


def _adaptive_fixtures(
    provider_id: str,
    media_type: str,
    initial: dict[str, Any],
    *,
    preferred: list[dict[str, Any]] | None = None,
    history: dict[str, Any] | None = None,
    anime_movie_only: bool = False,
) -> list[dict[str, Any]]:
    """Build a bounded provider-aware fixture queue.

    Explicit corpus ownership is stronger catalogue evidence than the global
    representative. Historical strict-46 proof used provider-targeted fixtures
    first; quick-yield must preserve that ordering or it can manufacture false
    ZERO states from an unrelated representative title.
    """
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int, str]] = set()

    def add(candidate: dict[str, Any]) -> None:
        identity = _fixture_identity(candidate)
        if identity in seen or len(rows) >= MAX_SAMPLES:
            return
        seen.add(identity)
        rows.append(dict(candidate))

    history = history or {}

    # Retained positive proof is always replayed first. It is the cheapest
    # regression detector and avoids rediscovering a known catalogue match.
    for candidate in _history_proof_fixtures(history, provider_id, media_type):
        add(candidate)
    for candidate in _history_chain_fixtures(history, provider_id, media_type):
        add(candidate)
    for candidate in preferred or []:
        add(candidate)
    add(initial)

    if anime_movie_only or MAX_SAMPLES <= len(rows):
        return rows

    # Clean catalogue misses are remembered across runs and skipped until the
    # corpus has been exhausted, so repeated censuses advance instead of testing
    # the same four works forever.
    excluded = _history_miss_slugs(history, provider_id, media_type) | {
        str(row.get("slug") or "").strip() for row in rows if str(row.get("slug") or "").strip()
    }
    for candidate in provider_census_candidates(
        media_type,
        seed=default_seed(),
        provider=provider_id,
        exclude=excluded,
    ):
        add(candidate)
        if len(rows) >= MAX_SAMPLES:
            break
    return rows


def build_tasks(provider_filter: set[str] | None = None, *, history: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], int]:
    manifest = load(MANIFEST)
    corpus = load(CORPUS)
    history = history or {}
    fixture_records = {
        str(row.get("slug") or ""): row
        for row in corpus.get("fixtures") or []
        if isinstance(row, dict) and isinstance(row.get("fixture"), dict)
    }
    fixture_rows = {slug: row["fixture"] for slug, row in fixture_records.items()}
    fixtures: dict[str, dict[str, Any]] = {}
    for media_type, slug in REPRESENTATIVE.items():
        fixture = fixture_rows.get(slug)
        if not isinstance(fixture, dict):
            raise RuntimeError(f"missing representative fixture {slug}")
        fixtures[media_type] = fixture

    # Anime catalogues may legitimately expose a movie lane for anime films.
    # That lane must be proven with the corpus-owned animeMovie fixture rather
    # than a generic movie such as Interstellar; otherwise semantic/transport
    # separation is violated and healthy anime-film lanes are false-negative.
    anime_movie_records = [
        row for row in fixture_records.values()
        if isinstance(row.get("fixture"), dict) and row["fixture"].get("animeMovie") is True
    ]
    if len(anime_movie_records) != 1:
        raise RuntimeError(f"expected exactly one animeMovie representative fixture, got {len(anime_movie_records)}")
    anime_movie_record = anime_movie_records[0]
    anime_movie_fixture = anime_movie_record["fixture"]
    anime_movie_providers = {
        str(value or "").strip().casefold()
        for value in (anime_movie_record.get("providers") or [])
        if str(value or "").strip()
    }

    tasks: list[dict[str, Any]] = []
    providers = 0
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        filename = str(row.get("filename") or "").strip()
        if not provider_id or not filename or not (ROOT / filename).is_file():
            continue
        if provider_filter is not None and provider_id not in provider_filter:
            continue
        providers += 1
        for media_type in semantic_types(row):
            anime_movie_only = media_type == "movie" and provider_id in anime_movie_providers
            fixture = anime_movie_fixture if anime_movie_only else fixtures[media_type]
            preferred: list[dict[str, Any]] = []
            if not anime_movie_only:
                preferred_records: list[dict[str, Any]] = []
                for record in fixture_records.values():
                    candidate = record.get("fixture")
                    if not isinstance(candidate, dict):
                        continue
                    candidate_type = str(candidate.get("mediaType") or candidate.get("category") or "").strip().casefold()
                    owners = {
                        str(value or "").strip().casefold()
                        for value in (record.get("providers") or [])
                        if str(value or "").strip()
                    }
                    if candidate_type == media_type and provider_id in owners:
                        preferred_records.append(record)
                preferred_records.sort(
                    key=lambda record: _provider_fixture_priority(record, provider_id),
                    reverse=True,
                )
                preferred = [
                    record["fixture"]
                    for record in preferred_records
                    if isinstance(record.get("fixture"), dict)
                ]
            tasks.append({
                "provider_id": provider_id,
                "provider_name": str(row.get("name") or row.get("id") or provider_id),
                "filename": filename,
                "semantic_type": media_type,
                "fixture": fixture,
                "fixtures": _adaptive_fixtures(
                    provider_id,
                    media_type,
                    fixture,
                    preferred=preferred,
                    history=history,
                    anime_movie_only=anime_movie_only,
                ),
            })
    return tasks, providers


def _provider_fetches(debug: dict[str, Any]) -> list[dict[str, Any]]:
    rows = debug.get("fetches") if isinstance(debug.get("fetches"), list) else []
    output = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            host = str(urlsplit(str(row.get("url") or "")).hostname or "").casefold()
        except ValueError:
            host = ""
        if host == "api.themoviedb.org":
            continue
        output.append(row)
    return output


def _provider_progress_stage(debug: dict[str, Any]) -> str:
    """Describe how far a zero-stream provider got without calling it healthy."""
    successful = []
    for row in _provider_fetches(debug):
        if row.get("error"):
            continue
        status = int(row.get("status") or 0)
        if 200 <= status < 400:
            successful.append(row)
    if not successful:
        return "none"
    for row in successful:
        for key in ("url", "response_url"):
            if CHAIN_ROUTE_RE.search(str(row.get(key) or "")):
                return "chain_reached"
    return "lookup_only"


def _provider_value_trace_history(debug: dict[str, Any]) -> list[dict[str, Any]]:
    rows = debug.get("provider_value_trace_history_v21")
    if not isinstance(rows, list):
        return []
    output: list[dict[str, Any]] = []
    for row in rows[-48:]:
        if not isinstance(row, dict):
            continue
        output.append({
            "stage": str(row.get("stage") or "")[:64],
            "lane": str(row.get("lane") or "")[:32],
            "provider_id": str(row.get("provider_id") or "")[:160],
            "step_index": row.get("step_index") if isinstance(row.get("step_index"), int) else None,
            "route": str(row.get("route") or "")[:240],
        })
    return output


def _identity_diagnostics(probe: dict[str, Any]) -> list[dict[str, Any]]:
    rows = probe.get("streams") if isinstance(probe.get("streams"), list) else []
    output: list[dict[str, Any]] = []
    for item in rows[:16]:
        if not isinstance(item, dict):
            continue
        row = item.get("row") if isinstance(item.get("row"), dict) else {}
        media = item.get("media") if isinstance(item.get("media"), dict) else {}
        identity = item.get("identity") if isinstance(item.get("identity"), dict) else {}
        metadata = item.get("metadata_identity") if isinstance(item.get("metadata_identity"), dict) else {}
        duration = item.get("duration_identity") if isinstance(item.get("duration_identity"), dict) else {}
        try:
            host = str(urlsplit(str(row.get("url") or "")).hostname or "").casefold()
        except ValueError:
            host = ""
        output.append({
            "host": host[:160],
            "title": str(row.get("title") or "")[:240],
            "filename": str(row.get("filename") or "")[:240],
            "identity_status": str(identity.get("status") or "")[:40],
            "identity_reason": str(identity.get("reason") or "")[:120],
            "metadata_status": str(metadata.get("status") or "")[:40],
            "metadata_reason": str(metadata.get("reason") or "")[:120],
            "duration_status": str(duration.get("status") or "")[:40],
            "duration_reason": str(duration.get("reason") or "")[:120],
            "duration_ratio": duration.get("ratio") if isinstance(duration.get("ratio"), (int, float)) else None,
            "media_kind": str(media.get("kind") or "")[:40],
            "media_status": media.get("status") if isinstance(media.get("status"), int) else None,
            "media_error": str(media.get("error") or "")[:120],
        })
    return output


def classify_debug_stage(task: dict[str, Any], probe: dict[str, Any], debug: dict[str, Any]) -> str:
    model = debug.get("model") if isinstance(debug.get("model"), dict) else {}
    raw = int(probe.get("raw_stream_count") or 0)
    contradictions = int(probe.get("identity_contradiction_count") or 0)
    if raw > 0:
        return "provider_returned_wrong_content" if contradictions else "provider_returned_streams"

    supported = [str(v or "").casefold() for v in model.get("supported_types") or []]
    requested = str(task.get("semantic_type") or "").casefold()
    if supported and requested not in supported and not (requested == "tv" and "anime" in supported):
        return "gate_type_capability"

    dispatch_error = debug.get("provider_runtime_dispatch_error_v1")
    if isinstance(dispatch_error, dict) and str(dispatch_error.get("name") or "").strip():
        return "provider_runtime_hook_exception"

    provider_fetches = _provider_fetches(debug)
    if not provider_fetches:
        if not bool(model.get("has_api_recipe")) and int(model.get("route_count") or 0) <= 0:
            return "gate_runtime_plan_missing"
        family = str(model.get("source_runtime_family") or "unknown").casefold()
        return "gate_source_family_unknown" if family == "unknown" else "provider_zero_before_provider_network"

    for row in provider_fetches:
        raw_url = str(row.get("url") or "")
        try:
            parsed = urlsplit(raw_url)
            host = str(parsed.hostname or "").casefold()
            path = str(parsed.path or "")
        except ValueError:
            host = ""
            path = raw_url
        if (
            host == "api.themoviedb.org"
            or TMDB_ERASED_HOST_RE.match(path)
            or TMDB_CORE_ROUTE_RE.match(path)
        ):
            return "source_plan_core_metadata_leak"

    # Use the terminal meaningful provider request as the causal network verdict.
    # Incidental 4xx/errors followed by a later successful route must not poison
    # the whole probe (common with aliases, optional assets and crawl fallbacks).
    meaningful_fetches = []
    for row in provider_fetches:
        raw_url = str(row.get("url") or "").strip()
        try:
            parsed = urlsplit(raw_url)
            if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
                continue
        except ValueError:
            continue
        meaningful_fetches.append(row)
    if not meaningful_fetches:
        return "provider_network_zero_result"
    terminal = meaningful_fetches[-1]
    if str(terminal.get("challenge") or "").strip():
        return "provider_waf_challenge"
    if terminal.get("error"):
        return "provider_network_exception"
    if int(terminal.get("status") or 0) >= 400:
        return "provider_network_http_error"
    return "provider_network_zero_result"


def run_single(task: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    command = [
        "node", str(PROBE), str(ROOT / task["filename"]),
        json.dumps(task["fixture"], ensure_ascii=False, separators=(",", ":")), "{}",
    ]
    fixture = {
        key: task["fixture"].get(key)
        for key in ("slug", "tmdbId", "mediaType", "category", "title", "year", "season", "episode", "animeMovie")
        if task["fixture"].get(key) is not None
    }
    base = {
        "provider_id": task["provider_id"],
        "provider_name": task["provider_name"],
        "semantic_type": task["semantic_type"],
        "fixture_title": str(task["fixture"].get("title") or ""),
        "fixture": fixture,
    }
    try:
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT, check=False, env=os.environ.copy())
    except subprocess.TimeoutExpired:
        return {**base, "status": "timeout", "debug_stage": "timeout", "raw": 0, "playable": 0, "verified": 0, "contradictions": 0, "duration_ms": round((time.monotonic() - started) * 1000)}
    except Exception as exc:
        return {**base, "status": "audit_error", "debug_stage": "audit_error", "raw": 0, "playable": 0, "verified": 0, "contradictions": 0, "duration_ms": round((time.monotonic() - started) * 1000), "error": type(exc).__name__}

    probe = parse_probe(proc.stdout)
    if probe is None:
        marker = "missing_tmdb_credential" if "missing_tmdb_credential" in proc.stderr else "invalid_probe_output"
        return {**base, "status": marker, "debug_stage": marker, "raw": 0, "playable": 0, "verified": 0, "contradictions": 0, "duration_ms": round((time.monotonic() - started) * 1000), "stderr_tail": proc.stderr[-1000:]}

    raw = int(probe.get("raw_stream_count") or 0)
    playable = int(probe.get("playable_stream_count") or 0)
    verified = int(probe.get("content_verified_count") or probe.get("identity_verified_count") or 0)
    contradictions = int(probe.get("identity_contradiction_count") or 0)
    runtime_error = bool(probe.get("runtime_error"))
    if contradictions:
        status = "wrong_content"
    elif runtime_error:
        status = "runtime_error"
    elif playable and verified:
        status = "playable_verified"
    elif playable:
        status = "playable_unverified"
    elif raw:
        status = "returned_unplayable"
    else:
        status = "no_streams"
    debug = probe.get("debug") if isinstance(probe.get("debug"), dict) else {}
    stage = classify_debug_stage(task, probe, debug)
    return {
        **base,
        "status": status,
        "debug_stage": stage,
        "debug_model": debug.get("model"),
        "debug_fetch_count": int(debug.get("fetch_count") or 0),
        "debug_provider_fetch_count": len(_provider_fetches(debug)),
        "debug_progress_stage": _provider_progress_stage(debug),
        "debug_fetches": debug.get("fetches") or [],
        "debug_provider_value_trace_v18": debug.get("provider_value_trace_v18"),
        "debug_provider_value_trace_history_v21": _provider_value_trace_history(debug),
        "debug_provider_runtime_dispatch_error_v1": (
            debug.get("provider_runtime_dispatch_error_v1")
            if isinstance(debug.get("provider_runtime_dispatch_error_v1"), dict)
            else None
        ),
        "debug_identity_reasons": _identity_diagnostics(probe),
        "raw": raw,
        "playable": playable,
        "verified": verified,
        "contradictions": contradictions,
        "identity_safe": contradictions == 0,
        "duration_ms": int(probe.get("duration_ms") or round((time.monotonic() - started) * 1000)),
    }


def _compact_sample(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "fixture_title", "fixture", "status", "debug_stage", "debug_progress_stage",
            "raw", "playable", "verified", "contradictions", "duration_ms",
        )
    }


def run(task: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    fixtures = [
        row for row in (task.get("fixtures") or [task["fixture"]])
        if isinstance(row, dict)
    ]
    if not fixtures:
        fixtures = [task["fixture"]]
    samples: list[dict[str, Any]] = []
    final: dict[str, Any] | None = None
    for fixture in fixtures:
        current = dict(task)
        current["fixture"] = fixture
        row = run_single(current)
        samples.append(_compact_sample(row))
        final = row
        # A single title-level no-stream, HTTP error or provider exception is
        # not enough to classify the whole declared lane. Historical strict
        # proof advanced to the next provider fixture; keep the same bounded
        # behaviour here. Stop only once output (good or bad) is observed, or
        # once the bounded fixture queue is exhausted.
        keep_sampling = row.get("status") in {"no_streams", "timeout"}
        if not keep_sampling:
            break
    if final is None:
        raise RuntimeError(f"{task.get('provider_id')}: empty adaptive fixture set")
    result = dict(final)
    result["sample_count"] = len(samples)
    progress_rank = {"none": 0, "lookup_only": 1, "chain_reached": 2}
    result["debug_progress_stage"] = max(
        (str(row.get("debug_progress_stage") or "none") for row in samples),
        key=lambda value: progress_rank.get(value, 0),
        default="none",
    )
    result["sample_titles"] = [str(row.get("fixture_title") or "") for row in samples]
    result["adaptive_rotated"] = len(samples) > 1
    result["samples"] = samples
    result["duration_ms"] = round((time.monotonic() - started) * 1000)
    return result


def _provider_shard(provider_id: str, shard_count: int) -> int:
    if shard_count <= 1:
        return 0
    digest = hashlib.sha256(str(provider_id).casefold().encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % shard_count


def _shard_filter(provider_filter: set[str] | None, shard_count: int, shard_index: int) -> set[str] | None:
    if shard_count <= 1:
        return provider_filter
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError(f"shard index {shard_index} outside [0,{shard_count})")
    if provider_filter is None:
        manifest = load(MANIFEST)
        provider_filter = {
            str(row.get("id") or "").strip().casefold()
            for row in manifest.get("scrapers") or []
            if isinstance(row, dict) and str(row.get("id") or "").strip()
        }
    return {provider for provider in provider_filter if _provider_shard(provider, shard_count) == shard_index}


def _scope_provider_filter(scope: str, status_file: Path, explicit: list[str]) -> tuple[set[str] | None, str]:
    requested = {
        str(value or "").strip().casefold()
        for item in explicit
        for value in str(item or "").split(",")
        if str(value or "").strip()
    }
    if requested:
        return requested, "explicit"
    if scope == "all":
        return None, "all"
    if not status_file.is_file():
        return None, "unresolved-bootstrap-all"
    status = load(status_file)
    status_rows = [row for row in status.get("providers") or [] if isinstance(row, dict)]
    known = {
        str(row.get("provider") or "").strip().casefold()
        for row in status_rows
        if str(row.get("provider") or "").strip()
    }
    unresolved = {
        str(row.get("provider") or "").strip().casefold()
        for row in status_rows
        if str(row.get("status") or "") not in {"FULL OK", "PARTIAL OK"}
        and str(row.get("provider") or "").strip()
    }
    # A newly onboarded provider is unresolved by definition until it gets its
    # first census verdict. This matters when hundreds of providers are added
    # between status snapshots: never let a stale status file hide new manifest
    # entries from the next unresolved pass.
    manifest = load(MANIFEST)
    current = {
        str(row.get("id") or "").strip().casefold()
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    unresolved.update(current - known)
    return unresolved, "unresolved"


def main() -> int:
    parser = argparse.ArgumentParser(description="Adaptive provider playback census")
    parser.add_argument("--scope", choices=("unresolved", "all"), default="all")
    parser.add_argument("--status-file", type=Path, default=STATUS_FILE)
    parser.add_argument("--history", type=Path, default=PROOF_HISTORY)
    parser.add_argument("--provider", action="append", default=[], help="Exact provider id; repeat or comma-separate")
    parser.add_argument("--shard-count", type=int, default=1, help="Deterministic provider shard count")
    parser.add_argument("--shard-index", type=int, default=0, help="Zero-based deterministic provider shard index")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    if not (str(os.environ.get("TMDB_API_KEY") or "").strip() or str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        raise SystemExit("TMDB_API_KEY or TMDB_ACCESS_TOKEN is required for quick yield census")

    history = load(args.history) if args.history.is_file() else {}
    provider_filter, resolved_scope = _scope_provider_filter(args.scope, args.status_file, args.provider)
    if args.shard_count < 1:
        raise SystemExit("--shard-count must be >= 1")
    if args.shard_index < 0 or args.shard_index >= args.shard_count:
        raise SystemExit("--shard-index must satisfy 0 <= index < shard-count")
    provider_filter = _shard_filter(provider_filter, args.shard_count, args.shard_index)
    if args.shard_count > 1:
        resolved_scope = f"{resolved_scope}-shard-{args.shard_index + 1}-of-{args.shard_count}"
    tasks, provider_count = build_tasks(provider_filter, history=history)
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(run, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())

    by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_provider[row["provider_id"]].append(row)

    raw_providers = sorted(provider for provider, values in by_provider.items() if any(int(row.get("raw") or 0) > 0 for row in values))
    playable_providers = sorted(provider for provider, values in by_provider.items() if any(int(row.get("playable") or 0) > 0 for row in values))
    accepted_playable_providers = sorted(
        provider for provider, values in by_provider.items()
        if any(int(row.get("playable") or 0) > 0 and int(row.get("contradictions") or 0) == 0 for row in values)
    )
    verified_providers = sorted(provider for provider, values in by_provider.items() if any(int(row.get("verified") or 0) > 0 for row in values))
    wrong_content = sorted(provider for provider, values in by_provider.items() if any(row.get("status") == "wrong_content" for row in values))
    statuses = Counter(str(row.get("status") or "unknown") for row in rows)
    debug_stages = Counter(str(row.get("debug_stage") or "unknown") for row in rows)

    type_summary: dict[str, dict[str, int]] = {}
    for media_type in REPRESENTATIVE:
        subset = [row for row in rows if row.get("semantic_type") == media_type]
        type_summary[media_type] = {
            "tasks": len(subset),
            "raw": sum(1 for row in subset if int(row.get("raw") or 0) > 0),
            "playable": sum(1 for row in subset if int(row.get("playable") or 0) > 0),
            "accepted_playable": sum(1 for row in subset if int(row.get("playable") or 0) > 0 and int(row.get("contradictions") or 0) == 0),
            "verified": sum(1 for row in subset if int(row.get("verified") or 0) > 0),
            "wrong_content": sum(1 for row in subset if int(row.get("contradictions") or 0) > 0),
        }

    stage_providers: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        stage = str(row.get("debug_stage") or "unknown")
        provider = str(row.get("provider_id") or "")
        if provider and provider not in stage_providers[stage]:
            stage_providers[stage].append(provider)

    probe_count = sum(int(row.get("sample_count") or 1) for row in rows)
    rotated_task_count = sum(1 for row in rows if row.get("adaptive_rotated") is True)
    report = {
        "schema_version": 6,
        "requested_scope": args.scope,
        "resolved_scope": resolved_scope,
        "selected_providers": sorted(provider_filter) if provider_filter is not None else None,
        "shard_count": args.shard_count,
        "shard_index": args.shard_index,
        "environment": "node-adaptive-provider-targeted-first-real-stream-census-with-tmdb-runtime-context",
        "fixture_selection_policy": "retained-proof-first-then-provider-targeted-then-representative-then-three-corpus-rotated",
        "provider_count": provider_count,
        "task_count": len(tasks),
        "probe_count": probe_count,
        "rotated_task_count": rotated_task_count,
        "max_samples_per_lane": MAX_SAMPLES,
        "raw_provider_count": len(raw_providers),
        "playable_provider_count": len(playable_providers),
        "accepted_playable_provider_count": len(accepted_playable_providers),
        "verified_provider_count": len(verified_providers),
        "wrong_content_provider_count": len(wrong_content),
        "raw_providers": raw_providers,
        "playable_providers": playable_providers,
        "accepted_playable_providers": accepted_playable_providers,
        "verified_providers": verified_providers,
        "wrong_content_providers": wrong_content,
        "type_summary": type_summary,
        "status_counts": dict(sorted(statuses.items())),
        "debug_stage_counts": dict(sorted(debug_stages.items())),
        "debug_stage_providers": {key: sorted(value) for key, value in sorted(stage_providers.items())},
        "rows": sorted(rows, key=lambda row: (row["provider_id"], row["semantic_type"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_QUICK_YIELD "
        f"scope={resolved_scope} providers={provider_count} tasks={len(tasks)} probes={probe_count} rotated_tasks={rotated_task_count} raw={len(raw_providers)} "
        f"playable={len(playable_providers)} accepted_playable={len(accepted_playable_providers)} "
        f"verified={len(verified_providers)} wrong_content={len(wrong_content)}"
    )
    print("FIELD_PROVIDER_QUICK_YIELD_PLAYABLE providers=" + ",".join(playable_providers))
    print("FIELD_PROVIDER_QUICK_YIELD_ACCEPTED_PLAYABLE providers=" + ",".join(accepted_playable_providers))
    print("FIELD_PROVIDER_QUICK_YIELD_VERIFIED providers=" + ",".join(verified_providers))
    for stage, count in sorted(debug_stages.items(), key=lambda item: (-item[1], item[0])):
        print(f"FIELD_PROVIDER_QUICK_YIELD_STAGE stage={stage} tasks={count} providers={len(stage_providers.get(stage) or [])}")
    for media_type, summary in type_summary.items():
        print(
            "FIELD_PROVIDER_QUICK_YIELD_TYPE "
            f"type={media_type} tasks={summary['tasks']} raw={summary['raw']} "
            f"playable={summary['playable']} accepted_playable={summary['accepted_playable']} "
            f"verified={summary['verified']} wrong_content={summary['wrong_content']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
