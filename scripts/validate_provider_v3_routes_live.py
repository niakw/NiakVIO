#!/usr/bin/env python3
"""Promote Provider v3 routes only after real runtime traversal.

The static recognizer is intentionally only a candidate generator. This gate runs
materialized Provider JS through the canonical TMDB-aware Nuvio probe, observes the
actual provider HTTP requests, and then rewrites canonical route DATA so that only
routes with successful live evidence remain executable authority.

Candidate routes are preserved separately for the next discovery/probe pass. A
candidate that was never reached, was blocked, or failed HTTP is never called
"real", "current", "validated" or "http proven" by this script.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import json
import os
import re
import subprocess
import time
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
CORPUS = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_route_validation.cjs"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
OVERRIDES = ROOT / "provider-overrides.json"
OUTPUT = ROOT / "provider-v3-live-route-validation.json"
EXPECTED = 96
REPRESENTATIVE = {
    "movie": "interstellar",
    "tv": "breaking-bad-s01e01",
    "anime": "jujutsu-kaisen-s01e01",
}
ROUTE_FIELD_SUFFIXES = ("route", "routes", "path", "paths", "endpoint", "endpoints", "url", "urls")
ROUTE_FIELD_EXCLUDED = {
    "base", "baseurl", "referer", "referrer", "origin", "host", "domain",
    "officialsite", "officialhub", "officialapi", "fixedapi",
}
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique(values: Iterable[Any], limit: int = 256) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def semantic_types(row: dict[str, Any]) -> list[str]:
    values = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip().casefold()
        if value in REPRESENTATIVE and value not in out:
            out.append(value)
    return out


def parse_probe(stdout: str) -> dict[str, Any] | None:
    for raw in reversed(stdout.splitlines()):
        text = raw.strip()
        if not text.startswith("{"):
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def fixture_map() -> dict[str, dict[str, Any]]:
    corpus = load(CORPUS)
    rows = {
        str(row.get("slug") or ""): row.get("fixture")
        for row in corpus.get("fixtures") or []
        if isinstance(row, dict) and isinstance(row.get("fixture"), dict)
    }
    fixtures: dict[str, dict[str, Any]] = {}
    for media_type, slug in REPRESENTATIVE.items():
        fixture = rows.get(slug)
        if not isinstance(fixture, dict):
            raise RuntimeError(f"missing representative fixture: {slug}")
        fixtures[media_type] = fixture
    return fixtures


def build_tasks() -> tuple[list[dict[str, Any]], int]:
    manifest = load(MANIFEST)
    fixtures = fixture_map()
    tasks: list[dict[str, Any]] = []
    provider_count = 0
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        filename = str(row.get("filename") or "").strip()
        if not provider_id or not filename or not (ROOT / filename).is_file():
            continue
        provider_count += 1
        for media_type in semantic_types(row):
            tasks.append({
                "provider_id": provider_id,
                "provider_name": str(row.get("name") or row.get("id") or provider_id),
                "filename": filename,
                "semantic_type": media_type,
                "fixture": fixtures[media_type],
            })
    return tasks, provider_count


def provider_fetch(row: dict[str, Any]) -> bool:
    url = str(row.get("final_url") or row.get("url") or "")
    try:
        host = (urllib.parse.urlsplit(url).hostname or "").casefold()
    except ValueError:
        host = ""
    return host not in {"api.themoviedb.org", "www.themoviedb.org"}


def run_task(task: dict[str, Any], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    base = {
        "provider_id": task["provider_id"],
        "provider_name": task["provider_name"],
        "semantic_type": task["semantic_type"],
        "fixture_title": str(task["fixture"].get("title") or ""),
    }
    command = [
        "node",
        str(PROBE),
        str(ROOT / task["filename"]),
        json.dumps(task["fixture"], ensure_ascii=False, separators=(",", ":")),
        "{}",
    ]
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        return {**base, "status": "timeout", "raw": 0, "playable": 0, "verified": 0, "fetches": [], "duration_ms": round((time.monotonic() - started) * 1000)}
    except Exception as exc:
        return {**base, "status": "probe_error", "raw": 0, "playable": 0, "verified": 0, "fetches": [], "error": type(exc).__name__, "duration_ms": round((time.monotonic() - started) * 1000)}

    probe = parse_probe(proc.stdout)
    if probe is None:
        marker = "missing_tmdb_credential" if "missing_tmdb_credential" in proc.stderr else "invalid_probe_output"
        return {**base, "status": marker, "raw": 0, "playable": 0, "verified": 0, "fetches": [], "duration_ms": round((time.monotonic() - started) * 1000)}

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

    route_validation = probe.get("route_validation") if isinstance(probe.get("route_validation"), dict) else {}
    fetches = [row for row in route_validation.get("fetches") or [] if isinstance(row, dict) and provider_fetch(row)]
    return {
        **base,
        "status": status,
        "raw": raw,
        "playable": playable,
        "verified": verified,
        "contradictions": contradictions,
        "fetches": fetches[:100],
        "duration_ms": int(probe.get("duration_ms") or round((time.monotonic() - started) * 1000)),
    }


def route_parts(route: str) -> tuple[str, dict[str, list[str]]] | None:
    raw = str(route or "").strip()
    if not raw:
        return None
    try:
        if raw.startswith(("http://", "https://")):
            parsed = urllib.parse.urlsplit(raw)
        else:
            parsed = urllib.parse.urlsplit("https://candidate.invalid" + (raw if raw.startswith("/") else "/" + raw))
    except ValueError:
        return None
    path = parsed.path or "/"
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    return path, query


def path_regex(template: str) -> re.Pattern[str]:
    pieces: list[str] = []
    cursor = 0
    for match in PLACEHOLDER_RE.finditer(template):
        pieces.append(re.escape(template[cursor:match.start()]))
        pieces.append(r"[^/?#&]+")
        cursor = match.end()
    pieces.append(re.escape(template[cursor:]))
    return re.compile(r"^" + "".join(pieces) + r"/?$")


def route_matches_url(route: str, actual_url: str) -> bool:
    candidate = route_parts(route)
    if candidate is None:
        return False
    try:
        actual = urllib.parse.urlsplit(str(actual_url or ""))
    except ValueError:
        return False
    candidate_path, candidate_query = candidate
    if not path_regex(candidate_path).match(actual.path or "/"):
        return False
    actual_query = urllib.parse.parse_qs(actual.query, keep_blank_values=True)
    for key, expected_values in candidate_query.items():
        if key not in actual_query:
            return False
        actual_values = actual_query.get(key) or []
        for expected in expected_values:
            if not expected or PLACEHOLDER_RE.search(expected):
                continue
            if expected not in actual_values:
                return False
    return True


def routeish_key(key: str) -> bool:
    compact = str(key or "").strip().replace("-", "").replace("_", "").casefold()
    if not compact or compact in ROUTE_FIELD_EXCLUDED:
        return False
    return compact.endswith(ROUTE_FIELD_SUFFIXES)


def iter_recipe_routes(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if routeish_key(str(key)):
                if isinstance(child, str) and child.strip():
                    yield child.strip()
                elif isinstance(child, list):
                    for item in child:
                        if isinstance(item, str) and item.strip():
                            yield item.strip()
            if isinstance(child, (dict, list)):
                yield from iter_recipe_routes(child)
    elif isinstance(value, list):
        for child in value:
            if isinstance(child, (dict, list)):
                yield from iter_recipe_routes(child)


def live_evidence(fetch: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    return {
        "semanticType": task.get("semantic_type"),
        "fixtureTitle": task.get("fixture_title"),
        "url": fetch.get("url"),
        "finalUrl": fetch.get("final_url"),
        "method": fetch.get("method"),
        "status": int(fetch.get("status") or 0),
        "contentType": fetch.get("content_type"),
        "headerNames": list(fetch.get("header_names") or []),
        "bodyKind": fetch.get("body_kind"),
        "bodyFields": list(fetch.get("body_fields") or []),
        "durationMs": int(fetch.get("duration_ms") or 0),
        "error": fetch.get("error"),
    }


def success(fetch: dict[str, Any]) -> bool:
    status = int(fetch.get("status") or 0)
    return not fetch.get("error") and 200 <= status < 400


def prepare_candidates(knowledge_path: Path, overrides_path: Path) -> dict[str, int]:
    knowledge = load(knowledge_path)
    overrides = load(overrides_path)
    restored_routes = 0
    restored_recipes = 0
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        candidate_data = model.get("candidateRouteData") if isinstance(model.get("candidateRouteData"), list) else None
        candidate_routes = model.get("candidateRoutes") if isinstance(model.get("candidateRoutes"), list) else None
        if candidate_data is not None:
            model["routeData"] = copy.deepcopy(candidate_data)
            restored_routes += len(candidate_data)
        if candidate_routes is not None:
            model["routes"] = list(candidate_routes)
        if isinstance(model.get("candidateApiRecipe"), dict):
            model["apiRecipe"] = copy.deepcopy(model["candidateApiRecipe"])
            restored_recipes += 1
        row["model"] = model

        patch = patches.get(provider_id)
        if not isinstance(patch, dict):
            continue
        if isinstance(patch.get("candidate_learned_routes"), list):
            patch["learned_routes"] = list(patch["candidate_learned_routes"])
        if isinstance(patch.get("candidate_api_recipe"), dict):
            patch["api_recipe"] = copy.deepcopy(patch["candidate_api_recipe"])
    write(knowledge_path, knowledge)
    write(overrides_path, overrides)
    return {"restoredRoutes": restored_routes, "restoredRecipes": restored_recipes}


def recipe_is_live(recipe: dict[str, Any], live_routes: set[str]) -> bool:
    routes = unique(iter_recipe_routes(recipe), 192)
    if not routes:
        return True
    return all(route in live_routes for route in routes)


def validate_and_promote(
    knowledge: dict[str, Any],
    overrides: dict[str, Any],
    task_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    if len(providers) != EXPECTED:
        raise ValueError(f"live route validation expects {EXPECTED} providers, got {len(providers)}")
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in task_rows:
        by_provider[str(task.get("provider_id") or "")].append(task)

    provider_reports: list[dict[str, Any]] = []
    totals = Counter()
    providers_with_http: list[str] = []
    providers_with_live_routes: list[str] = []
    playable_verified: list[str] = []

    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        knowledge_row = row.get("knowledge") if isinstance(row.get("knowledge"), dict) else {}
        tasks = by_provider.get(provider_id, [])
        fetch_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for task in tasks:
            for fetch in task.get("fetches") or []:
                if isinstance(fetch, dict):
                    fetch_rows.append((fetch, task))

        if fetch_rows:
            providers_with_http.append(provider_id)
        if any(task.get("status") == "playable_verified" for task in tasks):
            playable_verified.append(provider_id)

        current_route_data = model.get("routeData") if isinstance(model.get("routeData"), list) else []
        candidate_route_data = copy.deepcopy(current_route_data)
        candidate_routes = unique(model.get("routes") or [item.get("route") for item in current_route_data if isinstance(item, dict)], 192)
        model["candidateRoutes"] = candidate_routes

        live_rows: list[dict[str, Any]] = []
        enriched_candidates: list[dict[str, Any]] = []
        attempted = blocked = failed = unexecuted = live_count = 0
        matched_request_indexes: set[int] = set()

        for raw in candidate_route_data:
            if not isinstance(raw, dict):
                continue
            candidate = copy.deepcopy(raw)
            route = str(candidate.get("route") or "").strip()
            matches: list[tuple[dict[str, Any], dict[str, Any], int]] = []
            for index, (fetch, task) in enumerate(fetch_rows):
                actual_url = str(fetch.get("final_url") or fetch.get("url") or "")
                if route and route_matches_url(route, actual_url):
                    matches.append((fetch, task, index))
                    matched_request_indexes.add(index)

            candidate["staticCallEvidence"] = bool(candidate.get("executedEvidence"))
            candidate["executedEvidence"] = False
            candidate["httpUsed"] = False
            candidate.pop("liveEvidence", None)
            candidate.pop("attemptEvidence", None)

            successful = [(fetch, task, idx) for fetch, task, idx in matches if success(fetch)]
            if matches:
                attempted += 1
                candidate["attemptEvidence"] = [live_evidence(fetch, task) for fetch, task, _idx in matches[:12]]
            if successful:
                live_count += 1
                candidate["validationState"] = "live-validated"
                candidate["executedEvidence"] = True
                candidate["httpUsed"] = True
                candidate["liveEvidence"] = [live_evidence(fetch, task) for fetch, task, _idx in successful[:12]]
                strongest, _task, _index = successful[0]
                candidate["method"] = str(strongest.get("method") or candidate.get("method") or "GET").upper()
                candidate["observedHeaderNames"] = list(strongest.get("header_names") or [])
                candidate["observedBodyKind"] = strongest.get("body_kind")
                candidate["observedBodyFields"] = list(strongest.get("body_fields") or [])
                candidate["observedContentType"] = strongest.get("content_type")
                live_rows.append(copy.deepcopy(candidate))
            elif matches:
                statuses = {int(fetch.get("status") or 0) for fetch, _task, _idx in matches}
                if statuses & {401, 403, 407, 429}:
                    blocked += 1
                    candidate["validationState"] = "blocked-live"
                else:
                    failed += 1
                    candidate["validationState"] = "failed-live"
            else:
                unexecuted += 1
                candidate["validationState"] = "candidate-not-executed"
            enriched_candidates.append(candidate)

        live_routes = unique([item.get("route") for item in live_rows], 192)
        live_route_set = set(live_routes)
        if live_routes:
            providers_with_live_routes.append(provider_id)

        unmatched = []
        for index, (fetch, task) in enumerate(fetch_rows):
            if index in matched_request_indexes:
                continue
            unmatched.append(live_evidence(fetch, task))

        model["candidateRouteData"] = enriched_candidates
        model["candidateRoutes"] = candidate_routes
        model["routeData"] = live_rows
        model["routes"] = live_routes

        if isinstance(model.get("apiRecipe"), dict):
            if not isinstance(model.get("candidateApiRecipe"), dict):
                model["candidateApiRecipe"] = copy.deepcopy(model["apiRecipe"])
            if not recipe_is_live(model["apiRecipe"], live_route_set):
                model.pop("apiRecipe", None)

        model["observedLiveRequests"] = unmatched[:40]
        model["routeRecognition"] = {
            "version": 2,
            "status": "live-validated" if live_count and live_count == len(enriched_candidates) else ("partially-live-validated" if live_count else "candidate-only"),
            "candidateRouteCount": len(enriched_candidates),
            "attemptedRouteCount": attempted,
            "liveValidatedRouteCount": live_count,
            "blockedRouteCount": blocked,
            "failedRouteCount": failed,
            "unexecutedCandidateRouteCount": unexecuted,
            "providerJavaScriptExecuted": True,
            "liveTraversalRequiredForPromotion": True,
            "staticEvidenceIsNotHttpProof": True,
        }

        recognized = knowledge_row.get("recognizedContract") if isinstance(knowledge_row.get("recognizedContract"), dict) else {}
        recognized["requests"] = copy.deepcopy(live_rows)
        recognized["candidateRequests"] = copy.deepcopy(enriched_candidates)
        recognized["candidateRouteCount"] = len(enriched_candidates)
        recognized["attemptedRouteCount"] = attempted
        recognized["liveValidatedRouteCount"] = live_count
        recognized["httpProvenRouteCount"] = live_count
        recognized["providerJavaScriptExecuted"] = True
        recognized["liveTraversalRequiredForPromotion"] = True
        recognized["staticEvidenceIsNotHttpProof"] = True
        knowledge_row["recognizedContract"] = recognized
        row["model"] = model
        row["knowledge"] = knowledge_row

        patch = patches.get(provider_id)
        if isinstance(patch, dict):
            if isinstance(patch.get("learned_routes"), list) and not isinstance(patch.get("candidate_learned_routes"), list):
                patch["candidate_learned_routes"] = list(patch.get("learned_routes") or [])
            candidate_learned = patch.get("candidate_learned_routes") if isinstance(patch.get("candidate_learned_routes"), list) else patch.get("learned_routes") or []
            patch["learned_routes"] = [str(route) for route in candidate_learned if str(route) in live_route_set]

            if isinstance(patch.get("api_recipe"), dict) and not isinstance(patch.get("candidate_api_recipe"), dict):
                patch["candidate_api_recipe"] = copy.deepcopy(patch["api_recipe"])
            candidate_recipe = patch.get("candidate_api_recipe") if isinstance(patch.get("candidate_api_recipe"), dict) else patch.get("api_recipe")
            if isinstance(candidate_recipe, dict):
                if recipe_is_live(candidate_recipe, live_route_set):
                    patch["api_recipe"] = copy.deepcopy(candidate_recipe)
                else:
                    patch.pop("api_recipe", None)

        totals["candidates"] += len(enriched_candidates)
        totals["attempted"] += attempted
        totals["live"] += live_count
        totals["blocked"] += blocked
        totals["failed"] += failed
        totals["unexecuted"] += unexecuted
        totals["provider_fetches"] += len(fetch_rows)
        totals["unmatched_live_requests"] += len(unmatched)

        provider_reports.append({
            "providerId": provider_id,
            "candidateRouteCount": len(enriched_candidates),
            "attemptedRouteCount": attempted,
            "liveValidatedRouteCount": live_count,
            "blockedRouteCount": blocked,
            "failedRouteCount": failed,
            "unexecutedCandidateRouteCount": unexecuted,
            "providerRequestCount": len(fetch_rows),
            "unmatchedObservedRequestCount": len(unmatched),
            "playableVerified": provider_id in playable_verified,
            "tasks": [{k: v for k, v in task.items() if k != "fetches"} for task in tasks],
            "candidateRoutes": enriched_candidates,
            "unmatchedObservedRequests": unmatched[:40],
        })

    knowledge["liveRouteValidation"] = {
        "schemaVersion": 1,
        "method": "materialized-provider-runtime-live-traversal",
        "candidateRoutesAreExecutableAuthority": False,
        "staticEvidenceIsHttpProof": False,
        "providerJavaScriptExecuted": True,
        "providerCount": len(providers),
        "candidateRouteCount": totals["candidates"],
        "attemptedRouteCount": totals["attempted"],
        "liveValidatedRouteCount": totals["live"],
        "blockedRouteCount": totals["blocked"],
        "failedRouteCount": totals["failed"],
        "unexecutedCandidateRouteCount": totals["unexecuted"],
    }

    report = {
        "schemaVersion": 1,
        "environment": "node-materialized-provider-live-route-traversal-with-tmdb-context",
        "providerCount": len(providers),
        "taskCount": len(task_rows),
        "candidateRouteCount": totals["candidates"],
        "attemptedRouteCount": totals["attempted"],
        "liveValidatedRouteCount": totals["live"],
        "blockedRouteCount": totals["blocked"],
        "failedRouteCount": totals["failed"],
        "unexecutedCandidateRouteCount": totals["unexecuted"],
        "providerRequestCount": totals["provider_fetches"],
        "unmatchedObservedRequestCount": totals["unmatched_live_requests"],
        "providersWithProviderHttpCount": len(set(providers_with_http)),
        "providersWithLiveValidatedRouteCount": len(set(providers_with_live_routes)),
        "playableVerifiedProviderCount": len(set(playable_verified)),
        "providersWithProviderHttp": sorted(set(providers_with_http)),
        "providersWithLiveValidatedRoutes": sorted(set(providers_with_live_routes)),
        "playableVerifiedProviders": sorted(set(playable_verified)),
        "statusCounts": dict(sorted(Counter(str(row.get("status") or "unknown") for row in task_rows).items())),
        "providers": sorted(provider_reports, key=lambda item: item["providerId"]),
    }
    return knowledge, overrides, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Provider v3 route candidates by real runtime traversal")
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--prepare-candidates", action="store_true")
    parser.add_argument("--workers", type=int, default=int(os.environ.get("NIAKVIO_ROUTE_VALIDATION_WORKERS", "12")))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("NIAKVIO_ROUTE_VALIDATION_TIMEOUT", "50")))
    args = parser.parse_args()

    knowledge_path = args.knowledge.resolve()
    overrides_path = args.overrides.resolve()
    if args.prepare_candidates:
        summary = prepare_candidates(knowledge_path, overrides_path)
        print(
            "FIELD_PROVIDER_ROUTE_CANDIDATES_PREPARED "
            f"routes={summary['restoredRoutes']} recipes={summary['restoredRecipes']}"
        )
        return 0

    if not (str(os.environ.get("TMDB_API_KEY") or "").strip() or str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        raise SystemExit("TMDB_API_KEY or TMDB_ACCESS_TOKEN is required for live route validation")
    if not PROBE.is_file():
        raise SystemExit(f"missing live route probe: {PROBE}")

    tasks, provider_count = build_tasks()
    if provider_count != EXPECTED:
        raise SystemExit(f"manifest provider count={provider_count}, expected={EXPECTED}")
    rows: list[dict[str, Any]] = []
    workers = max(1, min(int(args.workers), 20))
    timeout = max(20, min(int(args.timeout), 120))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_task, task, timeout) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())

    knowledge = load(knowledge_path)
    overrides = load(overrides_path)
    knowledge, overrides, report = validate_and_promote(knowledge, overrides, rows)
    write(knowledge_path, knowledge)
    write(overrides_path, overrides)
    write(args.output.resolve(), report)

    print(
        "FIELD_PROVIDER_ROUTE_LIVE_VALIDATION "
        f"providers={report['providerCount']} tasks={report['taskCount']} "
        f"candidates={report['candidateRouteCount']} attempted={report['attemptedRouteCount']} "
        f"live={report['liveValidatedRouteCount']} blocked={report['blockedRouteCount']} "
        f"failed={report['failedRouteCount']} unexecuted={report['unexecutedCandidateRouteCount']} "
        f"provider_http={report['providersWithProviderHttpCount']} "
        f"providers_live={report['providersWithLiveValidatedRouteCount']} "
        f"playable_verified={report['playableVerifiedProviderCount']}"
    )
    if report["providersWithProviderHttpCount"] == 0:
        raise SystemExit("live route validation produced zero provider HTTP requests; refusing false validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
