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

yflix=over["provider_patches"]["yflix"]
assert yflix["provider_lego_scripts"]==["scripts/provider_patches/yflix_runtime_v1.py"]
assert "api_recipe" not in yflix and "candidate_api_recipe" not in yflix
yflixlego=(ROOT/"scripts/provider_patches/yflix_runtime_v1.py").read_text(encoding="utf-8")
for token in ("NIAKVIO_YFLIX_RUNTIME_V1", "/find?tmdb_id=", "/enc-movies-flix?text=", "/links/list?eid=", "/links/view?id=", "/dec-movies-flix", "/dec-rapid"):
    assert token in yflixlego, token

allanime=(ROOT/"scripts/provider_patches/allanime_site_runtime_v1.py").read_text(encoding="utf-8")
for token in ("d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec", '"?variables="', "persistedQuery:{version:1,sha256Hash:SOURCE_HASH}", '"https://allmanga.to"', '"https://youtu-chan.com"'):
    assert token in allanime, token
assert "SOURCE_GQL" not in allanime

anikoto=(ROOT/"scripts/provider_patches/anikototv_runtime_v2.py").read_text(encoding="utf-8")
for token in ("NIAKVIO_ANIKOTOTV_RUNTIME_V3", "https://arm.haglund.dev/api/v2/tmdb", "megaplay.buzz", "/stream/getSources?id=", "AES-CBC", "j&&j.enc", "await sourceFile(j)", '"semanticLanes": ["anime"]'):
    assert token in anikoto, token
for stale in ("/ajax/anime/search", "/ajax/episode/list/", "/ajax/server/list", "/ajax/server?get="):
    assert stale not in anikoto, stale

print("AnimeVOST-FR, UHDMovies, VidFast, YFlix, AllAnime and AniKotoTV capability contracts passed")
