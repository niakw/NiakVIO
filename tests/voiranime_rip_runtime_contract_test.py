#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["voiranime-rip"]
src=(ROOT/"scripts/provider_patches/voiranime_rip_runtime_v1.py").read_text(encoding="utf-8")
assert 'NIAKVIO_VOIRANIME_RIP_RUNTIME_V1' in src
assert '/template-php/defaut/fetch.php' in src
assert 'body:"query="+encodeURIComponent(q)' in src
assert '"/saison-"+q.season+"/episode-"+q.episode+"/"' in src
assert 'await _crawlDirectMedia([row.url],episodeUrl,2)' in src
assert '__niakvioProviderRuntimeResolverV1={provider:"voiranime-rip",resolve:resolve}' in src
assert "api_recipe" not in ov
assert "candidate_api_recipe" not in ov
assert ov["learned_routes"] == ["/template-php/defaut/fetch.php", "/{slug}/saison-{season}/episode-{episode}/"]
assert ov["source_runtime_family"] == "search-episode-embed"
print("VoirAnime.rip runtime contract passed")
