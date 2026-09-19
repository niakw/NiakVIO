#!/usr/bin/env python3
"""Persist provider/lane proof fixtures and clean catalogue misses across census runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rotating_corpus import all_fixtures, canonical_lane

GOOD = "playable_verified"
TECHNICAL_STAGES = {
    "gate_runtime_plan_missing",
    "gate_source_family_unknown",
    "provider_zero_before_provider_network",
    "provider_runtime_hook_exception",
    "source_plan_core_metadata_leak",
    "runtime_error",
    "audit_error",
    "invalid_probe_output",
    "missing_tmdb_credential",
}
NETWORK_STAGES = {
    "provider_network_http_error",
    "provider_network_exception",
    "timeout",
}


def load(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else default


def fixture_key(fixture: dict[str, Any]) -> str:
    return "|".join([
        str(fixture.get("slug") or ""),
        str(fixture.get("tmdbId") or ""),
        str(fixture.get("mediaType") or fixture.get("category") or ""),
        str(fixture.get("season") or 0),
        str(fixture.get("episode") or 0),
    ])


def clean_fixture(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    allowed = ("slug", "tmdbId", "mediaType", "category", "title", "year", "season", "episode", "animeMovie")
    return {key: value.get(key) for key in allowed if value.get(key) is not None}


def fixture_lookup() -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for fixture in all_fixtures():
        title = str(fixture.get("title") or fixture.get("label") or "").strip().casefold()
        if not title:
            continue
        lane = canonical_lane(fixture)
        out.setdefault((lane, title), clean_fixture(fixture))
    return out


def upsert_front(rows: list[dict[str, Any]], item: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    key = fixture_key(item.get("fixture") or {})
    kept = [row for row in rows if fixture_key(row.get("fixture") or {}) != key]
    return [item, *kept][:limit]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("report", type=Path)
    p.add_argument("--history", type=Path, default=Path("automation/provider-census-proof-history.json"))
    p.add_argument("--run-id", default="")
    p.add_argument("--sha", default="")
    args = p.parse_args()

    report = load(args.report, {})
    lookup = fixture_lookup()
    history = load(args.history, {"schemaVersion": 1, "providers": {}})
    history["schemaVersion"] = 1
    providers = history.setdefault("providers", {})
    if not isinstance(providers, dict):
        providers = {}
        history["providers"] = providers

    for row in report.get("rows") or []:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider_id") or "").strip().casefold()
        lane = str(row.get("semantic_type") or "").strip().casefold()
        if not provider or not lane:
            continue
        provider_state = providers.setdefault(provider, {"lanes": {}})
        lanes = provider_state.setdefault("lanes", {})
        lane_state = lanes.setdefault(lane, {
            "proofs": [],
            "misses": [],
            "consecutiveTechnicalRuns": 0,
            "consecutiveNetworkRuns": 0,
        })
        proofs = lane_state.get("proofs") if isinstance(lane_state.get("proofs"), list) else []
        misses = lane_state.get("misses") if isinstance(lane_state.get("misses"), list) else []

        samples = row.get("samples") if isinstance(row.get("samples"), list) else []
        for sample in samples:
            if not isinstance(sample, dict):
                continue
            fixture = clean_fixture(sample.get("fixture"))
            if not fixture:
                title = str(sample.get("fixture_title") or "").strip().casefold()
                fixture = dict(lookup.get((lane, title)) or {})
            if not fixture:
                continue
            status = str(sample.get("status") or "")
            stage = str(sample.get("debug_stage") or "")
            verified = int(sample.get("verified") or 0)
            contradictions = int(sample.get("contradictions") or 0)
            if status == GOOD and verified > 0 and contradictions == 0:
                proofs = upsert_front(proofs, {
                    "fixture": fixture,
                    "runId": str(args.run_id),
                    "sha": str(args.sha),
                }, limit=4)
                miss_key = fixture_key(fixture)
                misses = [item for item in misses if fixture_key(item.get("fixture") or {}) != miss_key]
            elif stage == "provider_network_zero_result":
                misses = upsert_front(misses, {
                    "fixture": fixture,
                    "runId": str(args.run_id),
                    "sha": str(args.sha),
                }, limit=256)

        current_stage = str(row.get("debug_stage") or "")
        if str(row.get("status") or "") == GOOD and int(row.get("verified") or 0) > 0:
            lane_state["consecutiveTechnicalRuns"] = 0
            lane_state["consecutiveNetworkRuns"] = 0
        elif current_stage in TECHNICAL_STAGES:
            lane_state["consecutiveTechnicalRuns"] = int(lane_state.get("consecutiveTechnicalRuns") or 0) + 1
            lane_state["consecutiveNetworkRuns"] = 0
        elif current_stage in NETWORK_STAGES:
            # A blocked/failed transport is not evidence that provider-owned JS
            # is structurally broken. Keep its streak separate so the renderer
            # can never manufacture JS FULLY BROKEN from repeated 403/DNS/timeouts.
            lane_state["consecutiveTechnicalRuns"] = 0
            lane_state["consecutiveNetworkRuns"] = int(lane_state.get("consecutiveNetworkRuns") or 0) + 1
        elif current_stage == "provider_network_zero_result":
            lane_state["consecutiveTechnicalRuns"] = 0
            lane_state["consecutiveNetworkRuns"] = 0

        lane_state["proofs"] = proofs
        lane_state["misses"] = misses
        lane_state["lastStatus"] = str(row.get("status") or "")
        lane_state["lastStage"] = current_stage
        lane_state["lastRunId"] = str(args.run_id)
        lane_state["lastSha"] = str(args.sha)

    history["lastRunId"] = str(args.run_id)
    history["lastSha"] = str(args.sha)
    args.history.parent.mkdir(parents=True, exist_ok=True)
    args.history.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PROVIDER_CENSUS_PROOF_HISTORY_WRITTEN output={args.history}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
