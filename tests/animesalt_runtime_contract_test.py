#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/animesalt_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_ANIMESALT_RUNTIME_V1" in src
assert 'c.base+"/?s="+encodeURIComponent(m.title)' in src
assert 'action=action_select_season&season=' in src
assert '"&post="+encodeURIComponent(chosen.post)' in src
assert '/player/index.php?data=' in src
assert '"hash="+encodeURIComponent(hash)+"&r="+encodeURIComponent(c.base+"/")' in src
assert 'data.videoSource||data.securedLink' in src
assert 'semanticLanes": ["anime"]' in src
print("AnimeSalt runtime contract passed")
