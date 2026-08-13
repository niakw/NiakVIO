#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic self-test for strict and runtime-evidence activation policy.

No network endpoint is contacted. The test proves that all eleven gates remain
mandatory for automatic activation and that a SHA-pinned Nuvio observation can
only resolve a CI-inconclusive result for the exact confirmed provider file.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "health-config.json"
PROMOTE_PATH = ROOT / "scripts" / "promote_candidates.py"


def load_promote_module():
    spec = importlib.util.spec_from_file_location("nuvio_promote_policy", PROMOTE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load promote_candidates.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_item() -> dict[str, Any]:
    return {
        "key": "aio:policy-test",
        "source": "aio",
        "upstream_id": "policy-test",
        "canonical_id": "policy-test",
        "sha256": "a" * 64,
        "metadata": {"id": "policy-test", "enabled": True},
        "health": {
            "status": "healthy",
            "ci_classification": "conclusive_success",
            "score": 95,
            "evidence": {
                "fixtures_tested": 1,
                "healthy_fixtures": 1,
                "healthy_fixture_ratio": 1.0,
                "playable_fixtures": 1,
                "required_fixture_categories": ["movie", "tv"],
                "healthy_fixture_categories": ["movie"],
                "streams_playable": 1,
                "payload_verified_streams": 1,
                "distinct_reachable_hosts": 1,
                "reachable_hosts": ["a.example"],
                "effective_max_height": 1080,
                "max_bandwidth": 2_000_000,
                "accepted_audio_languages": ["en"],
                "accepted_subtitle_languages": ["fr"],
                "accepted_subtitles_advertised": 1,
                "accepted_subtitles_reachable": 1,
                "provider_median_latency_ms": 1_000,
                "stream_median_latency_ms": 900,
                "disallowed_streams": 0,
                "provider_server_successful_response": True,
                "provider_server_hosts": ["provider.example"],
                "provider_server_http_statuses": [200],
            },
        },
    }


def inconclusive_item() -> dict[str, Any]:
    item = base_item()
    item["health"] = {
        "status": "no_streams",
        "ci_classification": "inconclusive",
        "score": 10,
        "evidence": {
            "fixtures_tested": 7,
            "healthy_fixtures": 0,
            "healthy_fixture_ratio": 0,
            "playable_fixtures": 0,
            "required_fixture_categories": ["movie", "tv"],
            "healthy_fixture_categories": [],
            "streams_playable": 0,
            "payload_verified_streams": 0,
            "distinct_reachable_hosts": 0,
            "reachable_hosts": [],
            "effective_max_height": None,
            "max_bandwidth": None,
            "accepted_audio_languages": [],
            "accepted_subtitle_languages": [],
            "accepted_subtitles_advertised": 0,
            "accepted_subtitles_reachable": 0,
            "provider_median_latency_ms": None,
            "stream_median_latency_ms": None,
            "disallowed_streams": 0,
            "provider_server_successful_response": False,
            "provider_server_hosts": [],
            "provider_server_http_statuses": [],
        },
    }
    return item


def runtime_registry(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "providers": {
            item["canonical_id"]: {
                "enabled": True,
                "kind": "confirmed_working_in_nuvio",
                "source": item["source"],
                "upstream_id": item["upstream_id"],
                "sha256": item["sha256"],
                "allowed_ci_statuses": [
                    "no_streams",
                    "blocked",
                    "provider_unreachable",
                    "runtime_error",
                ],
            }
        }
    }


def assert_gate_fails(module, activation, mutate, expected: str) -> None:
    item = base_item()
    mutate(item)
    gates, _proof = module.evaluate_pre_stability_gates(item, activation)
    failed = {name for name, value in gates.items() if not value.get("passed")}
    if expected not in failed:
        raise AssertionError(f"{expected} was not enforced; failed={sorted(failed)}")


def strict_history(item: dict[str, Any], *, inconclusive: int = 0) -> dict[str, Any]:
    return {
        "sha256": item["sha256"],
        "strict_consecutive_deep_passes": 1,
        "strict_total_deep_passes": 1,
        "strict_validated_sha256": item["sha256"],
        "consecutive_inconclusive_deep_checks": inconclusive,
        "last_deep_pre_stability_pass": inconclusive == 0,
    }


def decide(module, activation, item, history=None, registry=None, auto_disabled=False, previous_record=None):
    return module.activation_decision(
        item,
        activation,
        history or {},
        auto_disabled,
        module.evaluate_pre_stability_gates(item, activation),
        registry or {"providers": {}},
        previous_record or {},
    )


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    activation = config.get("activation", {})
    module = load_promote_module()

    assert activation.get("required_validation_mode") == "deep"
    assert int(activation.get("activation_gate_count", 0)) == 11
    assert int(activation.get("minimum_consecutive_deep_passes", 0)) == 1
    assert int(activation.get("minimum_total_deep_passes", 0)) == 1
    assert int(activation.get("minimum_healthy_fixtures", 0)) == 1
    assert int(activation.get("minimum_playable_streams", 0)) == 1
    assert int(activation.get("minimum_playable_fixtures", 0)) == 1
    assert int(activation.get("minimum_distinct_hosts", 0)) == 1
    assert int(activation.get("minimum_payload_verified_streams", 0)) == 1
    assert bool(activation.get("representative_fixture_mode"))
    assert int(activation.get("minimum_effective_height", -1)) == 0
    assert int(activation.get("minimum_bandwidth_bps_when_reported", -1)) == 0
    assert not bool(activation.get("require_accepted_language_evidence"))
    assert int(activation.get("minimum_score_enabled", 0)) == 55
    assert bool(activation.get("require_reachable_accepted_subtitle_when_advertised"))
    assert bool(activation.get("manual_runtime_evidence_requires_matching_sha256"))
    assert bool(activation.get("manual_runtime_evidence_never_bypasses_p2p_or_hard_failure"))

    # Three-manifest editorial curation is intentionally stricter than a bare
    # HTTP endpoint. A Purstream-like FR/EN entry with direct media formats
    # reaches the threshold, while a generic one-language description does not.
    purstream_claims = module.aggregate_manifest_claims([
        {
            "source": "aio",
            "canonical_id": "purstream",
            "metadata": {
                "id": "purstream",
                "name": "Purstream",
                "description": "Films and series in French (VF) / subtitled French (VOSTFR) / multi-language (MULTI).",
                "contentLanguage": ["en", "fr"],
                "supportedTypes": ["movie", "tv"],
                "formats": ["mp4", "m3u8"],
            },
        }
    ])
    if purstream_claims["curation_score"] < int(activation.get("minimum_manifest_curation_score", 5)):
        raise AssertionError(f"Purstream-like editorial metadata was under-scored: {purstream_claims}")
    generic_claims = module.aggregate_manifest_claims([
        {
            "source": "aio",
            "canonical_id": "generic",
            "metadata": {
                "id": "generic",
                "name": "Generic",
                "description": "Popular cartoons streaming",
                "contentLanguage": ["en"],
                "supportedTypes": ["movie", "tv"],
                "formats": ["m3u8"],
            },
        }
    ])
    if generic_claims["curation_score"] >= int(activation.get("minimum_manifest_curation_score", 5)):
        raise AssertionError(f"generic endpoint metadata became curated: {generic_claims}")
    merged_claims = module.aggregate_manifest_claims([
        {
            "source": "aio",
            "canonical_id": "merged",
            "metadata": {"description": "Movies in English", "contentLanguage": ["en"], "formats": ["m3u8"], "supportedTypes": ["movie"]},
        },
        {
            "source": "yoru",
            "canonical_id": "merged",
            "metadata": {"description": "4K direct streams with multiple servers", "contentLanguage": ["en"], "formats": ["mp4"], "supportedTypes": ["movie", "tv"]},
        },
    ])
    if merged_claims["max_height"] != 2160 or merged_claims["source_count"] != 2:
        raise AssertionError(f"duplicate manifest metadata was not merged: {merged_claims}")
    if not {"vf", "vostfr"}.issubset(set(purstream_claims.get("language_modes", []))):
        raise AssertionError(f"VF/VOSTFR modes were not detected: {purstream_claims}")

    movix_variant = {
        "source": "gowaru",
        "canonical_id": "movix",
        "upstream_id": "movix",
        "metadata": {
            "id": "movix",
            "name": "Movix",
            "description": "Films, Séries et Animes en VF et VOSTFR.",
            # Deliberately incomplete upstream field: description is richer.
            "supportedTypes": ["anime"],
            "contentLanguage": ["fr"],
            "formats": ["m3u8", "mp4"],
        },
    }
    movix_claims = module.aggregate_manifest_claims([movix_variant])
    if set(movix_claims.get("supported_types", [])) != {"movie", "tv", "anime"}:
        raise AssertionError(f"Movix catalogue coverage was collapsed to anime: {movix_claims}")
    curated_entry = module.build_entry(
        movix_variant,
        ROOT / "providers" / "movix-policy-test.js",
        True,
        movix_claims,
    )
    if set(curated_entry.get("supportedTypes", [])) != {"movie", "tv", "anime"}:
        raise AssertionError(f"curated manifest entry lost Movix movie/tv coverage: {curated_entry}")

    anime_only_claims = module.aggregate_manifest_claims([
        {
            "source": "aio",
            "canonical_id": "anime-only",
            "metadata": {
                "description": "Animes et mangas en streaming",
                "supportedTypes": ["movie", "tv"],
                "contentLanguage": ["ja", "fr"],
                "formats": ["m3u8"],
            },
        },
        {
            "source": "yoru",
            "canonical_id": "anime-only",
            "metadata": {
                "description": "Anime VOSTFR",
                "supportedTypes": ["anime"],
                "contentLanguage": ["ja", "fr"],
                "formats": ["mp4"],
            },
        },
    ])
    if set(anime_only_claims.get("supported_types", [])) != {"anime"}:
        raise AssertionError(f"anime-only provider was broadened to general movies/TV: {anime_only_claims}")

    # Manifest loading order: enabled VF first, then VOSTFR, then generic FR,
    # then other languages. Resolution wins inside a language group, followed
    # by health score and curation score.
    def ordered_profile(modes, languages, height, score, curation=5, **observed):
        result = {
            "score": score,
            "candidate_profile": {
                "manifest_claims_aggregated": {"language_modes": modes}
            },
        }
        proof = {
            "manifest_accepted_languages": languages,
            "effective_max_height": height,
            "manifest_effective_height": None,
            "manifest_curation_score": curation,
            "provider_server_successful_response": True,
            "audio_languages": observed.get("audio_languages", []),
            "accepted_audio_languages": observed.get("accepted_audio_languages", []),
            "subtitle_languages": observed.get("subtitle_languages", []),
            "accepted_subtitle_languages": observed.get("accepted_subtitle_languages", []),
        }
        return module.manifest_ordering_profile(result, proof)

    profiles = {
        "vf-4k": ordered_profile(["vf"], ["fr"], 2160, 80),
        "vf-hd": ordered_profile(["vf"], ["fr"], 720, 99),
        "vostfr-4k": ordered_profile(["vostfr"], ["fr"], 2160, 100),
        "fr-generic": ordered_profile(["fr_unspecified"], ["fr"], 2160, 100),
        "observed-vostfr": ordered_profile(
            [], ["fr"], 1080, 88,
            audio_languages=["vostfr"],
            subtitle_languages=["fr"],
            accepted_subtitle_languages=["fr"],
        ),
        "vo-high-score": ordered_profile([], ["en"], 720, 99),
        "vo-4k": ordered_profile([], ["en"], 2160, 80),
    }
    entries = [
        {"id": "vo-4k", "enabled": True},
        {"id": "vo-high-score", "enabled": True},
        {"id": "fr-generic", "enabled": True},
        {"id": "observed-vostfr", "enabled": True},
        {"id": "vostfr-4k", "enabled": True},
        {"id": "vf-hd", "enabled": True},
        {"id": "vf-4k", "enabled": True},
    ]
    ordered_ids = [
        entry["id"]
        for entry in sorted(
            entries, key=lambda entry: module.manifest_entry_sort_key(entry, profiles)
        )
    ]
    expected_order = [
        "vf-4k",
        "vf-hd",
        "vostfr-4k",
        "observed-vostfr",
        "fr-generic",
        "vo-high-score",
        "vo-4k",
    ]
    if ordered_ids != expected_order:
        raise AssertionError(f"manifest language/quality ordering is wrong: {ordered_ids}")
    if profiles["observed-vostfr"].get("language_group") != "vostfr":
        raise AssertionError(f"runtime VOSTFR evidence was ignored: {profiles['observed-vostfr']}")

    reachable = inconclusive_item()
    reachable["health"]["status"] = "reachable"
    reachable["health"]["score"] = 75
    reachable["health"]["evidence"].update(
        provider_server_accessible=True,
        provider_server_http_statuses=[403],
        manifest_description_present=True,
        manifest_accepted_languages=["fr", "en"],
        manifest_formats=["mp4", "m3u8"],
        manifest_curation_score=purstream_claims["curation_score"],
        manifest_quality_signals=purstream_claims["quality_signals"],
        manifest_usable_stream_format=True,
        manifest_sources=["aio"],
    )
    reachable_gates, _reachable_proof = module.evaluate_pre_stability_gates(reachable, activation)
    if not module.all_gates_pass(reachable_gates):
        failed = [name for name, value in reachable_gates.items() if not value.get("passed")]
        raise AssertionError(f"curated reachable provider did not pass pre-stability gates: {failed}")
    uncurated = copy.deepcopy(reachable)
    uncurated["health"]["evidence"]["manifest_curation_score"] = generic_claims["curation_score"]
    uncurated_gates, _ = module.evaluate_pre_stability_gates(uncurated, activation)
    if uncurated_gates["08_quality_and_bitrate"]["passed"]:
        raise AssertionError("bare reachable server bypassed manifest curation gate")

    item = base_item()
    gates, proof = module.evaluate_pre_stability_gates(item, activation)
    expected_pre_gates = {
        "01_policy_safe_no_p2p",
        "02_healthy_functional_status",
        "03_minimum_score",
        "04_fixture_and_type_coverage",
        "05_stream_and_fixture_coverage",
        "06_distinct_host_diversity",
        "07_verified_payload_playability",
        "08_quality_and_bitrate",
        "09_language_and_subtitle_integrity",
        "10_content_identity_integrity",
    }
    if set(gates) != expected_pre_gates or not module.all_gates_pass(gates):
        raise AssertionError("the ten pre-stability gates are incomplete or permissive")
    if not proof.get("performance", {}).get("passed"):
        raise AssertionError("valid latency evidence did not pass")

    mutations = [
        (lambda value: value["health"]["evidence"].update(disallowed_streams=1), "01_policy_safe_no_p2p"),
        (lambda value: value["health"].update(status="no_streams"), "02_healthy_functional_status"),
        (lambda value: value["health"].update(score=54), "03_minimum_score"),
        (lambda value: value["health"]["evidence"].update(healthy_fixtures=0, healthy_fixture_ratio=0.0, healthy_fixture_categories=[]), "04_fixture_and_type_coverage"),
        (lambda value: value["health"]["evidence"].update(streams_playable=0, playable_fixtures=0), "05_stream_and_fixture_coverage"),
        (lambda value: value["health"]["evidence"].update(distinct_reachable_hosts=0, reachable_hosts=[]), "06_distinct_host_diversity"),
        (lambda value: value["health"]["evidence"].update(payload_verified_streams=0), "07_verified_payload_playability"),
        (lambda value: value["health"]["evidence"].update(identity_contradiction_count=1), "10_content_identity_integrity"),
    ]
    for mutate, expected in mutations:
        assert_gate_fails(module, activation, mutate, expected)

    # General activation must not reject a real payload merely because it is
    # SD/low bitrate or uses a language outside FR/EN. Those signals are used
    # for ordering and language projections, not provider liveness.
    broad = copy.deepcopy(item)
    broad["health"]["evidence"].update(
        effective_max_height=360,
        max_bandwidth=350_000,
        audio_languages=["hi"],
        accepted_audio_languages=[],
        accepted_subtitle_languages=[],
    )
    broad_gates, _ = module.evaluate_pre_stability_gates(broad, activation)
    if not broad_gates["08_quality_and_bitrate"]["passed"]:
        raise AssertionError("verified SD payload was incorrectly rejected from the general manifest")
    if not broad_gates["09_language_and_subtitle_integrity"]["passed"]:
        raise AssertionError("non-FR/EN payload was incorrectly rejected from the general manifest")

    # Optional subtitles cannot disable a playable accepted-audio stream.
    optional_subtitles = copy.deepcopy(item)
    optional_subtitles["health"]["evidence"].update(
        accepted_audio_languages=["fr"],
        accepted_subtitle_languages=["fr"],
        accepted_subtitles_advertised=3,
        accepted_subtitles_reachable=0,
    )
    optional_gates, _ = module.evaluate_pre_stability_gates(optional_subtitles, activation)
    if not optional_gates["09_language_and_subtitle_integrity"]["passed"]:
        raise AssertionError("optional unreachable subtitles disabled accepted audio")

    # Runtime mode evidence overrides broad descriptions mentioning both VF/VOSTFR.
    runtime_vostfr = copy.deepcopy(item["health"])
    runtime_vostfr["candidate_profile"] = {
        "manifest_claims_aggregated": {"language_modes": ["vf", "vostfr"]}
    }
    runtime_vostfr["evidence"].update(
        audio_languages=["vostfr"],
        subtitle_languages=["fr"],
        accepted_audio_languages=[],
        accepted_subtitle_languages=["fr"],
    )
    profile = module.manifest_ordering_profile(runtime_vostfr, runtime_vostfr["evidence"])
    if profile["language_group"] != "vostfr":
        raise AssertionError("runtime-only VOSTFR was incorrectly promoted to VF")

    strict = decide(module, activation, item, strict_history(item))
    if not strict["enabled"] or strict["activation_mode"] != "strict_current":
        raise AssertionError("a provider passing all eleven gates was not strictly enabled")

    # A current exact end-to-end strict pass is stronger evidence than an
    # upstream manifest's editorial enabled=false flag. This prevents a healthy
    # provider from disappearing without any failed Niakvio activation gate.
    upstream_disabled_strict = copy.deepcopy(item)
    upstream_disabled_strict["metadata"]["enabled"] = False
    upstream_disabled_strict_result = decide(
        module, activation, upstream_disabled_strict, strict_history(upstream_disabled_strict)
    )
    if not upstream_disabled_strict_result["enabled"]:
        raise AssertionError("strict current proof did not override advisory upstream disabled state")
    if not upstream_disabled_strict_result.get("upstream_disabled_overridden_by_current_strict_proof"):
        raise AssertionError("upstream-disabled strict override was not explicitly reported")
    if "upstream_disabled" in upstream_disabled_strict_result.get("activation_blockers", []):
        raise AssertionError("proven provider retained a contradictory upstream_disabled blocker")

    no_deep_validation = decide(
        module,
        activation,
        item,
        {"strict_consecutive_deep_passes": 0, "strict_total_deep_passes": 0},
    )
    if not no_deep_validation["enabled"] or not no_deep_validation["activation_eligible"]:
        raise AssertionError("current successful deep check did not activate a new SHA immediately")

    inconclusive = inconclusive_item()
    no_evidence = decide(module, activation, inconclusive)
    if no_evidence["enabled"] or no_evidence["activation_eligible"]:
        raise AssertionError("generic no_streams was enabled without direct evidence")

    registry = runtime_registry(inconclusive)
    runtime = decide(module, activation, inconclusive, registry=registry)
    if runtime["enabled"] or runtime["runtime_evidence_eligible"]:
        raise AssertionError("manual runtime evidence bypassed current execution proof")

    mismatch_cases = []
    bad = copy.deepcopy(registry); bad["providers"]["policy-test"]["sha256"] = "b" * 64; mismatch_cases.append(bad)
    bad = copy.deepcopy(registry); bad["providers"]["policy-test"]["source"] = "other"; mismatch_cases.append(bad)
    bad = copy.deepcopy(registry); bad["providers"]["policy-test"]["upstream_id"] = "other"; mismatch_cases.append(bad)
    for bad_registry in mismatch_cases:
        result = decide(module, activation, inconclusive, registry=bad_registry)
        if result["enabled"] or result["runtime_evidence_eligible"]:
            raise AssertionError("mismatched runtime evidence bypassed the policy")

    upstream_disabled = copy.deepcopy(inconclusive)
    upstream_disabled["metadata"]["enabled"] = False
    if decide(module, activation, upstream_disabled, registry=runtime_registry(upstream_disabled))["enabled"]:
        raise AssertionError("runtime evidence overrode upstream disabled state")

    p2p = copy.deepcopy(inconclusive)
    p2p["health"]["status"] = "excluded"
    p2p["health"]["ci_classification"] = "conclusive_failure"
    p2p["health"]["evidence"]["disallowed_streams"] = 1
    if decide(module, activation, p2p, registry=runtime_registry(p2p))["enabled"]:
        raise AssertionError("runtime evidence overrode P2P evidence")

    for hard_status in ("unavailable", "degraded"):
        hard = copy.deepcopy(inconclusive)
        hard["health"]["status"] = hard_status
        hard["health"]["ci_classification"] = "conclusive_failure"
        if decide(module, activation, hard, registry=runtime_registry(hard))["enabled"]:
            raise AssertionError(f"runtime evidence overrode conclusive {hard_status}")

    # No historical, same-SHA or inconclusive grace may activate a provider.
    for count in (1, 2, 3):
        grace = decide(module, activation, inconclusive, strict_history(inconclusive, inconclusive=count))
        if grace["enabled"] or grace["activation_eligible"]:
            raise AssertionError("inconclusive historical grace bypassed current proof")

    prior = {
        "sha256": inconclusive["sha256"],
        "health_score": 100,
        "activation_gates": {name: {"passed": True} for name in (
            "01_policy_safe_no_p2p", "03_minimum_score",
            "04_fixture_and_type_coverage", "05_stream_and_fixture_coverage",
            "06_distinct_host_diversity", "07_verified_payload_playability",
            "08_quality_and_bitrate", "09_language_and_subtitle_integrity",
            "10_content_identity_integrity",
        )},
    }
    historical = decide(module, activation, inconclusive, previous_record=prior)
    if historical["enabled"] or historical["historical_quality_grace_eligible"]:
        raise AssertionError("historical quality state bypassed current proof")

    # Nuvio TV cache workaround: only a real payload change increments the version.
    if module.next_manifest_version("5.13.4", "5.14.2", False) != "5.14.2":
        raise AssertionError("obsolete manifest series was not raised to the configured version floor")
    if module.next_manifest_version("5.14.2", "5.14.2", False) != "5.14.2":
        raise AssertionError("unchanged manifest payload incorrectly bumped the version")
    if module.next_manifest_version("5.14.2", "5.14.2", True) != "5.14.3":
        raise AssertionError("changed manifest payload did not bump the configured version series")
    if module.next_manifest_version("5.11.9", "5.14.2", True) != "5.14.2":
        raise AssertionError("new policy series did not start at 5.13.1")

    auto_disabled = decide(
        module, activation, item, strict_history(item), auto_disabled=True
    )
    if auto_disabled["enabled"] or not auto_disabled["activation_eligible"]:
        raise AssertionError("availability auto-disable state was bypassed")

    # Verify history mutation itself: strict success -> inconclusive preservation ->
    # conclusive failure reset.
    candidates = [{key: value for key, value in item.items() if key != "health"}]
    healthy_result = {**item["health"], **{k: item[k] for k in ("key", "source", "upstream_id", "canonical_id", "sha256")}}
    pre = {item["key"]: module.evaluate_pre_stability_gates(item, activation)}
    h1 = module.update_strict_history({}, candidates, [healthy_result], pre, "deep", activation)
    h2 = h1
    inconclusive_result = {**inconclusive["health"], **{k: inconclusive[k] for k in ("key", "source", "upstream_id", "canonical_id", "sha256")}}
    pre_i = {item["key"]: module.evaluate_pre_stability_gates(inconclusive, activation)}
    # Migration from older history: one successful pass of the same SHA must be
    # recognized before the first v5.13
    # inconclusive result is processed.
    legacy = {
        "schema_version": 53,
        "variants": {
            item["key"]: {
                "sha256": item["sha256"],
                "strict_consecutive_deep_passes": 1,
                "strict_total_deep_passes": 1,
                "last_deep_pre_stability_pass": True,
                "last_checked_at": "2026-07-26T00:00:00+00:00",
            }
        },
    }
    migrated = module.update_strict_history(
        legacy, candidates, [inconclusive_result], pre_i, "deep", activation
    )
    migrated_state = migrated["variants"][item["key"]]
    if (
        migrated_state.get("strict_validated_sha256") != item["sha256"]
        or migrated_state.get("consecutive_inconclusive_deep_checks") != 1
    ):
        raise AssertionError("v5.3 strict history was not migrated into finite grace")

    h3 = module.update_strict_history(h2, candidates, [inconclusive_result], pre_i, "deep", activation)
    state = h3["variants"][item["key"]]
    if state.get("strict_validated_sha256") != item["sha256"] or state.get("consecutive_inconclusive_deep_checks") != 1:
        raise AssertionError("inconclusive deep incorrectly erased strict history")
    hard = copy.deepcopy(inconclusive); hard["health"]["status"] = "unavailable"
    hard_result = {**hard["health"], **{k: hard[k] for k in ("key", "source", "upstream_id", "canonical_id", "sha256")}}
    pre_h = {item["key"]: module.evaluate_pre_stability_gates(hard, activation)}
    h4 = module.update_strict_history(h3, candidates, [hard_result], pre_h, "deep", activation)
    if h4["variants"][item["key"]].get("strict_validated_sha256") is not None:
        raise AssertionError("conclusive failure did not reset strict validation")

    print(
        "Activation policy self-test passed: current DNS, provider access, playable-stream "
        "and quality proof are required; historical, manual and inconclusive grace cannot enable providers."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
