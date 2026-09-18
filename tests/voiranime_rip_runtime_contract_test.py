#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/voiranime_rip_runtime_v1.py").read_text(encoding="utf-8")
assert 'NIAKVIO_VOIRANIME_RIP_RUNTIME_V1' in src
assert '/template-php/defaut/fetch.php' in src
assert 'body:"query="+encodeURIComponent(q)' in src
assert '"/saison-"+q.season+"/episode-"+q.episode+"/"' in src
assert 'await _crawlDirectMedia([row.url],episodeUrl,2)' in src
assert '__niakvioProviderRuntimeResolverV1={provider:"voiranime-rip",resolve:resolve}' in src
print("VoirAnime.rip runtime contract passed")
