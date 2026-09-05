#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
EXPECTED = 96


def canonical(value: object) -> str:
    return "".join(ch for ch in str(value or "").strip().casefold() if ch.isalnum() or ch in "-_")


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
knowledge = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))

assert knowledge.get("schemaVersion") == 1
assert knowledge.get("providerCount") == EXPECTED
assert knowledge.get("legacyProviderJsExecuted") is False
assert knowledge.get("upstreamJsExecuted") is False
assert knowledge.get("role") == "durable-structured-provider-data"

manifest_ids = {
    canonical(row.get("id"))
    for row in manifest.get("scrapers") or []
    if isinstance(row, dict)
}
providers = knowledge.get("providers")
assert isinstance(providers, dict)
assert manifest_ids == set(providers), (sorted(manifest_ids - set(providers)), sorted(set(providers) - manifest_ids))

patches = overrides.get("provider_patches") or {}
unusable = []
routeful = 0
for provider_id in sorted(manifest_ids):
    row = providers[provider_id]
    assert row.get("legacyProviderJsExecuted") is False
    assert row.get("upstreamJsExecuted") is False
    model = row.get("model")
    assert isinstance(model, dict)
    sources = row.get("sources")
    assert isinstance(sources, list) and sources, provider_id
    assert all(source.get("codeRole") == "knowledge-only" and source.get("codeExecuted") is False for source in sources)

    if model.get("routes"):
        routeful += 1
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    has_plan = bool(
        model.get("knownSite")
        or model.get("officialSite")
        or model.get("officialApi")
        or model.get("fixedApi")
        or model.get("routes")
        or model.get("observedUrls")
        or model.get("origins")
        or isinstance(model.get("apiRecipe"), dict)
        or (isinstance(patch.get("api_recipe"), dict))
        or (isinstance(patch.get("provider_lego_scripts"), list) and patch.get("provider_lego_scripts"))
    )
    if not has_plan:
        unusable.append(provider_id)

assert not unusable, unusable
assert routeful >= 30, routeful

for provider_id in ("purstream", "vegamovies", "hindmoviez", "4khdhub", "animezey", "4khdhubnew", "vidlove", "castle", "kehflix", "streamzo"):
    assert provider_id in providers
    model = providers[provider_id]["model"]
    assert any(
        [
            model.get("routes"),
            model.get("observedUrls"),
            model.get("origins"),
            model.get("knownSite"),
            model.get("officialApi"),
            isinstance(model.get("apiRecipe"), dict),
            (patches.get(provider_id) or {}).get("provider_lego_scripts"),
        ]
    ), provider_id

# Current-site authority and route execution evidence are deliberately separate.
# The reviewed seed may refresh VegaMovies' terminal before the live loop, but
# /?s={query} must remain an unexecuted candidate until the N-to-N probe calls it.
vega = providers["vegamovies"]["model"]
assert vega.get("knownSite") == "https://new2.vegamovies.futbol", vega.get("knownSite")
assert vega.get("officialSite") == "https://new2.vegamovies.futbol", vega.get("officialSite")
assert vega.get("officialHub") == "https://vglist.top/", vega.get("officialHub")
assert "/?s={query}" in (vega.get("routes") or []), vega.get("routes")
vega_search = next(
    row for row in vega.get("routeData") or []
    if isinstance(row, dict) and row.get("route") == "/?s={query}"
)
assert vega_search.get("executedEvidence") is False, vega_search
assert vega_search.get("httpUsed") is False, vega_search
assert "current-domain-candidate-unexecuted" in (vega_search.get("evidenceSources") or []), vega_search

# 4KHDHub and HDHub4u are separate catalogues. Reviewed authority must keep
# provider 4khdhub on 4khdhub.one and must not treat the site refresh as HTTP proof.
hub4k = providers["4khdhub"]["model"]
assert hub4k.get("knownSite") == "https://4khdhub.one", hub4k.get("knownSite")
assert hub4k.get("officialSite") == "https://4khdhub.one", hub4k.get("officialSite")
assert hub4k.get("officialHub") == "https://4khdhub.one/", hub4k.get("officialHub")
assert "/?s={query}" in (hub4k.get("routes") or []), hub4k.get("routes")
hub4k_search = next(
    row for row in hub4k.get("routeData") or []
    if isinstance(row, dict) and row.get("route") == "/?s={query}"
)
assert hub4k_search.get("executedEvidence") is False, hub4k_search
assert hub4k_search.get("httpUsed") is False, hub4k_search

print(
    f"Provider v3 durable static knowledge contract passed providers={len(providers)} routeful={routeful} "
    "vegamovies_current_domain=reviewed route_candidate=unexecuted "
    "4khdhub_current_domain=reviewed separate_from_hdhub4u=true"
)
