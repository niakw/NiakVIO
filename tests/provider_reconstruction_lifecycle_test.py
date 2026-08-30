#!/usr/bin/env python3
"""Lifecycle contracts for ProviderBase onboarding and explicit reconstruction."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import discover_candidates as discovery  # noqa: E402
import provider_base_store as base_store  # noqa: E402
import reapply_published_overrides as reapply  # noqa: E402

overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
provenance = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

# 1) A brand-new provider gets one NiakVIO-owned clean seed even without a
# periodic rebuild flag. Upstream JavaScript remains structured knowledge only.
fresh_entry = {
    "id": "fresh-provider",
    "name": "Fresh Provider",
    "supportedTypes": ["movie", "tv"],
    "formats": ["m3u8", "mp4"],
}
fresh_source = (
    "const api='https://freshprovider.dev/api/v1';"
    "const search='/search/';"
    "const stream='/stream/';"
    "module.exports={getStreams};"
).encode()
(
    fresh_seed,
    fresh_origin,
    fresh_site,
    fresh_reconstruction,
    fresh_knowledge,
    fresh_model,
) = discovery.executable_seed(
    "fresh-provider",
    fresh_entry,
    fresh_source,
    {},
    overrides,
    clean_reconstruction=False,
    force_clean_reconstruction=False,
)
assert fresh_origin == "new-niakvio-clean-seed"
assert fresh_reconstruction is True
expected_fresh_seed = base_store.build_clean_provider_seed(
    "fresh-provider",
    discovery.reconstruction_manifest_entry("fresh-provider", fresh_entry, overrides),
    known_site=fresh_site,
    provider_model=fresh_model,
)
assert fresh_seed == expected_fresh_seed, (
    fresh_seed[:240],
    expected_fresh_seed[:240],
)
assert b"NUVIO_PROVIDER_BASE_OWNED_V2" in expected_fresh_seed, expected_fresh_seed[:500]
assert b'"authoring":"niakvio-owned-v2"' in fresh_seed
assert b'"upstreamCodeEmbedded":false' in fresh_seed
assert b'"upstreamCodeExecuted":false' in fresh_seed
assert fresh_knowledge["codeExecuted"] is False
assert fresh_model["legacyCodeEmbedded"] is False
assert fresh_model["legacyCodeExecuted"] is False
assert "freshprovider.dev" in fresh_knowledge["hosts"]

fresh_metadata = discovery.reconstruction_manifest_entry(
    "fresh-provider", fresh_entry, overrides
)
assert fresh_metadata["supportedTypes"] == ["movie", "tv"]
assert fresh_metadata["formats"] == ["m3u8", "mp4"]

# 2) Routine discovery of an existing pending clean candidate reuses it and
# does not silently reconstruct it on every Learning pass.
provider_id = "purstream"
row = provenance["providers"][provider_id]
assert base_store.is_clean_reconstruction_candidate(row)
runtime_before, runtime_sha_before = base_store.resolve_runtime_base(
    provider_id, row, require=True
)
candidate_before, candidate_sha_before = base_store.resolve_base(
    provider_id, row, require=True
)
assert runtime_before is not None and candidate_before is not None
assert runtime_before.resolve() != candidate_before.resolve(), (
    "pending clean candidate must not replace preserved production LKG"
)

purstream_entry = next(
    item for item in manifest["scrapers"]
    if str(item.get("id") or "").casefold() == provider_id
)
purstream_source = (
    "const api='https://api.purstream.id/api/v1';"
    "const site='https://purstream.id/';"
    "const a='/search-bar/search/';"
    "const b='/media/';"
    "const c='/sheet';"
    "const d='/stream/';"
    "const e='/episode/';"
).encode()

routine = discovery.executable_seed(
    provider_id,
    purstream_entry,
    purstream_source,
    provenance["providers"],
    overrides,
    clean_reconstruction=False,
    force_clean_reconstruction=False,
)
assert routine[1] == "pending-niakvio-clean-reconstruction-v2"
assert routine[0] == candidate_before.read_bytes()

# 3) Explicit force reconstruction creates a new clean candidate from current
# + preserved structured knowledge, but cannot mutate/swap the production LKG.
forced = discovery.executable_seed(
    provider_id,
    purstream_entry,
    purstream_source,
    provenance["providers"],
    overrides,
    clean_reconstruction=False,
    force_clean_reconstruction=True,
)
assert forced[1] == "new-niakvio-clean-seed"
assert b"NUVIO_PROVIDER_BASE_OWNED_V2" in forced[0]
assert forced[4].get("historicalKnowledgeMerged") is True
assert forced[5]["apiRecipe"]["base"] == "https://api.purstream.id/api/v1"
assert forced[5]["apiRecipe"]["movieRoute"] == "/media/{id}/sheet"
assert forced[5]["apiRecipe"]["episodeRoute"] == (
    "/stream/{id}/episode?season={season}&episode={episode}"
)

runtime_after, runtime_sha_after = base_store.resolve_runtime_base(
    provider_id, row, require=True
)
candidate_after, candidate_sha_after = base_store.resolve_base(
    provider_id, row, require=True
)
assert runtime_after == runtime_before
assert runtime_sha_after == runtime_sha_before
assert candidate_after == candidate_before
assert candidate_sha_after == candidate_sha_before

# 4) Durable semantic types and media formats are publication contracts and
# survive future discovery/reconstruction independently of transport aliases.
synthetic_cfg = {
    "provider_patches": {
        "anime-demo": {
            "published_types": ["anime"],
            "published_formats": ["mp4", "mkv", "m3u8"],
        }
    }
}
semantic = discovery.reconstruction_manifest_entry(
    "anime-demo",
    {
        "id": "anime-demo",
        "supportedTypes": ["anime", "movie", "tv"],
        "formats": ["mp4", "mkv", "m3u8"],
    },
    synthetic_cfg,
)
assert semantic["canonicalSupportedTypes"] == ["anime"]
assert semantic["supportedTypes"] == ["anime", "movie", "tv"]
assert semantic["formats"] == ["mp4", "mkv", "m3u8"]
manifest_overrides = reapply.configured_manifest_overrides(
    synthetic_cfg, "anime-demo"
)
assert manifest_overrides["formats"] == ["mp4", "mkv", "m3u8"]

print(
    "ProviderBase lifecycle contracts passed: "
    "new-provider=clean-seed routine=stable force=non-destructive "
    "semantic-types=preserved formats=preserved"
)
