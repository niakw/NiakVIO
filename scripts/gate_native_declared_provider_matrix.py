#!/usr/bin/env python3
"""Fail closed unless a native Lab traversed the complete enabled Provider matrix.

The quality/certification denominator is the published active set, not every
catalogue row. Disabled providers remain valid repair telemetry but cannot make
an enabled Hub-46 native matrix fail merely because an OFF route times out.
Every enabled provider must appear on at least one representative
movie/tv/anime route, and every declared enabled route must begin and reach an
explicit terminal observation (result/error/skipped/watchdog timeout).

Provider health is deliberately separated from catalogue sampling:
- FULL: every declared lane returned at least one stream on the sampled work;
- PARTIAL: at least one lane is positive and at least one other lane has a
  technical/error outcome that needs targeted repair;
- RESAMPLE: every still-unproved lane ended cleanly with zero streams. This is
  catalogue uncertainty, not a repair verdict; another work must be sampled;
- ZERO: no lane has positive proof and at least one lane has a technical/error
  outcome. It needs individual diagnosis/repair.

A clean zero-stream result must therefore never be silently folded into ZERO.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

TYPES = ("movie", "tv", "anime")
FIELD_RE = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")
OUTCOME_PRIORITY = {"unobserved": 0, "catalog_miss": 1, "technical_error": 2, "positive": 3}


def fields(line: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in FIELD_RE.finditer(line)}


def decode64(value: str) -> str:
    raw = value.strip().replace("-", "+").replace("_", "/")
    raw += "=" * ((4 - len(raw) % 4) % 4)
    try:
        return base64.b64decode(raw).decode("utf-8")
    except Exception:
        return ""


def route(provider: str, media_type: str) -> tuple[str, str]:
    return (provider.casefold(), media_type.casefold())


def load_scope_ids(scope_path: Path | None) -> set[str] | None:
    raw_env = __import__("os").environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()
    path = scope_path
    if path is None and raw_env:
        candidate = Path(raw_env)
        path = candidate if candidate.is_absolute() else Path.cwd() / candidate
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    ids = {
        str(row.get("manifestId") or row.get("provider") or "").strip().casefold()
        for row in rows if isinstance(row, dict)
        if str(row.get("manifestId") or row.get("provider") or "").strip()
    }
    expected = int(data.get("hubCount") or data.get("providerCount") or len(ids))
    if not ids or len(ids) != expected:
        raise SystemExit(f"invalid native provider scope: ids={len(ids)} expected={expected} path={path}")
    return ids


def merge_outcome(current: str, incoming: str) -> str:
    """Keep positive proof once observed; otherwise retain the strongest problem."""
    if current == "positive" or incoming == "positive":
        return "positive"
    return incoming if OUTCOME_PRIORITY.get(incoming, 0) >= OUTCOME_PRIORITY.get(current, 0) else current


def provider_status(lane_outcomes: dict[str, str]) -> str:
    values = list(lane_outcomes.values())
    if values and all(value == "positive" for value in values):
        return "FULL"
    positive = sum(value == "positive" for value in values)
    unresolved = [value for value in values if value != "positive"]
    # RESAMPLE is intentionally checked before PARTIAL/ZERO: a clean catalogue
    # miss is not a technical defect even when another lane already works.
    if unresolved and all(value == "catalog_miss" for value in unresolved):
        return "RESAMPLE"
    if positive:
        return "PARTIAL"
    return "ZERO"


def parse_ios_result(line: str) -> tuple[str, str, str] | None:
    marker = "FIELD_NATIVE_IOS_RESULT "
    if not line.startswith(marker):
        return None
    try:
        payload = json.loads(line[len(marker):].strip())
    except Exception:
        return None
    provider = str(payload.get("provider") or "").strip()
    media_type = str(payload.get("mediaType") or "").strip().casefold()
    state = str(payload.get("state") or "").strip().casefold()
    count = int(payload.get("count") or 0)
    if not provider or media_type not in TYPES:
        return None
    if state == "completed":
        outcome = "positive" if count > 0 else "catalog_miss"
    else:
        outcome = "technical_error"
    return provider, media_type, outcome


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True, choices=("tv", "mobile", "desktop", "ios"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--scope-matrix", type=Path, default=None)
    parser.add_argument("logs", nargs="+", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    fixture_by_type = ((corpus.get("native_reader_acceptance") or {}).get("fixture_by_type") or {})
    scope_ids = load_scope_ids(args.scope_matrix)

    expected: set[tuple[str, str]] = set()
    provider_ids: set[str] = set()
    display: dict[str, str] = {}
    disabled_ids: set[str] = set()
    for row in manifest.get("scrapers") or []:
        provider = str(row.get("id") or "").strip()
        if not provider:
            continue
        key = provider.casefold()
        if scope_ids is not None and key not in scope_ids:
            disabled_ids.add(key)
            continue
        if scope_ids is None and row.get("enabled") is not True:
            disabled_ids.add(key)
            continue
        provider_ids.add(key)
        display[key] = provider
        declared = {
            str(value).strip().casefold()
            for value in (row.get("supportedTypes") or [])
            if str(value).strip()
        }
        for media_type in TYPES:
            if media_type in declared:
                expected.add(route(provider, media_type))

    if scope_ids is not None:
        missing_scope = sorted(scope_ids - provider_ids)
        if missing_scope:
            raise SystemExit("scope provider(s) missing from manifest: " + ",".join(missing_scope))
        if len(provider_ids) != len(scope_ids):
            raise SystemExit(f"scope mismatch: providers={len(provider_ids)} expected={len(scope_ids)}")

    missing_fixture_types = [kind for kind in TYPES if not str(fixture_by_type.get(kind) or "").strip()]
    if missing_fixture_types:
        raise SystemExit("missing representative fixture mapping for: " + ",".join(missing_fixture_types))
    providers_without_route = sorted(
        display[key] for key in provider_ids if not any(p == key for p, _ in expected)
    )
    if providers_without_route:
        raise SystemExit("enabled providers without movie/tv/anime route: " + ",".join(providers_without_route))

    begun: set[tuple[str, str]] = set()
    completed: set[tuple[str, str]] = set()
    observed_disabled: set[tuple[str, str]] = set()
    lane_outcomes: dict[tuple[str, str], str] = defaultdict(lambda: "unobserved")
    readable = 0

    for log in args.logs:
        if not log.is_file():
            continue
        readable += 1
        for raw in log.read_text(encoding="utf-8", errors="replace").splitlines():
            marker = raw.find("FIELD_NATIVE_")
            if marker < 0:
                continue
            line = raw[marker:].strip()

            if args.client == "ios":
                parsed = parse_ios_result(line)
                if parsed:
                    provider, media_type, outcome = parsed
                    r = route(provider, media_type)
                    if r[0] in provider_ids:
                        completed.add(r)
                        lane_outcomes[r] = merge_outcome(lane_outcomes[r], outcome)
                    elif r[0] in disabled_ids:
                        observed_disabled.add(r)
                if line.startswith("FIELD_NATIVE_IOS_PROVIDER_BEGIN "):
                    f = fields(line)
                    provider = f.get("provider", "")
                    media_type = f.get("type", "")
                    if provider and media_type:
                        r = route(provider, media_type)
                        if r[0] in provider_ids: begun.add(r)
                        elif r[0] in disabled_ids: observed_disabled.add(r)
                elif line.startswith("FIELD_NATIVE_IOS_PROVIDER_END "):
                    f = fields(line)
                    provider = f.get("provider", "")
                    fixture = f.get("fixture", "")
                    media_type = next((kind for kind in TYPES if str(fixture_by_type.get(kind) or "") == fixture), "")
                    if provider and media_type:
                        r = route(provider, media_type)
                        if r[0] in provider_ids: completed.add(r)
                        elif r[0] in disabled_ids: observed_disabled.add(r)
                continue

            if line.startswith("FIELD_NATIVE_PROVIDER_BEGIN "):
                f = fields(line)
                provider = decode64(f.get("provider64", "")) or f.get("provider", "")
                media_type = f.get("request_type", "")
                client = f.get("client", "")
                if client == args.client and provider and media_type:
                    r = route(provider, media_type)
                    if r[0] in provider_ids: begun.add(r)
                    elif r[0] in disabled_ids: observed_disabled.add(r)
                continue

            if line.startswith("FIELD_NATIVE_RESULT "):
                f = fields(line)
                provider = decode64(f.get("provider64", "")) or f.get("provider", "")
                media_type = f.get("request_type", "")
                client = f.get("client", "")
                if client == args.client and provider and media_type:
                    r = route(provider, media_type)
                    count = int(f.get("count") or 0)
                    outcome = "positive" if count > 0 else "catalog_miss"
                    if r[0] in provider_ids:
                        completed.add(r)
                        lane_outcomes[r] = merge_outcome(lane_outcomes[r], outcome)
                    elif r[0] in disabled_ids:
                        observed_disabled.add(r)
                continue

            if line.startswith("FIELD_NATIVE_ERROR ") or line.startswith("FIELD_NATIVE_PROVIDER_SKIPPED "):
                f = fields(line)
                provider = decode64(f.get("provider64", "")) or f.get("provider", "")
                media_type = f.get("request_type", "")
                client = f.get("client", "")
                if client == args.client and provider and media_type:
                    r = route(provider, media_type)
                    if r[0] in provider_ids:
                        completed.add(r)
                        lane_outcomes[r] = merge_outcome(lane_outcomes[r], "technical_error")
                    elif r[0] in disabled_ids:
                        observed_disabled.add(r)

    if readable == 0:
        print(f"FIELD_NATIVE_DECLARED_MATRIX state=infra_error client={args.client} reason=no_readable_log")
        return 2

    missing_begin = sorted(expected - begun)
    missing_end = sorted(expected - completed)
    unexpected = sorted((begun | completed) - expected)
    covered_providers = {provider for provider, _ in completed if provider in provider_ids}
    missing_providers = sorted(provider_ids - covered_providers)

    counts = {kind: sum(1 for _, media_type in expected if media_type == kind) for kind in TYPES}
    state = "passed" if not missing_begin and not missing_end and not missing_providers and not unexpected else "failed"
    print(
        "FIELD_NATIVE_DECLARED_MATRIX "
        f"state={state} client={args.client} providers={len(provider_ids)} disabled={len(disabled_ids)} "
        f"routes={len(expected)} movie={counts['movie']} tv={counts['tv']} anime={counts['anime']} "
        f"begun={len(begun & expected)} completed={len(completed & expected)} "
        f"missing_providers={len(missing_providers)} missing_begin={len(missing_begin)} "
        f"missing_end={len(missing_end)} unexpected={len(unexpected)} observed_disabled={len(observed_disabled)}"
    )

    status_counts: Counter[str] = Counter()
    for provider in sorted(provider_ids):
        lanes = sorted(media_type for p, media_type in expected if p == provider)
        outcomes = {media_type: lane_outcomes[(provider, media_type)] for media_type in lanes}
        status = provider_status(outcomes)
        status_counts[status] += 1
        lane_text = ",".join(f"{media_type}:{outcomes[media_type]}" for media_type in lanes)
        print(
            "FIELD_NATIVE_PROVIDER_STATUS "
            f"client={args.client} provider={display.get(provider, provider)} status={status} lanes={lane_text}"
        )
    print(
        "FIELD_NATIVE_PROVIDER_STATUS_SUMMARY "
        f"client={args.client} total={len(provider_ids)} FULL={status_counts['FULL']} "
        f"PARTIAL={status_counts['PARTIAL']} RESAMPLE={status_counts['RESAMPLE']} ZERO={status_counts['ZERO']}"
    )

    for provider in missing_providers[:120]:
        print(f"FIELD_NATIVE_DECLARED_MATRIX_FAILURE reason=missing_provider provider={display.get(provider, provider)}")
    for provider, media_type in missing_begin[:240]:
        print(f"FIELD_NATIVE_DECLARED_MATRIX_FAILURE reason=missing_begin provider={display.get(provider, provider)} type={media_type}")
    for provider, media_type in missing_end[:240]:
        print(f"FIELD_NATIVE_DECLARED_MATRIX_FAILURE reason=missing_terminal provider={display.get(provider, provider)} type={media_type}")
    for provider, media_type in unexpected[:120]:
        print(f"FIELD_NATIVE_DECLARED_MATRIX_FAILURE reason=undeclared_route provider={display.get(provider, provider)} type={media_type}")
    for provider, media_type in sorted(observed_disabled)[:120]:
        print(f"FIELD_NATIVE_DISABLED_TELEMETRY provider={provider} type={media_type} excluded_from_quality_gate=true")
    return 0 if state == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
