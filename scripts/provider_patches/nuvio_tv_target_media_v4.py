#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


TARGET = load_apply(ROOT / "nuvio_tv_target_media_v3.py")
EXPOSE = load_apply(ROOT / "expose_strict_wrapper_original.py")
FILTER = load_apply(ROOT / "target_media_host_filter_v4.py")

V4_MARKER = "/* NUVIO_TV_TARGET_MEDIA_V4 */"
VIDZY_DECODER_START = "function decodeVidzy(text){"
VIDZY_DECODER_END = "function genericUrls(text,base){"
GENERIC_URLS_START = "function genericUrls(text,base){"
GENERIC_URLS_END = "function normalizeRows(value){"
LEGACY_DIRECT_MEDIA_MARKER = "/* NUVIO_TV_DIRECT_MEDIA_V2"
LEGACY_DIRECT_MEDIA_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
TARGET_MEDIA_MARKER = "/* NUVIO_TV_TARGET_MEDIA_V3:"
TARGET_MEDIA_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
REJECTED_V3 = r'''function rejected(u){var h=hostname(u);return !h||ASSET.test(u)||SOCIAL.test(h)||DEMO.test(u)||/\$\{|encodeURIComponent\(|credentials:/i.test(u)}'''
STRICT_BLOCKED_HOSTS = {
    "cloudflare.com",
    "googletagmanager.com",
    "google-analytics.com",
    "analytics.google.com",
    "static.cloudflareinsights.com",
    "cloudflareinsights.com",
    "connect.facebook.net",
    "doubleclick.net",
    "googlesyndication.com",
    "pagead2.googlesyndication.com",
    "api.themoviedb.org",
    "graphql.anilist.co",
    "arm.haglund.dev",
    "v3-cinemeta.strem.io",
}
VIDZY_DECODER_V4 = r'''function decodeVidzy(text,base){var out=[];if(!/charCodeAt[\s\S]{0,420}(?:0x3d|61)[\s\S]{0,240}\*\s*89/i.test(text))return out;var host=hostname(base),H=0;for(var j=0;j<host.length;j++)H=(H+host.charCodeAt(j))&255;var hostKeyed=/\+\s*H\s*\)\s*&\s*255|\+\s*H\s*&\s*255/i.test(text),re=/["']([A-Za-z0-9+/=]{24,})["']/g,m;while((m=re.exec(text))!==null){try{var raw=typeof g.atob==="function"?g.atob(m[1]):"",rev=raw.split("").reverse().join(""),keys=hostKeyed?[H]:[0],value="";for(var k=0;k<keys.length;k++){value="";for(var i=0;i<rev.length;i++)value+=String.fromCharCode(rev.charCodeAt(i)^((0x3d+i*89+keys[k])&255));if(/^https?:\/\//i.test(value)&&!rejected(value)&&out.indexOf(value)<0){out.push(value);break}}}catch(_){}}return out}'''
LECTEURVIDEO_DECODER_V4 = r'''function decodeLecteurVideo(text,base){var out=[],seen={},re=/\bshowVideo\s*\(\s*["']([A-Za-z0-9+/=]{16,})["']/gi,m;while((m=re.exec(String(text||"")))!==null){try{var raw=typeof g.atob==="function"?g.atob(m[1]):"",u=abs(raw,base);if(u&&!rejected(u)&&!seen[u]){seen[u]=1;out.push(u)}}catch(_){}}return out}'''
GENERIC_URLS_V4 = r'''function genericUrls(text,base){var out=[],seen={};var PLAYER_HOST=/(?:^|\.)(?:vidzy\.(?:org|live|cc)|fsvid\.lol|uqload\.(?:is|co|cx)|lecteurvideo\.com|xtremestream\.xyz|megaup\.net|veev\.to|veevcdn\.co|waaw\.to|lulustream\.com|luluvdo\.com|vidmoly\.(?:me|biz)|emmmmbed\.com|ironwallnet\.net)$/i;var DIRECT=/(?:\.m3u8|\.mpd)(?:[?#]|$)|\/hls2?\//i;var MEDIA_FILE=/\.(?:mp4|mkv|webm)(?:[?#]|$)/i;var PLAYER_PATH=/(?:\/embed(?:[-./?]|$)|\/player(?:[-./?]|$)|\/e\/|\/f\/|\/video\.php(?:[?#]|$)|download\.megaup)/i;var MEDIAISH_HOST=/(?:^|\.)(?:cdn|media|video|stream|vod|edge|storage|files?|cloud)[-.]/i;function allowed(u){if(!u||rejected(u))return false;var h=hostname(u);if(DIRECT.test(u))return true;if(PLAYER_HOST.test(h))return true;if(PLAYER_PATH.test(u))return true;if(MEDIA_FILE.test(u)&&MEDIAISH_HOST.test(h))return true;return false}function add(v,front){var u=abs(v,base);if(!allowed(u)||seen[u])return;seen[u]=1;if(front)out.unshift(u);else out.push(u)}var normalized=clean(text),packed=unpackPackers(normalized);packed.forEach(function(body){decodeVidzy(body,base).forEach(function(u){add(u,true)});decodeLecteurVideo(body,base).forEach(function(u){add(u,true)});scan(body)});decodeVidzy(normalized,base).forEach(function(u){add(u,true)});decodeLecteurVideo(normalized,base).forEach(function(u){add(u,true)});scan(normalized);function scan(body){var patterns=[/(?:src|data-src|data-url|data-embed|data-player|data-link|data-file|href)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl|_fsvHls)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+)/gi],m;for(var i=0;i<patterns.length;i++){patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null)add(m[1])}}return out.slice(0,c.maxCandidates)}'''


def strip_legacy_direct_media(text: str, enabled: bool) -> str:
    """Remove only the obsolete V2 wrapper, preserving wrappers around it.

    V2 is not guaranteed to be the terminal block anymore: durable recovery can
    append catalogue and media wrappers after an older published V2 bundle.
    Truncating from the V2 marker to EOF therefore deletes freshly applied
    recovery hooks and makes the first/second reapply passes diverge.
    """
    if not enabled:
        return text
    while True:
        start = text.find(LEGACY_DIRECT_MEDIA_MARKER)
        if start < 0:
            return text
        call = text.find(LEGACY_DIRECT_MEDIA_CALL, start)
        if call < 0:
            raise RuntimeError("unterminated direct-media v2 wrapper: call boundary missing")
        end = text.find(");", call)
        if end < 0:
            raise RuntimeError("unterminated direct-media v2 wrapper: closing boundary missing")
        text = text[:start] + text[end + 2 :]


def strip_target_media_wrappers(text: str, enabled: bool) -> str:
    """Remove stale v3 wrappers once so the current v4 resolver can be outermost."""
    if not enabled:
        return text
    while True:
        start = text.find(TARGET_MEDIA_MARKER)
        if start < 0:
            return text.rstrip()
        call = text.find(TARGET_MEDIA_CALL, start)
        if call < 0:
            raise RuntimeError("unterminated target-media wrapper: call boundary missing")
        end = text.find(");", call)
        if end < 0:
            raise RuntimeError("unterminated target-media wrapper: closing boundary missing")
        text = (text[:start] + text[end + 2 :]).rstrip()


def rejected_v4(blocked_hosts: list[str]) -> str:
    payload = json.dumps(blocked_hosts, ensure_ascii=False, separators=(",", ":"))
    return (
        "function rejected(u){var h=hostname(u);"
        "if(!h||ASSET.test(u)||SOCIAL.test(h)||DEMO.test(u)||/\\/troll\\/master\\.m3u8(?:[?#]|$)/i.test(u)||/\\/(?:static\\/hero(?:[-_][^/?#]*)?\\.(?:mp4|webm|avif)|cdn-cgi\\/challenge-platform)(?:[?#]|$)/i.test(u)||/%7b|%7d|decodedlink|\\$\\{|encodeURIComponent\\(|credentials:/i.test(u))return true;"
        f"var blocked={payload};for(var bi=0;bi<blocked.length;bi++){{var rule=blocked[bi];if(h===rule||h.endsWith('.'+rule))return true}}"
        "return false}"
    )


def upgrade_player_decoders(text: str, blocked_hosts: list[str]) -> str:
    start = text.find(VIDZY_DECODER_START)
    if start >= 0:
        end = text.find(VIDZY_DECODER_END, start)
        if end < 0:
            raise RuntimeError("target media v3 decoder found without genericUrls boundary")
        replacement = VIDZY_DECODER_V4 + LECTEURVIDEO_DECODER_V4
        text = text[:start] + replacement + text[end:]

    generic_start = text.find(GENERIC_URLS_START)
    if generic_start < 0:
        raise RuntimeError("target media genericUrls() not found")
    generic_end = text.find(GENERIC_URLS_END, generic_start)
    if generic_end < 0:
        raise RuntimeError("target media normalizeRows boundary not found")
    text = text[:generic_start] + GENERIC_URLS_V4 + text[generic_end:]

    if REJECTED_V3 in text:
        text = text.replace(REJECTED_V3, rejected_v4(blocked_hosts), 1)
    elif "function rejected(u){" in text and "var blocked=" not in text:
        raise RuntimeError("unrecognized target-media rejected() implementation")
    return text


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    # Once this exact composition has been materialized, reapplying it must be a
    # byte-for-byte no-op. This is required by the override pipeline and avoids
    # moving terminal wrappers around on every refresh.
    if V4_MARKER in text:
        return text
    cfg = dict(options or {})
    blocked_hosts = sorted(
        STRICT_BLOCKED_HOSTS
        | {str(value).lower().lstrip(".") for value in cfg.get("blocked_hosts", []) if str(value).strip()}
    )
    cfg["blocked_hosts"] = blocked_hosts
    text = strip_legacy_direct_media(text, bool(cfg.get("strip_legacy_direct_media_v2")))
    text = strip_target_media_wrappers(text, bool(cfg.get("force_rewrap_target_media", False)))
    patched = TARGET(text, options=cfg, **kwargs)
    patched = upgrade_player_decoders(patched, blocked_hosts)
    patched = EXPOSE(patched)
    patched = FILTER(patched, options=cfg)
    return patched.rstrip() + "\n" + V4_MARKER + "\n"