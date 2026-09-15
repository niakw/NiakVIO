#!/usr/bin/env python3
"""Reconcile Hub46 media types from the current general manifest contract.

The general manifest is the executable capability contract. Its semantic
canonicalSupportedTypes are projected to Nuvio transport supportedTypes. This
script aligns provider_catalog.json and every release projection without ever
adding/removing/reordering providers or changing any field outside those two
media-type fields.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from current_provider_scope import visible_provider_count
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "provider_catalog.json"
MANIFEST = ROOT / "manifest.json"
PROJECTIONS = (
    ROOT / "manifest.json",
    ROOT / "vf" / "manifest.json",
    ROOT / "no-anime" / "manifest.json",
    ROOT / "vf-no-anime" / "manifest.json",
)
CANONICAL = {"movie", "tv", "anime"}
TRANSPORT = CANONICAL | {"series"}
EXPECTED_CURRENT = visible_provider_count()


def norm(values: object, allowed: set[str]) -> list[str]:
    out: list[str] = []
    for value in values if isinstance(values, list) else []:
        item = str(value or "").strip().casefold()
        if item in allowed and item not in out:
            out.append(item)
    return out


def expected_transport(canonical: list[str]) -> list[str]:
    out = list(canonical)
    if ("anime" in canonical or "tv" in canonical) and "tv" not in out:
        out.append("tv")
    if ("anime" in canonical or "tv" in canonical) and "series" not in out:
        out.append("series")
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
        wanted_transport = expected_transport(canonical)
        if not canonical or not transport:
            raise AssertionError(f"{provider_id}: missing semantic/transport media contract")
        if transport != wanted_transport:
            raise AssertionError(
                f"{provider_id}: general manifest transport drift {transport} != {wanted_transport}"
            )
        if "anime" in canonical and "movie" not in canonical and "movie" in transport:
            raise AssertionError(f"{provider_id}: anime-only provider exposes fake movie transport")
        out[provider_id] = (canonical, wanted_transport)
    return out


def reconcile_catalog(contract: dict[str, tuple[list[str], list[str]]]) -> tuple[dict[str, Any], list[str]]:
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
    return data, changed


def reconcile_projection(
    path: Path,
    contract: dict[str, tuple[list[str], list[str]]],
) -> tuple[dict[str, Any], list[str]]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("scrapers") or []
    changed: list[str] = []
    seen: set[str] = set()
    for row in rows:
        provider_id = str(row.get("id") or "").strip().casefold()
        if not provider_id or provider_id in seen:
            raise AssertionError(f"{path}: invalid/duplicate provider id {provider_id!r}")
        seen.add(provider_id)
        if provider_id not in contract:
            raise AssertionError(f"{path}: historical/unknown provider leaked into current projection: {provider_id}")
        canonical, transport = contract[provider_id]
        before_canonical = norm(row.get("canonicalSupportedTypes"), CANONICAL)
        before_transport = norm(row.get("supportedTypes"), TRANSPORT)
        if before_canonical != canonical or before_transport != transport:
            row["canonicalSupportedTypes"] = canonical
            row["supportedTypes"] = transport
            changed.append(provider_id)
    return data, changed


def reconcile(apply: bool) -> dict[str, list[str]]:
    contract = manifest_contract()
    catalog_data, catalog_changed = reconcile_catalog(contract)
    projection_docs: dict[Path, dict[str, Any]] = {}
    projection_changed: dict[Path, list[str]] = {}
    for path in PROJECTIONS:
        data, changed = reconcile_projection(path, contract)
        projection_docs[path] = data
        projection_changed[path] = changed

    if apply:
        if catalog_changed:
            CATALOG.write_text(json.dumps(catalog_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for path, changed in projection_changed.items():
            if changed:
                path.write_text(json.dumps(projection_docs[path], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = {"provider_catalog.json": catalog_changed}
    for path, changed in projection_changed.items():
        result[str(path.relative_to(ROOT))] = changed
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    changed = reconcile(args.apply)
    total = sum(len(values) for values in changed.values())
    details = ";".join(
        f"{path}={','.join(values) if values else '-'}" for path, values in changed.items()
    )
    print(
        "FIELD_PROVIDER_CATALOG_MEDIA_TYPES "
        f"mode={'apply' if args.apply else 'check'} changes={total} "
        f"current={EXPECTED_CURRENT} historical=50 {details}"
    )
    if total and not args.apply:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
