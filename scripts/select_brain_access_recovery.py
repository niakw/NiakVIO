#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

ACCESS_STATUSES = {
    "provider_unreachable": 100,
    "blocked": 90,
    "runtime_error": 80,
    "unavailable": 70,
    "no_streams": 30,
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


def access_score(row: dict[str, Any]) -> tuple[int, str]:
    provider_id = norm(row.get("id") or row.get("canonical_id"))
    status = str(row.get("observed_status") or row.get("status") or "").strip()
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    server_ok = bool(evidence.get("provider_server_successful_response", False))
    server_accessible = bool(evidence.get("provider_server_accessible", False))
    hosts = evidence.get("provider_server_hosts") or []

    score = ACCESS_STATUSES.get(status, 0)
    if status in {"blocked", "runtime_error", "no_streams"} and server_ok:
        score -= 60
    if status in {"provider_unreachable", "blocked", "runtime_error"} and not server_accessible:
        score += 20
    if not hosts:
        score += 10
    return max(0, score), provider_id


def select(report: dict[str, Any], explicit: str = "", day: str = "") -> dict[str, Any]:
    rows = provider_rows(report)
    by_id = {norm(row.get("id") or row.get("canonical_id")): row for row in rows if norm(row.get("id") or row.get("canonical_id"))}

    if explicit:
        key = norm(explicit)
        if key not in by_id:
            raise ValueError(f"unknown access-recovery provider: {explicit}")
        row = by_id[key]
        score, _ = access_score(row)
        return {
            "provider": key,
            "selected": True,
            "reason": "manual_target",
            "status": row.get("observed_status") or row.get("status"),
            "score": score,
        }

    candidates = []
    for row in rows:
        score, provider_id = access_score(row)
        if provider_id and score > 0:
            candidates.append((score, provider_id, row))

    if not candidates:
        return {"provider": "", "selected": False, "reason": "no_access_failure"}

    highest = max(score for score, _, _ in candidates)
    pool = sorted((item for item in candidates if item[0] == highest), key=lambda item: item[1])
    date = dt.date.fromisoformat(day) if day else dt.datetime.now(dt.timezone.utc).date()
    index = date.toordinal() % len(pool)
    score, provider_id, row = pool[index]
    return {
        "provider": provider_id,
        "selected": True,
        "reason": "daily_rotating_access_failure",
        "status": row.get("observed_status") or row.get("status"),
        "score": score,
        "candidate_pool_size": len(pool),
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
            for key in ("provider", "selected", "reason", "status", "score"):
                fh.write(f"{key}={result.get(key, '')}\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
