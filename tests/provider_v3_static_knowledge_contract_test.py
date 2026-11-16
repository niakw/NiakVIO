#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from current_provider_scope import (
    projection_runtime_visible_provider_count,
    projection_runtime_visible_provider_ids,
)

OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
SEEDS = ROOT / "automation" / "provider-v3-recognition-seeds.json"
EXPECTED = projection_runtime_visible_provider_count()


def canonical(value: object) -> str:
    return "".join(ch for ch in str(value or "").strip().casefold() if ch.isalnum() or ch in "-_")


overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
knowledge = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
seeds = json.loads(SEEDS.read_text(encoding="utf-8"))

assert knowledge.get("schemaVersion") == 1
assert knowledge.get("providerCount") == EXPECTED
assert knowledge.get("legacyProviderJsExecuted") is False
assert knowledge.get("upstreamJsExecuted") is False
assert knowledge.get("role") == "durable-structured-provider-data"

runtime_ids = projection_runtime_visible_provider_ids()
providers = knowledge.get("providers")
assert isinstance(providers, dict)
assert runtime_ids == set(providers), (
    sorted(runtime_ids - set(providers)),
    sorted(set(providers) - runtime_ids),
)

patches = overrides.get("provider_patches") or {}
unusable = []
routeful = 0
for provider_id in sorted(runtime_ids):
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

for provider_id in ("purstream", "hindmoviez", "4khdhub", "vidlove", "castle", "kehflix", "streamzo"):
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

# Historical providers that have left the current Global+France runtime-visible
# catalogue are not static-knowledge authority. Their old observations remain
# in archived evidence/provenance instead of being forced back into this set.

# 4KHDHub and HDHub4u are separate catalogues. The reviewed recognition seed is
# intentionally still unexecuted: merely refreshing the current site must never
# manufacture HTTP proof. The accepted strict-46 durable DATA, however, now has
# independent executed proof for the same search route and route reconstruction
# must preserve that stronger evidence rather than downgrade it back to the seed.
hub4k_seed = (seeds.get("providers") or {}).get("4khdhub") or {}
hub4k_seed_search = next(
    row for row in hub4k_seed.get("requests") or []
    if isinstance(row, dict) and row.get("route") == "/?s={query}"
)
assert hub4k_seed_search.get("executedEvidence") is False, hub4k_seed_search

hub4k = providers["4khdhub"]["model"]
assert hub4k.get("knownSite") == "https://4khdhub.one", hub4k.get("knownSite")
assert hub4k.get("officialSite") == "https://4khdhub.one", hub4k.get("officialSite")
assert hub4k.get("officialHub") == "https://4khdhub.one/", hub4k.get("officialHub")
assert "/?s={query}" in (hub4k.get("routes") or []), hub4k.get("routes")
hub4k_search = next(
    row for row in hub4k.get("routeData") or []
    if isinstance(row, dict) and row.get("route") == "/?s={query}"
)
assert hub4k_search.get("executedEvidence") is True, hub4k_search
assert hub4k_search.get("httpUsed") is True, hub4k_search
assert "current-domain-candidate-unexecuted" in (hub4k_search.get("evidenceSources") or []), hub4k_search

print(
    f"Provider v3 durable static knowledge contract passed providers={len(providers)} routeful={routeful} "
    "current_scope=exact historical_removed=archive-only "
    "4khdhub_seed=unexecuted durable_route=http-proven separate_from_hdhub4u=true"
)
