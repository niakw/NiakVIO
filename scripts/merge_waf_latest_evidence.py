#!/usr/bin/env python3
"""Merge current transport evidence into the durable WAF/Tailscale latest ledger.

Current-run GitHub/browser evidence always replaces the same provider/lane rows.
Residential evidence is replaced only when the current run actually measured it.
If Tailscale/residential probing is unavailable, previously proven residential
evidence is preserved instead of being overwritten by an empty/unavailable marker.

This ledger is diagnostic evidence only; it never grants playback authority.
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


def _pid(row: dict[str, Any]) -> str:
    return str(row.get("provider") or "").strip().casefold()


def _lane(row: dict[str, Any]) -> str:
    return str(row.get("lane") or "").strip().casefold()


def _row_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _pid(row),
        _lane(row),
        str(row.get("seedKind") or "").strip().casefold(),
        str(row.get("publicUrl") or "").strip(),
    )


def _merge_rows(previous: list[Any], current: list[Any]) -> tuple[list[dict[str, Any]], set[str]]:
    current_rows = [copy.deepcopy(row) for row in current if isinstance(row, dict) and _pid(row)]
    refreshed = {_pid(row) for row in current_rows}
    old_by_key = {
        _row_key(row): row
        for row in previous
        if isinstance(row, dict) and _pid(row)
    }

    # Preserve previous residential profile on a lane when the current run did
    # not actually produce a residential measurement for that lane.
    for row in current_rows:
        old = old_by_key.get(_row_key(row))
        if (
            isinstance(old, dict)
            and "residentialExitNodeProfile" not in row
            and isinstance(old.get("residentialExitNodeProfile"), dict)
        ):
            row["residentialExitNodeProfile"] = copy.deepcopy(old["residentialExitNodeProfile"])

    kept = [
        copy.deepcopy(row)
        for row in previous
        if isinstance(row, dict) and _pid(row) not in refreshed
    ]
    rows = kept + current_rows
    rows.sort(key=_row_key)
    return rows, refreshed


def _replay_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        copy.deepcopy(row)
        for row in summary.get("rows") or []
        if isinstance(row, dict) and _pid(row)
    ]


def _rebuild_replay(
    previous: dict[str, Any],
    current: dict[str, Any],
    refreshed: set[str],
) -> dict[str, Any]:
    prev = previous.get("residentialProviderReplay")
    cur = current.get("residentialProviderReplay")
    prev = prev if isinstance(prev, dict) else {}
    cur = cur if isinstance(cur, dict) else {}

    cur_rows = _replay_rows(cur)
    cur_providers = {_pid(row) for row in cur_rows}
    # Only replace replay evidence for providers for which the current run
    # actually produced replay rows. A Tailscale-offline run has none.
    replace = cur_providers
    rows = [
        row for row in _replay_rows(prev)
        if _pid(row) not in replace
    ] + cur_rows
    rows.sort(key=lambda row: (_pid(row), _lane(row)))

    base = copy.deepcopy(prev)
    if cur.get("available") is True:
        for key, value in cur.items():
            if key not in {
                "rows", "providers", "providerCount", "rawProviders",
                "playableProviders", "verifiedProviders", "wrongContentProviders",
            }:
                base[key] = copy.deepcopy(value)

    providers = sorted({_pid(row) for row in rows if _pid(row)})
    raw = sorted({_pid(row) for row in rows if int(row.get("raw") or 0) > 0})
    playable = sorted({_pid(row) for row in rows if int(row.get("playable") or 0) > 0})
    verified = sorted({_pid(row) for row in rows if int(row.get("verified") or 0) > 0})
    wrong = sorted({_pid(row) for row in rows if int(row.get("contradictions") or 0) > 0})
    base.update({
        "available": bool(base.get("available") is True and rows),
        "providerCount": len(providers),
        "providers": providers,
        "rawProviders": raw,
        "playableProviders": playable,
        "verifiedProviders": verified,
        "wrongContentProviders": wrong,
        "rows": rows,
    })

    if isinstance(cur, dict):
        base["lastAttempt"] = {
            "available": cur.get("available") is True,
            "providerCount": len(cur_providers),
            "refreshedProviders": sorted(refreshed),
        }
    return base


def merge(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(previous)
    for key, value in current.items():
        if key not in {
            "rows", "counts", "targetCount", "providerFilter",
            "residentialExitNodeEvidence", "residentialProviderReplay",
        }:
            out[key] = copy.deepcopy(value)

    rows, refreshed = _merge_rows(
        list(previous.get("rows") or []),
        list(current.get("rows") or []),
    )
    counts: dict[str, int] = {}
    for row in rows:
        outcome = str(row.get("outcome") or "unknown")
        counts[outcome] = counts.get(outcome, 0) + 1
    out["rows"] = rows
    out["targetCount"] = len(rows)
    out["counts"] = dict(sorted(counts.items()))
    out["lastRefreshProviderFilter"] = sorted(refreshed)

    prev_res = previous.get("residentialExitNodeEvidence")
    cur_res = current.get("residentialExitNodeEvidence")
    prev_res = prev_res if isinstance(prev_res, dict) else {}
    cur_res = cur_res if isinstance(cur_res, dict) else {}
    if cur_res.get("available") is True:
        out["residentialExitNodeEvidence"] = copy.deepcopy(cur_res)
    elif prev_res.get("available") is True:
        out["residentialExitNodeEvidence"] = copy.deepcopy(prev_res)
    elif cur_res:
        out["residentialExitNodeEvidence"] = copy.deepcopy(cur_res)
    if cur_res:
        out["residentialExitNodeLastAttempt"] = copy.deepcopy(cur_res)

    replay = _rebuild_replay(previous, current, refreshed)
    if replay:
        out["residentialProviderReplay"] = replay
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--previous", type=Path, required=True)
    ap.add_argument("--current", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = merge(load(args.previous), load(args.current))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    res = result.get("residentialExitNodeEvidence")
    replay = result.get("residentialProviderReplay")
    print(
        "FIELD_WAF_LATEST_MERGE "
        f"refreshed={len(result.get('lastRefreshProviderFilter') or [])} "
        f"rows={len(result.get('rows') or [])} "
        f"residential_available={str(bool(isinstance(res, dict) and res.get('available') is True)).lower()} "
        f"replay_rows={len((replay or {}).get('rows') or []) if isinstance(replay, dict) else 0}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
