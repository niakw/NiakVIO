#!/usr/bin/env python3
"""Finalize the durable Hub46 + provider-old repository contract.

This is a consistency migration only. It never touches main implicitly and never
modifies archived ProviderBase bytes. The executable catalogue is exactly the 46
providers in hub-lab-matrix-46.json; non-hub ProviderBase history lives only in
provider-old/.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"
EXPECTED = 46


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def base_slug(path: Path) -> str:
    return re.sub(r"--base--[0-9a-f]+\.js$", "", path.name.casefold())


def replace_text(path: Path, pairs: list[tuple[str, str]]) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in pairs:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")


def fix_prune_script() -> None:
    path = ROOT / "scripts/prune_to_hub46_catalog.py"
    replace_text(path, [
        (
            "Their historical\nProviderBase bytes under provider-bases/ are deliberately preserved.",
            "Their historical\nProviderBase bytes are deliberately preserved under provider-old/.",
        ),
        (
            "assert any((ROOT / \"provider-bases\").glob(f\"{slug}--base--*.js\")), f\"missing historical ProviderBase for {slug}\"",
            "assert any((ROOT / \"provider-old\").glob(f\"{slug}--base--*.js\")), f\"missing historical ProviderBase for {slug}\"",
        ),
        (
            'for p in (ROOT / "provider-bases").glob("*--base--*.js")',
            'for p in (ROOT / "provider-old").glob("*--base--*.js")',
        ),
        (
            "The 50 providers outside automation/evidence/hub-lab-matrix-46.json are removed\nfrom active catalogue/config/materialization/repair projections. Their historical\nProviderBase bytes under provider-bases/ are deliberately preserved.",
            "The 50 providers outside automation/evidence/hub-lab-matrix-46.json are removed\nfrom active catalogue/config/materialization/repair projections. Their historical\nProviderBase bytes are archived under provider-old/ and are never part of active reconstruction.",
        ),
    ])

    # Make the one-way migration itself perform the archive separation, so a
    # future replay from a pre-migration tree cannot leave non-hub bases active.
    text = path.read_text(encoding="utf-8")
    needle = "    deleted = delete_excluded_generated_bundles(excluded)\n    patch_contract_counts()"
    if needle in text and "archive.mkdir(parents=True, exist_ok=True)" not in text:
        block = """    deleted = delete_excluded_generated_bundles(excluded)\n\n    # Historical non-hub ProviderBase bytes belong outside the active reconstruction store.\n    archive = ROOT / \"provider-old\"\n    archive.mkdir(parents=True, exist_ok=True)\n    for base in sorted((ROOT / \"provider-bases\").glob(\"*--base--*.js\")):\n        slug = re.sub(r\"--base--[0-9a-f]+\\.js$\", \"\", base.name.casefold())\n        if slug in keep_registry:\n            continue\n        target = archive / base.name\n        if target.exists():\n            if target.read_bytes() != base.read_bytes():\n                raise SystemExit(f\"provider-old collision with different bytes: {base.name}\")\n            base.unlink()\n        else:\n            base.rename(target)\n\n    patch_contract_counts()"""
        text = text.replace(needle, block, 1)
        path.write_text(text, encoding="utf-8")


def fix_current_docs() -> None:
    for rel in ("ARCHITECTURE.md", "automation/OPEN-TASKS-20260911.md", "VALIDATION.md"):
        replace_text(ROOT / rel, [
            ("historical ProviderBase bytes remain under `provider-bases/`", "historical ProviderBase bytes live under `provider-old/`"),
            ("ProviderBase historiques restent archivés sous `provider-bases/`", "ProviderBase historiques restent archivés sous `provider-old/`"),
            ("only their historical ProviderBase bytes remain under `provider-bases/`", "only their historical ProviderBase bytes remain under `provider-old/`"),
            ("ProviderBase history under `provider-bases/`", "ProviderBase history under `provider-old/`"),
        ])


def checkpoint_memory() -> None:
    path = ROOT / "MEMORY.md"
    marker = "## 2026-09-14 — Hub46 executable catalogue / provider-old archive"
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    block = f"""

{marker}

- Executable catalogue is now **exactly the 46 providers** from `automation/evidence/hub-lab-matrix-46.json`; the former 50 non-hub providers are no longer OFF rows and are absent from active manifests/catalogue/overrides/static knowledge/materialization/repair disposition.
- `automation/provider-repair-disposition.json` now carries **46 catalogue / 46 enabled / 0 disabled**; generated `providers/` bundles for the former non-hub set were removed.
- Historical non-hub ProviderBase bytes were preserved byte-for-byte but physically moved out of active reconstruction: **46 provider slugs remain in `provider-bases/`, 50 historical provider slugs live in `provider-old/`**. The archive migration moved 951 files with Git rename semantics.
- Durable migration/verification scripts: `scripts/prune_to_hub46_catalog.py` and `scripts/archive_nonhub_providerbases.py`. A replay of the prune now archives non-hub bases to `provider-old/` rather than resurrecting an OFF catalogue.
- Evidence: catalogue-prune run `34786010735` and ProviderBase archive run `34786047300` both green on `fix/labs-5.21.44-20260912`. **main was not modified.**
"""
    path.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def verify() -> None:
    matrix = load(MATRIX)
    keep_manifest = {
        cid(row.get("manifestId"))
        for row in matrix.get("rows") or []
        if isinstance(row, dict) and cid(row.get("manifestId"))
    }
    keep_registry = {
        cid(row.get("registryId"))
        for row in matrix.get("rows") or []
        if isinstance(row, dict) and cid(row.get("registryId"))
    }
    assert int(matrix.get("hubCount") or 0) == EXPECTED
    assert len(keep_manifest) == EXPECTED and len(keep_registry) == EXPECTED

    manifest = load(ROOT / "manifest.json")
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    manifest_ids = {cid(row.get("id")) for row in rows}
    assert len(rows) == EXPECTED and manifest_ids == keep_manifest
    assert all(row.get("enabled") is True for row in rows)

    catalog = load(ROOT / "provider_catalog.json")
    catalog_ids = {
        cid(row.get("canonicalId"))
        for row in catalog.get("providers") or []
        if isinstance(row, dict)
    }
    assert catalog_ids == keep_registry and len(catalog_ids) == EXPECTED

    material = load(ROOT / "provider-v3-materialization.json")
    material_ids = {
        cid(row.get("provider"))
        for row in material.get("providers") or []
        if isinstance(row, dict)
    }
    assert material_ids == keep_registry and material.get("providerCount") == EXPECTED
    assert material.get("expectedProviderCount") == EXPECTED

    disposition = load(ROOT / "automation/provider-repair-disposition.json")
    disposition_ids = {
        cid(row.get("provider"))
        for row in disposition.get("providers") or []
        if isinstance(row, dict)
    }
    assert disposition_ids == keep_registry
    assert disposition.get("catalogueProviderCount") == EXPECTED
    assert disposition.get("enabledProviderCount") == EXPECTED
    assert disposition.get("disabledProviderCount") == 0
    assert disposition.get("disabledProviders") == []

    patches = load(ROOT / "provider-overrides.json").get("provider_patches") or {}
    assert {cid(key) for key in patches} <= keep_registry
    static = load(ROOT / "automation/provider-v3-static-knowledge.json").get("providers") or {}
    assert {cid(key) for key in static} <= keep_registry

    active_slugs = {base_slug(p) for p in (ROOT / "provider-bases").glob("*--base--*.js")}
    old_slugs = {base_slug(p) for p in (ROOT / "provider-old").glob("*--base--*.js")}
    assert active_slugs == keep_registry and len(active_slugs) == EXPECTED
    assert len(old_slugs) == 50, len(old_slugs)
    assert not active_slugs & old_slugs

    for slug in old_slugs:
        assert not any((ROOT / "providers").glob(f"{slug}-*.js")), f"old generated bundle remains: {slug}"

    prune = (ROOT / "scripts/prune_to_hub46_catalog.py").read_text(encoding="utf-8")
    assert 'ROOT / "provider-old"' in prune
    assert "archive.mkdir(parents=True, exist_ok=True)" in prune
    print("HUB46_PROVIDER_OLD_CONTRACT_OK active=46 archived=50 disabled_rows=0 main_write=false")


def main() -> int:
    fix_prune_script()
    fix_current_docs()
    checkpoint_memory()
    verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
