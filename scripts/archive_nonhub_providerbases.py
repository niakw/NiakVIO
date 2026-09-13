#!/usr/bin/env python3
"""Move non-hub ProviderBase history out of the active provider-bases directory.

Active reconstruction reads provider-bases/ for the retained hub catalogue.
Providers outside the authoritative hub46 matrix are historical only and live in
provider-old/. No bytes are modified; files are renamed in-tree.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"
ACTIVE = ROOT / "provider-bases"
ARCHIVE = ROOT / "provider-old"
EXPECTED_ACTIVE = 46
EXPECTED_ARCHIVED_MIN = 50


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def base_slug(path: Path) -> str:
    return re.sub(r"--base--[0-9a-f]+\.js$", "", path.name.casefold())


def main() -> int:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    keep = {
        cid(row.get("registryId"))
        for row in matrix.get("rows") or []
        if isinstance(row, dict) and cid(row.get("registryId"))
    }
    if int(matrix.get("hubCount") or 0) != EXPECTED_ACTIVE or len(keep) != EXPECTED_ACTIVE:
        raise SystemExit(f"invalid hub46 authority: hubCount={matrix.get('hubCount')} ids={len(keep)}")

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in sorted(ACTIVE.glob("*--base--*.js")):
        slug = base_slug(path)
        if slug in keep:
            continue
        target = ARCHIVE / path.name
        if target.exists():
            if target.read_bytes() != path.read_bytes():
                raise SystemExit(f"archive collision with different bytes: {path.name}")
            path.unlink()
        else:
            path.rename(target)
        moved += 1

    active_slugs = {base_slug(p) for p in ACTIVE.glob("*--base--*.js")}
    archive_slugs = {base_slug(p) for p in ARCHIVE.glob("*--base--*.js")}

    extra_active = sorted(active_slugs - keep)
    missing_active = sorted(keep - active_slugs)
    if extra_active:
        raise SystemExit(f"non-hub ProviderBase remains active: {extra_active}")
    if missing_active:
        raise SystemExit(f"active hub ProviderBase missing: {missing_active}")
    if len(active_slugs) != EXPECTED_ACTIVE:
        raise SystemExit(f"active ProviderBase providers={len(active_slugs)} expected={EXPECTED_ACTIVE}")
    if len(archive_slugs) < EXPECTED_ARCHIVED_MIN:
        raise SystemExit(f"archived ProviderBase providers={len(archive_slugs)} expected>={EXPECTED_ARCHIVED_MIN}")
    overlap = sorted(active_slugs & archive_slugs)
    if overlap:
        raise SystemExit(f"active/archive ProviderBase overlap: {overlap}")

    print(
        "PROVIDERBASE_ARCHIVE_OK "
        f"active={len(active_slugs)} archived={len(archive_slugs)} moved_files={moved} archive=provider-old"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
