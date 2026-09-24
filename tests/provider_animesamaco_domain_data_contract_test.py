#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/animesamaco_site_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["animesama-co"]

assert "NIAKVIO_ANIMESAMACO_SITE_RUNTIME_V1" in src
assert "function runtimeBase()" in src
assert 'm&&(m.officialSite||m.knownSite)||c.base' in src
assert 'runtimeBase()+"/catalogue/?search="+encodeURIComponent(t)' in src
assert 'runtimeBase()+"/template-php/defaut/fetch.php"' not in src
assert '"Referer":runtimeBase()+"/"' not in src
assert '{referer:runtimeBase()+"/"}' in src
js=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
assert js.count("c.base")==2, "only runtimeBase fallback may reference legacy cfg base"
assert ov["official_site"]=="https://animesama.co"
assert ov.get("domain_substitutions",{}).get("animesama.co") is None
assert ov.get("runtime_domain_replacements",{}).get("animesama.co") is None
assert "api_recipe" not in ov
assert "/catalogue/?search={query}" in ov["learned_routes"]
assert "/template-php/defaut/fetch.php" not in ov["learned_routes"]
assert "/template-php/defaut/fetch.php" in ov.get("candidate_learned_routes",[])
assert ov["provider_lego_scripts"]==["scripts/provider_patches/animesamaco_site_runtime_v1.py"]

print("AnimeSama-Co runtime Provider DATA domain contract passed")
