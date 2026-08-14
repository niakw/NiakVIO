#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'activation_guard_manual_test',
    ROOT / 'scripts' / 'validate_activation_preservation.py',
)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

reason = 'synthetic_wrong_content'
bundle = (
    f'/* NUVIO_PROVIDER_QUARANTINE_V1 reason={reason} */\n'
    'module.exports={getStreams:async()=>[]};\n'
)
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'providers').mkdir()
    digest = hashlib.sha256(bundle.encode()).hexdigest()
    filename = f'providers/test--quarantine--{digest[:16]}.js'
    (root / filename).write_text(bundle)
    mod.ROOT = root
    manifest = {'enabled': False, 'filename': filename}
    patch = {
        'capability': 'quarantined',
        'manifest_overrides': {'enabled': False},
        'patch_scripts': [mod.QUARANTINE_PATCH],
        'patch_script_options': {mod.QUARANTINE_PATCH: {'reason': reason}},
    }
    provenance = {
        'activation_mode': 'configured_safety_quarantine',
        'activation_eligible': False,
        'activation_blockers': ['configured_safety_quarantine'],
        'published_filename': filename,
        'patched_sha256': digest,
    }
    tested_sha = 'a' * 64
    base = {
        'evidence_source': 'operator_live_client_report',
        'operator_confirmed': True,
        'quarantine_reason': reason,
        'tested_commit_sha': 'b' * 40,
        'tested_bundle': f'providers/test--published-baseline--{tested_sha[:16]}.js',
        'tested_bundle_sha256': tested_sha,
        'fixture': {'tmdbId': '1215638', 'title': 'Mon ninja et moi 3'},
        'quarantined_bundle': filename,
        'quarantined_bundle_sha256': digest,
    }
    wrong = dict(
        base,
        evidence_type='manual_live_wrong_content',
        transport_playable=True,
        observed_content='unrelated event',
        clients_with_contradiction=['tv'],
    )
    ok, why = mod.configured_safety_quarantine('test', manifest, patch, provenance, wrong)
    assert ok, why
    bad = dict(wrong, operator_confirmed=False)
    ok, _ = mod.configured_safety_quarantine('test', manifest, patch, provenance, bad)
    assert not ok
    nonplay = dict(
        base,
        evidence_type='manual_live_non_playable',
        transport_playable=False,
        observed_failure='infinite_loading',
        clients_with_failure=['desktop_macos'],
    )
    ok, why = mod.configured_safety_quarantine('test', manifest, patch, provenance, nonplay)
    assert ok, why
print('manual negative safety evidence tests passed')
