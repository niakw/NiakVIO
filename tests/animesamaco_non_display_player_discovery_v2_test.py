#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "provider_patches" / "non_display_recovery_runtime_v1.py").read_text(encoding="utf-8")

assert "NIAKVIO_ANIMESAMACO_PLAYER_DISCOVERY_V2" in source
assert "videoUrls|filmUrls" in source
assert "function animeSamaPlayers(html,base)" in source
assert "var players=animeSamaPlayers(eh.text,eh.url)" in source
assert "uniq(shells.concat(players))" in source
assert "await crawl(uniq(shells.concat(players))" in source

assert "NIAKVIO_ANIMESAMACO_KEYWORD_FALLBACK_V3" in source
assert "function animeSamaFallbackQueries(titles)" in source
assert "queries=uniq(q.titles.concat(animeSamaFallbackQueries(q.titles)))" in source
assert "for(var ti=0;ti<queries.length&&ti<10;ti++)" in source
assert "for(var si=0;si<q.titles.length;si++)sc=Math.max(sc,score(label||u,q.titles[si]))" in source

# Fallback queries may broaden discovery, but ranking remains anchored to the
# original metadata titles before the fallback query itself can contribute.
assert "if(sc<35)sc=score(label||u,t)" in source

# Player pages are discovery inputs only. Every candidate must still pass
# through the bounded direct-media crawler; an iframe/embed is never emitted
# as a stream merely because it was discovered.
assert "return decorate(rows,name,language,ref)" in source
assert "_crawlDirectMedia(clean" in source

print("ANIMESAMACO_NON_DISPLAY_PLAYER_DISCOVERY_V3_OK")
