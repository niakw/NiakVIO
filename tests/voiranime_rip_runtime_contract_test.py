#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
ROOT=Path(__file__).resolve().parents[1]
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["voiranime-rip"]
src=(ROOT/"scripts/provider_patches/voiranime_rip_runtime_v1.py").read_text(encoding="utf-8")
assert 'NIAKVIO_VOIRANIME_RIP_RUNTIME_V1' in src
assert '/template-php/defaut/fetch.php' in src
assert "va-search-result-title" in src
assert "function attr(" in src
assert "function fallbackQueries" in src
assert "function seasonHint" in src
assert "base-=180" in src
assert "return200" not in src and "return140" not in src
assert 'body:"query="+encodeURIComponent(query)' in src
assert '"/saison-"+q.season+"/episode-"+q.episode+"/"' in src
assert 'await _crawlDirectMedia([row.url],episodeUrl,2)' in src
assert '__niakvioProviderRuntimeResolverV1={provider:"voiranime-rip",resolve:resolve}' in src
assert "api_recipe" not in ov
assert "candidate_api_recipe" not in ov
assert ov["learned_routes"] == ["/template-php/defaut/fetch.php", "/{slug}/saison-{season}/episode-{episode}/"]
assert ov["source_runtime_family"] == "search-episode-embed"
js=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0].replace("CONFIG_PLACEHOLDER","{}")
subprocess.run(["node","-e","new Function(process.argv[1]);",js],check=True)
print("VoirAnime.rip runtime contract passed")
