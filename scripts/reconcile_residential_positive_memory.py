#!/usr/bin/env python3
"""Retain same-byte residential playback proof across pre-provider harness failures."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

PRE_PROVIDER_STAGES = {
    "provider_zero_before_provider_network",
    "gate_runtime_plan_missing",
    "provider_waf_challenge",
    "provider_not_invoked",
    "harness_transport_blocked",
    "browser_challenge_persisted",
}


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return copy.deepcopy(default)


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def strict_verified(row: dict[str, Any]) -> bool:
    playable = max(0, int(row.get("playable") or 0))
    verified = max(0, int(row.get("verified") or 0))
    return (
        playable > 0
        and verified == playable
        and row.get("identitySafe") is True
        and max(0, int(row.get("contradictions") or 0)) == 0
    )


def manifest_files(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        canon(row.get("id")): str(row.get("filename") or "").strip()
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and canon(row.get("id")) and str(row.get("filename") or "").strip()
    }


def memory_key(row: dict[str, Any]) -> tuple[str, str]:
    return canon(row.get("provider")), canon(row.get("lane"))


def reconcile(
    waf: dict[str, Any],
    memory: dict[str, Any],
    manifest: dict[str, Any],
    *,
    source_sha: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    out = copy.deepcopy(waf)
    summary = out.get("residentialProviderReplay")
    if not isinstance(summary, dict):
        summary = {}
        out["residentialProviderReplay"] = summary
    current_rows = [
        copy.deepcopy(row)
        for row in summary.get("rows") or []
        if isinstance(row, dict) and all(memory_key(row))
    ]
    files = manifest_files(manifest)

    remembered: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in memory.get("rows") or []:
        if not isinstance(raw, dict):
            continue
        key = memory_key(raw)
        provider = key[0]
        if not all(key) or files.get(provider) != str(raw.get("publishedFile") or ""):
            continue
        if strict_verified(raw):
            remembered[key] = copy.deepcopy(raw)

    current_by_key = {memory_key(row): row for row in current_rows}

    # Current verified playback refreshes durable positive memory.
    for key, row in current_by_key.items():
        if not strict_verified(row):
            continue
        provider = key[0]
        published = files.get(provider, "")
        if not published:
            continue
        remembered[key] = {
            "provider": provider,
            "lane": key[1],
            "status": "playable_verified",
            "debugStage": "provider_returned_streams",
            "raw": max(1, int(row.get("raw") or 0)),
            "playable": max(1, int(row.get("playable") or 0)),
            "verified": max(1, int(row.get("verified") or 0)),
            "contradictions": 0,
            "identitySafe": True,
            "publishedFile": published,
            "sourceSha": str(source_sha or memory.get("sourceSha") or ""),
        }

    merged_rows: list[dict[str, Any]] = []
    retained: list[str] = []
    invalidated: list[str] = []
    for row in current_rows:
        key = memory_key(row)
        prior = remembered.get(key)
        if strict_verified(row) or prior is None:
            merged_rows.append(row)
            continue

        stage = str(row.get("debugStage") or "").strip().casefold()
        safe_zero = (
            max(0, int(row.get("raw") or 0)) == 0
            and max(0, int(row.get("playable") or 0)) == 0
            and max(0, int(row.get("verified") or 0)) == 0
            and max(0, int(row.get("contradictions") or 0)) == 0
            and row.get("identitySafe") is True
        )
        if safe_zero and stage in PRE_PROVIDER_STAGES:
            restored = {
                key: value
                for key, value in prior.items()
                if key not in {"publishedFile", "sourceSha"}
            }
            restored["retainedFromResidentialPositiveMemory"] = True
            restored["currentAttemptStage"] = stage
            restored["currentAttemptStatus"] = str(row.get("status") or "")
            merged_rows.append(restored)
            retained.append(f"{key[0]}:{key[1]}")
            continue

        # A current attempt that got beyond the pre-provider/harness boundary or
        # produced an explicit identity contradiction is allowed to invalidate
        # the old positive proof.
        if stage or int(row.get("contradictions") or 0) > 0 or row.get("identitySafe") is False:
            remembered.pop(key, None)
            invalidated.append(f"{key[0]}:{key[1]}")
        merged_rows.append(row)

    # Keep rows not replayed this run out of the WAF overlay. They remain in
    # memory only and cannot manufacture a current census promotion by absence.
    summary["rows"] = merged_rows
    strict_rows = [row for row in merged_rows if strict_verified(row)]
    summary["verifiedProviders"] = sorted({canon(row.get("provider")) for row in strict_rows})
    summary["playableProviders"] = sorted({
        canon(row.get("provider"))
        for row in merged_rows
        if int(row.get("playable") or 0) > 0
    })
    summary["rawProviders"] = sorted({
        canon(row.get("provider"))
        for row in merged_rows
        if int(row.get("raw") or 0) > 0
    })
    summary["positiveMemoryRetained"] = sorted(retained)
    summary["positiveMemoryInvalidated"] = sorted(invalidated)

    next_memory = {
        "schemaVersion": 1,
        "role": "same-byte-residential-positive-proof",
        "proofAuthority": False,
        "sourceSha": str(source_sha or memory.get("sourceSha") or ""),
        "rows": sorted(remembered.values(), key=lambda row: memory_key(row)),
    }
    return out, next_memory


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--waf", type=Path, required=True)
    ap.add_argument("--memory", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    ap.add_argument("--output-waf", type=Path, required=True)
    ap.add_argument("--output-memory", type=Path, required=True)
    ap.add_argument("--source-sha", default="")
    args = ap.parse_args()
    waf, memory = reconcile(
        load(args.waf, {}),
        load(args.memory, {"schemaVersion": 1, "rows": []}),
        load(args.manifest, {}),
        source_sha=args.source_sha,
    )
    args.output_waf.parent.mkdir(parents=True, exist_ok=True)
    args.output_memory.parent.mkdir(parents=True, exist_ok=True)
    args.output_waf.write_text(json.dumps(waf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_memory.write_text(json.dumps(memory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    replay = waf.get("residentialProviderReplay") or {}
    print(
        "FIELD_RESIDENTIAL_POSITIVE_MEMORY "
        f"retained={len(replay.get('positiveMemoryRetained') or [])} "
        f"invalidated={len(replay.get('positiveMemoryInvalidated') or [])} "
        f"memory={len(memory.get('rows') or [])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
