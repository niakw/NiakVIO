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


def _outcome_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        outcome = str(row.get("outcome") or "unknown")
        counts[outcome] = counts.get(outcome, 0) + 1
    return dict(sorted(counts.items()))


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

    # The targeted merge supplied the actual current-run scope. Its retained
    # replay rows may include 40+ older providers, even for a three-provider run.
    fresh_run = current.get("freshRunReceipt")
    fresh_run = fresh_run if isinstance(fresh_run, dict) else {}
    attempt = cur.get("lastAttempt")
    if isinstance(attempt, dict):
        attempt = copy.deepcopy(attempt)
        if fresh_run and (
            str(attempt.get("runId") or "") != str(fresh_run.get("runId") or "")
            or str(attempt.get("sourceNiakvioSha") or "") != str(fresh_run.get("sourceNiakvioSha") or "")
        ):
            attempt = None
    if not isinstance(attempt, dict):
        if fresh_run:
            selected = [
                row for row in cur_rows
                if isinstance(row.get("residentialReplayReceipt"), dict)
                and str(row["residentialReplayReceipt"].get("runId") or "") == str(fresh_run.get("runId") or "")
                and str(row["residentialReplayReceipt"].get("sourceNiakvioSha") or "")
                == str(fresh_run.get("sourceNiakvioSha") or "")
            ]
        else:
            # Legacy direct-unmerged observations remain diagnostic-only.
            selected = cur_rows if cur.get("available") is True else []
        selected_ids = sorted({_pid(row) for row in selected})
        attempt = {
            "available": cur.get("available") is True and bool(selected_ids),
            "providerCount": len(selected_ids),
            "refreshedProviders": sorted(refreshed),
            "replayedProviders": selected_ids,
            "rawProviders": sorted({_pid(row) for row in selected if int(row.get("raw") or 0) > 0}),
            "playableProviders": sorted({_pid(row) for row in selected if int(row.get("playable") or 0) > 0}),
            "verifiedProviders": sorted({_pid(row) for row in selected if int(row.get("verified") or 0) > 0}),
            "sourceNiakvioSha": str(fresh_run.get("sourceNiakvioSha") or ""),
            "runId": str(fresh_run.get("runId") or ""),
            "proofAuthority": False,
            "publicationAuthority": False,
        }
    base["lastAttempt"] = attempt
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
    out["rows"] = rows
    out["targetCount"] = len(rows)
    out["counts"] = _outcome_counts(rows)
    out["lastRefreshProviderFilter"] = (
        sorted({str(value or "").strip().casefold() for value in current.get("lastRefreshProviderFilter") or [] if str(value or "").strip()})
        if isinstance(current.get("lastRefreshProviderFilter"), list)
        else sorted(refreshed)
    )
    current_scope = set(out["lastRefreshProviderFilter"])
    current_rows = [row for row in rows if _pid(row) in current_scope]
    historical_rows = [row for row in rows if _pid(row) not in current_scope]
    out["currentRefreshProviderCount"] = len(current_scope)
    out["currentRefreshRowCount"] = len(current_rows)
    out["currentRefreshCounts"] = _outcome_counts(current_rows)
    out["historicalRetainedRowCount"] = len(historical_rows)
    out["historicalRetainedCounts"] = _outcome_counts(historical_rows)

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
        f"current_rows={int(result.get('currentRefreshRowCount') or 0)} "
        f"historical_rows={int(result.get('historicalRetainedRowCount') or 0)} "
        f"residential_available={str(bool(isinstance(res, dict) and res.get('available') is True)).lower()} "
        f"replay_rows={len((replay or {}).get('rows') or []) if isinstance(replay, dict) else 0}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
