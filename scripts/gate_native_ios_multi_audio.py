#!/usr/bin/env python3
"""Fail closed when a proven multi-audio HLS master collapses in Nuvio iOS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MARKER = "FIELD_NATIVE_IOS_PLAYER "


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    expected = 0
    verified = 0
    collapsed: list[str] = []

    for raw in args.log.read_text(encoding="utf-8", errors="replace").splitlines():
        marker = raw.find(MARKER)
        if marker < 0:
            continue
        payload = raw[marker + len(MARKER):].strip()
        try:
            row = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue

        master_count = int(row.get("masterAudioTrackCount") or 0)
        if master_count < 2:
            continue
        expected += 1
        player_count = int(row.get("audioTrackCount") if row.get("audioTrackCount") is not None else -1)
        if player_count >= 2:
            verified += 1
            continue
        collapsed.append(
            f"{row.get('fixture') or 'unknown'}:{row.get('provider') or 'unknown'}:"
            f"master={master_count}:player={player_count}"
        )

    if collapsed:
        print(
            "FIELD_NATIVE_IOS_MULTI_AUDIO_GATE "
            f"status=fail expected={expected} verified={verified} collapsed={len(collapsed)} "
            f"details={';'.join(collapsed[:12])}"
        )
        return 2

    print(
        "FIELD_NATIVE_IOS_MULTI_AUDIO_GATE "
        f"status=pass expected={expected} verified={verified} collapsed=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
