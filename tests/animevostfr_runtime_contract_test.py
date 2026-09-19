#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/"scripts/provider_patches/animevostfr_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_ANIMEVOSTFR_RUNTIME_V1" in p
assert 'c.base+"/?s="+encodeURIComponent' in p
assert '/animes\\/' in p or '/animes/' in p
assert "episodeScore" in p
assert "trembed" in p
assert "await _crawlDirectMedia([ext],players[i],2)" in p
assert 'provider:"animevostfr"' in p
print("AnimeVOSTFR runtime contract passed")
