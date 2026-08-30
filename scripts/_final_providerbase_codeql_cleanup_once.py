#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROV = ROOT / "PROVENANCE.json"
BASE_DIR = ROOT / "provider-bases"
TARGET_SOURCE = ROOT / "scripts/provider_patches/nuvio_tv_target_media_v3.py"

BASE_BASE_OLD_CLEAN = r'''function clean(v){return s(v).replace(/&amp;|&#038;/gi,"&").replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").split("\\/").join("/").replace(/\\u0026/gi,"&").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/")}'''
BASE_BASE_NEW_CLEAN = r'''function clean(v){return s(v).replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").split("\\/").join("/").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/").replace(/&amp;|&#038;/gi,"&").replace(/\\u0026/gi,"&")}'''
SOURCE_BASE_OLD_CLEAN = r'''function clean(v){return s(v).replace(/&amp;|&#038;/gi,"&").replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").replace(/\\\//g,"/").replace(/\\u0026/gi,"&").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/")}'''
SOURCE_BASE_NEW_CLEAN = r'''function clean(v){return s(v).replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").split("\\/").join("/").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/").replace(/&amp;|&#038;/gi,"&").replace(/\\u0026/gi,"&")}'''

OLD_ALERT_PATHS = {
    "provider-bases/movix--base--860cda2de2e43ee4.js",
    "provider-bases/frenchstream--base--17b877b327a7c257.js",
    "provider-bases/flemmix--base--6a4a60dd99a557fa.js",
    "provider-bases/coflix--base--ff40507ba5889296.js",
}

def patch_source() -> None:
    text = TARGET_SOURCE.read_text(encoding="utf-8")
    count = text.count(SOURCE_BASE_OLD_CLEAN)
    if count != 1:
        raise RuntimeError(f"target-media source clean() expected once, found {count}")
    TARGET_SOURCE.write_text(text.replace(SOURCE_BASE_OLD_CLEAN, SOURCE_BASE_NEW_CLEAN), encoding="utf-8")
    print("FIELD_CODEQL_CLEAN_SOURCE replacements=1")

def migrate_active_bases() -> tuple[dict, list[tuple[str,str,str]]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from provider_base_store import validate_base, write_base

    provenance = json.loads(PROV.read_text(encoding="utf-8"))
    rows = provenance.get("providers")
    if not isinstance(rows, dict) or len(rows) != 96:
        raise RuntimeError(f"expected 96 provider provenance rows, got {0 if not isinstance(rows,dict) else len(rows)}")

    changed = []
    for provider_id, row in sorted(rows.items()):
        if not isinstance(row, dict):
            raise RuntimeError(f"{provider_id}: invalid provenance row")
        rel = str(row.get("base_filename") or "")
        path = ROOT / rel
        if not rel.startswith("provider-bases/") or not path.is_file():
            raise RuntimeError(f"{provider_id}: active ProviderBase missing: {rel}")
        before = path.read_text(encoding="utf-8")
        count = before.count(BASE_OLD_CLEAN)
        if count == 0:
            continue
        if count != 1:
            raise RuntimeError(f"{provider_id}: clean() pattern occurs {count} times")
        after = before.replace(BASE_OLD_CLEAN, BASE_NEW_CLEAN)
        data = after.encode("utf-8")
        validate_base(data, provider_id)
        new_rel, digest = write_base(provider_id, data)
        row["base_filename"] = new_rel
        row["base_sha256"] = digest
        changed.append((provider_id, rel, new_rel))

    if len(changed) < 4:
        raise RuntimeError(f"expected at least 4 active ProviderBase migrations, got {len(changed)}")

    PROV.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FIELD_CODEQL_ACTIVE_CLEAN_MIGRATION changed=" + str(len(changed)) +
          " ids=" + ",".join(x[0] for x in changed))
    for provider_id, old_rel, new_rel in changed:
        print(f"FIELD_CODEQL_ACTIVE_CLEAN provider={provider_id} old={old_rel} new={new_rel}")
    return provenance, changed

def prune_unreferenced_bases(provenance: dict) -> None:
    rows = provenance.get("providers") or {}
    active = {
        str(row.get("base_filename") or "")
        for row in rows.values()
        if isinstance(row, dict)
    }
    if len(active) != 96:
        raise RuntimeError(f"active ProviderBase references are not unique: {len(active)}")

    all_bases = sorted(BASE_DIR.glob("*--base--*.js"))
    stale = [path for path in all_bases if path.relative_to(ROOT).as_posix() not in active]
    for path in stale:
        path.unlink()

    remaining = sorted(BASE_DIR.glob("*--base--*.js"))
    remaining_rel = {path.relative_to(ROOT).as_posix() for path in remaining}
    if remaining_rel != active:
        missing = sorted(active - remaining_rel)
        extra = sorted(remaining_rel - active)
        raise RuntimeError(f"ProviderBase prune mismatch missing={missing} extra={extra}")

    still_old = sorted(OLD_ALERT_PATHS & remaining_rel)
    if still_old:
        raise RuntimeError(f"old CodeQL-alert ProviderBases survived prune: {still_old}")

    print(f"FIELD_PROVIDER_BASE_GC removed={len(stale)} remaining={len(remaining)} active={len(active)}")
    for path in stale:
        print("FIELD_PROVIDER_BASE_GC_REMOVED=" + path.relative_to(ROOT).as_posix())

def verify_no_double_unescape(provenance: dict) -> None:
    for provider_id, row in (provenance.get("providers") or {}).items():
        rel = str((row or {}).get("base_filename") or "")
        text = (ROOT / rel).read_text(encoding="utf-8")
        if BASE_OLD_CLEAN in text:
            raise RuntimeError(f"{provider_id}: old double-unescape clean() remains")
    source = TARGET_SOURCE.read_text(encoding="utf-8")
    if BASE_OLD_CLEAN in source or BASE_NEW_CLEAN not in source:
        raise RuntimeError("target-media clean() source did not reach fixed point")
    print("FIELD_CODEQL_DOUBLE_UNESCAPE status=clean")

def main() -> int:
    patch_source()
    provenance, _ = migrate_active_bases()
    prune_unreferenced_bases(provenance)
    verify_no_double_unescape(provenance)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
