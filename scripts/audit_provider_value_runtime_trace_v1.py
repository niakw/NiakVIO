#!/usr/bin/env python3
"""Run targeted providers and persist only the bounded V18 provider-value trace.

This diagnostic intentionally stores no response body, headers, cookies, tokens or
media URLs. The generated provider runtime exposes only stage/lane/providerId,
step index and the already-known DATA route template through the CI probe.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
CORPUS = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"
DEFAULT_OUTPUT = ROOT / "automation" / "provider-value-runtime-trace-v1.json"
REPRESENTATIVE = {
    "movie": "interstellar",
    "tv": "breaking-bad-s01e01",
    "anime": "jujutsu-kaisen-s01e01",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


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


def bounded_trace(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    stage = str(value.get("stage") or "")[:64]
    lane = str(value.get("lane") or "")[:32]
    provider_id = str(value.get("provider_id") or "")[:160]
    route = str(value.get("route") or "")[:240]
    raw_index = value.get("step_index")
    step_index = raw_index if isinstance(raw_index, int) and -1 <= raw_index <= 3 else None
    if not any((stage, lane, provider_id, route)) and step_index is None:
        return None
    return {
        "stage": stage,
        "lane": lane,
        "providerId": provider_id,
        "stepIndex": step_index,
        "route": route,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--timeout", type=int, default=55)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT.relative_to(ROOT))
    args = parser.parse_args()

    if not (str(os.environ.get("TMDB_API_KEY") or "").strip() or str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        raise SystemExit("TMDB_API_KEY or TMDB_ACCESS_TOKEN is required")

    manifest = load(MANIFEST)
    rows = {
        cid(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    }
    corpus = load(CORPUS)
    fixture_by_slug = {
        str(row.get("slug") or ""): row.get("fixture")
        for row in corpus.get("fixtures") or []
        if isinstance(row, dict) and isinstance(row.get("fixture"), dict)
    }

    requested: list[str] = []
    for value in args.provider:
        provider = cid(value)
        if provider and provider not in requested:
            requested.append(provider)

    output_rows: list[dict[str, Any]] = []
    timeout = max(15, min(int(args.timeout), 90))
    for provider in requested:
        row = rows.get(provider)
        if not isinstance(row, dict):
            output_rows.append({"provider": provider, "status": "missing_manifest_row", "trace": None})
            continue
        filename = str(row.get("filename") or "").strip()
        provider_path = ROOT / filename
        if not filename or not provider_path.is_file():
            output_rows.append({"provider": provider, "status": "missing_provider_file", "trace": None})
            continue
        types = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
        semantic_types: list[str] = []
        for value in types:
            media_type = str(value or "").strip().casefold()
            if media_type == "series":
                media_type = "tv"
            if media_type in REPRESENTATIVE and media_type not in semantic_types:
                semantic_types.append(media_type)
        for media_type in semantic_types:
            fixture = fixture_by_slug.get(REPRESENTATIVE[media_type])
            if not isinstance(fixture, dict):
                output_rows.append({
                    "provider": provider,
                    "semanticType": media_type,
                    "status": "missing_fixture",
                    "trace": None,
                })
                continue
            command = [
                "node",
                str(PROBE),
                str(provider_path),
                json.dumps(fixture, ensure_ascii=False, separators=(",", ":")),
                "{}",
            ]
            try:
                proc = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=os.environ.copy(),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                output_rows.append({
                    "provider": provider,
                    "semanticType": media_type,
                    "status": "timeout",
                    "trace": None,
                })
                continue
            probe = parse_probe(proc.stdout)
            if not isinstance(probe, dict):
                output_rows.append({
                    "provider": provider,
                    "semanticType": media_type,
                    "status": "invalid_probe_output",
                    "trace": None,
                })
                continue
            debug = probe.get("debug") if isinstance(probe.get("debug"), dict) else {}
            trace = bounded_trace(debug.get("provider_value_trace_v18"))
            record = {
                "provider": provider,
                "semanticType": media_type,
                "status": "trace" if trace else "no_trace",
                "raw": int(probe.get("raw_stream_count") or 0),
                "playable": int(probe.get("playable_stream_count") or 0),
                "trace": trace,
            }
            output_rows.append(record)
            trace_text = trace or {}
            print(
                "FIELD_PROVIDER_VALUE_RUNTIME_TRACE "
                f"provider={provider} type={media_type} status={record['status']} "
                f"stage={trace_text.get('stage') or '-'} lane={trace_text.get('lane') or '-'} "
                f"providerId={trace_text.get('providerId') or '-'} "
                f"stepIndex={trace_text.get('stepIndex') if trace_text.get('stepIndex') is not None else '-'} "
                f"route={trace_text.get('route') or '-'}",
                flush=True,
            )

    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schemaVersion": 1,
        "sanitized": True,
        "publicationAllowed": False,
        "providers": requested,
        "rows": output_rows,
    }
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PROVIDER_VALUE_RUNTIME_TRACE_V1_OK rows={len(output_rows)} output={output_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
