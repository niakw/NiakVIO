#!/usr/bin/env python3
"""Attach private residential-exit transport evidence to the ordinary WAF report.

The residential path is evidence-only. It never records the exit-node name,
Tailscale addresses, the residential public IP, cookies, response bodies or
challenge tokens. Only bounded transport outcomes are merged back into the
provider/lane rows consumed by the census renderer.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _profile_summary(row: dict[str, Any]) -> dict[str, Any]:
    matrix = []
    for item in row.get("clientProfileMatrix") or []:
        if not isinstance(item, dict):
            continue
        matrix.append({
            "profile": str(item.get("profile") or ""),
            "outcome": str(item.get("outcome") or ""),
            "attemptCount": int(item.get("attemptCount") or 0),
        })

    def one(name: str) -> dict[str, Any] | None:
        value = row.get(name)
        if not isinstance(value, dict):
            return None
        return {
            "profile": str(value.get("profile") or ""),
            "outcome": str(value.get("outcome") or ""),
            "attemptCount": int(value.get("attemptCount") or 0),
        }

    return {
        "profile": "tailscale-residential-exit",
        "outcome": str(row.get("outcome") or ""),
        "attemptCount": int(row.get("attemptCount") or 0),
        "clientProfileMatrix": matrix,
        "directHttpProfile": one("directHttpProfile"),
        "okHttpJvmProfile": one("okHttpJvmProfile"),
        "contentProfiles": [
            str(value)
            for value in row.get("contentProfiles") or []
            if str(value)
        ],
    }


def merge_profiles(
    baseline: dict[str, Any],
    residential: dict[str, Any],
) -> dict[str, Any]:
    out = copy.deepcopy(baseline)
    rows = out.get("rows")
    if not isinstance(rows, list):
        raise ValueError("baseline WAF report rows must be a list")

    by_key = {}
    for row in residential.get("rows") or []:
        if not isinstance(row, dict):
            continue
        key = (
            str(row.get("provider") or "").strip().casefold(),
            str(row.get("lane") or "").strip().casefold(),
        )
        if all(key):
            by_key[key] = row

    matched = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = (
            str(row.get("provider") or "").strip().casefold(),
            str(row.get("lane") or "").strip().casefold(),
        )
        residential_row = by_key.get(key)
        if not residential_row:
            continue
        row["residentialExitNodeProfile"] = _profile_summary(residential_row)
        matched += 1

    out["residentialExitNodeEvidence"] = {
        "enabled": True,
        "profile": "tailscale-residential-exit",
        "matchedProviderLanes": matched,
        "privacy": {
            "exitNodeNamePersisted": False,
            "tailscaleAddressPersisted": False,
            "residentialPublicIpPersisted": False,
            "responseBodiesPersisted": False,
            "cookiesPersisted": False,
        },
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--residential", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    merged = merge_profiles(load(args.baseline), load(args.residential))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_WAF_RESIDENTIAL_PROFILE_MERGE "
        f"matched={int((merged.get('residentialExitNodeEvidence') or {}).get('matchedProviderLanes') or 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
