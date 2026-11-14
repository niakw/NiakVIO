#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/"scripts/provider_patches/streamzo_runtime_v1.py").read_text(encoding="utf-8")
assert 'function stream(u,lang,quality,q,player)' in p
assert 'function seasonCoord(v)' in p
assert 'function episodeCoord(v)' in p
assert 'row.season=q.season;row.episode=q.episode' in p
assert 'S"+String(q.season).padStart(2,"0")+"E"+String(q.episode).padStart(2,"0")' in p
assert 'q.season||1' not in p
assert 'Number(q.season)||1' not in p
assert 'resolveEmbed(vars[i].embed,vars[i].lang,hit.quality,page.url,q,vars[i].player)' in p
assert 'movieRows=await resolveEmbed(embeds[mi].embed,movieLang,hit.quality,page.url,q,embeds[mi].player)' in p
assert 'out.length<8' in p
assert 'movieOut.length<8' in p
assert 'if(rows[j]&&rows[j].url&&!seen[rows[j].url])' in p
assert 'row.sourceLabel=label' in p
assert 'x.sourceLabel=x.sourceLabel||player' in p
print("StreamZo episodic identity contract passed")
