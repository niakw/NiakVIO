#!/usr/bin/env python3
"""Reconcile provider_catalog media types from the current 46-provider manifest.

The general manifest is the current executable projection. Its
canonicalSupportedTypes describe semantic capability (movie/tv/anime), while
supportedTypes contains the Nuvio transport aliases (including series and TV for
anime). This script copies only those two type fields back into the catalog; it
never adds/removes providers or changes projections/order.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "provider_catalog.json"
MANIFEST = ROOT / "manifest.json"
CANONICAL = {"movie", "tv", "anime"}
TRANSPORT = CANONICAL | {"series"}
EXPECTED_CURRENT = 46


def norm(values: object, allowed: set[str]) -> list[str]:
    out: list[str] = []
    for value in values if isinstance(values, list) else []:
        item = str(value or "").strip().casefold()
        if item in allowed and item not in out:
            out.append(item)
    return out


def manifest_contract() -> dict[str, tuple[list[str], list[str]]]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = data.get("scrapers") or []
    if len(rows) != EXPECTED_CURRENT:
        raise AssertionError(f"current manifest providers={len(rows)} expected={EXPECTED_CURRENT}")
    out: dict[str, tuple[list[str], list[str]]] = {}
    for row in rows:
        provider_id = str(row.get("id") or "").strip().casefold()
        if not provider_id or provider_id in out:
            raise AssertionError(f"invalid/duplicate manifest provider id: {provider_id!r}")
        transport = norm(row.get("supportedTypes"), TRANSPORT)
        canonical = norm(row.get("canonicalSupportedTypes"), CANONICAL)
        if not canonical:
            canonical = [value for value in transport if value != "series"]
        if not canonical or not transport:
            raise AssertionError(f"{provider_id}: missing semantic/transport media contract")
        if "anime" in canonical and "movie" not in canonical and "movie" in transport:
            raise AssertionError(f"{provider_id}: anime-only provider exposes fake movie transport")
        out[provider_id] = (canonical, transport)
    return out


def reconcile(apply: bool) -> list[str]:
    contract = manifest_contract()
    data: dict[str, Any] = json.loads(CATALOG.read_text(encoding="utf-8"))
    if data.get("sourceOfTruth") is not True:
        raise AssertionError("provider_catalog.json must remain sourceOfTruth")
    providers = data.get("providers") or []
    if len(providers) != EXPECTED_CURRENT:
        raise AssertionError(f"catalog providers={len(providers)} expected={EXPECTED_CURRENT}")

    changed: list[str] = []
    seen: set[str] = set()
    for entry in providers:
        scraper = entry.get("scraper") if isinstance(entry, dict) else None
        if not isinstance(scraper, dict):
            raise AssertionError("catalog provider missing scraper object")
        provider_id = str(scraper.get("id") or "").strip().casefold()
        if not provider_id or provider_id in seen:
            raise AssertionError(f"invalid/duplicate catalog scraper id: {provider_id!r}")
        seen.add(provider_id)
        if provider_id not in contract:
            raise AssertionError(f"catalog provider absent from current manifest: {provider_id}")
        canonical, transport = contract[provider_id]
        before_canonical = norm(scraper.get("canonicalSupportedTypes"), CANONICAL)
        before_transport = norm(scraper.get("supportedTypes"), TRANSPORT)
        if before_canonical != canonical or before_transport != transport:
            scraper["canonicalSupportedTypes"] = canonical
            scraper["supportedTypes"] = transport
            changed.append(provider_id)

    missing = sorted(set(contract) - seen)
    if missing:
        raise AssertionError(f"current manifest providers absent from catalog: {missing}")

    if apply and changed:
        CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    changed = reconcile(args.apply)
    print(
        "FIELD_PROVIDER_CATALOG_MEDIA_TYPES "
        f"mode={'apply' if args.apply else 'check'} changed={len(changed)} "
        f"providers={','.join(changed) if changed else '-'} current={EXPECTED_CURRENT} historical=50"
    )
    if changed and not args.apply:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
