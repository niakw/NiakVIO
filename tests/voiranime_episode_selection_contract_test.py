#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/voiranime_anime_runtime_v2.py").read_text(encoding="utf-8")
assert "NIAKVIO_VOIRANIME_ANIME_RUNTIME_V5_MULTI_SERIES_FALLBACK" in src
assert "Number(tail[1])===Number(q.episode)" in src
assert "wp-manga-chapter|listing-chapters|list-chapter|episode|chapitre|chapter" in src
assert "indexed[q.episode-1].url" in src
assert "if(sm&&Number(sm[1])!==Number(q.season))continue" in src
print("VoirAnime episode selection contract passed")

assert "function canonicalAnime(v,base)" in src
assert "var u=canonicalAnime(m[1],base)" in src
assert 'return c.base+p.pathname+(p.search||"")+(p.hash||"")' in src
assert "async function seriesPages(q)" in src
assert 'direct.push(c.base+"/anime/"+bases[0]+"-vf/")' in src
assert 'direct.push(c.base+"/anime/"+bases[0]+"-vostfr/")' in src
assert "for(var si=0;si<seriesRows.length;si++)" in src
assert '?"VF":"VOSTFR"' in src
