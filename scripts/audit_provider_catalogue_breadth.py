#!/usr/bin/env python3
"""Broad, report-only provider catalogue census.

This complements the six-work native device corpus. It measures catalogue breadth
across the larger set of trusted fixtures already maintained in health-config.json
plus the rare/native regression fixtures. It never changes provider activation.

The report intentionally strips media endpoints. Provider retirement stays a
human/review decision: wrong-content evidence can quarantine, while runtime or
transport failures remain repair signals and unique/VF coverage is preserved.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
VF_MANIFEST = ROOT / "vf" / "manifest.json"
HEALTH_CONFIG = ROOT / "health-config.json"
NATIVE_CORPUS = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
POLICY = ROOT / ".github" / "provider-portfolio-policy.json"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_v2.cjs"
DEFAULT_OUTPUT = ROOT / "audit-output" / "provider-catalogue-breadth.json"
WORKERS = max(1, min(int(os.environ.get("NUVIO_BREADTH_WORKERS", "6")), 10))
TIMEOUT = max(30, min(int(os.environ.get("NUVIO_BREADTH_TIMEOUT", "80")), 120))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid JSON object: {path}")
    return value


def canonical_types(row: dict[str, Any]) -> set[str]:
    values = row.get("supportedTypes") or row.get("published_types") or []
    if isinstance(values, str):
        values = [values]
    return {str(value).strip().casefold() for value in values if str(value).strip()}


def fixture_identity(fixture: dict[str, Any]) -> tuple[str, str, int | None, int | None]:
    return (
        str(fixture.get("mediaType") or fixture.get("type") or "movie").casefold(),
        str(fixture.get("tmdbId") or fixture.get("id") or ""),
        int(fixture["season"]) if fixture.get("season") is not None else None,
        int(fixture["episode"]) if fixture.get("episode") is not None else None,
    )


def slug(value: str) -> str:
    text = str(value or "fixture").casefold().replace("œ", "oe")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "fixture"


def build_fixtures() -> list[dict[str, Any]]:
    health = load_json(HEALTH_CONFIG)
    native = load_json(NATIVE_CORPUS)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int | None, int | None]] = set()

    for group, fixtures in (health.get("fixtures") or {}).items():
        if not isinstance(fixtures, list):
            continue
        for index, raw in enumerate(fixtures):
            if not isinstance(raw, dict):
                continue
            fixture = dict(raw)
            identity = fixture_identity(fixture)
            if not identity[1] or identity in seen:
                continue
            seen.add(identity)
            rows.append(
                {
                    "key": f"health-{slug(str(group))}-{index + 1}-{slug(str(fixture.get('label') or fixture.get('title') or identity[1]))}",
                    "group": str(group).casefold(),
                    "source": "health-config",
                    "fixture": fixture,
                }
            )

    for native_row in native.get("fixtures") or []:
        if not isinstance(native_row, dict) or not isinstance(native_row.get("fixture"), dict):
            continue
        fixture = dict(native_row["fixture"])
        identity = fixture_identity(fixture)
        if not identity[1] or identity in seen:
            continue
        seen.add(identity)
        category = str(fixture.get("category") or fixture.get("mediaType") or "movie").casefold()
        rows.append(
            {
                "key": f"native-{slug(str(native_row.get('slug') or fixture.get('title') or identity[1]))}",
                "group": category,
                "source": "native-corpus",
                "fixture": fixture,
            }
        )

    return rows


def group_relevant(types: set[str], group: str) -> bool:
    group = str(group).casefold()
    if group == "movie":
        return "movie" in types
    if group == "tv":
        return "tv" in types
    if group == "anime":
        return "anime" in types
    if group == "anime_movie":
        return "anime" in types or "movie" in types
    return str(group) in types


def build_plan() -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    manifest = load_json(MANIFEST)
    vf_manifest = load_json(VF_MANIFEST)
    fixtures = build_fixtures()
    vf_ids = {
        str(row.get("id") or "").strip().casefold()
        for row in vf_manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    tasks: list[dict[str, Any]] = []
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        filename = str(row.get("filename") or "").strip()
        if not provider_id or not filename or not (ROOT / filename).is_file():
            continue
        types = canonical_types(row)
        identity = {
            "provider_id": provider_id,
            "provider_name": str(row.get("name") or row.get("id") or provider_id),
            "enabled": bool(row.get("enabled")),
            "vf_declared": provider_id in vf_ids,
            "supported_types": sorted(types),
        }
        for fixture_row in fixtures:
            if not group_relevant(types, fixture_row["group"]):
                continue
            tasks.append(
                {
                    "identity": identity,
                    "filename": filename,
                    "fixture_key": fixture_row["key"],
                    "fixture_group": fixture_row["group"],
                    "fixture_source": fixture_row["source"],
                    "fixture": fixture_row["fixture"],
                }
            )
    return tasks, fixtures, vf_ids


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


def normalize(value: Any) -> str:
    import unicodedata

    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.casefold().strip()


def french_audio_evidence(row: dict[str, Any]) -> bool:
    language = normalize(row.get("language"))
    labels = normalize(f"{row.get('title') or ''} {row.get('name') or ''} {language}")
    if re.search(r"\bvostfr\b|\bvost\b|\bsub(?:bed|title|titles)?\b|sous[- ]?titr", labels):
        return False
    if language in {"fr", "fr-fr", "fra", "fre", "french", "francais", "vf", "truefrench"}:
        return True
    return bool(re.search(r"\b(?:truefrench|vf|french audio|audio fr|audio francais|francais)\b", labels))


def run_probe(task: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    command = [
        "node",
        str(PROBE),
        str(ROOT / task["filename"]),
        json.dumps(task["fixture"], ensure_ascii=False, separators=(",", ":")),
        "{}",
    ]
    base = {
        **task["identity"],
        "fixture_key": task["fixture_key"],
        "fixture_group": task["fixture_group"],
        "fixture_source": task["fixture_source"],
        "fixture_title": str(task["fixture"].get("title") or task["fixture"].get("label") or ""),
        "fixture_year": task["fixture"].get("year"),
    }
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            **base,
            "status": "timeout",
            "duration_ms": round((time.monotonic() - started) * 1000),
            "raw_stream_count": 0,
            "playable_stream_count": 0,
            "verified_stream_count": 0,
            "vf_verified_stream_count": 0,
            "identity_contradiction_count": 0,
        }
    except Exception:
        return {
            **base,
            "status": "audit_error",
            "duration_ms": round((time.monotonic() - started) * 1000),
            "raw_stream_count": 0,
            "playable_stream_count": 0,
            "verified_stream_count": 0,
            "vf_verified_stream_count": 0,
            "identity_contradiction_count": 0,
        }

    probe = parse_probe(proc.stdout)
    if probe is None:
        return {
            **base,
            "status": "probe_output_invalid",
            "duration_ms": round((time.monotonic() - started) * 1000),
            "raw_stream_count": 0,
            "playable_stream_count": 0,
            "verified_stream_count": 0,
            "vf_verified_stream_count": 0,
            "identity_contradiction_count": 0,
        }

    playable = int(probe.get("playable_stream_count") or 0)
    verified = int(probe.get("content_verified_count") or probe.get("identity_verified_count") or 0)
    contradictions = int(probe.get("identity_contradiction_count") or 0)
    raw_count = int(probe.get("raw_stream_count") or 0)
    vf_verified = 0
    for item in probe.get("streams") or []:
        if not isinstance(item, dict):
            continue
        media = item.get("media") if isinstance(item.get("media"), dict) else {}
        identity = item.get("identity") if isinstance(item.get("identity"), dict) else {}
        row = item.get("row") if isinstance(item.get("row"), dict) else {}
        if media.get("playable") is True and identity.get("status") == "match" and french_audio_evidence(row):
            vf_verified += 1

    runtime_error = bool(probe.get("runtime_error"))
    if contradictions > 0:
        status = "wrong_content"
    elif runtime_error:
        status = "runtime_error"
    elif playable > 0 and verified == playable:
        status = "playable_verified"
    elif playable > 0:
        status = "identity_unverified"
    elif raw_count > 0:
        status = "returned_unplayable"
    else:
        status = "no_streams"

    return {
        **base,
        "status": status,
        "duration_ms": int(probe.get("duration_ms") or round((time.monotonic() - started) * 1000)),
        "raw_stream_count": raw_count,
        "playable_stream_count": playable,
        "verified_stream_count": verified,
        "vf_verified_stream_count": vf_verified,
        "identity_contradiction_count": contradictions,
    }


def summarize(rows: list[dict[str, Any]], fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    policy = load_json(POLICY)
    min_breadth = int((policy.get("retirement_guard") or {}).get("minimum_breadth_fixtures_before_redundancy_deactivation") or 20)
    by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
    fixture_hits: dict[str, set[str]] = defaultdict(set)
    fixture_vf_hits: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        provider = str(row.get("provider_id") or "")
        fixture = str(row.get("fixture_key") or "")
        by_provider[provider].append(row)
        if row.get("status") == "playable_verified":
            fixture_hits[fixture].add(provider)
            if int(row.get("vf_verified_stream_count") or 0) > 0:
                fixture_vf_hits[fixture].add(provider)

    unique_by_provider: dict[str, list[str]] = defaultdict(list)
    unique_vf_by_provider: dict[str, list[str]] = defaultdict(list)
    for fixture, providers in fixture_hits.items():
        if len(providers) == 1:
            unique_by_provider[next(iter(providers))].append(fixture)
    for fixture, providers in fixture_vf_hits.items():
        if len(providers) == 1:
            unique_vf_by_provider[next(iter(providers))].append(fixture)

    provider_summaries: list[dict[str, Any]] = []
    for provider, values in sorted(by_provider.items()):
        opportunities = len(values)
        verified = sum(1 for row in values if row.get("status") == "playable_verified")
        vf_verified_fixtures = sum(1 for row in values if row.get("status") == "playable_verified" and int(row.get("vf_verified_stream_count") or 0) > 0)
        wrong = sum(1 for row in values if row.get("status") == "wrong_content")
        repairable = sum(1 for row in values if row.get("status") in {"runtime_error", "timeout", "audit_error", "probe_output_invalid", "returned_unplayable"})
        first = values[0]
        unique = sorted(unique_by_provider.get(provider, []))
        unique_vf = sorted(unique_vf_by_provider.get(provider, []))
        if wrong:
            disposition = "quarantine_wrong_content"
        elif unique_vf or unique:
            disposition = "preserve_unique_coverage"
        elif repairable:
            disposition = "repair_before_redundancy_review"
        elif len(fixtures) < min_breadth:
            disposition = "insufficient_corpus_for_redundancy_review"
        else:
            disposition = "redundancy_review_allowed_not_automatic"
        provider_summaries.append(
            {
                "provider_id": provider,
                "provider_name": first.get("provider_name"),
                "enabled": first.get("enabled"),
                "vf_declared": first.get("vf_declared"),
                "supported_types": first.get("supported_types") or [],
                "opportunities": opportunities,
                "verified_playable_fixtures": verified,
                "catalogue_coverage_rate": round(verified / opportunities, 4) if opportunities else 0.0,
                "vf_verified_fixtures": vf_verified_fixtures,
                "wrong_content_fixtures": wrong,
                "repairable_failure_fixtures": repairable,
                "unique_coverage_fixtures": unique,
                "unique_vf_coverage_fixtures": unique_vf,
                "disposition": disposition,
            }
        )

    group_counts = Counter(str(row.get("group") or "unknown") for row in fixtures)
    return {
        "schema_version": 1,
        "generated_at_epoch": int(time.time()),
        "environment": "nuvio-tv-compatible-node-probe-report-only",
        "activation_mutation": False,
        "corpus_fixture_count": len(fixtures),
        "corpus_group_counts": dict(sorted(group_counts.items())),
        "minimum_breadth_fixture_policy": min_breadth,
        "broad_retirement_evidence_ready": len(fixtures) >= min_breadth,
        "provider_count": len(provider_summaries),
        "execution_count": len(rows),
        "providers": provider_summaries,
        "fixture_provider_counts": {key: len(value) for key, value in sorted(fixture_hits.items())},
        "fixture_vf_provider_counts": {key: len(value) for key, value in sorted(fixture_vf_hits.items())},
        "policy_note": "Portfolio ranking is advisory. Unique/VF coverage is preserved; runtime/transport failures mean repair; only confirmed identity contradictions are unsafe-content evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()

    tasks, fixtures, _vf_ids = build_plan()
    policy = load_json(POLICY)
    min_breadth = int((policy.get("retirement_guard") or {}).get("minimum_breadth_fixtures_before_redundancy_deactivation") or 20)
    if len(fixtures) < min_breadth:
        raise RuntimeError(f"catalogue breadth corpus too small: {len(fixtures)} < {min_breadth}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.plan_only:
        group_counts = Counter(str(row.get("group") or "unknown") for row in fixtures)
        plan = {
            "schema_version": 1,
            "plan_only": True,
            "corpus_fixture_count": len(fixtures),
            "corpus_group_counts": dict(sorted(group_counts.items())),
            "provider_count": len({task["identity"]["provider_id"] for task in tasks}),
            "execution_count": len(tasks),
            "minimum_breadth_fixture_policy": min_breadth,
        }
        output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("FIELD_PROVIDER_CATALOGUE_BREADTH_PLAN " + json.dumps(plan, separators=(",", ":")))
        return 0

    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_map = {executor.submit(run_probe, task): task for task in tasks}
        total = len(future_map)
        for index, future in enumerate(concurrent.futures.as_completed(future_map), 1):
            row = future.result()
            rows.append(row)
            print(
                f"[{index}/{total}] {row.get('provider_id')} {row.get('fixture_key')}: "
                f"{row.get('status')} playable={row.get('playable_stream_count', 0)} vf={row.get('vf_verified_stream_count', 0)}"
            )

    report = summarize(rows, fixtures)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_CATALOGUE_BREADTH "
        + json.dumps(
            {
                "corpusFixtureCount": report["corpus_fixture_count"],
                "providerCount": report["provider_count"],
                "executionCount": report["execution_count"],
                "broadRetirementEvidenceReady": report["broad_retirement_evidence_ready"],
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
