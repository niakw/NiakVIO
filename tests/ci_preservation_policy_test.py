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
    'blocked', 'provider_unreachable', 'runtime_error',
    'no_streams', 'reachable',
}
preserve_statuses = set(config.get('preserve_enabled_on_ci_uncertain_statuses', []))
inconclusive_statuses = set(config.get('inconclusive_statuses', []))
assert expected <= preserve_statuses
assert preserve_statuses <= inconclusive_statuses
assert 'degraded' in inconclusive_statuses
assert 'degraded' in preserve_statuses
assert 'unavailable' in preserve_statuses
assert 'unavailable' in inconclusive_statuses
assert config.get('zero_stream_is_per_work_not_manifest_disable') is True
assert config.get('provider_accessibility_is_separate_from_stream_accessibility') is True
assert config.get('provider_latency_is_separate_from_stream_latency') is True

promoter = (ROOT / 'scripts/promote_candidates.py').read_text()
assert 'preserved-current-enabled-ci-uncertain' in promoter
assert 'ci_uncertain_kept_last_published_artifact' in promoter
assert '"no_streams"' in promoter
assert 'preserved-current-enabled-ci-uncertain' in promoter
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
assert 'destination, digest, base_filename, base_sha256 = copy_candidate(' in promoter
assert 'previous_provenance.get("providers", {}).get(cid, {})' in promoter
assert '"base_filename": base_filename' in promoter
assert '"base_sha256": base_sha256' in promoter
assert 'previous_state_is_safety_quarantine' in promoter
assert 'ci_result_is_inconclusive' in promoter
assert 'preserved-conclusive-safety-quarantine-ci-uncertain' in promoter
assert 'ci_uncertain_kept_last_conclusive_safety_quarantine' in promoter
assert '''if old_safety_quarantine:
                    provenance[cid] = {
                        **old_provenance,
                        "id": cid,
                        "published_filename": old_filename,
                        "sha256": retained_digest,
                        "patched_sha256": retained_digest,''' in promoter

validator_source = (ROOT / 'scripts/validate_activation_preservation.py').read_text(encoding='utf-8')
assert 'ci_inconclusive_is_not_disablement_proof' in validator_source
assert 'removed-disallowed-p2p' in validator_source
assert 'configured_safety_quarantine' in validator_source
assert 'NIAKVIO_HUB46_ACTIVATION_AUTHORITY_V1' in validator_source
assert 'declared-hub activation mismatch' not in validator_source
assert '["git", "show", "HEAD:manifest.json"]' in validator_source
assert 'NUVIO_PUBLISHED_MANIFEST_BASELINE' in validator_source


def run_validator(*, manifest_rows, report_rows, mode='deep', safety=None):
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
        (root / 'provider-overrides.json').write_text(json.dumps(
            (safety or {}).get('overrides', {})
        ), encoding='utf-8')
        (root / 'PROVENANCE.json').write_text(json.dumps(
            (safety or {}).get('provenance', {})
        ), encoding='utf-8')
        (root / 'automation').mkdir()
        (root / 'automation' / 'evidence').mkdir()
        (root / 'automation' / 'evidence' / 'hub-lab-matrix-46.json').write_text(json.dumps({'hubCount': 46, 'rows': [{'manifestId': 'a'}] + [{'manifestId': f'x{i}'} for i in range(45)]}), encoding='utf-8')
        (root / 'automation' / 'nuvio-client-safety-findings.json').write_text(json.dumps(
            (safety or {}).get('findings', {})
        ), encoding='utf-8')
        for relative, content in (safety or {}).get('files', {}).items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
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


# Activation is targeted: only members of the selected hub matrix may be ON.
# The synthetic validator fixture uses target 'a'; the other 45 matrix rows are
# intentionally absent from this tiny catalogue, so this unit checks the specific
# active/non-target invariant via the exact expected error surface.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': False}],
    report_rows=[],
)
assert result.returncode == 1
assert 'canonical catalogue must contain 96 providers' in result.stderr
assert '46-hub target missing from canonical catalogue' in result.stderr
assert 'non-target provider unexpectedly enabled' not in result.stderr

result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': True}],
    report_rows=[],
)
assert result.returncode == 1
assert 'non-target provider unexpectedly enabled: b' in result.stderr

# official_hub itself is not activation authority; registry-only targets are legal.
assert 'FIELD_ACTIVATION_HUB46_REGISTRY_ONLY' in validator_source


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


# Generic Brain state preservation: no provider-specific exception is allowed.
assert promoter_module.ci_result_is_inconclusive(
    {"health": {"status": "no_streams", "ci_classification": ""}}, config
) is True
assert promoter_module.ci_result_is_inconclusive(
    {"health": {"status": "unavailable", "ci_classification": ""}}, config
) is True
assert promoter_module.ci_result_is_inconclusive(
    {"health": {"status": "unavailable", "ci_classification": "conclusive_failure"}}, config
) is False
assert promoter_module.ci_result_is_inconclusive(
    {"health": {"status": "healthy", "ci_classification": "conclusive"}}, config
) is False
assert promoter_module.previous_state_is_safety_quarantine(
    {"enabled": False, "filename": "providers/example--nuvio-audit-quarantine--deadbeef.js"},
    {"activation_blockers": ["catalogue_audit_playable_identity_contradiction"]},
) is True
assert promoter_module.previous_state_is_safety_quarantine(
    {"enabled": False, "filename": "providers/example--ordinary.js"},
    {"activation_mode": "configured_safety_quarantine"},
) is True
assert promoter_module.previous_state_is_safety_quarantine(
    {"enabled": False, "filename": "providers/example--ordinary.js"},
    {"activation_mode": "disabled", "activation_blockers": ["02_healthy_functional_status"]},
) is False


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
assert gates["09_language_and_subtitle_integrity"]["passed"] is True, gates["09_language_and_subtitle_integrity"]
assert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is False

manifest_without_media = language_gate_item(
    streams=0, payloads=0, manifest_languages=["en"]
)
gates, _ = promoter_module.evaluate_pre_stability_gates(manifest_without_media, config)
assert gates["09_language_and_subtitle_integrity"]["passed"] is True, gates["09_language_and_subtitle_integrity"]
assert gates["07_verified_payload_playability"]["passed"] is False, gates["07_verified_payload_playability"]
assert gates["09_language_and_subtitle_integrity"]["evidence"]["verified_manifest_audio_fallback"] is False

print('CI uncertain last-known-good preservation tests passed')
