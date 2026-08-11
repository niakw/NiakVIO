#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'health-config.json').read_text())['activation']
expected = {
    'blocked', 'provider_unreachable', 'runtime_error', 'unavailable',
    'no_streams', 'reachable', 'degraded',
}
assert expected <= set(config.get('preserve_enabled_on_ci_uncertain_statuses', []))

promoter = (ROOT / 'scripts/promote_candidates.py').read_text()
assert 'preserved-current-enabled-ci-uncertain' in promoter
assert 'ci_uncertain_kept_last_published_artifact' in promoter
assert 'old_artifact_available' in promoter
assert 'ACTIVATION_LKG_PATH' in promoter
assert 'activation_lkg_ids' in promoter
assert 'current_ci_inconclusive' in promoter
assert 'restore_activation_lkg' in promoter
assert 'live_upstream_variants' in promoter
assert 'published-baseline' in promoter
assert 'preservation_upstream_enabled' in promoter
assert 'preservation_live_upstream_sources' in promoter
assert 'if live_upstream_variants' in promoter
assert 'if upstream_enabled and "upstream_disabled" in blockers' in promoter
assert 'restored-activation-lkg-enabled-ci-uncertain' in promoter
assert 'restored_from_activation_lkg' in promoter
assert 'gates.get("01_policy_safe_no_p2p", {}).get("passed", False)' in promoter
assert 'selected_is_published_baseline' not in promoter
assert 'entries[cid] = retained' in promoter
assert 'continue\n\n            try:\n                destination, digest = copy_candidate(selected)' in promoter

validator_source = (ROOT / 'scripts/validate_activation_preservation.py').read_text(encoding='utf-8')
assert 'ci_inconclusive_is_not_disablement_proof' in validator_source
assert 'removed-disallowed-p2p' in validator_source


def run_validator(*, manifest_rows, report_rows, mode='deep'):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'vf').mkdir()
        active_ids = ['a', 'b']
        (root / 'provider-activation-lkg.json').write_text(json.dumps({
            'minimum_enabled_count': 2,
            'active_ids': active_ids,
        }), encoding='utf-8')
        manifest = {'scrapers': manifest_rows}
        (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        # The projection may contain only the same fixture providers here; the
        # validator's concern is activation parity for ids present in both.
        (root / 'vf' / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        (root / 'health-report.json').write_text(json.dumps({
            'test_mode': mode,
            'providers': report_rows,
        }), encoding='utf-8')
        script = validator_source.replace(
            'ROOT = Path(__file__).resolve().parents[1]',
            f'ROOT = Path({str(root)!r})',
        )
        script_path = root / 'validate_activation.py'
        script_path.write_text(script, encoding='utf-8')
        return subprocess.run(
            [sys.executable, str(script_path)],
            text=True,
            capture_output=True,
        )


# A historical provider may be disabled only when the same deep promotion has
# conclusive strict-gate evidence for doing so.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': False}],
    report_rows=[
        {'id': 'a', 'enabled': True, 'action': 'enabled-current-dns-access-stream-quality-passed', 'failed_gates': []},
        {'id': 'b', 'enabled': False, 'action': 'published-disabled-failed-gates', 'failed_gates': ['08_quality_and_bitrate']},
    ],
)
assert result.returncode == 0, result.stdout + result.stderr

# CI uncertainty is never sufficient proof to shrink the historical active set.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': False}],
    report_rows=[
        {'id': 'a', 'enabled': True, 'action': 'enabled-current-dns-access-stream-quality-passed', 'failed_gates': []},
        {'id': 'b', 'enabled': False, 'action': 'published-disabled-ci-inconclusive-no-valid-runtime-evidence', 'failed_gates': ['02_healthy_functional_status']},
    ],
)
assert result.returncode == 1
assert 'ci_inconclusive_is_not_disablement_proof' in result.stderr

# A hard P2P exclusion may remove an old provider entirely, but only with the
# dedicated policy gate evidence. This does not weaken the P2P guard.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}],
    report_rows=[
        {'id': 'a', 'enabled': True, 'action': 'enabled-current-dns-access-stream-quality-passed', 'failed_gates': []},
        {'id': 'b', 'enabled': False, 'action': 'removed-disallowed-p2p', 'failed_gates': ['01_policy_safe_no_p2p']},
    ],
)
assert result.returncode == 0, result.stdout + result.stderr

# Ordinary gate failure can disable a published entry, not silently delete it.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}],
    report_rows=[
        {'id': 'a', 'enabled': True, 'action': 'enabled-current-dns-access-stream-quality-passed', 'failed_gates': []},
        {'id': 'b', 'enabled': False, 'action': 'published-disabled-failed-gates', 'failed_gates': ['08_quality_and_bitrate']},
    ],
)
assert result.returncode == 1
assert 'missing_provider_not_justified' in result.stderr

# A quick/report-only result can never authorize historical activation shrink.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': False}],
    report_rows=[
        {'id': 'a', 'enabled': True, 'action': 'enabled-current-dns-access-stream-quality-passed', 'failed_gates': []},
        {'id': 'b', 'enabled': False, 'action': 'published-disabled-failed-gates', 'failed_gates': ['08_quality_and_bitrate']},
    ],
    mode='quick',
)
assert result.returncode == 1
assert 'requires the current deep promotion report' in result.stderr


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

print('CI uncertain last-known-good preservation tests passed')
