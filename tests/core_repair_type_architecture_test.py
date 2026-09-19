#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
repair_types = json.loads((ROOT / "engine_v2/config/core-repair-types.json").read_text(encoding="utf-8"))
brain_policy = json.loads((ROOT / "engine_v2/config/brain-policy.json").read_text(encoding="utf-8"))
skills = json.loads((ROOT / "engine_v2/config/global-repair-skills.json").read_text(encoding="utf-8"))
health = json.loads((ROOT / "health-config.json").read_text(encoding="utf-8"))
apply_source = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
brain_runtime_source = (ROOT / "scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
brain_overlay_source = (ROOT / "scripts/adaptive_runtime/brain_repair_runtime.py").read_text(encoding="utf-8")
quick_source = (ROOT / "scripts/run_adaptive_quick_repair.py").read_text(encoding="utf-8")
runtime_upgrade_source = (ROOT / "scripts/apply_runtime_capability_upgrade_v4.py").read_text(encoding="utf-8")
reapply_source = (ROOT / "scripts/reapply_published_overrides.py").read_text(encoding="utf-8")
compiler_source = (ROOT / "scripts/provider_compiler.py").read_text(encoding="utf-8")
promoter_source = (ROOT / "scripts/promote_candidates.py").read_text(encoding="utf-8")
base_store_source = (ROOT / "scripts/provider_base_store.py").read_text(encoding="utf-8")
architecture_doc = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")

GLOBAL = {
    "scripts/provider_patches/runtime_capability_media_safety_v4.py",
    "scripts/provider_patches/global_runtime_compat_v1.py",
    "scripts/provider_patches/global_stream_presentation_v1.py",
    "scripts/provider_patches/global_provider_branding_v1.py",
    "scripts/provider_patches/global_media_type_resolution_v1.py",
}
leaks = {}
for provider_id, row in (overrides.get("provider_patches") or {}).items():
    if not isinstance(row, dict):
        continue
    found = sorted(GLOBAL & set(row.get("patch_scripts") or []))
    if found:
        leaks[provider_id] = found
assert not leaks, leaks
assert "contains Core-global modules" in apply_source
media_resolution_source = (ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py").read_text(encoding="utf-8")
assert "NUVIO_GLOBAL_PROVIDER_EXECUTION_BUDGET_V1" in media_resolution_source
assert "budgetedFetch" in media_resolution_source
assert "function providerBudgetMs()" in media_resolution_source
assert "c.tvProviderTimeoutMs" in media_resolution_source
assert "c.providerTimeoutMs" in media_resolution_source
deadline_anchor = "requestDeadline=Date.now()+providerBudgetMs()"
provisional_anchor = "var a=preflight?await resolve(originalArgs):provisional(originalArgs)"
verify_anchor = "var verified=await resolve(originalArgs)"
assert deadline_anchor in media_resolution_source
assert "g.__nuvioProviderDeadlineMs=requestDeadline" in media_resolution_source
assert "g.__nuvioProviderRequestToken=requestToken" in media_resolution_source
assert provisional_anchor in media_resolution_source
assert verify_anchor in media_resolution_source
assert media_resolution_source.index(deadline_anchor) < media_resolution_source.index(provisional_anchor) < media_resolution_source.index(verify_anchor)
playback = overrides.get("playback_integrity_policy") or {}
assert playback.get("pre_media_discovery_hooks") == [], playback
assert playback.get("post_media_discovery_hooks") == ["scripts/provider_patches/hls_runtime_integrity_v1.py"], playback
assert "scripts/provider_patches/native_hls_integrity_budget_v1.py" not in (playback.get("pre_media_discovery_hooks") or []), playback
assert playback.get("native_hls_probe_policy") == "skip_additional_integrity_network_probes_on_native_host_bridge"
worker_source = (ROOT / "scripts/provider_worker.cjs").read_text(encoding="utf-8")
assert "fixture.tmdbMetadata = fixtureMetadata" in worker_source
assert "globalThis.__nuvioMediaContext" in worker_source
assert "scripts.append(RUNTIME_PATCH)" not in runtime_upgrade_source
assert '"scope": "all_published_providers"' in runtime_upgrade_source
assert 'runtime_safety.pop("targets", None)' in runtime_upgrade_source
assert "core_global_safety=true" in runtime_upgrade_source
assert "from provider_base_store import (" in reapply_source
assert "    resolve_base," in reapply_source
assert "provider_base = provider_base_path.read_bytes()" in reapply_source
assert 'provider_base.decode("utf-8", errors="strict")' in reapply_source
assert "from provider_base_store import resolve_runtime_base" in compiler_source
assert "source_file == canonical_base" in compiler_source
assert '"provider_base_lkg_pending_clean_candidate"' in compiler_source
assert '"source_kind": source_kind if canonical_provider_base_mode else "explicit_manifest_source"' in compiler_source
assert "from provider_base_store import (" in promoter_source
assert "    persist_base_from_published," in promoter_source
assert "base_filename, base_sha256, base_stripped_generated_core = persist_base_from_published" in promoter_source
assert "def persist_base_from_published" in base_store_source

expected_pipeline = [
    "source_validation",
    "provider_recognition",
    "global_invariants",
    "capability_adapter",
    "capability_engine",
    "capability_global_invariants",
    "public_bundle",
]
assert [row["stage"] for row in repair_types["pipeline"]] == expected_pipeline
assert repair_types["evidencePolicy"]["monotonic"] is True
assert repair_types["learning"]["directDurablePatchFromSkillForbidden"] is True
assert repair_types["learning"]["providerLocalMutation"] == "lab_only_proof"
assert repair_types["learning"]["independentFromCoreRepair"] is True
assert repair_types["learning"]["coreRepairMayInvokeLearning"] is False
assert repair_types["executionLanes"]["coreRepair"]["learningAllowed"] is False
assert repair_types["executionLanes"]["coreRepair"]["learnedSkillInputAllowed"] is False
assert repair_types["executionLanes"]["coreRepair"]["unknownFailureAction"] == "queue_for_independent_learning"
assert repair_types["executionLanes"]["dailyLearning"]["partOfCoreRepair"] is False
assert repair_types["executionLanes"]["dailyLearning"]["requiredPublishedProviderObservationCoverage"] == 1.0
lifecycle = repair_types["providerArtifactLifecycle"]
assert lifecycle["model"] == "stable_provider_base_plus_derived_public_bundle"
assert lifecycle["providerBase"]["startsFromEmpty"] is False
assert lifecycle["providerBase"]["durableOwner"] == "provider_pipeline"
assert lifecycle["providerBase"]["coreMayReplaceProviderLogic"] is False
assert lifecycle["providerBase"]["durableSourceNormalizationAllowed"] == ["provider_security_hardening"]
assert lifecycle["providerBase"]["domainRoutingIsDerived"] is True
assert lifecycle["providerBase"]["maintenanceRepositoryInputsAllowed"] is True
assert lifecycle["providerBase"]["maintenanceRepositoryInputsExecuted"] is False
assert lifecycle["publicBundle"]["repositoryRuntimeDependenciesAllowed"] is False
assert lifecycle["publicBundle"]["domainRoutingMaterializedFromCurrentValidatedState"] is True
assert "publication_quarantine" in lifecycle["providerBase"]["forbiddenDerivedLayers"]
assert "runtime_domain_wrapper" in lifecycle["providerBase"]["forbiddenDerivedLayers"]
assert lifecycle["coreFinalizer"]["mode"] == "verify_first"
assert lifecycle["coreFinalizer"]["materializeOnlyWhenStale"] is True
assert lifecycle["coreFinalizer"]["noOpWhenFixedPoint"] is True
assert lifecycle["coreFinalizer"]["forbiddenTrigger"] == "core_invocation_alone"
assert lifecycle["publicBundle"]["rebuildOnlyOnInputChange"] is True
domain_intelligence = lifecycle["domainIntelligence"]
assert domain_intelligence["independentFromProviderBase"] is True
assert domain_intelligence["currentOfficialSiteIsResolvedStateNotIdentity"] is True
assert domain_intelligence["searchOnlyPromotionRequiresConsecutiveRuns"] == 2
assert domain_intelligence["inconclusiveKeepsLastKnownGood"] is True
assert domain_intelligence["domainChangeMayRebuildDerivedBundle"] is True
assert domain_intelligence["domainChangeMayReplaceProviderLogic"] is False
assert domain_intelligence["sources"][:2] == ["official_hub", "public_telegram"]
assert "yandex_deep_search" in domain_intelligence["sources"]
assert "duckduckgo_deep_fallback" in domain_intelligence["sources"]
assert "L'identité d'un provider et son domaine courant sont **deux états différents**." in architecture_doc
assert "ne remplace jamais la logique durable du ProviderBase" in architecture_doc

classes = repair_types["failureClasses"]
for failure in ("identity_mismatch", "short_media", "media_validation_gap", "audio_track_gap"):
    assert classes[failure]["scope"] == "global", (failure, classes[failure])
    assert classes[failure]["profiles"] == [], (failure, classes[failure])
for failure in ("search_gap", "episode_gap", "player_gap", "media_extraction_gap", "playback_context_gap"):
    assert classes[failure]["scope"] == "capability", (failure, classes[failure])
assert classes["unknown_failure"]["scope"] == "learning"
assert classes["unknown_failure"]["repairType"] == "architecture_gap"

assert brain_policy["controlPlaneVersion"] == 5
assert brain_policy["production"]["durableProviderSkillApplication"] is False
assert brain_policy["production"]["learningDuringCoreRepair"] is False
assert brain_policy["production"]["learnedSkillInputAllowed"] is False
assert brain_policy["production"]["unknownFailureAction"] == "queue_for_independent_learning"
assert brain_policy["learningLab"]["directSkillPublication"] is False
assert brain_policy["learningLab"]["independentFromCoreRepair"] is True
assert brain_policy["learningLab"]["dailyPublishedProviderCoverageTarget"] == 1.0
assert brain_policy["executionLanes"]["coreRepair"]["learningAllowed"] is False
assert brain_policy["executionLanes"]["dailyLearning"]["independent"] is True
assert brain_policy["executionLanes"]["dailyLearning"]["timeBudgetMinutes"] == 60
assert "persistent anomaly-first queue" in brain_policy["executionLanes"]["dailyLearning"]["providerScheduling"]
assert brain_policy["executionLanes"]["dailyLearning"]["productionWritesAllowed"] is False
assert brain_policy["executionLanes"]["dailyLearning"]["publicationAllowed"] is False
assert 'learnedSkills": learned_skills() if str(mode).casefold() == "learning" else {}' in brain_runtime_source
assert 'learnedSkills": _BASE.learned_skills() if str(mode).casefold() == "learning" else {}' in brain_overlay_source
assert '"profile_persistence"] = "learning_memory" if planner_mode == "learning" else "none_core_repair_only"' in quick_source
assert '"learning_executed"] = planner_mode == "learning"' in quick_source
assert 'skill["autoApply"] = trusted' not in brain_runtime_source
assert 'skill["autoApply"] = False' in brain_runtime_source
assert 'skill["proposalEligible"] = trusted' in brain_runtime_source
assert '"repairScope": "deferred" if unknown' in quick_source
assert '"repairEngine": "independent_learning_queue" if unknown' in quick_source
assert '"learningDisposition": "queue_for_independent_learning" if unknown' in quick_source

for skill in (skills.get("skills") or {}).values():
    assert skill.get("autoApply") is False, skill
    assert skill.get("learningOnly") is True, skill
    assert skill.get("durableImplementationForbidden") is True, skill

streamzo = (overrides.get("provider_capabilities") or {}).get("streamzo") or {}
assert streamzo.get("strategy") == "mixed_embed_resolver", streamzo
assert streamzo.get("request_type_aliases") == {"anime": "tv"}, streamzo
assert streamzo.get("identity_request_source") == "original_nuvio_request", streamzo
purstream_capability = (overrides.get("provider_capabilities") or {}).get("purstream") or {}
assert purstream_capability.get("request_type_aliases") == {"anime": "tmdb_namespace"}, purstream_capability
assert purstream_capability.get("identity_request_source") == "original_nuvio_request", purstream_capability

streamzo_patch = (overrides.get("provider_patches") or {}).get("streamzo") or {}
streamzo_scripts = [str(value) for value in streamzo_patch.get("patch_scripts") or []]
assert not [value for value in streamzo_scripts if "/streamzo_" in value], streamzo_scripts
catalogue_options = (streamzo_patch.get("patch_script_options") or {}).get(
    "scripts/provider_patches/global_catalogue_alias_recovery_v2.py"
) or {}
assert catalogue_options.get("detail_id_attributes") == ["data-film-id"], catalogue_options
assert catalogue_options.get("mirror_routes") == ["/api/mirrors/film/{id}"], catalogue_options
assert catalogue_options.get("mirror_types") == ["movie", "anime"], catalogue_options

policy = overrides.get("runtime_capability_media_safety") or {}
assert policy.get("scope") == "all_published_providers", policy
assert policy.get("provider_specific_core_script_entries_forbidden") is True, policy
assert policy.get("request_identity_source") == "original_nuvio_request", policy
assert (policy.get("options") or {}).get("duration_identity") is True, policy
assert "targets" not in policy, policy

anime = (health.get("fixtures") or {}).get("anime") or []
assert anime, "anime fixtures missing"
assert all(str(row.get("mediaType") or "") == "anime" for row in anime), anime
hell = [row for row in anime if str(row.get("tmdbId") or "") == "280049"]
assert len(hell) == 1, hell
assert hell[0]["season"] == 1 and hell[0]["episode"] == 1, hell[0]
assert 15 <= int(hell[0]["expectedDurationMinutes"]) <= 40, hell[0]

print("core repair type architecture tests passed")
