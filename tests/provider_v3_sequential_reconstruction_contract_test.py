#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
source = (ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py").read_text(encoding="utf-8")

assert "ThreadPoolExecutor" not in source
assert "as_completed" not in source
assert "for index, provider in enumerate(queue, start=1):" in source
assert "run_until_qualified(provider, model, minimum, timeout)" in source
assert "finalize_provider(" in source
assert source.count("materialize_one(provider_id)") >= 2
assert "prove_final_bundle(" in source
assert "refusing to materialize or advance to provider" in source
assert "active_coverage_main()" in source
assert '"globalCandidateMaterialization": False' in source

loop_at = source.index("for index, provider in enumerate(queue, start=1):")
candidate_materialize_at = source.index("candidate_materialized = materialize_one(provider_id)", loop_at)
probe_at = source.index("run_until_qualified(provider, model, minimum, timeout)", candidate_materialize_at)
finalize_at = source.index("finalize_provider(", probe_at)
final_materialize_at = source.index("materialized = materialize_one(provider_id)", finalize_at)
proof_at = source.index("prove_final_bundle(", final_materialize_at)
pass_at = source.index("FIELD_PROVIDER_SEQUENTIAL_PASS", proof_at)
assert loop_at < candidate_materialize_at < probe_at < finalize_at < final_materialize_at < proof_at < pass_at

one_path = ROOT / "scripts" / "materialize_provider_v3_one.py"
one = one_path.read_text(encoding="utf-8")
assert "materialize_one" in one
assert "build_provider_data_model" in one
assert "validate_managed_fixes" in one
assert "minimize_text" in one
assert "reconcile_provider_authority" in one
assert "FIELD_PROVIDER_STATIC_AUTHORITY_RECONCILED" in one
assert "reconcile_domain_substitutions" in one
assert "FIELD_PROVIDER_DOMAIN_SUBSTITUTIONS_RECONCILED" in one
assert "provider_id=provider_id" in one

spec = importlib.util.spec_from_file_location("materialize_provider_v3_one_contract", one_path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Generic stale chain still collapses when no canonical-model barrier is supplied.
sample = {
    "provider_patches": {
        "flemmix": {
            "domain_substitutions": {
                "legacy.example": "flemmix.men",
                "ww1.wiflix-adresses.fun": "flemmix.men",
            },
            "replacements": {
                "flemmix.men": "flemmix.kim",
                "ww1.wiflix-adresses.fun": "flemmix.kim",
                "unrelated.example": "elsewhere.example",
            },
            "runtime_domain_replacements": {},
        }
    }
}
changed = module.reconcile_domain_substitutions(sample)
assert changed == ["flemmix"], changed
mapping = sample["provider_patches"]["flemmix"]["domain_substitutions"]
assert mapping["legacy.example"] == "flemmix.kim", mapping
assert mapping["ww1.wiflix-adresses.fun"] == "flemmix.kim", mapping
assert mapping["flemmix.men"] == "flemmix.kim", mapping
assert "unrelated.example" not in mapping, mapping

# Current canonical DATA is stronger than a stale historical override. This is
# the exact failure mode that previously rebuilt Purstream on .ad even though the
# enriched current model already said .id + api.purstream.id/api/v1.
purstream_overrides = {
    "provider_patches": {
        "purstream": {
            "official_site": "https://purstream.ad",
            "official_hub": "https://purstream.wiki",
            "official_api": "https://purstream.ad/api",
            "fixed_endpoint": {"api": "https://purstream.ad/api"},
            "api_recipe": {
                "base": "https://purstream.ad/api",
                "referer": "https://purstream.ad/",
                "searchRoute": "/search-bar/search/{query}",
                "movieRoute": "/stream/{id}",
                "episodeRoute": "/stream/{id}/episode?season={season}&episode={episode}",
            },
            "domain_substitutions": {
                "purstream.stream": "purstream.id",
                "api.purstream.stream": "api.purstream.id",
            },
            "replacements": {
                "purstream.id": "purstream.ad",
                "api.purstream.id": "purstream.ad",
                "legacy-only.example": "elsewhere.example",
            },
            "runtime_domain_replacements": {
                "purstream.id": "purstream.ad",
                "api.purstream.id": "purstream.ad",
            },
        },
        "future-provider": {
            "domain_substitutions": {"old.future": "mid.future"},
            "replacements": {"mid.future": "new.future"},
        },
    }
}
purstream_static = {
    "providers": {
        "purstream": {
            "model": {
                "knownSite": "https://purstream.id",
                "officialSite": "https://purstream.id",
                "officialHub": "https://purstream.wiki",
                "officialApi": "https://api.purstream.id/api/v1",
                "fixedApi": "https://api.purstream.id/api/v1",
                "apiRecipe": {
                    "base": "https://api.purstream.id/api/v1",
                    "referer": "https://purstream.id/",
                    "searchRoute": "/search-bar/search/{query}",
                    "movieRoute": "/stream/{id}",
                    "episodeRoute": "/stream/{id}/episode?season={season}&episode={episode}",
                    "idFields": ["id"],
                    "titleFields": ["title"],
                    "yearFields": ["release_date"],
                    "sourceFields": ["url", "stream_url"],
                    "strictIdentity": True,
                    "directSourcesOnly": True,
                    "statusUrl": "https://purstream.wiki/api/status",
                    "statusDomainField": "domain",
                    "statusApiPrefix": "api.",
                    "statusApiSuffix": "/api/v1",
                },
            }
        }
    }
}
authority_changed = module.reconcile_provider_authority(
    purstream_overrides,
    purstream_static,
    "purstream",
)
assert authority_changed == ["purstream"], authority_changed
purstream = purstream_overrides["provider_patches"]["purstream"]
assert purstream["official_site"] == "https://purstream.id", purstream
assert purstream["official_hub"] == "https://purstream.wiki", purstream
assert purstream["official_api"] == "https://api.purstream.id/api/v1", purstream
assert purstream["fixed_endpoint"]["api"] == "https://api.purstream.id/api/v1", purstream
assert purstream["api_recipe"]["base"] == "https://api.purstream.id/api/v1", purstream
assert purstream["api_recipe"]["referer"] == "https://purstream.id/", purstream
assert "purstream.id" not in purstream["replacements"], purstream["replacements"]
assert "api.purstream.id" not in purstream["replacements"], purstream["replacements"]
assert "purstream.id" not in purstream["runtime_domain_replacements"], purstream["runtime_domain_replacements"]
assert "api.purstream.id" not in purstream["runtime_domain_replacements"], purstream["runtime_domain_replacements"]
assert purstream["replacements"]["legacy-only.example"] == "elsewhere.example"

# Domain reconciliation now runs only for provider N. It must preserve the
# canonical .id targets and must not pre-touch provider N+1.
domain_changed = module.reconcile_domain_substitutions(
    purstream_overrides,
    provider_id="purstream",
)
assert "future-provider" not in domain_changed, domain_changed
assert purstream["domain_substitutions"]["purstream.stream"] == "purstream.id", purstream
assert purstream["domain_substitutions"]["api.purstream.stream"] == "api.purstream.id", purstream
future = purstream_overrides["provider_patches"]["future-provider"]["domain_substitutions"]
assert future == {"old.future": "mid.future"}, future

print(
    "Provider v3 sequential reconstruction contract passed: candidate N materialize -> "
    "live proof -> DATA finalize -> final N materialize -> final JS live proof -> only then N+1; "
    "current canonical Provider DATA beats stale historical endpoint overrides, and domain "
    "substitution reconciliation is scoped to provider N."
)
