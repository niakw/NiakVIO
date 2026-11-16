#!/usr/bin/env python3
"""Reconcile published media types from the canonical Provider catalogue.

The catalogue owns semantic capability. Published manifests are projections for
Nuvio transport and may add only the TV launch alias required by anime-only
providers. Global and France are independent first-class projections; France-
only providers must never be forced into Global.

This reconciler is deliberately bounded: it may update only supportedTypes and
canonicalSupportedTypes on rows whose identity/order already matches the
catalogue projection. Membership drift fails closed and must be repaired by the
manifest projection synchronizer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_language_manifests import excluded_from_no_anime

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "provider_catalog.json"
PROJECTIONS: dict[Path, tuple[str, bool]] = {
    ROOT / "manifest.json": ("general", False),
    ROOT / "vf" / "manifest.json": ("vf", False),
    ROOT / "no-anime" / "manifest.json": ("general", True),
    ROOT / "vf-no-anime" / "manifest.json": ("vf", True),
}
CANONICAL = {"movie", "tv", "anime"}


def cid(value: object) -> str:
    return str(value or "").strip().casefold()


def semantic_types(values: object, label: str) -> list[str]:
    if not isinstance(values, list) or not values:
        raise AssertionError(f"{label}: non-empty semantic media types required")
    out: list[str] = []
    for raw in values:
        item = cid(raw)
        if item not in CANONICAL:
            raise AssertionError(
                f"{label}: invalid semantic media type {item!r}; "
                "published/catalogue semantics are movie|tv|anime only"
            )
        if item in out:
            raise AssertionError(f"{label}: duplicate semantic media type {item!r}")
        out.append(item)
    return out


def transport_types(canonical: list[str]) -> list[str]:
    """Project semantic capability onto the Nuvio launch surface."""
    out = list(canonical)
    if "anime" in canonical and "tv" not in out:
        out.append("tv")
    return out


def load_catalog() -> tuple[
    dict[str, dict[str, Any]],
    dict[str, list[str]],
]:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if data.get("sourceOfTruth") is not True:
        raise AssertionError("provider_catalog.json must remain sourceOfTruth")

    providers = data.get("providers")
    if not isinstance(providers, list) or not providers:
        raise AssertionError("provider_catalog.json must contain providers")

    contract: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(providers):
        if not isinstance(entry, dict):
            raise AssertionError(f"provider_catalog.json providers[{index}] must be an object")
        canonical_id = cid(entry.get("canonicalId"))
        scraper = entry.get("scraper")
        if not canonical_id or canonical_id in contract:
            raise AssertionError(f"invalid/duplicate catalogue id: {canonical_id!r}")
        if not isinstance(scraper, dict):
            raise AssertionError(f"{canonical_id}: catalogue scraper object missing")
        scraper_id = cid(scraper.get("id"))
        if scraper_id != canonical_id:
            raise AssertionError(
                f"{canonical_id}: scraper id mismatch {scraper_id!r}"
            )

        # The catalogue stores semantic capability directly in supportedTypes.
        # Transport-only aliases belong to rendered manifests, never the source
        # catalogue. engine_v2/src/provider-catalog.mjs enforces the same rule.
        canonical = semantic_types(
            scraper.get("supportedTypes"),
            f"provider_catalog.json:{canonical_id}:supportedTypes",
        )
        if scraper.get("canonicalSupportedTypes") is not None:
            raise AssertionError(
                f"{canonical_id}: canonicalSupportedTypes must not be stored in "
                "the source catalogue; supportedTypes is semantic there"
            )

        projections = entry.get("projections")
        if not isinstance(projections, dict):
            raise AssertionError(f"{canonical_id}: projections object missing")
        general = projections.get("general") is True
        vf = projections.get("vf") is True
        if not general and not vf:
            raise AssertionError(f"{canonical_id}: provider belongs to no projection")

        contract[canonical_id] = {
            "canonical": canonical,
            "transport": transport_types(canonical),
            "scraper": scraper,
            "general": general,
            "vf": vf,
        }

    raw_orders = data.get("manifestOrder")
    if not isinstance(raw_orders, dict):
        raise AssertionError("provider_catalog.json manifestOrder must be an object")
    orders: dict[str, list[str]] = {}
    for projection in ("general", "vf"):
        raw = raw_orders.get(projection)
        if not isinstance(raw, list):
            raise AssertionError(f"manifestOrder.{projection} must be a list")
        order = [cid(value) for value in raw]
        if any(not value for value in order) or len(order) != len(set(order)):
            raise AssertionError(f"manifestOrder.{projection} contains invalid identities")
        expected = {
            provider
            for provider, row in contract.items()
            if row[projection] is True
        }
        if set(order) != expected:
            raise AssertionError(
                f"manifestOrder.{projection} membership drift "
                f"missing={sorted(expected-set(order))} "
                f"extra={sorted(set(order)-expected)}"
            )
        orders[projection] = order

    return contract, orders


def expected_projection_order(
    contract: dict[str, dict[str, Any]],
    orders: dict[str, list[str]],
    projection: str,
    no_anime: bool,
) -> list[str]:
    order = list(orders[projection])
    if not no_anime:
        return order
    return [
        provider
        for provider in order
        if not excluded_from_no_anime(contract[provider]["scraper"])
    ]


def reconcile_projection(
    path: Path,
    projection: str,
    no_anime: bool,
    contract: dict[str, dict[str, Any]],
    orders: dict[str, list[str]],
) -> tuple[dict[str, Any], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("scrapers")
    if not isinstance(rows, list):
        raise AssertionError(f"{path}: scraper list missing")

    actual_order = [cid(row.get("id")) for row in rows if isinstance(row, dict)]
    if len(actual_order) != len(rows):
        raise AssertionError(f"{path}: invalid provider row")
    if any(not value for value in actual_order) or len(actual_order) != len(set(actual_order)):
        raise AssertionError(f"{path}: empty or duplicate provider identity")

    expected_order = expected_projection_order(
        contract, orders, projection, no_anime
    )
    if actual_order != expected_order:
        raise AssertionError(
            f"{path}: projection membership/order drift; "
            "run scripts/sync_manifest_projection_rows.py before media reconciliation"
        )

    changed: list[str] = []
    for row, provider_id in zip(rows, actual_order, strict=True):
        semantic = contract[provider_id]["canonical"]
        transport = contract[provider_id]["transport"]

        before_supported = row.get("supportedTypes")
        before_canonical = row.get("canonicalSupportedTypes", None)
        row["supportedTypes"] = transport
        if transport != semantic:
            row["canonicalSupportedTypes"] = semantic
        else:
            row.pop("canonicalSupportedTypes", None)

        if (
            before_supported != row.get("supportedTypes")
            or before_canonical != row.get("canonicalSupportedTypes", None)
        ):
            changed.append(provider_id)

    return data, changed


def reconcile(apply: bool) -> dict[str, list[str]]:
    contract, orders = load_catalog()
    docs: dict[Path, dict[str, Any]] = {}
    changed_by_path: dict[Path, list[str]] = {}

    for path, (projection, no_anime) in PROJECTIONS.items():
        data, changed = reconcile_projection(
            path,
            projection,
            no_anime,
            contract,
            orders,
        )
        docs[path] = data
        changed_by_path[path] = changed

    if apply:
        for path, changed in changed_by_path.items():
            if changed:
                path.write_text(
                    json.dumps(docs[path], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

    return {
        str(path.relative_to(ROOT)): changed
        for path, changed in changed_by_path.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    contract, orders = load_catalog()
    changed = reconcile(args.apply)
    total = sum(len(values) for values in changed.values())
    details = ";".join(
        f"{path}={','.join(values) if values else '-'}"
        for path, values in changed.items()
    )
    print(
        "FIELD_PROVIDER_CATALOG_MEDIA_TYPES "
        f"mode={'apply' if args.apply else 'check'} changes={total} "
        f"catalog={len(contract)} global={len(orders['general'])} "
        f"vf={len(orders['vf'])} no_series_synthesis=true {details}"
    )
    if total and not args.apply:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
