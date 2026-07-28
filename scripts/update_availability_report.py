#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Update availability reports without modifying the public manifest.

This script is intentionally report-only. A health result may be useful for
diagnostics, but Node/GitHub-runner results must never activate, disable, replace
or select a Nuvio provider.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.json"
RESULTS_PATH = Path(
    os.environ.get(
        "NUVIO_HEALTH_RESULTS",
        ROOT / "health-results.json",
    )
).resolve()
HISTORY_PATH = ROOT / "availability-history.json"
REPORT_PATH = ROOT / "availability-report.json"


def load_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def atomic_write_json(path: Path, payload: Any) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=".tmp",
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def safe_fragment(value: str) -> str:
    return re.sub(
        r"[^a-zA-Z0-9._-]+",
        "-",
        str(value).strip(),
    ).strip(".-")[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def provider_sha(entry: dict[str, Any]) -> str | None:
    filename = entry.get("filename")
    if not isinstance(filename, str):
        return None
    path = (ROOT / filename).resolve()
    try:
        path.relative_to((ROOT / "providers").resolve())
    except ValueError:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main() -> int:
    manifest = load_json(MANIFEST_PATH, {"scrapers": []})
    results = load_json(RESULTS_PATH, {})
    history = load_json(
        HISTORY_PATH,
        {"schema_version": 4, "providers": {}},
    )

    if results.get("mode") not in {"availability", "retry"}:
        raise RuntimeError("availability or retry health results are required")

    result_by_id = {
        canonical_id(str(item.get("canonical_id", ""))): item
        for item in results.get("results", [])
    }
    previous = dict(history.get("providers", {}))
    updated = dict(previous)
    report_items: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()

    for entry in manifest.get("scrapers", []):
        cid = canonical_id(str(entry.get("id", "")))
        current_sha = provider_sha(entry)
        result = result_by_id.get(cid)
        result_matches = (
            result is not None
            and result.get("sha256") == current_sha
        )
        status = result.get("status") if result_matches else "stale-or-missing-result"
        old = dict(previous.get(cid, {}))

        hard_failure = status in {"unavailable", "failed"}
        success = status == "healthy"
        hard_failures = (
            int(old.get("consecutive_hard_failures", 0)) + 1
            if hard_failure
            else 0
        )
        successes = (
            int(old.get("consecutive_successes", 0)) + 1
            if success
            else 0
        )

        state = {
            **old,
            "last_checked_at": now,
            "last_status": status,
            "last_sha256": current_sha,
            "last_score": result.get("score") if result_matches else None,
            "consecutive_hard_failures": hard_failures,
            "consecutive_successes": successes,
            "consecutive_blocked": (
                int(old.get("consecutive_blocked", 0)) + 1
                if status == "blocked"
                else 0
            ),
            "consecutive_no_streams": (
                int(old.get("consecutive_no_streams", 0)) + 1
                if status == "no_streams"
                else 0
            ),
            "hosts": result.get("hosts", []) if result_matches else old.get("hosts", []),
            "response_categories": (
                result.get("response_categories", [])
                if result_matches
                else old.get("response_categories", [])
            ),
        }
        updated[cid] = state
        report_items.append({
            "id": cid,
            "status": status,
            "enabled": bool(entry.get("enabled", False)),
            "advisory_only": True,
            "manifest_action": "none",
            "consecutive_hard_failures": hard_failures,
            "consecutive_successes": successes,
            "hosts": state.get("hosts", []),
            "response_categories": state.get("response_categories", []),
        })

    public_report = {
        "schema_version": 4,
        "generated_at": now,
        "mode": results.get("mode"),
        "test_environment": results.get("environment"),
        "checked_providers": len(results.get("results", [])),
        "status_counts": results.get("counts", {}),
        "advisory_only": True,
        "manifest_modified": False,
        "notice": (
            "Results were produced outside the Nuvio runtime. They are diagnostic "
            "only and never activate, disable, replace or select providers."
        ),
        "providers": report_items,
    }
    new_history = {
        "schema_version": 4,
        "updated_at": now,
        "advisory_only": True,
        "providers": updated,
    }

    atomic_write_json(HISTORY_PATH, new_history)
    atomic_write_json(REPORT_PATH, public_report)
    print(
        f"Updated report-only availability state for {len(report_items)} providers."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
