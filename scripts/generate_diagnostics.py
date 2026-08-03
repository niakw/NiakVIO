#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate a compact, actionable provider diagnostic report.

The report preserves exact runtime failure classes and structured exceptions.
Endpoint paths remain normalized and final stream URLs are never emitted.
"""
from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def route_summary(test: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in test.get("network_observations") or []:
        if item.get("infrastructure") or not item.get("host"):
            continue
        rows.append(
            {
                "stage": item.get("stage") or "unknown",
                "host": item.get("host"),
                "method": item.get("method") or "GET",
                "path_pattern": item.get("path_pattern"),
                "status": item.get("status"),
                "invocation": item.get("invocation"),
                "settings_profile": item.get("settings_profile"),
                "error_code": item.get("error_code"),
                "error": item.get("error"),
            }
        )
    return rows


def classify(test: dict[str, Any]) -> str:
    failure = str(test.get("failure_class") or "").strip()
    if failure:
        return failure
    status = str(test.get("status") or "runtime_error")
    if status == "healthy":
        return "stream_valid"
    if status == "runtime_error":
        return "provider_runtime_exception"
    if status == "blocked":
        return "provider_http_blocked"
    if status == "unavailable":
        return "provider_http_unavailable"
    if status == "provider_unreachable":
        return "network_unreachable"
    if status == "degraded":
        return "stream_not_playback_verified"
    if status == "no_streams":
        return "content_lookup_completed_no_streams"
    if status == "reachable":
        return "origin_only_reachable"
    return status


def language(test: dict[str, Any]) -> dict[str, Any]:
    audio = set(test.get("audio_languages") or [])
    subs = set(test.get("subtitle_languages") or [])
    raw = " ".join(str(x) for x in (test.get("stream_titles") or [])).lower()
    if "fr" in audio or "truefrench" in raw or " vf" in f" {raw}":
        return {"group": "vf", "confidence": "high", "evidence": ["runtime_audio_or_label"]}
    if "fr" in subs or "vostfr" in raw:
        return {"group": "vostfr", "confidence": "high", "evidence": ["runtime_subtitle_or_label"]}
    return {"group": "unknown", "confidence": "none", "evidence": []}


def error_summary(test: dict[str, Any]) -> dict[str, Any] | None:
    detail = test.get("error_details") or {}
    if not detail and not test.get("error"):
        return None
    return {
        "fixture": (test.get("fixture") or {}).get("label") or (test.get("fixture") or {}).get("tmdbId"),
        "fixture_phase": test.get("fixture_phase"),
        "failure_class": test.get("failure_class"),
        "name": detail.get("name"),
        "code": detail.get("code"),
        "message": detail.get("message") or test.get("error"),
        "phase": detail.get("phase"),
        "invocation": detail.get("invocation"),
        "settings_profile": detail.get("settings_profile"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=ROOT / "health-output/health-results.json")
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    payload = json.loads(args.results.read_text(encoding="utf-8"))

    providers: list[dict[str, Any]] = []
    global_failures: Counter[str] = Counter()
    global_statuses: Counter[str] = Counter()
    for item in payload.get("results", []):
        tests = item.get("tests") or []
        stages = [classify(test) for test in tests]
        global_failures.update(stages)
        global_statuses.update([str(item.get("status") or "unknown")])
        preflight = item.get("dns_preflight") or {}
        decision = preflight.get("decision") or {}
        errors = [summary for test in tests if (summary := error_summary(test))]
        status_counts = Counter(str(test.get("status") or "unknown") for test in tests)
        providers.append(
            {
                "id": item.get("canonical_id") or item.get("id"),
                "key": item.get("key"),
                "source": item.get("source"),
                "status": item.get("status"),
                "score": item.get("score"),
                "dns_preflight_status": decision.get("status"),
                "dns_resolver": decision.get("selected_resolver"),
                "dns_migration_candidate": (decision.get("migration_candidate") or {}).get("host")
                if isinstance(decision.get("migration_candidate"), dict)
                else None,
                "fixture_status_counts": dict(status_counts),
                "failure_classes": sorted(set(stages)),
                "errors": errors,
                "runtime_error_count": sum(1 for test in tests if test.get("status") == "runtime_error" or test.get("error_details")),
                "malformed_request_count": sum(
                    1
                    for test in tests
                    for row in test.get("network_observations") or []
                    if row.get("error_code") == "NUVIO_INVALID_REQUEST_ARGUMENT"
                    or "object%20object" in str(row.get("path_pattern") or "").casefold()
                ),
                "streams_returned": sum(int(test.get("streams_returned") or test.get("stream_count") or 0) for test in tests),
                "streams_playable": sum(int(test.get("streams_playable") or 0) for test in tests),
                "language_evidence": [language(test) for test in tests],
                "route_observations": [route_summary(test) for test in tests],
                "last_checked": payload.get("generated_at"),
            }
        )

    report = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_health_schema_version": payload.get("schema_version"),
        "provider_count": len(providers),
        "status_counts": dict(global_statuses),
        "failure_class_counts": dict(global_failures),
        "providers": providers,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "diagnostics-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    body = "".join(
        "<tr>"
        f"<td>{html.escape(str(row['id']))}</td>"
        f"<td>{html.escape(str(row['source']))}</td>"
        f"<td>{html.escape(str(row['status']))}</td>"
        f"<td>{html.escape(str(row['score']))}</td>"
        f"<td>{html.escape(', '.join(row['failure_classes']))}</td>"
        f"<td>{row['streams_returned']}</td>"
        f"<td>{row['streams_playable']}</td>"
        f"<td>{row['runtime_error_count']}</td>"
        f"<td>{row['malformed_request_count']}</td>"
        f"<td>{html.escape('; '.join(str(error.get('code') or error.get('name') or error.get('message') or '') for error in row['errors'][:3]))}</td>"
        "</tr>"
        for row in providers
    )
    document = f"""<!doctype html><html lang=\"fr\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>Nuvio diagnostics</title><style>body{{font-family:system-ui;margin:2rem;line-height:1.4}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:.45rem;text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#fff}}</style><h1>Diagnostic des providers Nuvio</h1><p>Généré le {html.escape(report['generated_at'])}. Les URLs finales ne sont jamais publiées.</p><table><thead><tr><th>Provider</th><th>Source</th><th>Statut</th><th>Score</th><th>Cause(s)</th><th>Flux retournés</th><th>Flux lisibles</th><th>Runtime errors</th><th>Requêtes mal formées</th><th>Erreur</th></tr></thead><tbody>{body}</tbody></table></html>"""
    (args.output / "diagnostics-report.html").write_text(document, encoding="utf-8")


if __name__ == "__main__":
    main()
