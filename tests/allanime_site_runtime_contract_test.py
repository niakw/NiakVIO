#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/allanime_site_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["allanime"]

assert "NIAKVIO_ALLANIME_SITE_RUNTIME_V1" in src
assert 'function base()' in src
assert 'm&&(m.officialSite||m.knownSite)||c.base' in src
assert 'base()+"/?s="+encodeURIComponent(meta.title)' in src
assert '-episode-' in src
assert '.m3u8' in src
assert '^#EXTM3U' in src
assert 'provider:"allanime",resolve:resolve' in src
assert ov["official_site"]=="https://ww2.aniwatch.fit"
assert ov["provider_lego_scripts"]==["scripts/provider_patches/allanime_site_runtime_v1.py"]
assert ov["source_runtime_family"]=="catalogue-html"

print("AllAnime current-site runtime contract passed")
