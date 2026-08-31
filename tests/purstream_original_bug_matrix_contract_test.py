#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
purstream = (overrides.get("provider_patches") or {}).get("purstream") or {}
capability = (overrides.get("provider_capabilities") or {}).get("purstream") or {}
recipe = purstream.get("api_recipe") or {}
playback = overrides.get("playback_integrity_policy") or {}

# Original P0 identity failures: provider-owned search must be strict and typed.
assert purstream.get("patch_scripts") == [], purstream.get("patch_scripts")
assert purstream.get("published_types") == ["movie", "tv", "anime"]
assert recipe.get("base") == "https://api.purstream.id/api/v1"
assert recipe.get("searchRoute") == "/search-bar/search/{query}"
assert recipe.get("movieRoute") == "/media/{id}/sheet"
assert recipe.get("episodeRoute") == "/stream/{id}/episode?season={season}&episode={episode}"
assert "first_air_date" in (recipe.get("yearFields") or [])
assert recipe.get("strictIdentity") is True
assert recipe.get("directSourcesOnly") is True
assert capability.get("request_type_aliases") == {"anime": "tmdb_namespace"}
assert capability.get("identity_request_source") == "original_nuvio_request"

# Native HLS guard must run immediately after the HLS wrapper.
pre_hooks = playback.get("pre_media_discovery_hooks") or []
assert pre_hooks[:2] == [
    "scripts/provider_patches/hls_runtime_integrity_v1.py",
    "scripts/provider_patches/native_hls_integrity_budget_v1.py",
], pre_hooks
assert playback.get("native_hls_probe_policy") == "skip_additional_integrity_network_probes_on_native_host_bridge"

base_store = (SCRIPTS / "provider_base_store.py").read_text(encoding="utf-8")
assert "function _collectionMediaType" in base_store
assert "__nuvioCollectionMediaType" in base_store
assert "recipe.strictIdentity" in base_store
assert "expectedTitles.includes(title)" in base_store
assert "Math.abs(Number(year) - Number(expectedYear)) > 1" in base_store
assert "recipe.directSourcesOnly" in base_store
assert "urls.filter(_directMedia)" in base_store
assert "const searchQueries = _uniq([" in base_store
assert "meta && Array.isArray(meta.aliases)" in base_store

# Clean ProviderBase consumes Core-owned TMDB context/cache only.
tmdb_block = base_store.split("async function _tmdb(tmdbId, mediaType) {", 1)[1].split("function _runtimeBases() {", 1)[0]
assert "api.themoviedb.org" not in tmdb_block
assert "TMDB_API_KEY" not in tmdb_block
assert "__nuvioMediaContext" in tmdb_block
assert "__nuvioTmdbMetadataCacheV1" in tmdb_block
assert "original_title" in tmdb_block
assert "alternative_titles" in tmdb_block

# The global provider budget must exist before canonical Core/TMDB resolution.
media_resolution = (SCRIPTS / "provider_patches" / "global_media_type_resolution_v1.py").read_text(encoding="utf-8")
install_block = media_resolution.split("var wrap=async function(){", 1)[1].split("wrap.__nuvioMediaTypeResolutionV1=true", 1)[0]
deadline_anchor = 'g.__nuvioProviderDeadlineMs=Date.now()+c.providerTimeoutMs'
resolve_anchor = "var a=await resolve(arguments)"
assert deadline_anchor in install_block
assert resolve_anchor in install_block
assert install_block.index(deadline_anchor) < install_block.index(resolve_anchor)
assert "g.fetch=budgetedFetch(previousFetch)" in install_block
assert "if(deadlineExpired())throw providerTimeoutError()" in media_resolution
compact_media_resolution = "".join(media_resolution.split())
assert "if(!a||deadlineExpired())return[];" in compact_media_resolution
assert "if(deadlineExpired())return[];" in compact_media_resolution

# Desktop compatibility is revision 5 and cannot invent TLD failovers.
desktop_compat = (SCRIPTS / "provider_patches" / "desktop_runtime_compat_v1.py").read_text(encoding="utf-8")
assert "PATCH_REVISION = 5" in desktop_compat
assert 'forbidden = {"domain_replacements", "domain_failover"}' in desktop_compat
assert "Never rewrite provider URLs/domains here." in desktop_compat
for stale_suffix in (".club", ".mx", ".ch", ".ac", ".cx", ".art", ".co", ".me", ".to", ".store"):
    assert stale_suffix not in desktop_compat

# Health execution must reproduce the Core metadata contract.
worker = (SCRIPTS / "provider_worker.cjs").read_text(encoding="utf-8")
assert "globalThis.__nuvioMediaContext = {" in worker
assert "tmdbMetadata: fixtureMetadata" in worker
assert "canonicalMediaType: canonicalType" in worker
assert "nuvioInputMediaType: inputType" in worker

# Engine-v2 regression fixture must contain separate movie/series collections.
engine_test = (ROOT / "engine_v2" / "tests" / "purstream-adapter.test.mjs").read_text(encoding="utf-8")
assert "movies: { items:" in engine_test
assert "series: { items:" in engine_test
assert "first_air_date" in engine_test
engine = (ROOT / "engine_v2" / "providers" / "purstream.mjs").read_text(encoding="utf-8")
assert "strictIdentityScore" in engine
assert "__collectionType" in engine
assert "function normalizeSource" in engine
assert 'if (!url || !/^https?:\\/\\//i.test(url)) return null;' in engine
assert 'lower.endsWith(".m3u8") || lower.endsWith(".mp4")' in engine

# Nuvio transport aliases must never erase semantic anime capability in manifests.
for manifest_path in (ROOT / "manifest.json", ROOT / "vf" / "manifest.json"):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in manifest.get("scrapers") or []:
        supported = [str(value).lower() for value in row.get("supportedTypes") or []]
        canonical = [str(value).lower() for value in row.get("canonicalSupportedTypes") or []]
        if "anime" in canonical or ("anime" in supported and canonical == []):
            assert "tv" in supported, (manifest_path, row.get("id"), supported, canonical)

# Explicit one-shot migration remains scoped to Purstream until the clean base is materialized.
trigger = ROOT / ".github" / "triggers" / "force-clean-provider-reconstruction.json"
if trigger.exists():
    request = json.loads(trigger.read_text(encoding="utf-8"))
    assert request.get("providers") == ["purstream"], request
    assert request.get("remove_after_materialization") is True

print("Purstream original bug matrix contract passed")
