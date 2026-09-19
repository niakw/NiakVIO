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

vid=over["provider_patches"]["vidfast"]
assert vid["published_types"]==["movie","tv"], vid.get("published_types")
assert vid["provider_lego_scripts"]==["scripts/provider_patches/vidfast_runtime_v1.py"]
vidlego=(ROOT/"scripts/provider_patches/vidfast_runtime_v1.py").read_text(encoding="utf-8")
for token in ("NIAKVIO_VIDFAST_RUNTIME_V1", "/movie/"+'"+q.id+"/', "/tv/"+'"+q.id+"/"+q.season+"/"+q.episode+"/', "/enc-vidfast?text=", "/dec-vidfast", '"X-CSRF-Token"'):
    assert token in vidlego, token

print("AnimeVOST-FR, UHDMovies and VidFast capability contracts passed")
