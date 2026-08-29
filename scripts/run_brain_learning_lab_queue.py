#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def remaining_ms(deadline_ms: int) -> int:
    return max(0, deadline_ms - int(time.time() * 1000))


def manifest_rows(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = norm(row.get("id") or row.get("name"))
        if provider_id:
            out[provider_id] = row
    return out


def declared_type(row: dict[str, Any]) -> str:
    raw = row.get("supportedTypes") or []
    if isinstance(raw, str):
        raw = [raw]
    first = norm(raw[0] if raw else "movie")
    if first in {"anime", "animation"}:
        return "anime"
    if first in {"tv", "series", "serie"}:
        return "tv"
    return "movie"


def fixture_category(item: dict[str, Any]) -> str:
    fixture = item.get("fixture") if isinstance(item.get("fixture"), dict) else {}
    category = norm(fixture.get("category") or fixture.get("mediaType") or "movie")
    if category == "anime":
        return "anime"
    if category == "tv":
        return "tv"
    return "movie"


def choose_fixture(
    provider: str,
    media_type: str,
    fixture_config: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any] | None:
    fixtures = [item for item in fixture_config.get("fixtures") or [] if isinstance(item, dict)]
    compatible = []
    fallback = []
    for item in fixtures:
        if fixture_category(item) != media_type:
            continue
        providers = {norm(value) for value in item.get("providers") or [] if norm(value)}
        fallback.append(item)
        if not providers or provider in providers:
            compatible.append(item)
    pool = compatible or fallback
    if not pool:
        return None

    scheduler = previous.get("learningScheduler") if isinstance(previous.get("learningScheduler"), dict) else {}
    history = scheduler.get("fixtureHistory") if isinstance(scheduler.get("fixtureHistory"), dict) else {}
    used = [str(value) for value in history.get(provider) or [] if str(value)]
    by_slug = {str(item.get("slug") or ""): item for item in pool}
    ordered_slugs = [str(item.get("slug") or "") for item in pool if str(item.get("slug") or "")]
    unseen = [slug for slug in ordered_slugs if slug not in set(used)]
    if unseen:
        return by_slug[unseen[0]]
    if ordered_slugs:
        return by_slug[ordered_slugs[len(used) % len(ordered_slugs)]]
    return pool[0]


def summarize_provider(report: dict[str, Any]) -> dict[str, Any]:
    provider = (report.get("providers") or [{}])[0]
    clients = provider.get("clients") if isinstance(provider.get("clients"), dict) else {}
    client_rows = {}
    hidden_failure = False
    for name in ("tv", "desktop", "mobile"):
        row = clients.get(name) if isinstance(clients.get(name), dict) else {}
        verdict = str(row.get("verdict") or "missing")
        unplayable = int(row.get("unplayable_probe_count") or 0)
        inconclusive = int(row.get("inconclusive_probe_count") or 0)
        complete = bool(row.get("probe_coverage_complete", False))
        if verdict != "playable" or unplayable > 0 or not complete:
            hidden_failure = True
        client_rows[name] = {
            "verdict": verdict,
            "runtimeStreamCount": int(row.get("runtime_stream_count") or 0),
            "probedStreams": int(row.get("probed_stream_count") or 0),
            "playableProbes": int(row.get("playable_probe_count") or 0),
            "unplayableProbes": unplayable,
            "inconclusiveProbes": inconclusive,
            "probeCoverageComplete": complete,
            "identityStatus": row.get("identity_status"),
        }
    return {
        "clients": client_rows,
        "hiddenFailure": hidden_failure,
        "policy": report.get("policy") if isinstance(report.get("policy"), dict) else {},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    parser.add_argument("--state", type=Path, default=Path("brain-learning-input/previous.json"))
    parser.add_argument("--fixture-config", type=Path, default=Path(".github/triggers/nuvio-client-lab.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--deadline-epoch-ms", type=int, default=0)
    parser.add_argument("--stream-safety-cap", type=int, default=40)
    args = parser.parse_args()

    queue = load(args.queue, {})
    manifest = load(args.manifest, {})
    previous = load(args.state, {})
    fixture_config = load(args.fixture_config, {})
    rows = manifest_rows(manifest)
    deadline_ms = int(
        args.deadline_epoch_ms
        or os.environ.get("NUVIO_BRAIN_DEADLINE_EPOCH_MS")
        or (int(time.time() * 1000) + 55 * 60 * 1000)
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    completed: list[str] = []
    pending: list[str] = []
    observations: list[dict[str, Any]] = []
    fixture_updates: dict[str, list[str]] = {}

    scheduler = previous.get("learningScheduler") if isinstance(previous.get("learningScheduler"), dict) else {}
    old_history = scheduler.get("fixtureHistory") if isinstance(scheduler.get("fixtureHistory"), dict) else {}

    provider_rows = [row for row in queue.get("providers") or [] if isinstance(row, dict)]
    for index, queue_row in enumerate(provider_rows):
        provider = norm(queue_row.get("provider"))
        if not provider or provider not in rows:
            continue
        if remaining_ms(deadline_ms) < 125_000:
            pending.extend(
                norm(row.get("provider"))
                for row in provider_rows[index:]
                if norm(row.get("provider"))
            )
            break

        media_type = declared_type(rows[provider])
        fixture_item = choose_fixture(provider, media_type, fixture_config, previous)
        if fixture_item is None:
            observations.append({
                "provider": provider,
                "status": "no_fixture_for_declared_type",
                "declaredType": media_type,
                "coreHypothesisOnly": True,
            })
            completed.append(provider)
            continue

        fixture = fixture_item.get("fixture") if isinstance(fixture_item.get("fixture"), dict) else {}
        slug = str(fixture_item.get("slug") or "")
        config = {
            "providers": [provider],
            "fixture": fixture,
            "clients": ["tv", "desktop", "mobile"],
            "probe_all_streams": True,
            "all_streams_safety_cap": max(1, min(int(args.stream_safety_cap), 200)),
            "provider_timeout_ms": 45000,
            "retry_provider_timeouts": False,
            "playback_timeout_ms": 8000,
            "require_identity_match": True,
            "blocking": False,
        }
        provider_dir = args.output_dir / provider
        provider_dir.mkdir(parents=True, exist_ok=True)
        config_path = provider_dir / "config.json"
        report_path = provider_dir / "report.json"
        md_path = provider_dir / "report.md"
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        timeout_seconds = max(30, min(115, remaining_ms(deadline_ms) // 1000 - 5))
        try:
            proc = subprocess.run(
                [
                    "node", "scripts/nuvio_client_lab.cjs",
                    "--config", str(config_path),
                    "--out", str(report_path),
                    "--markdown", str(md_path),
                ],
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            exit_code = proc.returncode
            log_tail = (proc.stdout + "\n" + proc.stderr)[-8000:]
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            log_tail = f"lab_timeout:{exc}"
        
        report = load(report_path, {}) if report_path.is_file() else {}
        summary = summarize_provider(report) if report else {
            "clients": {},
            "hiddenFailure": True,
            "policy": {},
        }
        core_status = str(queue_row.get("status") or "unknown")
        observation = {
            "provider": provider,
            "fixtureSlug": slug,
            "declaredType": media_type,
            "coreStatus": core_status,
            "coreHypothesisOnly": True,
            "labExit": exit_code,
            "hiddenFailure": bool(summary.get("hiddenFailure")),
            "hiddenFailureAgainstHealthyCore": core_status in {"healthy", "reachable"} and bool(summary.get("hiddenFailure")),
            "clients": summary.get("clients"),
            "logTail": log_tail,
        }
        observations.append(observation)
        completed.append(provider)
        history = [str(value) for value in old_history.get(provider) or [] if str(value)]
        history.append(slug)
        fixture_updates[provider] = history[-12:]

    result = {
        "schemaVersion": 1,
        "deadlineEpochMs": deadline_ms,
        "completedProviders": list(dict.fromkeys(completed)),
        "pendingProviders": list(dict.fromkeys(pending)),
        "fixtureHistoryUpdates": fixture_updates,
        "observations": observations,
        "hiddenFailureProviders": [
            row["provider"] for row in observations if row.get("hiddenFailureAgainstHealthyCore")
        ],
    }
    summary_path = args.output_dir / "learning-lab-queue-summary.json"
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_LAB_QUEUE "
        f"completed={len(result['completedProviders'])} pending={len(result['pendingProviders'])} "
        f"hidden_against_core={len(result['hiddenFailureProviders'])} remaining_ms={remaining_ms(deadline_ms)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
