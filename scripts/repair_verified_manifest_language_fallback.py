#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTER = ROOT / "scripts" / "promote_candidates.py"
TEST = ROOT / "tests" / "ci_preservation_policy_test.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = PROMOTER.read_text(encoding="utf-8")

    old_runtime = '''    accepted_subtitles = {
        str(value).casefold()
        for value in proof.get("accepted_subtitle_languages", [])
        if value
    }
    advertised_subtitles = int(
'''
    new_runtime = '''    accepted_subtitles = {
        str(value).casefold()
        for value in proof.get("accepted_subtitle_languages", [])
        if value
    }
    runtime_observed_languages = {
        str(value).casefold()
        for key in ("audio_languages", "subtitle_languages")
        for value in proof.get(key, [])
        if value
    }
    advertised_subtitles = int(
'''
    text = replace_once(text, old_runtime, new_runtime, "runtime language observations")

    old_quality = '''    quality_ok = (
        (effective_height >= minimum_height and (bandwidth is None or bandwidth >= minimum_bandwidth))
        or (runtime_light and (manifest_height >= minimum_height or manifest_curated))
    )
    if runtime_light:
'''
    new_quality = '''    quality_ok = (
        (effective_height >= minimum_height and (bandwidth is None or bandwidth >= minimum_bandwidth))
        or (runtime_light and (manifest_height >= minimum_height or manifest_curated))
    )

    # Some verified containers expose no audio/subtitle language tags at all.
    # In that narrow case, a current upstream manifest language may fill the
    # metadata gap, but only after the same deep run has already proved playable
    # media payloads. Any observed runtime language disables this fallback so a
    # manifest claim can never override contradictory stream evidence.
    manifest_audio_fallback_languages = manifest_languages & accepted_audio_languages
    verified_manifest_audio_fallback = (
        status == "healthy"
        and playable_streams >= minimum_streams
        and payloads >= minimum_payload
        and not runtime_observed_languages
        and bool(manifest_audio_fallback_languages)
    )
    if verified_manifest_audio_fallback:
        accepted_audio = accepted_audio | manifest_audio_fallback_languages
        language_present = bool(accepted_audio or accepted_subtitles)
        accepted_audio_path = allow_audio_without_subtitles and bool(accepted_audio)
        language_subtitle_pass = (
            (not require_language or language_present)
            and (accepted_audio_path or accepted_subtitle_path)
        )

    if runtime_light:
'''
    text = replace_once(text, old_quality, new_quality, "verified manifest audio fallback")

    old_evidence = '''            {
                "accepted_audio_languages": sorted(accepted_audio),
                "accepted_subtitle_languages": sorted(accepted_subtitles),
                "accepted_subtitles_advertised": advertised_subtitles,
                "accepted_subtitles_reachable": reachable_subtitles,
            },
'''
    new_evidence = '''            {
                "accepted_audio_languages": sorted(accepted_audio),
                "accepted_subtitle_languages": sorted(accepted_subtitles),
                "accepted_subtitles_advertised": advertised_subtitles,
                "accepted_subtitles_reachable": reachable_subtitles,
                "runtime_observed_languages": sorted(runtime_observed_languages),
                "manifest_accepted_languages": sorted(manifest_languages),
                "verified_manifest_audio_fallback": verified_manifest_audio_fallback,
            },
'''
    text = replace_once(text, old_evidence, new_evidence, "language gate evidence")
    PROMOTER.write_text(text, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    marker = "# Verified manifest-language fallback regression tests.\n"
    if marker not in test:
        insert = '''

# Verified manifest-language fallback regression tests.
# A current, payload-verified stream may rely on current manifest language only
# when the runtime exposes no language metadata at all. Explicit runtime
# language evidence always wins, and a manifest alone never proves playability.
import importlib.util

sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "promote_candidates_language_gate_test",
    ROOT / "scripts" / "promote_candidates.py",
)
assert spec is not None and spec.loader is not None
promoter_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promoter_module)


def language_gate_item(*, streams=1, payloads=1, runtime_languages=None, manifest_languages=None):
    runtime_languages = list(runtime_languages or [])
    manifest_languages = list(manifest_languages or [])
    return {
        "health": {
            "status": "healthy",
            "score": 90,
            "evidence": {
                "fixtures_tested": 1,
                "healthy_fixtures": 1,
                "healthy_fixture_ratio": 1.0,
                "playable_fixtures": 1 if streams else 0,
                "required_fixture_categories": ["movie"],
                "healthy_fixture_categories": ["movie"],
                "streams_playable": streams,
                "payload_verified_streams": payloads,
                "distinct_reachable_hosts": 1 if streams else 0,
                "reachable_hosts": ["media.example"] if streams else [],
                "effective_max_height": 1080 if streams else None,
                "max_bandwidth": 2_000_000 if streams else None,
                "audio_languages": runtime_languages,
                "subtitle_languages": [],
                "accepted_audio_languages": [
                    value for value in runtime_languages if value in {"fr", "en"}
                ],
                "accepted_subtitle_languages": [],
                "accepted_subtitles_advertised": 0,
                "accepted_subtitles_reachable": 0,
                "provider_median_latency_ms": 100,
                "stream_median_latency_ms": 100,
                "disallowed_streams": 0,
                "provider_server_accessible": True,
                "provider_server_successful_response": True,
                "manifest_description_present": True,
                "manifest_supported_types": ["movie"],
                "manifest_effective_height": 1080,
                "manifest_accepted_languages": manifest_languages,
                "manifest_formats": ["m3u8"],
                "manifest_curation_score": 5,
                "manifest_quality_signals": ["explicit_height:1080"],
            },
        }
    }


verified_no_tags = language_gate_item(manifest_languages=["en", "pe"])
gates, _ = promoter_module.evaluate_pre_stability_gates(verified_no_tags, config)
assert gates["09_language_and_subtitle_integrity"]["passed"] is True, gates["09_language_and_subtitle_integrity"]
assert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is True
assert gates["09_language_and_subtitle_integrity"]["evidence"]["accepted_audio_languages"] == ["en"]

explicit_unaccepted_runtime = language_gate_item(
    runtime_languages=["ru"], manifest_languages=["en"]
)
gates, _ = promoter_module.evaluate_pre_stability_gates(explicit_unaccepted_runtime, config)
assert gates["09_language_and_subtitle_integrity"]["passed"] is False, gates["09_language_and_subtitle_integrity"]
assert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is False

manifest_without_media = language_gate_item(
    streams=0, payloads=0, manifest_languages=["en"]
)
gates, _ = promoter_module.evaluate_pre_stability_gates(manifest_without_media, config)
assert gates["09_language_and_subtitle_integrity"]["passed"] is False, gates["09_language_and_subtitle_integrity"]
assert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is False
'''
        needle = "\nprint('CI uncertain last-known-good preservation tests passed')\n"
        if test.count(needle) != 1:
            raise SystemExit("CI preservation test footer changed")
        test = test.replace(needle, insert + needle, 1)
    TEST.write_text(test, encoding="utf-8")

    final = PROMOTER.read_text(encoding="utf-8")
    required = [
        "runtime_observed_languages",
        "manifest_audio_fallback_languages",
        "verified_manifest_audio_fallback",
        'status == "healthy"',
        "playable_streams >= minimum_streams",
        "payloads >= minimum_payload",
        "and not runtime_observed_languages",
        "manifest_languages & accepted_audio_languages",
    ]
    missing = [value for value in required if value not in final]
    if missing:
        raise SystemExit("post-migration assertions failed: " + ", ".join(missing))

    print("verified manifest language fallback migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
