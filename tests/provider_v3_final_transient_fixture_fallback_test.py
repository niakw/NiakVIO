#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_adaptive_live_retry_v1 as adaptive  # noqa: E402
import upgrade_provider_final_transient_fixture_fallback_v1 as migration  # noqa: E402

adaptive.patch()
adaptive.validate()
migration.patch()
migration.validate()

import reconstruct_provider_v3_sequential_live as sequential  # noqa: E402

sequential.provider_fetch = lambda fetch: bool(fetch.get("provider", True))
sequential.success = lambda fetch: 200 <= int(fetch.get("status") or 0) < 400


def fake_evaluate(_provider_id, _model, task_rows, _minimum):
    required = {"movie"}
    validated = {
        str(row.get("semantic_type") or "").strip().casefold()
        for row in task_rows
        if row.get("status") == "playable_verified"
        and any(200 <= int(fetch.get("status") or 0) < 400 for fetch in row.get("fetches") or [])
    }
    request_count = sum(len(row.get("fetches") or []) for row in task_rows)
    live = sum(
        1 for row in task_rows for fetch in row.get("fetches") or []
        if 200 <= int(fetch.get("status") or 0) < 400
    )
    ratio = len(validated) / len(required)
    return {
        "requiredTypes": sorted(required),
        "validatedTypes": sorted(validated),
        "missingTypes": sorted(required - validated),
        "declaredTypeRouteEvidence": {},
        "declaredTypeCoverageRatio": ratio,
        "effectiveCoverageRatio": ratio,
        "typeComplete": required <= validated,
        "directOutputOnly": False,
        "providerSuccessHttp": bool(validated),
        "providerRequestCount": request_count,
        "liveValidatedRouteCount": live,
    }


sequential.evaluate_provider = fake_evaluate

primary = {
    "fixture_slug": "primary-movie",
    "semantic_type": "movie",
    "fixture": {"tmdbId": "1", "mediaType": "movie", "title": "Primary"},
}
alternate = {
    "fixture_slug": "alternate-movie",
    "semantic_type": "movie",
    "fixture": {"tmdbId": "2", "mediaType": "movie", "title": "Alternate"},
}
provider = {"provider_id": "transient-provider", "tasks": [copy.deepcopy(primary), copy.deepcopy(alternate)]}
model = {"routeData": [], "routes": [], "canonicalSupportedTypes": ["movie"]}

calls: list[str] = []
primary_attempt = 0


def transient_then_alternate(task, _timeout):
    global primary_attempt
    slug = str(task.get("fixture_slug") or "")
    calls.append(slug)
    if slug == "primary-movie":
        primary_attempt += 1
        if primary_attempt == 1:
            return {"status": "timeout", "semantic_type": "movie", "fetches": []}
        if primary_attempt == 2:
            return {
                "status": "no_streams", "semantic_type": "movie",
                "fetches": [{"provider": True, "status": 500, "url": "https://p.test/a"}],
            }
        return {
            "status": "no_streams", "semantic_type": "movie",
            "fetches": [{"provider": True, "status": 525, "url": "https://p.test/a"}],
        }
    return {
        "status": "playable_verified", "semantic_type": "movie",
        "fetches": [{"provider": True, "status": 200, "url": "https://p.test/b"}],
    }


sequential.run_task = transient_then_alternate
proof = sequential.prove_final_bundle(
    provider, copy.deepcopy(model), [copy.deepcopy(primary)],
    "providers/transient-provider-final.js", 0.75, 20,
)
assert proof["verified"] is True, proof
assert proof["validatedTypes"] == ["movie"], proof
assert calls == ["primary-movie", "primary-movie", "primary-movie", "alternate-movie"], calls

# Contradictory selected-fixture evidence must stay fail-closed: no alternate
# fixture is allowed to hide a deterministic wrong-content final regression.
calls.clear()


def wrong_content(task, _timeout):
    slug = str(task.get("fixture_slug") or "")
    calls.append(slug)
    return {
        "status": "wrong_content", "semantic_type": "movie",
        "fetches": [{"provider": True, "status": 200, "url": "https://p.test/wrong"}],
    }


sequential.run_task = wrong_content
proof = sequential.prove_final_bundle(
    provider, copy.deepcopy(model), [copy.deepcopy(primary)],
    "providers/transient-provider-final.js", 0.75, 20,
)
assert proof["verified"] is False, proof
assert calls == ["primary-movie"], calls

print(
    "PROVIDER_V3_FINAL_TRANSIENT_FIXTURE_FALLBACK_TEST_OK "
    "transient_exhaustion=alternate_fixture contradictory_wrong_content=fail_closed"
)
