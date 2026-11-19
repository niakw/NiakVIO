#!/usr/bin/env python3
"""Merge a targeted WAF/Tailscale refresh without dropping unrelated evidence."""
from __future__ import annotations
import argparse, copy, json
from pathlib import Path
from typing import Any


def provider_id(row: dict[str, Any]) -> str:
    return str(row.get("provider") or "").strip().casefold()


def merge_rows(base_rows: list[Any], refresh_rows: list[Any], targets: set[str]) -> list[dict[str, Any]]:
    kept = [
        copy.deepcopy(row)
        for row in base_rows
        if isinstance(row, dict) and provider_id(row) not in targets
    ]
    fresh = [
        copy.deepcopy(row)
        for row in refresh_rows
        if isinstance(row, dict) and provider_id(row) in targets
    ]
    out = kept + fresh
    out.sort(key=lambda row: (
        provider_id(row),
        str(row.get("lane") or ""),
        str(row.get("seedKind") or ""),
        str(row.get("publicUrl") or ""),
    ))
    return out



def outcome_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        outcome = str(row.get("outcome") or "unknown")
        counts[outcome] = counts.get(outcome, 0) + 1
    return dict(sorted(counts.items()))


def current_attempt_summary(refresh: dict[str, Any], targets: set[str]) -> dict[str, Any]:
    """Describe ONLY full provider replays executed by this targeted run.

    The durable history may retain many previous rows; it must not turn them
    into same-run evidence or permit Brain promotion.
    """
    summary = refresh.get("residentialProviderReplay")
    summary = summary if isinstance(summary, dict) else {}
    rows = [
        row for row in summary.get("rows") or []
        if isinstance(row, dict) and provider_id(row) in targets
    ]
    run = refresh.get("freshRunReceipt")
    run = run if isinstance(run, dict) else {}
    run_id = str(run.get("runId") or "")
    source_sha = str(run.get("sourceNiakvioSha") or "")
    ids = sorted({provider_id(row) for row in rows if provider_id(row)})
    available = summary.get("available") is True and bool(ids)

    def matching(field: str) -> list[str]:
        if not available:
            return []
        return sorted({
            provider_id(row) for row in rows
            if provider_id(row) and int(row.get(field) or 0) > 0
        })

    matched = []
    if available and run_id and source_sha:
        for row in rows:
            receipt = row.get("residentialReplayReceipt")
            digest = str(row.get("providerArtifactSha256") or "")
            if (
                isinstance(receipt, dict)
                and digest and digest == str(receipt.get("providerBundleSha256") or "")
                and str(receipt.get("runId") or "") == run_id
                and str(receipt.get("sourceNiakvioSha") or "") == source_sha
            ):
                matched.append(provider_id(row))
    return {
        "available": available,
        "providerCount": len(ids) if available else 0,
        "refreshedProviders": sorted(targets),
        "replayedProviders": ids if available else [],
        "rawProviders": matching("raw"),
        "playableProviders": matching("playable"),
        "verifiedProviders": matching("verified"),
        "byteMatchedProviders": sorted(set(matched)),
        "sourceNiakvioSha": source_sha,
        "runId": run_id,
        "proofAuthority": False,
        "publicationAuthority": False,
    }


def replay_summary(base: dict[str, Any], refresh: dict[str, Any], targets: set[str]) -> dict[str, Any]:
    base_replay = base.get("residentialProviderReplay")
    if not isinstance(base_replay, dict):
        base_replay = {}
    refresh_replay = refresh.get("residentialProviderReplay")
    if not isinstance(refresh_replay, dict):
        refresh_replay = {}

    out = copy.deepcopy(base_replay)
    for key, value in refresh_replay.items():
        if key not in {
            "rows", "providers", "providerCount", "rawProviders",
            "playableProviders", "verifiedProviders", "wrongContentProviders",
        }:
            out[key] = copy.deepcopy(value)
    rows = merge_rows(
        list(base_replay.get("rows") or []),
        list(refresh_replay.get("rows") or []),
        targets,
    )
    providers = sorted({provider_id(row) for row in rows if provider_id(row)})
    raw = sorted({
        provider_id(row) for row in rows
        if provider_id(row) and int(row.get("raw") or 0) > 0
    })
    playable = sorted({
        provider_id(row) for row in rows
        if provider_id(row) and int(row.get("playable") or 0) > 0
    })
    verified = sorted({
        provider_id(row) for row in rows
        if provider_id(row) and int(row.get("verified") or 0) > 0
    })
    wrong = sorted({
        provider_id(row) for row in rows
        if provider_id(row) and int(row.get("contradictions") or 0) > 0
    })
    out["lastAttempt"] = current_attempt_summary(refresh, targets)
    out.update({
        "providerCount": len(providers),
        "providers": providers,
        "rawProviders": raw,
        "playableProviders": playable,
        "verifiedProviders": verified,
        "wrongContentProviders": wrong,
        "rows": rows,
    })
    return out


def merge(base: dict[str, Any], refresh: dict[str, Any], targets: set[str]) -> dict[str, Any]:
    if not targets:
        raise ValueError("targeted WAF merge requires at least one provider")
    out = copy.deepcopy(base)
    for key, value in refresh.items():
        if key not in {
            "rows", "residentialProviderReplay", "counts",
            "targetCount", "providerFilter",
        }:
            out[key] = copy.deepcopy(value)
    rows = merge_rows(
        list(base.get("rows") or []),
        list(refresh.get("rows") or []),
        targets,
    )
    out["rows"] = rows
    out["targetCount"] = len(rows)
    out["counts"] = outcome_counts(rows)
    # The merged file remains the full latest ledger. Record only the cohort
    # refreshed by this execution separately.
    out["providerFilter"] = copy.deepcopy(base.get("providerFilter") or [])
    out["lastRefreshProviderFilter"] = sorted(targets)
    current_rows = [row for row in rows if provider_id(row) in targets]
    historical_rows = [row for row in rows if provider_id(row) not in targets]
    out["currentRefreshProviderCount"] = len(targets)
    out["currentRefreshRowCount"] = len(current_rows)
    out["currentRefreshCounts"] = outcome_counts(current_rows)
    out["historicalRetainedRowCount"] = len(historical_rows)
    out["historicalRetainedCounts"] = outcome_counts(historical_rows)
    out["residentialProviderReplay"] = replay_summary(base, refresh, targets)
    return out


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--baseline",type=Path,required=True)
    ap.add_argument("--refresh",type=Path,required=True)
    ap.add_argument("--providers",required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    targets={value.strip().casefold() for value in args.providers.split(",") if value.strip()}
    base=json.loads(args.baseline.read_text(encoding="utf-8"))
    refresh=json.loads(args.refresh.read_text(encoding="utf-8"))
    out=merge(base,refresh,targets)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(
        "FIELD_WAF_TARGETED_LEDGER_MERGE "
        f"refreshed={len(targets)} rows={len(out.get('rows') or [])} "
        f"current_rows={int(out.get('currentRefreshRowCount') or 0)} "
        f"historical_rows={int(out.get('historicalRetainedRowCount') or 0)} "
        f"replay_rows={len((out.get('residentialProviderReplay') or {}).get('rows') or [])}"
    )
    return 0

if __name__=="__main__":
    raise SystemExit(main())
