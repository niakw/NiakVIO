#!/usr/bin/env python3
"""Select current active providers for the read-only HD/4K diagnostic.

The quality diagnostic is evidence-only. Its cohort must therefore follow the
current executable Global+France projection instead of a frozen provider list.
One best current representative is chosen per published runtime family, then a
bounded greedy pass preserves movie/tv/anime and projection diversity.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import (  # noqa: E402
    projection_active_provider_ids,
    projection_active_provider_rows,
)

CENSUS = ROOT / "automation" / "provider-census-status.json"
CATALOG = ROOT / "provider_catalog.json"
FAMILY_RE = re.compile(r'"sourceRuntimeFamily"\s*:\s*"([^"]+)"')
STATUS_RANK = {
    "FULL OK": 0,
    "PARTIAL OK": 1,
    "CHAIN REACHED": 2,
    "REGRESSION PROVIDER": 3,
    "NO PROOF": 4,
    "HARNESS MISMATCH": 5,
    "HARNESS/ENV BLOCKED": 6,
    "PROVIDER NETWORK BLOCKED": 7,
}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _types(row: dict[str, Any]) -> tuple[str, ...]:
    raw = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
    values: list[str] = []
    for item in raw if isinstance(raw, list) else []:
        value = str(item or "").strip().casefold()
        if value in {"series", "show", "other"}:
            value = "tv"
        if value in {"movie", "tv", "anime"} and value not in values:
            values.append(value)
    return tuple(sorted(values))


def _provider_path(row: dict[str, Any]) -> Path:
    relative = str(row.get("filename") or "").strip().replace("\\", "/")
    while relative.startswith("../"):
        relative = relative[3:]
    if not relative.startswith("providers/"):
        raise ValueError(f"{cid(row.get('id'))}: active provider path is not current providers/: {relative}")
    path = (ROOT / relative).resolve()
    if path.parent != (ROOT / "providers").resolve() or not path.is_file():
        raise ValueError(f"{cid(row.get('id'))}: active provider asset missing/unsafe: {relative}")
    return path


def _runtime_family(row: dict[str, Any]) -> str:
    text = _provider_path(row).read_text(encoding="utf-8")
    families = {match.group(1).strip().casefold() for match in FAMILY_RE.finditer(text) if match.group(1).strip()}
    if len(families) == 1:
        return next(iter(families))
    provider = cid(row.get("id"))
    if not families:
        return f"unknown:{provider}"
    raise ValueError(f"{provider}: multiple runtime families in published bytes: {sorted(families)}")


def _projection_kind_by_id() -> dict[str, str]:
    payload = _load(CATALOG)
    out: dict[str, str] = {}
    for record in payload.get("providers") or []:
        if not isinstance(record, dict):
            continue
        scraper = record.get("scraper") if isinstance(record.get("scraper"), dict) else {}
        projections = record.get("projections") if isinstance(record.get("projections"), dict) else {}
        provider = cid(record.get("canonicalId") or scraper.get("id"))
        if not provider:
            continue
        general = projections.get("general") is True
        vf = projections.get("vf") is True
        out[provider] = "global+vf" if general and vf else ("france-only" if vf else "global")
    return out


def _status_by_id() -> dict[str, str]:
    payload = _load(CENSUS)
    out: dict[str, str] = {}
    for row in payload.get("providers") or []:
        if not isinstance(row, dict):
            continue
        provider = cid(row.get("provider"))
        if provider:
            out[provider] = str(row.get("status") or "UNKNOWN").strip().upper()
    return out


def select(max_providers: int = 8) -> list[dict[str, Any]]:
    if max_providers < 1:
        raise ValueError("max_providers must be positive")

    rows = [dict(row) for row in projection_active_provider_rows() if isinstance(row, dict)]
    expected = projection_active_provider_ids()
    by_id = {cid(row.get("id")): row for row in rows if cid(row.get("id"))}
    if set(by_id) != expected or len(by_id) != len(rows):
        raise ValueError("quality cohort active projection is not exact/unique")

    statuses = _status_by_id()
    projections = _projection_kind_by_id()
    candidates: list[dict[str, Any]] = []
    for provider in sorted(by_id):
        row = by_id[provider]
        family = _runtime_family(row)
        types = _types(row)
        status = statuses.get(provider, "UNKNOWN")
        candidates.append({
            "provider": provider,
            "family": family,
            "types": list(types),
            "projection": projections.get(provider, "global"),
            "status": status,
            "_rank": STATUS_RANK.get(status, 8),
        })

    # Keep the strongest current evidence representative per executable runtime
    # family. A family is only a sampling dimension; it grants no transitive
    # provider/playback proof.
    per_family: dict[str, dict[str, Any]] = {}
    for row in candidates:
        key = row["family"]
        current = per_family.get(key)
        candidate_key = (row["_rank"], -len(row["types"]), row["provider"])
        if current is None or candidate_key < (
            current["_rank"], -len(current["types"]), current["provider"]
        ):
            per_family[key] = row

    pool = list(per_family.values())
    selected: list[dict[str, Any]] = []
    covered_types: set[str] = set()
    covered_projection: set[str] = set()

    while pool and len(selected) < max_providers:
        def score(row: dict[str, Any]) -> tuple[int, int, int, int, str, str]:
            new_types = len(set(row["types"]) - covered_types)
            new_projection = int(row["projection"] not in covered_projection)
            return (
                -new_types,
                -new_projection,
                int(row["_rank"]),
                -len(row["types"]),
                str(row["family"]),
                str(row["provider"]),
            )

        row = min(pool, key=score)
        pool.remove(row)
        selected.append(row)
        covered_types.update(row["types"])
        covered_projection.add(row["projection"])

    available_types = {value for row in candidates for value in row["types"]}
    if not available_types.issubset(covered_types):
        raise ValueError(
            f"quality cohort lost active media lanes: available={sorted(available_types)} "
            f"selected={sorted(covered_types)}"
        )

    result: list[dict[str, Any]] = []
    for row in selected:
        result.append({
            "provider": row["provider"],
            "family": row["family"],
            "types": row["types"],
            "projection": row["projection"],
            "status": row["status"],
        })
    if not result:
        raise ValueError("quality cohort is empty")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-providers", type=int, default=8)
    parser.add_argument("--github-matrix", action="store_true")
    args = parser.parse_args()
    rows = select(max_providers=args.max_providers)
    payload = {"include": rows}
    if args.github_matrix:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
