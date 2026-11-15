#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import active_provider_ids, visible_provider_ids  # noqa: E402
from generate_language_manifests import france_only_catalog_rows  # noqa: E402

HISTORICAL_COUNT = 50


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def manifest_rows(path: Path) -> list[dict]:
    doc = load(path)
    return [row for row in doc.get("scrapers") or [] if isinstance(row, dict)]


def manifest_ids(path: Path) -> list[str]:
    rows = manifest_rows(path)
    ids = [canonical(row.get("id")) for row in rows]
    assert all(ids), f"{path}: empty provider id"
    assert len(ids) == len(set(ids)), f"{path}: duplicate provider ids"
    return ids


def assert_no_archive_paths(path: Path) -> None:
    leaked = [
        str(row.get("filename") or "")
        for row in manifest_rows(path)
        if "provider-old/" in str(row.get("filename") or "").replace("\\", "/")
    ]
    assert not leaked, f"{path}: archived provider path leaked into published projection: {leaked}"


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
# A currently-visible provider may legitimately have older generations preserved
# under provider-old/. Identity overlap is therefore expected after reactivation.
# The release invariant is path-based: no current projection may execute an
# archived provider-old artifact.
assert_no_archive_paths(ROOT / "manifest.json")

root_version = str(load(ROOT / "manifest.json").get("version") or "")
france_only_rows = france_only_catalog_rows(root=ROOT)
france_only_set = {canonical(row.get("id")) for row in france_only_rows}
assert len(france_only_set) == len(france_only_rows), "duplicate France-only catalogue identity"
assert france_only_set.isdisjoint(root_set), (
    f"France-only identity leaked into Global: {sorted(france_only_set & root_set)}"
)
union_visible = root_set | france_only_set

vf_ids = set(manifest_ids(ROOT / "vf/manifest.json"))
vf_only_actual = vf_ids - root_set
assert vf_only_actual == france_only_set, (
    f"VF-only projection drift missing={sorted(france_only_set-vf_only_actual)} "
    f"extra={sorted(vf_only_actual-france_only_set)}"
)
assert vf_ids <= union_visible

no_anime_ids = set(manifest_ids(ROOT / "no-anime/manifest.json"))
assert no_anime_ids <= root_set, (
    f"no-anime provider outside Global authority: {sorted(no_anime_ids-root_set)}"
)
vf_no_anime_ids = set(manifest_ids(ROOT / "vf-no-anime/manifest.json"))
assert vf_no_anime_ids <= vf_ids, (
    f"vf-no-anime provider outside VF authority: {sorted(vf_no_anime_ids-vf_ids)}"
)

for relative in ("vf/manifest.json", "no-anime/manifest.json", "vf-no-anime/manifest.json"):
    projection = load(ROOT / relative)
    ids = set(manifest_ids(ROOT / relative))
    assert_no_archive_paths(ROOT / relative)
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
    assert_no_archive_paths(path)
    assert str(projection.get("version") or "") == root_version, (
        f"{relative}: version drift {projection.get('version')!r} != {root_version!r}"
    )

catalog = load(ROOT / "provider_catalog.json")
catalog_ids = [canonical(row.get("canonicalId")) for row in catalog.get("providers") or [] if isinstance(row, dict)]
assert len(catalog_ids) == len(union_visible), (
    f"provider_catalog union scope drift: {len(catalog_ids)} != {len(union_visible)}"
)
assert set(catalog_ids) == union_visible, (
    "provider_catalog membership differs from Global + France-only union"
)
catalog_rows = [row for row in catalog.get("providers") or [] if isinstance(row, dict)]
catalog_archive_paths = [
    str((row.get("manifest") or {}).get("filename") or row.get("filename") or "")
    for row in catalog_rows
    if "provider-old/" in str((row.get("manifest") or {}).get("filename") or row.get("filename") or "").replace("\\", "/")
]
assert not catalog_archive_paths, f"historical provider path leaked into provider_catalog: {catalog_archive_paths}"

print(
    "release projection scope passed: "
    f"global_visible={len(visible_set)} france_only={len(france_only_set)} "
    f"union_visible={len(union_visible)} active={len(active_set)} historical={len(archive)} "
    "vf=global-subset+france-only no-anime=global-subset vf-no-anime=vf-subset "
    "hub46/native-hub46=global-active"
)
