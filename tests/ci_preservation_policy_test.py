#!/usr/bin/env python3
import json
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
print('CI uncertain last-known-good preservation tests passed')
