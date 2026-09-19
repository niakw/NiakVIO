#!/usr/bin/env python3
"""Reconcile ProviderBase files with active/disabled/archive lifecycle.

No provider count is hard-coded. Identity comes from the current manifest:

* enabled provider -> provider-bases/
* disabled visible provider -> provider-disabled/provider-bases/
* provider absent from current manifest -> provider-old/provider-bases/
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
ACTIVE = ROOT / "provider-bases"
DISABLED = ROOT / "provider-disabled/provider-bases"
ARCHIVE = ROOT / "provider-old/provider-bases"


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def base_slug(path: Path) -> str:
    return re.sub(r"--base--[0-9a-f]+\.js$", "", path.name.casefold())


def move(path: Path, target_dir: Path) -> bool:
    target = target_dir / path.name
    if target.exists():
        if target.read_bytes() != path.read_bytes():
            raise SystemExit(f"ProviderBase collision with different bytes: {path} -> {target}")
        path.unlink()
        return True
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(target))
    return True


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    active_ids = {cid(row.get("id")) for row in rows if cid(row.get("id")) and row.get("enabled") is not False}
    disabled_ids = {cid(row.get("id")) for row in rows if cid(row.get("id")) and row.get("enabled") is False}
    visible_ids = active_ids | disabled_ids
    if not visible_ids:
        raise SystemExit("current provider manifest is empty")
    if active_ids & disabled_ids:
        raise SystemExit("provider cannot be active and disabled simultaneously")

    moved_active = 0
    moved_disabled = 0
    moved_archive = 0

    ACTIVE.mkdir(parents=True, exist_ok=True)
    DISABLED.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    # Anything in active bases that is no longer active moves to retention or archive.
    for path in sorted(ACTIVE.glob("*--base--*.js")):
        slug = base_slug(path)
        if slug in active_ids:
            continue
        if slug in disabled_ids:
            moved_disabled += int(move(path, DISABLED))
        else:
            moved_archive += int(move(path, ARCHIVE))

    # Reactivation restores retained bases; expired/removed identities archive.
    for path in sorted(DISABLED.glob("*--base--*.js")):
        slug = base_slug(path)
        if slug in disabled_ids:
            continue
        if slug in active_ids:
            moved_active += int(move(path, ACTIVE))
        else:
            moved_archive += int(move(path, ARCHIVE))

    active_slugs = {base_slug(p) for p in ACTIVE.glob("*--base--*.js")}
    disabled_slugs = {base_slug(p) for p in DISABLED.glob("*--base--*.js")}
    archive_slugs = {base_slug(p) for p in ARCHIVE.glob("*--base--*.js")}

    extra_active = sorted(active_slugs - active_ids)
    extra_disabled = sorted(disabled_slugs - disabled_ids)
    if extra_active:
        raise SystemExit(f"non-active ProviderBase remains in provider-bases/: {extra_active}")
    if extra_disabled:
        raise SystemExit(f"non-disabled ProviderBase remains in provider-disabled/: {extra_disabled}")
    if active_slugs & disabled_slugs:
        raise SystemExit(f"active/disabled ProviderBase overlap: {sorted(active_slugs & disabled_slugs)}")

    # Missing bases remain a separate reconstruction concern; cardinality itself is never policy.
    print(
        "PROVIDERBASE_LIFECYCLE_OK "
        f"active_ids={len(active_ids)} disabled_ids={len(disabled_ids)} "
        f"active_base_ids={len(active_slugs)} disabled_base_ids={len(disabled_slugs)} archived_base_ids={len(archive_slugs)} "
        f"moved_to_active={moved_active} moved_to_disabled={moved_disabled} moved_to_archive={moved_archive}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
