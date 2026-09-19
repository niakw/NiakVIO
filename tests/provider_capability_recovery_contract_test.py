#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
common=(ROOT/"scripts/provider_patches/anime_catalogue_runtime_common.py").read_text(encoding="utf-8")
assert 'c.base+"/api/anime/search?q="+encodeURIComponent' in common
assert 'if(!data)data=await json(c.base+"/api/animes/search?q="+encodeURIComponent' in common
over=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))
uhd=over["provider_patches"]["uhdmovies"]
assert uhd["published_types"]==["movie"], uhd.get("published_types")
print("AnimeVOST-FR search and UHDMovies capability contracts passed")
