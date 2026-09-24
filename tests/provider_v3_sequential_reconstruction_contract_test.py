#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
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
assert 'provider.get("enabled") is False' in source
assert '"disabled-unqualified"' in source
assert "FIELD_PROVIDER_DISABLED_UNQUALIFIED_ADVANCE" in source
assert "PROVIDER_V3_BOUNDED_LIVE_RETRY_V1" in source
assert "LIVE_PROBE_ATTEMPTS = _live_probe_attempts()" in source
assert source.count("for attempt in range(1, LIVE_PROBE_ATTEMPTS + 1):") >= 2
assert 'result["probe_attempt"] = attempt' in source
assert "runtime_recovered_types" in source
assert "FIELD_PROVIDER_FIXTURE_SKIPPED_TYPE_ALREADY_PROVED" in source
from validate_provider_v3_routes_sequential import build_provider_queue, SEMANTIC_FIXTURE_FALLBACKS
from current_provider_scope import visible_provider_count, visible_provider_ids
assert len(SEMANTIC_FIXTURE_FALLBACKS["movie"]) >= 4
queue_rows, queue_count = build_provider_queue()
assert queue_count == visible_provider_count(), (queue_count, visible_provider_count())
assert {row["provider_id"] for row in queue_rows} == visible_provider_ids()
lifecycle = json.loads((ROOT / "automation/provider-disabled-lifecycle.json").read_text(encoding="utf-8"))
archived = lifecycle.get("archived") if isinstance(lifecycle.get("archived"), dict) else {}
if "desiflix" in visible_provider_ids():
    desiflix = next(row for row in queue_rows if row["provider_id"] == "desiflix")
    desiflix_movies = [task["fixture_slug"] for task in desiflix["tasks"] if task["semantic_type"] == "movie"]
    assert "interstellar" in desiflix_movies
    assert len(desiflix_movies) >= 4, desiflix_movies
else:
    record = archived.get("desiflix") if isinstance(archived.get("desiflix"), dict) else None
    assert record is not None and record.get("state") == "archived-provider-old", record
    assert all(row["provider_id"] != "desiflix" for row in queue_rows)
validator_source = (ROOT / "scripts" / "validate_provider_v3_routes_sequential.py").read_text(encoding="utf-8")
assert '"enabled": manifest_row.get("enabled") is not False' in validator_source
assert 'completion_state = "disabled-unqualified"' in validator_source

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
assert "PROVIDER_DOMAIN_EXPLICIT_CURRENT_PRECEDENCE_V1" in one
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

# Explicit-current Domain registry outranks stale static Provider memory. This
# protects incremental Brain materialization from resurrecting yesterday's host.
flemmix_overrides = {
    "provider_patches": {
        "flemmix": {
            "official_site": "https://flemmix.me",
            "domain_substitutions": {"flemmix.party": "flemmix.me", "flemmix.cloud": "flemmix.me"},
            "replacements": {"flemmix.me": "flemmix.party", "flemmix.cloud": "flemmix.party"},
            "runtime_domain_replacements": {"flemmix.me": "flemmix.party", "flemmix.cloud": "flemmix.party"},
        }
    }
}
flemmix_static = {
    "providers": {
        "flemmix": {
            "model": {
                "knownSite": "https://flemmix.cloud",
                "officialSite": "https://flemmix.cloud",
            }
        }
    }
}
flemmix_registry = {
    "providers": {
        "flemmix": {
            "direct": "https://flemmix.party/",
            "direct_authority": "explicit_current",
        }
    }
}
flemmix_changed = module.reconcile_provider_authority(
    flemmix_overrides,
    flemmix_static,
    "flemmix",
    flemmix_registry,
)
assert flemmix_changed == ["flemmix"], flemmix_changed
flemmix_patch = flemmix_overrides["provider_patches"]["flemmix"]
assert flemmix_patch["official_site"] == "https://flemmix.party", flemmix_patch
assert "flemmix.party" not in flemmix_patch["domain_substitutions"], flemmix_patch

# Runtime Lego options are executable address DATA too. If Domain already knows
# old -> current, materialization must not keep a stale provider-specific base.
animevostfr_overrides = {
    "provider_patches": {
        "animevostfr": {
            "official_site": "https://animevostfr.org",
            "provider_lego_options": {
                "scripts/provider_patches/animevostfr_runtime_v1.py": {
                    "base": "https://v2.animevostfr.org",
                    "nested": {"endpoint": "https://v2.animevostfr.org/api/test?q=1"},
                }
            },
            "runtime_domain_replacements": {
                "v2.animevostfr.org": "animevostfr.org",
            },
            "domain_substitutions": {
                "v2.animevostfr.org": "animevostfr.org",
            },
        }
    }
}
animevostfr_static = {
    "providers": {
        "animevostfr": {
            "model": {
                "knownSite": "https://v2.animevostfr.org",
                "officialSite": "https://v2.animevostfr.org",
            }
        }
    }
}
animevostfr_registry = {
    "providers": {
        "animevostfr": {
            "direct": "https://animevostfr.org/",
            "direct_authority": "explicit_current",
        }
    }
}
animevostfr_changed = module.reconcile_provider_authority(
    animevostfr_overrides,
    animevostfr_static,
    "animevostfr",
    animevostfr_registry,
)
assert animevostfr_changed == ["animevostfr"], animevostfr_changed
assert animevostfr_overrides["provider_patches"]["animevostfr"]["official_site"] == "https://animevostfr.org"
animevostfr_opts = animevostfr_overrides["provider_patches"]["animevostfr"]["provider_lego_options"]["scripts/provider_patches/animevostfr_runtime_v1.py"]
assert animevostfr_opts["base"] == "https://animevostfr.org", animevostfr_opts
assert animevostfr_opts["nested"]["endpoint"] == "https://animevostfr.org/api/test?q=1", animevostfr_opts

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

# Fresh proof-owned API recipe authority outranks stale static memory. This is
# the exact VidLove V1 regression: provider-overrides carried current playable
# api.vidlove.cc proof while static knowledge still described an older backend.
vidlove_overrides = {
    "provider_patches": {
        "vidlove": {
            "route_proof_version": 5,
            "official_site": "https://player.vidlove.cc",
            "api_recipe": {
                "proofModelVersion": 5,
                "base": "https://api.vidlove.cc",
                "referer": "https://player.vidlove.cc/",
                "origin": "https://player.vidlove.cc",
                "directRoute": "/{media}?id={tmdbId}&mode=json&season={season}&episode={episode}",
                "requestTimeoutMs": 8000,
            },
        }
    }
}
vidlove_static = {
    "providers": {
        "vidlove": {
            "model": {
                "knownSite": "https://player.vidlove.cc",
                "officialSite": "https://player.vidlove.cc",
                "apiRecipe": {
                    "base": "https://stale-api.example.invalid",
                    "referer": "https://stale-player.example.invalid/",
                    "directRoute": "/stale/{id}",
                },
            }
        }
    }
}
vidlove_before = dict(vidlove_overrides["provider_patches"]["vidlove"]["api_recipe"])
module.reconcile_provider_authority(vidlove_overrides, vidlove_static, "vidlove")
vidlove_recipe = vidlove_overrides["provider_patches"]["vidlove"]["api_recipe"]
assert vidlove_recipe == vidlove_before, vidlove_recipe
assert vidlove_recipe["base"] == "https://api.vidlove.cc", vidlove_recipe
assert vidlove_recipe["referer"] == "https://player.vidlove.cc/", vidlove_recipe
assert vidlove_recipe["directRoute"].startswith("/{media}?id={tmdbId}"), vidlove_recipe

print(
    "Provider v3 sequential reconstruction contract passed: candidate N materialize -> "
    "live proof -> DATA finalize -> final N materialize -> final JS live proof -> only then N+1; "
    "current canonical Provider DATA beats stale historical endpoint overrides, and domain "
    "substitution reconciliation is scoped to provider N."
)
