#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/"scripts/provider_patches/streamzo_runtime_v1.py").read_text(encoding="utf-8")
assert 'function stream(u,lang,quality,q)' in p
assert 'row.season=Number(q.season)||1' in p
assert 'row.episode=Number(q.episode)||1' in p
assert 'S"+String(q.season||1).padStart(2,"0")+"E"+String(q.episode||1).padStart(2,"0")' in p
assert 'resolveEmbed(vars[i].embed,vars[i].lang,hit.quality,page.url,q)' in p
assert 'resolveEmbed(e,/-vostfr' in p and 'page.url,q)' in p
print("StreamZo episodic identity contract passed")
