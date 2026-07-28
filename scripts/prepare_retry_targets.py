#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build a narrow hourly retry queue from availability history.

Only providers with a recent hard availability status are selected.
Blocked/rate-limited providers and fixture misses are intentionally excluded so the
workflow does not hammer anti-bot pages or treat catalogue gaps as outages.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HISTORY_PATH = ROOT / "availability-history.json"
OUTPUT_PATH = ROOT / "retry-targets.json"


def safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def write_output(name: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def main() -> int:
    history: dict[str, Any] = {"providers": {}}
    if HISTORY_PATH.exists():
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))

    retryable_statuses = {"unavailable"}
    targets = []
    for provider_id, state in history.get("providers", {}).items():
        if not isinstance(state, dict):
            continue
        status = str(state.get("last_status", ""))
        hard_hosts = [
            host
            for host, host_state in state.get("host_health", {}).items()
            if isinstance(host_state, dict)
            and str(host_state.get("last_category", "")) in {"host_down", "not_found"}
        ]
        if status not in retryable_statuses and not hard_hosts:
            continue
        targets.append({
            "id": canonical_id(str(provider_id)),
            "reason": status if status in retryable_statuses else "host_failure",
            "failed_hosts": sorted(hard_hosts),
            "consecutive_hard_failures": int(state.get("consecutive_hard_failures", 0)),
            "last_checked_at": state.get("last_checked_at"),
        })

    targets.sort(key=lambda item: (-item["consecutive_hard_failures"], item["id"]))
    OUTPUT_PATH.write_text(
        json.dumps({"schema_version": 63, "targets": targets}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_output("has_targets", "true" if targets else "false")
    write_output("target_count", str(len(targets)))
    print(f"Prepared {len(targets)} provider retry target(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
