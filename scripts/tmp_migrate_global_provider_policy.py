#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "health-config.json"
OVERRIDES = ROOT / "provider-overrides.json"
APPLY = ROOT / "scripts" / "apply_provider_overrides.py"
PROMOTE = ROOT / "scripts" / "promote_candidates.py"
VALIDATE = ROOT / "scripts" / "validate_policy.py"
CI_TEST = ROOT / "tests" / "ci_preservation_policy_test.py"
TYPE_TEST = ROOT / "tests" / "type_scoped_activation_test.py"
AUDIT = ROOT / "scripts" / "audit_catalogue_identity_media.py"
FIXTURE_TEST = ROOT / "tests" / "tv_catalogue_fixture_coverage_test.py"
PACKAGE = ROOT / "package.json"
GLOBAL_TEST = ROOT / "tests" / "global_provider_policy_test.py"

CATALOGUE_HOOK = "scripts/provider_patches/global_catalogue_alias_recovery_v1.py"
MEDIA_HOOK = "scripts/provider_patches/global_media_enrichment_v1.py"


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"missing migration anchor: {label}")
    return text.replace(old, new, 1)


def migrate_config() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["schema_version"] = max(68, int(cfg.get("schema_version") or 0))
    deep = cfg.setdefault("modes", {}).setdefault("deep", {})
    deep["fallback_fixture_limit_per_category"] = 3
    deep["fallback_only_when_all_primary_no_streams"] = False
    activation = cfg.setdefault("activation", {})
    activation["minimum_score_enabled"] = 55
    activation["minimum_healthy_fixture_ratio"] = 0.34
    # Resolution and bitrate are ranking/diagnostic signals for the general
    # manifest. Playback, payload, identity and duration remain hard gates.
    activation["minimum_effective_height"] = 0
    activation["minimum_bandwidth_bps_when_reported"] = 0
    activation["preferred_height"] = 1080
    activation["require_accepted_language_evidence"] = False
    activation["quality_auto_disable"] = False
    dump(CONFIG, cfg)


def migrate_overrides() -> None:
    cfg = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    cfg["schema_version"] = max(6, int(cfg.get("schema_version") or 0))
    cfg["catalogue_resolution_policy"] = {
        "version": 1,
        "enabled": True,
        "id_first": True,
        "provider_specific_titles_forbidden": True,
        "capabilities": ["html_scraper", "mixed_embed_resolver"],
        "require_official_site": True,
        "global_discovery_hook": CATALOGUE_HOOK,
        "options": {
            "max_aliases": 6,
            "max_candidates": 8,
            "max_players": 8,
            "timeout_ms": 7000,
        },
    }
    cfg["media_enrichment_policy"] = {
        "version": 1,
        "enabled": True,
        "transcoding": False,
        "preserve_original": True,
        "capabilities": ["html_scraper", "mixed_embed_resolver", "api_stream_resolver"],
        "global_discovery_hook": MEDIA_HOOK,
        "options": {
            "max_rows": 6,
            "max_depth": 2,
            "max_candidates": 10,
            "timeout_ms": 6500,
            "preserve_original": True,
        },
    }
    dump(OVERRIDES, cfg)


def migrate_apply_overrides() -> None:
    source = APPLY.read_text(encoding="utf-8")
    anchor = '''    # Playback integrity is a repository-wide discovery invariant, not a list\n    # of currently-known providers. Run it last so every native, recovered or\n'''
    block = '''    # Catalogue recovery is capability-based and ID-first. It is intentionally\n    # global: provider-specific title aliases are forbidden. Providers with a\n    # public HTML catalogue receive the same bounded TMDB localized/original\n    # alias fallback whenever their native resolver returns no stream.\n    if phase == "discovery":\n        capability = str(specific.get("capability") or "").strip().casefold()\n        catalogue_policy = config.get("catalogue_resolution_policy") or {}\n        if not isinstance(catalogue_policy, dict):\n            raise ValueError("catalogue_resolution_policy must be an object")\n        catalogue_capabilities = {\n            str(value).strip().casefold()\n            for value in catalogue_policy.get("capabilities", [])\n            if str(value).strip()\n        }\n        official_site = str(specific.get("official_site") or "").strip()\n        if (\n            catalogue_policy.get("enabled", False)\n            and capability in catalogue_capabilities\n            and official_site\n        ):\n            patch_script = str(catalogue_policy.get("global_discovery_hook") or "").strip()\n            if not patch_script:\n                raise ValueError("catalogue_resolution_policy.global_discovery_hook is required")\n            options = dict(catalogue_policy.get("options") or {})\n            options.update({\n                "base_url": official_site,\n                "provider_name": provider_id,\n            })\n            before = text\n            text = _apply_patch_script(text, provider_id, patch_script, options, None)\n            if text != before:\n                applied.append({\n                    "type": "patch_script",\n                    "path": patch_script,\n                    "phase": phase,\n                    "scope": "global_catalogue_resolution",\n                })\n\n        # HTML/embed/API rows are enriched globally with direct HLS/DASH/container\n        # media when it can be proven. The original row is always retained, so\n        # this never turns an iframe-capable provider into a direct-media-only one.\n        media_policy = config.get("media_enrichment_policy") or {}\n        if not isinstance(media_policy, dict):\n            raise ValueError("media_enrichment_policy must be an object")\n        media_capabilities = {\n            str(value).strip().casefold()\n            for value in media_policy.get("capabilities", [])\n            if str(value).strip()\n        }\n        if media_policy.get("enabled", False) and capability in media_capabilities:\n            patch_script = str(media_policy.get("global_discovery_hook") or "").strip()\n            if not patch_script:\n                raise ValueError("media_enrichment_policy.global_discovery_hook is required")\n            options = dict(media_policy.get("options") or {})\n            before = text\n            text = _apply_patch_script(text, provider_id, patch_script, options, None)\n            if text != before:\n                applied.append({\n                    "type": "patch_script",\n                    "path": patch_script,\n                    "phase": phase,\n                    "scope": "global_media_enrichment",\n                })\n\n'''
    if block not in source:
        if anchor not in source:
            raise SystemExit("apply_overrides global policy anchor missing")
        source = source.replace(anchor, block + anchor, 1)
    APPLY.write_text(source, encoding="utf-8")


def migrate_health_check() -> None:
    path = ROOT / "scripts" / "health_check.mjs"
    source = path.read_text(encoding="utf-8")
    old = '''  const fallbackToRun = requestedMode === 'deep'\n    ? fallbackFixtures.filter((fixture) => categoriesNeedingFallback.has(fixture.category))\n    : [];\n  const useFallback = fallbackToRun.length > 0;\n  if (useFallback) {\n    for (const fixture of fallbackToRun) await executeFixture(fixture, 'fallback');\n  }\n'''
    new = '''  // Deep fallback is a bounded cascade per catalogue category. Stop as soon\n  // as one alternate work proves the category healthy. A catalogue miss is not\n  // evidence that the provider itself is dead.\n  if (requestedMode === 'deep') {\n    for (const category of categoriesNeedingFallback) {\n      const categoryFallbacks = fallbackFixtures.filter((fixture) => fixture.category === category);\n      for (const fixture of categoryFallbacks) {\n        await executeFixture(fixture, 'fallback');\n        const latest = fixtureResults[fixtureResults.length - 1];\n        if (latest?.fixture?.category === category && latest.status === 'healthy') break;\n        if (latest?.status === 'excluded') break;\n      }\n    }\n  }\n'''
    source = replace_once(source, old, new, "adaptive fallback execution")
    old2 = '''    const fallback = fixtureResults.filter((item) => item.fixture_phase === 'fallback' && item.fixture?.category === category);\n    return fallback.length ? fallback : primary;\n'''
    new2 = '''    const fallback = fixtureResults.filter((item) => item.fixture_phase === 'fallback' && item.fixture?.category === category);\n    const healthyFallback = fallback.find((item) => item.status === 'healthy');\n    // Once an alternate title proves current playback, earlier catalogue misses\n    // remain diagnostics and do not dilute the activation coverage ratio.\n    return healthyFallback ? [healthyFallback] : (fallback.length ? fallback : primary);\n'''
    source = replace_once(source, old2, new2, "fallback activation sample")
    path.write_text(source, encoding="utf-8")


def migrate_promoter() -> None:
    source = PROMOTE.read_text(encoding="utf-8")
    source = source.replace(
        "Automatic activation still requires all ten strict gates.",
        "Automatic activation requires current playback/identity safety gates; quality and language are ranking/projection signals for the general manifest.",
        1,
    )
    source = source.replace(
        "8. minimum quality and non-deficient reported bitrate;\n9. accepted FR/EN language evidence and working advertised subtitles;",
        "8. media-quality diagnostics (non-blocking for a verified general stream);\n9. language/subtitle diagnostics (VF filtering is handled by language projection);",
        1,
    )
    source = source.replace(
        "minimum_height = int(activation.get(\"minimum_effective_height\", 720))",
        "minimum_height = int(activation.get(\"minimum_effective_height\", 0))",
    )
    source = source.replace(
        "minimum_bandwidth = int(activation.get(\"minimum_bandwidth_bps_when_reported\", 1_000_000))",
        "minimum_bandwidth = int(activation.get(\"minimum_bandwidth_bps_when_reported\", 0))",
    )
    source = source.replace(
        "require_language = bool(activation.get(\"require_accepted_language_evidence\", True))",
        "require_language = bool(activation.get(\"require_accepted_language_evidence\", False))",
    )
    # Type-scoped proof: current verified payload is mandatory; quality/language
    # thresholds apply only when explicitly configured above zero / true.
    source = source.replace(
        '''        if height < minimum_height or (bandwidth is not None and bandwidth < minimum_bandwidth):\n            continue\n''',
        '''        if minimum_height > 0 and height > 0 and height < minimum_height:\n            continue\n        if minimum_bandwidth > 0 and bandwidth is not None and bandwidth < minimum_bandwidth:\n            continue\n''',
        1,
    )
    old_lang = '''    language_subtitle_pass = (\n        (not require_language or language_present)\n        and (accepted_audio_path or accepted_subtitle_path)\n    )\n'''
    new_lang = '''    language_subtitle_pass = (\n        True\n        if not require_language\n        else (language_present and (accepted_audio_path or accepted_subtitle_path))\n    )\n'''
    source = replace_once(source, old_lang, new_lang, "general language gate")
    old_curated = '''    manifest_curated = (\n        manifest_description_present\n        and bool(manifest_languages & (accepted_audio_languages | accepted_subtitle_languages))\n        and manifest_usable_stream_format\n        and manifest_curation_score >= minimum_manifest_curation_score\n    )\n    quality_ok = (\n        (effective_height >= minimum_height and (bandwidth is None or bandwidth >= minimum_bandwidth))\n        or (runtime_light and (manifest_height >= minimum_height or manifest_curated))\n    )\n'''
    new_curated = '''    manifest_curated = (\n        manifest_description_present\n        and (not require_language or bool(manifest_languages & (accepted_audio_languages | accepted_subtitle_languages)))\n        and manifest_usable_stream_format\n        and manifest_curation_score >= minimum_manifest_curation_score\n    )\n    current_verified_media = playable_streams >= minimum_streams and payloads >= minimum_payload\n    measured_quality_ok = (\n        current_verified_media\n        and (minimum_height <= 0 or effective_height == 0 or effective_height >= minimum_height)\n        and (minimum_bandwidth <= 0 or bandwidth is None or bandwidth >= minimum_bandwidth)\n    )\n    runtime_light_quality_ok = runtime_light and (\n        (minimum_height > 0 and manifest_height >= minimum_height) or manifest_curated\n    )\n    quality_ok = measured_quality_ok or runtime_light_quality_ok\n'''
    source = replace_once(source, old_curated, new_curated, "quality gate semantics")
    # Recompute fallback language pass with the same global semantics.
    old_fallback = '''        language_subtitle_pass = (\n            (not require_language or language_present)\n            and (accepted_audio_path or accepted_subtitle_path)\n        )\n'''
    new_fallback = '''        language_subtitle_pass = (\n            True\n            if not require_language\n            else (language_present and (accepted_audio_path or accepted_subtitle_path))\n        )\n'''
    source = replace_once(source, old_fallback, new_fallback, "manifest language fallback semantics")
    old_light = '''        language_subtitle_pass = manifest_description_present and bool(manifest_languages & (accepted_audio_languages | accepted_subtitle_languages))\n'''
    new_light = '''        language_subtitle_pass = (\n            True\n            if not require_language\n            else manifest_description_present and bool(manifest_languages & (accepted_audio_languages | accepted_subtitle_languages))\n        )\n'''
    source = replace_once(source, old_light, new_light, "runtime-light language semantics")
    PROMOTE.write_text(source, encoding="utf-8")


def migrate_validate_policy() -> None:
    source = VALIDATE.read_text(encoding="utf-8")
    source = source.replace(
        'assert int(activation.get("minimum_effective_height", 0)) >= 720\n    assert bool(activation.get("require_accepted_language_evidence"))',
        'assert int(activation.get("minimum_effective_height", -1)) == 0\n    assert int(activation.get("minimum_bandwidth_bps_when_reported", -1)) == 0\n    assert not bool(activation.get("require_accepted_language_evidence"))\n    assert int(activation.get("minimum_score_enabled", 0)) == 55',
        1,
    )
    source = source.replace(
        '(lambda value: value["health"].update(score=69), "03_minimum_score"),',
        '(lambda value: value["health"].update(score=54), "03_minimum_score"),',
        1,
    )
    source = source.replace(
        '        (lambda value: value["health"]["evidence"].update(effective_max_height=480, max_bandwidth=500_000), "08_quality_and_bitrate"),\n        (lambda value: value["health"]["evidence"].update(accepted_audio_languages=[], accepted_subtitle_languages=["fr"], accepted_subtitles_advertised=1, accepted_subtitles_reachable=0), "09_language_and_subtitle_integrity"),\n',
        '',
        1,
    )
    marker = '''    for mutate, expected in mutations:\n        assert_gate_fails(module, activation, mutate, expected)\n\n'''
    extra = '''    for mutate, expected in mutations:\n        assert_gate_fails(module, activation, mutate, expected)\n\n    # General activation must not reject a real payload merely because it is\n    # SD/low bitrate or uses a language outside FR/EN. Those signals are used\n    # for ordering and language projections, not provider liveness.\n    broad = copy.deepcopy(item)\n    broad["health"]["evidence"].update(\n        effective_max_height=360,\n        max_bandwidth=350_000,\n        audio_languages=["hi"],\n        accepted_audio_languages=[],\n        accepted_subtitle_languages=[],\n    )\n    broad_gates, _ = module.evaluate_pre_stability_gates(broad, activation)\n    if not broad_gates["08_quality_and_bitrate"]["passed"]:\n        raise AssertionError("verified SD payload was incorrectly rejected from the general manifest")\n    if not broad_gates["09_language_and_subtitle_integrity"]["passed"]:\n        raise AssertionError("non-FR/EN payload was incorrectly rejected from the general manifest")\n\n'''
    source = replace_once(source, marker, extra, "broad general activation regression")
    source = source.replace(
        "Activation policy self-test passed: current DNS, provider access, playable-stream and quality proof are required; historical, manual and inconclusive grace cannot enable providers.",
        "Activation policy self-test passed: current playable payload/identity proof is required; quality and language rank/project but do not suppress general providers.",
    )
    VALIDATE.write_text(source, encoding="utf-8")


def migrate_ci_test() -> None:
    source = CI_TEST.read_text(encoding="utf-8")
    source = source.replace(
        '''gates, _ = promoter_module.evaluate_pre_stability_gates(explicit_unaccepted_runtime, config)\nassert gates["09_language_and_subtitle_integrity"]["passed"] is False, gates["09_language_and_subtitle_integrity"]\nassert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is False\n''',
        '''gates, _ = promoter_module.evaluate_pre_stability_gates(explicit_unaccepted_runtime, config)\nassert gates["09_language_and_subtitle_integrity"]["passed"] is True, gates["09_language_and_subtitle_integrity"]\nassert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is False\n''',
        1,
    )
    source = source.replace(
        '''gates, _ = promoter_module.evaluate_pre_stability_gates(manifest_without_media, config)\nassert gates["09_language_and_subtitle_integrity"]["passed"] is False, gates["09_language_and_subtitle_integrity"]\nassert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is False\n''',
        '''gates, _ = promoter_module.evaluate_pre_stability_gates(manifest_without_media, config)\nassert gates["09_language_and_subtitle_integrity"]["passed"] is True, gates["09_language_and_subtitle_integrity"]\nassert gates["07_verified_payload_playability"]["passed"] is False, gates["07_verified_payload_playability"]\nassert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is False\n''',
        1,
    )
    CI_TEST.write_text(source, encoding="utf-8")


def migrate_type_test() -> None:
    source = TYPE_TEST.read_text(encoding="utf-8")
    source = source.replace("assert 'height < minimum_height' in source", "assert 'minimum_height > 0 and height > 0 and height < minimum_height' in source")
    source = source.replace("assert 'bandwidth is not None and bandwidth < minimum_bandwidth' in source", "assert 'minimum_bandwidth > 0 and bandwidth is not None and bandwidth < minimum_bandwidth' in source")
    source = source.replace("quality_idx = source.index('if height < minimum_height')", "quality_idx = source.index('if minimum_height > 0 and height > 0 and height < minimum_height')")
    source = source.replace(
        "# explicitly requires a healthy current fixture plus verified media/quality.",
        "# explicitly requires a healthy current fixture plus verified media; optional quality/language thresholds apply only when configured.",
    )
    TYPE_TEST.write_text(source, encoding="utf-8")


def remove_title_specific_permanent_fixture() -> None:
    source = AUDIT.read_text(encoding="utf-8")
    block = '''    "animated_movie_ninja_3": {\n        "label": "Mon ninja et moi 3",\n        "tmdbId": "1215638",\n        "mediaType": "movie",\n        "title": "Mon ninja et moi 3",\n        "year": 2025,\n        "expectedDurationMinutes": 88,\n    },\n'''
    source = source.replace(block, "")
    source = source.replace(
        '''        if "movie" in types and (is_vf or provider_id in SUSPECTS):\n            fixture_names.append("animated_movie_ninja_3")\n''',
        "",
    )
    AUDIT.write_text(source, encoding="utf-8")

    fixture = FIXTURE_TEST.read_text(encoding="utf-8")
    fixture = fixture.replace(
        '''\nassert '\"animated_movie_ninja_3\"' in source\nassert '\"tmdbId\": \"1215638\"' in source\nassert '\"title\": \"Mon ninja et moi 3\"' in source\nassert 'fixture_names.append(\"animated_movie_ninja_3\")' in source\n''',
        "\n",
    )
    fixture = fixture.replace(
        "print('TV catalogue Revenant/Mushoku/animated-movie fixture coverage tests passed')",
        "print('TV catalogue Revenant/Mushoku fixture coverage tests passed')",
    )
    FIXTURE_TEST.write_text(fixture, encoding="utf-8")


def write_global_test() -> None:
    GLOBAL_TEST.write_text('''#!/usr/bin/env python3\nfrom __future__ import annotations\n\nimport importlib.util\nimport json\nimport sys\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "scripts"))\nspec = importlib.util.spec_from_file_location("apply_provider_overrides_global", ROOT / "scripts" / "apply_provider_overrides.py")\nassert spec and spec.loader\nmodule = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(module)\n\ncfg = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))\ncat = cfg["catalogue_resolution_policy"]\nmedia = cfg["media_enrichment_policy"]\nassert cat["enabled"] is True and cat["id_first"] is True\nassert cat["provider_specific_titles_forbidden"] is True\nassert set(cat["capabilities"]) == {"html_scraper", "mixed_embed_resolver"}\nassert media["enabled"] is True and media["transcoding"] is False\nassert media["preserve_original"] is True\n\ncat_source = (ROOT / cat["global_discovery_hook"]).read_text(encoding="utf-8")\nmedia_source = (ROOT / media["global_discovery_hook"]).read_text(encoding="utf-8")\nfor token in ("alternative_titles", "original_title", "language=en-US", "if(x&&x.list.length)return v", "q.tmdbId"):\n    assert token in cat_source, token\nfor forbidden in ("Mon ninja et moi 3", "Interstellar", "Ternet Ninja 3"):\n    assert forbidden not in cat_source, forbidden\nfor token in ("preserveOriginal", "m3u8|mpd|mp4|mkv|webm", "kindBytes", "add(row)"):\n    assert token in media_source, token\n\n# A configured HTML provider receives both global behaviours automatically.\nfuture = b'''async function getStreams(){return []};module.exports={getStreams};'''\npatched, records = module.apply_overrides("kurage", future, phase="discovery")\ntext = patched.decode("utf-8")\nassert "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V1" in text\nassert "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1" in text\nscopes = {row.get("scope") for row in records if isinstance(row, dict)}\nassert "global_catalogue_resolution" in scopes\nassert "global_media_enrichment" in scopes\n\n# Direct-media providers remain ID-native and are not wrapped in catalogue search.\ndirect, direct_records = module.apply_overrides("zinkmovies", future, phase="discovery")\nassert b"NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V1" not in direct\nassert not any(row.get("scope") == "global_catalogue_resolution" for row in direct_records if isinstance(row, dict))\n\nhealth = json.loads((ROOT / "health-config.json").read_text(encoding="utf-8"))\nactivation = health["activation"]\nassert activation["minimum_effective_height"] == 0\nassert activation["minimum_bandwidth_bps_when_reported"] == 0\nassert activation["require_accepted_language_evidence"] is False\nassert activation["quality_auto_disable"] is False\nassert health["modes"]["deep"]["fallback_fixture_limit_per_category"] == 3\n\naudit = (ROOT / "scripts" / "audit_catalogue_identity_media.py").read_text(encoding="utf-8")\nassert "Mon ninja et moi 3" not in audit\nassert "1215638" not in audit\nprint("global ID-first catalogue/media and broad activation policy tests passed")\n''', encoding="utf-8")


def migrate_package() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    cmd = package["scripts"]["test"]
    test_cmd = "python3 tests/global_provider_policy_test.py"
    if test_cmd not in cmd:
        cmd += " && " + test_cmd
    package["scripts"]["test"] = cmd
    dump(PACKAGE, package)


def main() -> int:
    migrate_config()
    migrate_overrides()
    migrate_apply_overrides()
    migrate_health_check()
    migrate_promoter()
    migrate_validate_policy()
    migrate_ci_test()
    migrate_type_test()
    remove_title_specific_permanent_fixture()
    write_global_test()
    migrate_package()
    print("global provider policy migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
