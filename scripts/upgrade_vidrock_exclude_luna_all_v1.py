#!/usr/bin/env python3
"""Exclude VidRock Luna on every declared lane after direct identity contradictions.

Evidence:
- movie: Luna previously contradicted the fixture by media filename identity;
- TV: Luna is currently playable with matching duration but contradicts Breaking Bad
  by media filename identity, while Atlas and Orion verify correctly.
ProviderBase remains untouched; this updates only the provider-owned runtime Lego.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "vidrock_runtime_v1.py"
MARKER = "NIAKVIO_VIDROCK_LUNA_ALL_LANES_EXCLUSION_V1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise AssertionError(f"{label}: boundary not found")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    original = text

    text = replace_once(
        text,
        '    Object.keys(data).forEach(function(name){if(!seenName[name]&&!(q.type==="movie"&&Array.isArray(c.movieExcludedServers)&&c.movieExcludedServers.indexOf(name)>=0)){seenName[name]=1;ordered.push(name)}});',
        '    /* ' + MARKER + ' */\n    Object.keys(data).forEach(function(name){if(!seenName[name]&&!(Array.isArray(c.excludedServers)&&c.excludedServers.indexOf(name)>=0)){seenName[name]=1;ordered.push(name)}});',
        "VidRock ordered-source exclusion",
    )
    text = replace_once(
        text,
        '      var name=ordered[i],row=data[name];if(q.type==="movie"&&Array.isArray(c.movieExcludedServers)&&c.movieExcludedServers.indexOf(name)>=0)continue;if(!row||typeof row!=="object")continue;',
        '      var name=ordered[i],row=data[name];if(Array.isArray(c.excludedServers)&&c.excludedServers.indexOf(name)>=0)continue;if(!row||typeof row!=="object")continue;',
        "VidRock loop exclusion",
    )
    text = replace_once(
        text,
        '    movie_excluded = cfg.get("movie_excluded_servers") or ["Luna"]\n    movie_order = cfg.get("movie_server_order") or [x for x in server_order if x not in movie_excluded]',
        '    excluded_all = cfg.get("excluded_servers") or ["Luna"]\n    movie_excluded = cfg.get("movie_excluded_servers") or list(excluded_all)\n    movie_order = cfg.get("movie_server_order") or [x for x in server_order if x not in movie_excluded and x not in excluded_all]',
        "VidRock Python exclusion config",
    )
    text = replace_once(
        text,
        '        "movieExcludedServers": movie_excluded,\n        "maxStreams": int(cfg.get("max_streams") or 5),',
        '        "movieExcludedServers": movie_excluded,\n        "excludedServers": excluded_all,\n        "maxStreams": int(cfg.get("max_streams") or 5),',
        "VidRock payload exclusion",
    )

    if text == original:
        return False
    TARGET.write_text(text, encoding="utf-8")
    return True


def validate() -> None:
    text = TARGET.read_text(encoding="utf-8")
    assert MARKER in text
    assert '"excludedServers": excluded_all' in text
    assert 'cfg.get("excluded_servers") or ["Luna"]' in text
    assert 'Array.isArray(c.excludedServers)' in text


def main() -> int:
    changed = patch()
    validate()
    print(f"VIDROCK_LUNA_ALL_LANES_EXCLUSION_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
