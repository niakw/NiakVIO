#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

ANOMALY_SCORES = {
    "provider_unreachable": 120,
    "unavailable": 110,
    "blocked": 100,
    "runtime_error": 90,
    "no_streams": 70,
    "degraded": 60,
    "reachable": 30,
    "healthy": 0,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def norm(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def provider_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("providers") or []
    return [row for row in rows if isinstance(row, dict)]


def diagnostic(row: dict[str, Any]) -> dict[str, Any]:
    provider_id = norm(row.get("id") or row.get("canonical_id"))
    status = str(row.get("observed_status") or row.get("status") or "").strip()
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    server_ok = bool(evidence.get("provider_server_successful_response", False))
    server_accessible = bool(evidence.get("provider_server_accessible", False))
    hosts = [str(x) for x in (evidence.get("provider_server_hosts") or []) if str(x)]

    score = int(ANOMALY_SCORES.get(status, 40 if status else 20))
    if status in {"blocked", "runtime_error", "no_streams"} and server_ok:
        score = max(1, score - 35)

    needs_route_search = (
        status in {"provider_unreachable", "unavailable"}
        or (status in {"blocked", "runtime_error"} and not server_accessible)
        or (not hosts and status not in {"healthy", "no_streams"})
    )

    return {
        "provider": provider_id,
        "status": status,
        "score": score,
        "needs_route_search": needs_route_search,
        "server_accessible": server_accessible,
        "server_successful_response": server_ok,
        "host_count": len(hosts),
    }


def _date(day: str) -> dt.date:
    return dt.date.fromisoformat(day) if day else dt.datetime.now(dt.timezone.utc).date()


def select(report: dict[str, Any], explicit: str = "", day: str = "") -> dict[str, Any]:
    rows = provider_rows(report)
    by_id = {
        norm(row.get("id") or row.get("canonical_id")): row
        for row in rows
        if norm(row.get("id") or row.get("canonical_id"))
    }
    if not by_id:
        return {"provider": "", "selected": False, "reason": "no_provider_rows", "needs_route_search": False}

    if explicit:
        key = norm(explicit)
        if key not in by_id:
            raise ValueError(f"unknown Learning provider: {explicit}")
        info = diagnostic(by_id[key])
        return {
            **info,
            "selected": True,
            "reason": "manual_target",
            "core_is_authoritative": False,
        }

    diagnostics = [diagnostic(row) for row in by_id.values()]
    anomalies = [row for row in diagnostics if int(row.get("score") or 0) > 0 and row.get("status") != "healthy"]
    date = _date(day)

    if anomalies:
        # Rotate through all anomalies instead of hammering the same provider every day.
        # Severity orders the pool, but the date advances the target.
        ordered = sorted(anomalies, key=lambda row: (-int(row["score"]), str(row["provider"])))
        selected = ordered[date.toordinal() % len(ordered)]
        return {
            **selected,
            "selected": True,
            "reason": "daily_anomaly_rotation",
            "candidate_pool_size": len(ordered),
            "core_is_authoritative": False,
        }

    # No visible anomaly: deliberately challenge a provider the Core currently
    # considers healthy/reachable so Learning can discover hidden stream/client failures.
    ordered = sorted(diagnostics, key=lambda row: str(row["provider"]))
    selected = ordered[date.toordinal() % len(ordered)]
    return {
        **selected,
        "selected": True,
        "reason": "daily_hidden_failure_exploration",
        "needs_route_search": False,
        "candidate_pool_size": len(ordered),
        "core_is_authoritative": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--health", type=Path, default=Path("health-report.json"))
    parser.add_argument("--provider", default="")
    parser.add_argument("--day", default="")
    parser.add_argument("--github-output", default="")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = select(load(args.health), args.provider, args.day)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as fh:
            for key in ("provider", "selected", "reason", "status", "score", "needs_route_search"):
                value = result.get(key, "")
                if isinstance(value, bool):
                    value = str(value).lower()
                fh.write(f"{key}={value}\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
