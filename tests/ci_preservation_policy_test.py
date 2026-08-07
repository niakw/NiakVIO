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

print('CI uncertain last-known-good preservation tests passed')
