#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

PLAYER = "FIELD_NATIVE_IOS_PLAYER "
SUITE = "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS "
FIXTURE_END = "FIELD_NATIVE_IOS_FIXTURE_END "
EXPECTED = {"interstellar", "breaking-bad-s01e01", "jujutsu-kaisen-s01e01"}


def parse_fields(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for token in text.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        out[key] = value
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    # This script is CI-only and intentionally accepts only the two fixed paths
    # owned by the current GitHub Actions workspace. CLI arguments are retained
    # as an explicit workflow contract, but never become filesystem authority.
    workspace = Path.cwd().resolve(strict=True)
    log_path = workspace / "mobile-ios-native-corpus.log"
    output_dir = workspace / "mobile-ios-diagnostics"
    if args.log.resolve(strict=False) != log_path:
        raise SystemExit(f"--log must be the workspace-owned iOS corpus log: {log_path}")
    if args.output_dir.resolve(strict=False) != output_dir:
        raise SystemExit(f"--output-dir must be the workspace-owned diagnosis directory: {output_dir}")

    text = log_path.read_text(encoding="utf-8", errors="replace")
    suite_lines = [line for line in text.splitlines() if SUITE in line]
    if not suite_lines or "status=completed" not in suite_lines[-1]:
        raise SystemExit("iOS native Lab did not emit a completed suite marker")

    ended: set[str] = set()
    players: list[dict] = []
    for raw in text.splitlines():
        marker = raw.find("FIELD_NATIVE_")
        if marker < 0:
            continue
        line = raw[marker:].strip()
        if line.startswith(FIXTURE_END):
            fixture = parse_fields(line[len(FIXTURE_END):]).get("fixture", "")
            if fixture:
                ended.add(fixture)
        elif line.startswith(PLAYER):
            try:
                row = json.loads(line[len(PLAYER):])
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                players.append(row)

    if ended != EXPECTED:
        raise SystemExit(
            f"incomplete iOS fixture traversal: ended={sorted(ended)} expected={sorted(EXPECTED)}"
        )

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    output_dir.mkdir(parents=True, exist_ok=True)
    for fixture in sorted(EXPECTED):
        observations = []
        for row in players:
            if str(row.get("fixture") or "") != fixture:
                continue
            state = str(row.get("state") or "unknown")
            healthy = state in {"ready", "ended"}
            observations.append(
                {
                    "client": "mobile-ios",
                    "provider": str(row.get("provider") or ""),
                    "fixture": fixture,
                    "requestType": str(row.get("mediaType") or "unknown"),
                    "routeMode": "declared",
                    "observationLayer": "player",
                    "failureClass": (
                        "healthy"
                        if healthy
                        else "reader_timeout"
                        if state == "timeout"
                        else "player_error"
                    ),
                    "readerState": state,
                    "engine": str(row.get("engine") or "nuvio-mobile-ios-production"),
                    "durationSeconds": float(row.get("durationSeconds") or 0.0),
                    "host": str(row.get("host") or ""),
                    "blocking": False,
                }
            )
        payload = {
            "schemaVersion": 1,
            "generatedAt": now,
            "evidenceComplete": True,
            "client": "mobile-ios",
            "fixture": fixture,
            "observations": observations,
        }
        (output_dir / f"mobile-ios-route-{fixture}-brain.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    healthy = sum(1 for row in players if str(row.get("state") or "") in {"ready", "ended"})
    print(
        "FIELD_NATIVE_IOS_DIAGNOSIS "
        f"fixtures={len(EXPECTED)} player_observations={len(players)} healthy={healthy}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
