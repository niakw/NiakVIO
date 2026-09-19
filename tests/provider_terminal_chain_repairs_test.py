#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
anime = (ROOT / "scripts/provider_patches/animesamaco_site_runtime_v1.py").read_text(encoding="utf-8")
neko = (ROOT / "scripts/provider_patches/neko_sama_runtime_v1.py").read_text(encoding="utf-8")

assert '"sibnetReferer": "https://video.sibnet.ru/"' in anime
assert 'c.sibnetReferer||"https://video.sibnet.ru/"' in anime
assert 'referer:episodeUrl,headers:headers(episodeUrl)' not in anime
assert 'headers:headers(ref,"video/mp4,*/*")' in anime

assert "NIAKVIO_NEKO_SEARCH_SEASON_EPLISTER_V3_TERMINAL_CRAWL" in neko
assert 'await _crawlDirectMedia([u],ep.url,2)' in neko
assert 'if(!Array.isArray(direct)||!direct.length)continue' in neko
assert 'out.push(stream(u,c.name+" ["+language+"]' not in neko

print("provider terminal chain repair contracts passed")
