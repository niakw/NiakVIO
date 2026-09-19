#!/usr/bin/env python3
"""Cross-check durable user manual evidence against current provider-local route contracts.

Historical domains are not asserted here. Only provider-local route/family anchors that
remain intentionally current are protected so Domain Refresh can rotate terminals
without erasing known execution structure.
"""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
ledger=(ROOT/"automation/USER-PROVIDER-EVIDENCE-LEDGER.md").read_text(encoding="utf-8")
patches=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]

for block in (
    "Evidence block A — live TV/Desktop behavior",
    "Evidence block B — browser route/hub captures",
    "Evidence block C — older VF/runtime diagnostics",
):
    assert block in ledger, block

# Block B: current provider-local route families.
animesalt_src=(ROOT/"scripts/provider_patches/animesalt_runtime_v1.py").read_text(encoding="utf-8")
assert "action_tr_search_suggest" in animesalt_src
assert "/wp-admin/admin-ajax.php" in animesalt_src

vost=patches["vostfree"]
assert vost["search_request_plan"][0]["route"]=="/index.php"
assert vost["search_request_plan"][0]["requestSpec"]["method"]=="POST"
vost_src=(ROOT/"scripts/provider_patches/vostfree_dle_uqload_runtime_v1.py").read_text(encoding="utf-8")
assert "sibnet" in vost_src.lower() and "uqload" in vost_src.lower()

flem=patches["flemmix"]
assert flem["search_request_plan"][0]["route"]=="/index.php?do=search&subaction=search&search_start=0&full_search=0&story={query}"
assert flem["search_request_plan"][0]["requestSpec"]["method"]=="GET"

uhd_src=(ROOT/"scripts/provider_patches/uhdmovies_runtime_v1.py").read_text(encoding="utf-8")
assert "/search/" in uhd_src

mugi=patches["mugiwarastream"]
assert any("/api/" in r for r in mugi.get("learned_routes") or [])

# Distinct DLE identity: never collapse AnimeSama.co into Anime-Sama.
asco=patches["animesama-co"]
assert asco["official_site"]=="https://animesama.co"
assert "/template-php/defaut/fetch.php" in asco["learned_routes"]
assert "/anime/{id}-{slug}.html" in asco["learned_routes"]
assert asco.get("domain_substitutions",{}).get("animesama.co") is None
assert asco.get("runtime_domain_replacements",{}).get("animesama.co") is None
assert "api_recipe" not in asco

# Block C: preserve the observed StreamZo/Videasy player family.
streamzo=patches["streamzo"]
recipe=streamzo.get("api_recipe") or {}
assert "videasy" in json.dumps(recipe).lower(), recipe

# Dedicated provider-local runtimes must not silently reacquire generic ARM.
sekai=patches["sekai"]
assert sekai["official_site"]=="https://sekai.one"
assert sekai["learned_routes"]==["/sitemap.xml","/{slug}"]
assert "api_recipe" not in sekai

for provider in ("vostfree","flemmix","animesama-co","sekai"):
    assert "api_recipe" not in patches[provider], provider

print("user manual evidence A/B/C cross-check passed")
