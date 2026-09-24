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
    "Evidence block D — exact user route captures recovered from prior test files",
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
# Manual DLE evidence remains immutable history, but a later current-source/live
# domain qualification may supersede it as the executable route.
assert "Flemmix**: DLE-style search" in ledger
assert "/index.php?do=search&subaction=search&...&story=<query>" in ledger
assert flem["search_request_plan"][0]["route"]=="/search?q={query}"
assert flem["search_request_plan"][0]["base"]=="https://flemmix.party"
assert flem["search_request_plan"][0]["requestSpec"]["method"]=="GET"
assert "flemmix.cloud" in (flem.get("domain_substitutions") or {})
assert (flem.get("domain_substitutions") or {}).get("flemmix.cloud")=="flemmix.party"

uhd_src=(ROOT/"scripts/provider_patches/uhdmovies_runtime_v1.py").read_text(encoding="utf-8")
assert "/search/" in uhd_src

mugi=patches["mugiwarastream"]
assert any("/api/" in r for r in mugi.get("learned_routes") or [])

# Distinct DLE identity: never collapse AnimeSama.co into Anime-Sama.
asco=patches["animesama-co"]
assert asco["official_site"]=="https://animesama.co"
assert "/catalogue/?search={query}" in asco["learned_routes"]
assert "/template-php/defaut/fetch.php" not in asco["learned_routes"]
assert "/template-php/defaut/fetch.php" in asco.get("candidate_learned_routes", [])
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


# Block D: preserve exact manual positives that still guide current repair.
for needle in (
    "AllAnime manual positive",
    "AniKotoTV historical positive",
    "MoviesMod manual chain",
    "HDHub4u manual chain",
    "AllWish manual positive",
    "MovieBox manual positive",
):
    assert needle in ledger, needle

# 4KHDHub is not HDHub4u. Historical HDHub4u route evidence must never
# overwrite 4KHDHub provider identity or current provider-local authority.
k4=patches["4khdhub"]
assert k4["official_site"]=="https://4khdhub.one"
assert "HDHub4u are separate catalogues" in " ".join(k4.get("notes") or [])
assert all("hdhub4u" not in str(v).lower() for v in (k4.get("domain_substitutions") or {}).values())
assert all("hdhub4u" not in str(v).lower() for v in (k4.get("runtime_domain_replacements") or {}).values())

# The user-observed AllAnime One Piece positive is retained as provider-targeted
# evidence so a generic JJK catalogue miss does not dominate the census.
corpus=json.loads((ROOT/".github/triggers/nuvio-client-lab.json").read_text(encoding="utf-8"))
one_piece=[
    row for row in corpus.get("fixtures") or []
    if isinstance(row,dict)
    and str((row.get("fixture") or {}).get("title") or "").casefold()=="one piece"
    and "allanime" in {str(v or "").casefold() for v in (row.get("providers") or [])}
]
assert one_piece, "AllAnime One Piece provider-targeted fixture missing"

# MovieBox has a clean NiakVIO-owned implementation of the exact manually
# observed vidsrcme TMDB resolver chain; keep that source available even while
# activation remains fail-closed until a fresh terminal proof is reproduced.
moviebox_src=(ROOT/"scripts/provider_patches/moviebox_vidsrcme_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_MOVIEBOX_VIDSRCME_RUNTIME_V1" in moviebox_src
assert "/vs_src.php?type=" in moviebox_src

print("user manual evidence A/B/C/D cross-check passed")
