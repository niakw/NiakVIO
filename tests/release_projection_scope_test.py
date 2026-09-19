#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import active_provider_ids, visible_provider_ids  # noqa: E402

HISTORICAL_COUNT = 50


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def manifest_ids(path: Path) -> list[str]:
    doc = load(path)
    rows = doc.get("scrapers") or []
    ids = [canonical(row.get("id")) for row in rows if isinstance(row, dict)]
    assert all(ids), f"{path}: empty provider id"
    assert len(ids) == len(set(ids)), f"{path}: duplicate provider ids"
    return ids


def archived_ids() -> set[str]:
    """Return unique historical provider identities, not every archived snapshot."""
    root = ROOT / "provider-old"
    ids: set[str] = set()
    for path in root.glob("*.js"):
        stem = path.stem
        provider_id = re.split(r"--(?:base|nuvio)--", stem, maxsplit=1)[0]
        provider_id = canonical(provider_id)
        if provider_id:
            ids.add(provider_id)
    return ids


root_ids = manifest_ids(ROOT / "manifest.json")
root_set = set(root_ids)
active_set = active_provider_ids()
visible_set = visible_provider_ids()
archive = archived_ids()

assert root_set == visible_set, (
    f"manifest visible scope drift: actual={len(root_set)} expected={len(visible_set)} "
    f"missing={sorted(visible_set-root_set)} extra={sorted(root_set-visible_set)}"
)
assert len(archive) == HISTORICAL_COUNT, f"provider-old historical scope drift: {len(archive)} != {HISTORICAL_COUNT}"
assert root_set.isdisjoint(archive), f"current/historical overlap: {sorted(root_set & archive)}"

root_version = str(load(ROOT / "manifest.json").get("version") or "")
for relative in ("vf/manifest.json", "no-anime/manifest.json", "vf-no-anime/manifest.json"):
    path = ROOT / relative
    projection = load(path)
    ids = manifest_ids(path)
    leaked = sorted(set(ids) - root_set)
    assert not leaked, f"{relative}: providers outside current manifest: {leaked}"
    archived_leak = sorted(set(ids) & archive)
    assert not archived_leak, f"{relative}: historical providers leaked into published projection: {archived_leak}"
    assert str(projection.get("version") or "") == root_version, (
        f"{relative}: version drift {projection.get('version')!r} != {root_version!r}"
    )

# The root manifest intentionally keeps disabled rows visible. Native/Hub Lab
# projections are executable transports and therefore contain active rows only.
for relative in ("manifest-hub46.json", "native-hub46/manifest.json"):
    path = ROOT / relative
    projection = load(path)
    ids = manifest_ids(path)
    assert set(ids) == active_set, (
        f"{relative}: active membership drift "
        f"actual={len(ids)} expected={len(active_set)} "
        f"missing={sorted(active_set-set(ids))} extra={sorted(set(ids)-active_set)}"
    )
    assert not (set(ids) & archive), f"{relative}: historical provider leaked into active projection"
    assert str(projection.get("version") or "") == root_version, (
        f"{relative}: version drift {projection.get('version')!r} != {root_version!r}"
    )

catalog = load(ROOT / "provider_catalog.json")
catalog_ids = [canonical(row.get("canonicalId")) for row in catalog.get("providers") or [] if isinstance(row, dict)]
assert len(catalog_ids) == len(visible_set), (
    f"provider_catalog visible scope drift: {len(catalog_ids)} != {len(visible_set)}"
)
assert set(catalog_ids) == visible_set, "provider_catalog membership differs from current visible manifest"
assert not (set(catalog_ids) & archive), "historical provider leaked into provider_catalog"

print(
    "release projection scope passed: "
    f"visible={len(visible_set)} active={len(active_set)} historical={len(archive)} "
    "vf/no-anime/vf-no-anime subset=visible hub46/native-hub46=active"
)
