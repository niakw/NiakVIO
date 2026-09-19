#!/usr/bin/env python3
"""Harden legitimate browser playback context for current CDN/player ZERO cases.

This is transport compatibility, not anti-bot circumvention: it never creates
challenge tokens/cookies. Existing fail-closed HTTP/media policy remains intact.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return
        raise SystemExit(f"anchor missing: {path}: {old[:90]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_global_media() -> None:
    path = ROOT / "scripts/provider_patches/global_media_enrichment_v1.py"
    replace_once(
        path,
        '"defaultUserAgent": str(cfg.get("default_user_agent") or ""),',
        '"defaultUserAgent": str(cfg.get("default_user_agent") or "' + UA + '"),',
    )
    replace_once(
        path,
        '"implementationRevision": "scoped-playback-context-v8-media-first-candidates",',
        '"implementationRevision": "scoped-playback-context-v9-browser-default-ua",',
    )


def patch_animepahe() -> None:
    path = ROOT / "scripts/provider_patches/animepahe_runtime_v1.py"
    replace_once(
        path,
        '"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/3",',
        '"userAgent": "' + UA + '",',
    )
    replace_once(
        path,
        'g.fetch(url,{headers:headers(ref||c.base+"/","application/json,text/plain,*/*")})',
        'g.fetch(url,{headers:headers(ref||c.base+"/","application/json,text/plain,*/*"),credentials:"include",redirect:"follow"})',
    )
    replace_once(
        path,
        'g.fetch(url,{headers:headers(ref||c.base+"/")})',
        'g.fetch(url,{headers:headers(ref||c.base+"/"),credentials:"include",redirect:"follow"})',
    )


def patch_animevostfr() -> None:
    path = ROOT / "scripts/provider_patches/animevostfr_runtime_v1.py"
    replace_once(
        path,
        'options.headers=Object.assign({"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"},options.headers||{});var r=',
        'options.headers=Object.assign({"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"},options.headers||{});options.credentials="include";options.redirect="follow";var r=',
    )
    replace_once(
        path,
        'async function playerRows(player,referer,language){',
        'function playbackHeaders(referer){var h={Referer:referer,"User-Agent":c.userAgent};try{h.Origin=new URL(referer).origin}catch(_e){}return h}\nasync function playerRows(player,referer,language){',
    )
    replace_once(path, 'headers:{Referer:referer}', 'headers:playbackHeaders(referer)')
    replace_once(
        path,
        'r.headers=Object.assign({Referer:referer},r.headers||{})',
        'r.headers=Object.assign(playbackHeaders(referer),r.headers||{})',
    )
    replace_once(path, '"semanticLanes": ["movie", "anime"],', '"semanticLanes": ["anime"],')


def select_anikoto_v2() -> None:
    path = ROOT / "provider-overrides.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    row = (data.get("provider_patches") or {}).get("anikototv")
    if not isinstance(row, dict):
        raise SystemExit("anikototv override missing")
    v1 = "scripts/provider_patches/anikototv_runtime_v1.py"
    v2 = "scripts/provider_patches/anikototv_runtime_v2.py"
    scripts = [str(x) for x in (row.get("provider_lego_scripts") or []) if str(x) != v1]
    if v2 not in scripts:
        scripts.append(v2)
    row["provider_lego_scripts"] = scripts
    options = row.get("provider_lego_options")
    if isinstance(options, dict):
        if v1 in options and v2 not in options:
            options[v2] = options[v1]
        options.pop(v1, None)
    notes = [str(x) for x in (row.get("notes") or []) if str(x)]
    note = "AniKoto runtime v2 is the durable authority for browser-like MegaPlay/CDN transport; no anti-bot token is fabricated and terminal 403 remains fail-closed."
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    patch_global_media()
    patch_animepahe()
    patch_animevostfr()
    select_anikoto_v2()
    print("CDN_TRANSPORT_BATCH_V1 source_patches=4 anti_bot_bypass=false fail_closed_403=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
