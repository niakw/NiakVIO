#!/usr/bin/env python3
"""Fail closed unless a native Lab traversed the complete declared Provider matrix.

For the current 96-provider catalog this is 214 declared routes:
82 movie + 92 tv + 40 anime. Every provider must appear on at least one
representative route, and every declared movie/tv/anime route must begin and reach
an explicit terminal observation (result/error/skipped/watchdog timeout).
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path

TYPES = ("movie", "tv", "anime")
FIELD_RE = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True, choices=("tv", "mobile", "desktop", "ios"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("logs", nargs="+", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    fixture_by_type = ((corpus.get("native_reader_acceptance") or {}).get("fixture_by_type") or {})

    expected: set[tuple[str, str]] = set()
    provider_ids: set[str] = set()
    display: dict[str, str] = {}
    for row in manifest.get("scrapers") or []:
        provider = str(row.get("id") or "").strip()
        if not provider:
            continue
        key = provider.casefold()
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

    missing_fixture_types = [kind for kind in TYPES if not str(fixture_by_type.get(kind) or "").strip()]
    if missing_fixture_types:
        raise SystemExit("missing representative fixture mapping for: " + ",".join(missing_fixture_types))
    providers_without_route = sorted(
        display[key] for key in provider_ids if not any(p == key for p, _ in expected)
    )
    if providers_without_route:
        raise SystemExit("providers without movie/tv/anime route: " + ",".join(providers_without_route))

    begun: set[tuple[str, str]] = set()
    completed: set[tuple[str, str]] = set()
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
                if line.startswith("FIELD_NATIVE_IOS_PROVIDER_BEGIN "):
                    f = fields(line)
                    provider = f.get("provider", "")
                    media_type = f.get("type", "")
                    if provider and media_type:
                        begun.add(route(provider, media_type))
                elif line.startswith("FIELD_NATIVE_IOS_PROVIDER_END "):
                    f = fields(line)
                    provider = f.get("provider", "")
                    fixture = f.get("fixture", "")
                    media_type = next(
                        (kind for kind in TYPES if str(fixture_by_type.get(kind) or "") == fixture),
                        "",
                    )
                    if provider and media_type:
                        completed.add(route(provider, media_type))
                continue

            if line.startswith("FIELD_NATIVE_PROVIDER_BEGIN "):
                f = fields(line)
                provider = decode64(f.get("provider64", "")) or f.get("provider", "")
                media_type = f.get("request_type", "")
                client = f.get("client", "")
                if client == args.client and provider and media_type:
                    begun.add(route(provider, media_type))
                continue

            if (
                line.startswith("FIELD_NATIVE_RESULT ")
                or line.startswith("FIELD_NATIVE_ERROR ")
                or line.startswith("FIELD_NATIVE_PROVIDER_SKIPPED ")
            ):
                f = fields(line)
                provider = decode64(f.get("provider64", "")) or f.get("provider", "")
                media_type = f.get("request_type", "")
                client = f.get("client", "")
                if client == args.client and provider and media_type:
                    completed.add(route(provider, media_type))

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
        f"state={state} client={args.client} providers={len(provider_ids)} "
        f"routes={len(expected)} movie={counts['movie']} tv={counts['tv']} anime={counts['anime']} "
        f"begun={len(begun & expected)} completed={len(completed & expected)} "
        f"missing_providers={len(missing_providers)} missing_begin={len(missing_begin)} "
        f"missing_end={len(missing_end)} unexpected={len(unexpected)}"
    )
    for provider in missing_providers[:120]:
        print(f"FIELD_NATIVE_DECLARED_MATRIX_FAILURE reason=missing_provider provider={display.get(provider, provider)}")
    for provider, media_type in missing_begin[:240]:
        print(
            "FIELD_NATIVE_DECLARED_MATRIX_FAILURE "
            f"reason=missing_begin provider={display.get(provider, provider)} type={media_type}"
        )
    for provider, media_type in missing_end[:240]:
        print(
            "FIELD_NATIVE_DECLARED_MATRIX_FAILURE "
            f"reason=missing_terminal provider={display.get(provider, provider)} type={media_type}"
        )
    for provider, media_type in unexpected[:120]:
        print(
            "FIELD_NATIVE_DECLARED_MATRIX_FAILURE "
            f"reason=undeclared_route provider={display.get(provider, provider)} type={media_type}"
        )
    return 0 if state == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
