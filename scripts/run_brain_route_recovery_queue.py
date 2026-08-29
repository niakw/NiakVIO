#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def remaining_ms(deadline_ms: int) -> int:
    return max(0, deadline_ms - int(time.time() * 1000))


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    output = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
    return proc.returncode, output[-6000:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--deadline-epoch-ms", type=int, default=0)
    args = parser.parse_args()

    queue = load(args.queue)
    deadline_ms = int(
        args.deadline_epoch_ms
        or os.environ.get("NUVIO_BRAIN_DEADLINE_EPOCH_MS")
        or (int(time.time() * 1000) + 55 * 60 * 1000)
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    attempts: list[dict[str, Any]] = []
    pending: list[str] = []

    for row in queue.get("providers") or []:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider") or "").strip().casefold()
        if not provider or row.get("needs_route_search") is not True:
            continue
        if remaining_ms(deadline_ms) < 45_000:
            pending.append(provider)
            continue

        hub_report = args.output_dir / f"{provider}-hub-report.json"
        fallback_report = args.output_dir / f"{provider}-search-fallback.json"

        first_cmd = [
            "python", "scripts/resolve_provider_hubs.py",
            "--apply",
            "--mode", "deep",
            "--include-disabled",
            "--search-disabled",
            "--provider", provider,
            "--workers", "1",
            "--timeout", "8",
            "--output", str(hub_report),
        ]
        rc1, out1 = run(first_cmd)

        rc2 = 0
        out2 = ""
        if hub_report.is_file() and remaining_ms(deadline_ms) >= 25_000:
            second_cmd = [
                "python", "scripts/resolve_provider_hub_search_fallback.py",
                "--report", str(hub_report),
                "--output", str(fallback_report),
                "--apply",
                "--max-providers", "1",
                "--timeout", "8",
            ]
            rc2, out2 = run(second_cmd)

        attempts.append(
            {
                "provider": provider,
                "coreHypothesisOnly": True,
                "methods": [
                    "known_hub_to_terminal_url",
                    "known_telegram_latest_message_url",
                    "yandex_or_ddg_direct_search",
                    "search_discovered_public_telegram_latest_url",
                    "direct_search_candidate_validation",
                    "historical_or_lkg_route",
                ],
                "hubResolverExit": rc1,
                "searchFallbackExit": rc2,
                "hubReport": hub_report.name if hub_report.is_file() else None,
                "fallbackReport": fallback_report.name if fallback_report.is_file() else None,
                "logTail": (out1 + "\n" + out2)[-8000:],
            }
        )

    result = {
        "schemaVersion": 1,
        "deadlineEpochMs": deadline_ms,
        "attemptedProviders": [row["provider"] for row in attempts],
        "pendingProviders": pending,
        "attempts": attempts,
    }
    output = args.output_dir / "route-recovery-summary.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_ROUTE_QUEUE "
        f"attempted={len(attempts)} pending={len(pending)} deadline_remaining_ms={remaining_ms(deadline_ms)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
