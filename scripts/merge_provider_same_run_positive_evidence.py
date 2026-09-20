#!/usr/bin/env python3
"""Merge stronger same-run positive provider evidence into a current-byte portfolio.

This is deliberately monotonic and narrow:
- only identity-safe positive evidence (raw/playable/verified > 0) can be imported;
- evidence is compared per (provider_id, semantic_type);
- stronger evidence replaces weaker evidence, never the reverse;
- current-run negative observations remain in merged sample history;
- aggregate quick-yield counters are recomputed from the merged rows.

The caller is responsible for ensuring both inputs describe the same current
provider bytes/run.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def key(row: dict[str, Any]) -> tuple[str, str]:
    return cid(row.get("provider_id") or row.get("providerId")), cid(
        row.get("semantic_type") or row.get("semanticType")
    )


def identity_safe(row: dict[str, Any]) -> bool:
    return int(row.get("contradictions") or 0) == 0 and str(row.get("status") or "") != "wrong_content"


def positive_rank(row: dict[str, Any]) -> tuple[int, int, int]:
    if not identity_safe(row):
        return (0, 0, 0)
    return (
        max(0, int(row.get("verified") or 0)),
        max(0, int(row.get("playable") or 0)),
        max(0, int(row.get("raw") or 0)),
    )


def positive(row: dict[str, Any]) -> bool:
    return max(positive_rank(row)) > 0


def fixture_identity(sample: dict[str, Any]) -> str:
    fixture = sample.get("fixture") if isinstance(sample.get("fixture"), dict) else {}
    return "|".join(
        [
            cid(fixture.get("tmdbId") or fixture.get("tmdb_id")),
            cid(fixture.get("mediaType") or fixture.get("category")),
            cid(fixture.get("season")),
            cid(fixture.get("episode")),
            cid(fixture.get("slug")),
            cid(sample.get("fixture_title")),
        ]
    )


def merge_samples(primary: dict[str, Any], prior: dict[str, Any]) -> None:
    combined: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in (primary.get("samples") or [], prior.get("samples") or []):
        for source in group:
            if not isinstance(source, dict):
                continue
            marker = fixture_identity(source) or json.dumps(source, sort_keys=True, separators=(",", ":"))
            if marker in seen:
                continue
            seen.add(marker)
            combined.append(deepcopy(source))
    if combined:
        primary["samples"] = combined
        primary["sample_count"] = len(combined)
        titles: list[str] = []
        for row in combined:
            title = str(row.get("fixture_title") or "").strip()
            if title and title not in titles:
                titles.append(title)
        primary["sample_titles"] = titles


def recompute(report: dict[str, Any]) -> None:
    rows = [row for row in report.get("rows") or [] if isinstance(row, dict)]
    by_provider: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        provider_id, _media = key(row)
        if provider_id:
            by_provider.setdefault(provider_id, []).append(row)

    raw = sorted(pid for pid, vals in by_provider.items() if any(int(v.get("raw") or 0) > 0 for v in vals))
    playable = sorted(pid for pid, vals in by_provider.items() if any(int(v.get("playable") or 0) > 0 for v in vals))
    accepted = sorted(
        pid
        for pid, vals in by_provider.items()
        if any(int(v.get("playable") or 0) > 0 and identity_safe(v) for v in vals)
    )
    verified = sorted(
        pid
        for pid, vals in by_provider.items()
        if any(int(v.get("verified") or 0) > 0 and identity_safe(v) for v in vals)
    )
    wrong = sorted(pid for pid, vals in by_provider.items() if any(not identity_safe(v) for v in vals))

    report["raw_provider_count"] = len(raw)
    report["playable_provider_count"] = len(playable)
    report["accepted_playable_provider_count"] = len(accepted)
    report["verified_provider_count"] = len(verified)
    report["wrong_content_provider_count"] = len(wrong)
    report["raw_providers"] = raw
    report["playable_providers"] = playable
    report["accepted_playable_providers"] = accepted
    report["verified_providers"] = verified
    report["wrong_content_providers"] = wrong
    report["status_counts"] = dict(sorted(Counter(str(row.get("status") or "unknown") for row in rows).items()))
    report["debug_stage_counts"] = dict(sorted(Counter(str(row.get("debug_stage") or "unknown") for row in rows).items()))


def merge(base: dict[str, Any], supplement: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    output = deepcopy(base)
    rows = [deepcopy(row) for row in output.get("rows") or [] if isinstance(row, dict)]
    index = {key(row): pos for pos, row in enumerate(rows) if all(key(row))}
    applied: list[dict[str, Any]] = []

    for source in supplement.get("rows") or []:
        if not isinstance(source, dict) or not positive(source):
            continue
        row_key = key(source)
        if not all(row_key):
            continue
        pos = index.get(row_key)
        prior = rows[pos] if pos is not None else {}
        if pos is not None and positive_rank(source) <= positive_rank(prior):
            continue
        replacement = deepcopy(source)
        if prior:
            merge_samples(replacement, prior)
        replacement["same_run_positive_evidence_merge"] = {
            "source": "provider-repair-yield",
            "priorRank": list(positive_rank(prior)),
            "mergedRank": list(positive_rank(source)),
        }
        if pos is None:
            index[row_key] = len(rows)
            rows.append(replacement)
        else:
            rows[pos] = replacement
        applied.append(
            {
                "provider": row_key[0],
                "semanticType": row_key[1],
                "priorRank": list(positive_rank(prior)),
                "mergedRank": list(positive_rank(source)),
            }
        )

    output["rows"] = sorted(rows, key=lambda row: key(row))
    recompute(output)
    output["same_run_positive_evidence_merge"] = {
        "appliedCount": len(applied),
        "applied": applied,
        "policy": "identity-safe current-run evidence is monotonic by verified/playable/raw",
    }
    return output, applied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--supplement", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    merged, applied = merge(load(args.base), load(args.supplement))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_SAME_RUN_POSITIVE_MERGE "
        f"applied={len(applied)} providers={','.join(sorted({row['provider'] for row in applied})) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
