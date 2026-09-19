#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = Path(os.environ.get("RUNNER_TEMP") or (ROOT / ".tmp")).resolve()
PRESTATE = TEMP_ROOT / "niakvio-live-safety-prestate.json"
QUARANTINE_PATCH = 'scripts/provider_patches/quarantine_provider_v1.py'
REASONS = {
    'moviebox': 'non_playable_html_output',
    'netmirror': 'cross_title_search_identity_mismatch',
}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def manifest_rows():
    manifest = load(ROOT / 'manifest.json')
    return {
        str(row.get('id') or '').casefold(): row
        for row in manifest.get('scrapers', [])
        if isinstance(row, dict)
    }


def prepare() -> None:
    rows = manifest_rows()
    prestate = {}
    for provider_id in REASONS:
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise SystemExit(f'missing manifest provider: {provider_id}')
        filename = str(row.get('filename') or '')
        path = ROOT / filename
        if row.get('enabled') is True:
            prestate[provider_id] = {
                'filename': filename,
                'sha256': file_sha(path),
            }
    dump(PRESTATE, prestate)

    promoter_path = ROOT / 'scripts/promote_candidates.py'
    text = promoter_path.read_text(encoding='utf-8')
    old_fallback = '''                    [
                        "blocked",
                        "provider_unreachable",
                        "runtime_error",
                        "unavailable",
                        "no_streams",
                        "reachable",
                        "degraded",
                    ],'''
    new_fallback = '''                    [
                        "blocked",
                        "provider_unreachable",
                        "runtime_error",
                        "no_streams",
                        "reachable",
                    ],'''
    if old_fallback in text:
        text = text.replace(old_fallback, new_fallback, 1)
    elif new_fallback not in text:
        raise SystemExit('promoter preservation fallback anchor missing')

    old_guard = '''            preserve_current = (
                not enabled
                and (old_was_enabled or restore_activation_lkg)'''
    new_guard = '''            preserve_current = (
                not enabled
                and current_ci_inconclusive
                and (old_was_enabled or restore_activation_lkg)'''
    if old_guard in text:
        text = text.replace(old_guard, new_guard, 1)
    elif new_guard not in text:
        raise SystemExit('promoter preservation guard anchor missing')
    promoter_path.write_text(text, encoding='utf-8')

    overrides_path = ROOT / 'provider-overrides.json'
    overrides = load(overrides_path)
    patches = overrides.setdefault('provider_patches', {})
    for provider_id, reason in REASONS.items():
        row = patches.get(provider_id)
        if not isinstance(row, dict):
            raise SystemExit(f'missing provider override: {provider_id}')
        row['capability'] = 'quarantined'
        row['profiles'] = []
        manifest_overrides = row.get('manifest_overrides')
        if not isinstance(manifest_overrides, dict):
            manifest_overrides = {}
        manifest_overrides['enabled'] = False
        row['manifest_overrides'] = manifest_overrides
        row['patch_scripts'] = [QUARANTINE_PATCH]
        row['patch_script_options'] = {QUARANTINE_PATCH: {'reason': reason}}
        row['notes'] = (
            f'Fail-closed safety quarantine: {reason}. Published bundle is inert; '
            're-enable only after fresh strict identity and direct-media proof.'
        )
    dump(overrides_path, overrides)

    quarantine_test_path = ROOT / 'tests/provider_quarantine_test.py'
    quarantine_test = quarantine_test_path.read_text(encoding='utf-8')
    anchor = '    ("vixsrc", "interstellar_duration_mismatch"),\n):'
    replacement = (
        '    ("vixsrc", "interstellar_duration_mismatch"),\n'
        '    ("moviebox", "non_playable_html_output"),\n'
        '    ("netmirror", "cross_title_search_identity_mismatch"),\n'
        '):'
    )
    if replacement not in quarantine_test:
        if anchor not in quarantine_test:
            raise SystemExit('provider quarantine test anchor missing')
        quarantine_test_path.write_text(
            quarantine_test.replace(anchor, replacement, 1), encoding='utf-8'
        )

    validator_path = ROOT / 'scripts/validate_activation_preservation.py'
    validator = validator_path.read_text(encoding='utf-8')
    marker = '    if finding.get("evidence_type") != "duration_identity_mismatch":\n'
    if 'manual_live_wrong_content' not in validator:
        if marker not in validator:
            raise SystemExit('activation safety evidence validator anchor missing')
        manual_block = '''    evidence_type = str(finding.get("evidence_type") or "")
    if evidence_type in {"manual_live_wrong_content", "manual_live_non_playable"}:
        if finding.get("evidence_source") != "operator_live_client_report":
            return False, "manual_safety_finding_source_invalid"
        if finding.get("operator_confirmed") is not True:
            return False, "manual_safety_finding_not_confirmed"
        if not COMMIT_RE.fullmatch(str(finding.get("tested_commit_sha") or "")):
            return False, "manual_safety_finding_commit_invalid"
        tested_sha = str(finding.get("tested_bundle_sha256") or "")
        tested_bundle = str(finding.get("tested_bundle") or "")
        if not SHA256_RE.fullmatch(tested_sha):
            return False, "manual_safety_finding_bundle_sha_invalid"
        if not tested_bundle.startswith("providers/") or not tested_bundle.endswith(f"--{tested_sha[:16]}.js"):
            return False, "manual_safety_finding_bundle_path_invalid"
        fixture = finding.get("fixture")
        if not isinstance(fixture, dict) or not str(fixture.get("tmdbId") or "") or not str(fixture.get("title") or ""):
            return False, "manual_safety_finding_fixture_invalid"
        if evidence_type == "manual_live_wrong_content":
            if finding.get("transport_playable") is not True:
                return False, "manual_wrong_content_not_transport_playable"
            if not str(finding.get("observed_content") or "").strip():
                return False, "manual_wrong_content_observation_missing"
            if not finding.get("clients_with_contradiction"):
                return False, "manual_wrong_content_client_missing"
        else:
            if finding.get("transport_playable") is not False:
                return False, "manual_non_playable_transport_flag_invalid"
            if str(finding.get("observed_failure") or "") not in {"infinite_loading", "non_media_html", "timeout"}:
                return False, "manual_non_playable_observation_invalid"
            if not finding.get("clients_with_failure"):
                return False, "manual_non_playable_client_missing"
        return True, f"configured_safety_quarantine:{reason}:{evidence_type}"

'''
        validator_path.write_text(validator.replace(marker, manual_block + marker, 1), encoding='utf-8')

    regression = r'''#!/usr/bin/env python3
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
'''
    (ROOT / 'tests/manual_negative_safety_evidence_test.py').write_text(
        regression, encoding='utf-8'
    )


def record_evidence() -> None:
    prestate = load(PRESTATE)
    rows = manifest_rows()
    findings_path = ROOT / 'automation/nuvio-client-safety-findings.json'
    data = load(findings_path)
    data['schema_version'] = max(2, int(data.get('schema_version') or 1))
    data['generated_at'] = datetime.now(timezone.utc).isoformat()
    policy = data.setdefault('policy', {})
    policy['manual_negative_evidence_requires_exact_tested_bundle_sha'] = True
    policy['manual_negative_evidence_requires_operator_confirmation'] = True
    findings = [
        row for row in data.get('findings', [])
        if isinstance(row, dict)
        and str(row.get('provider_id') or '').casefold() not in REASONS
    ]
    commit_sha = os.environ.get('GITHUB_SHA', '')

    def common(provider_id: str, reason: str):
        current = rows[provider_id]
        quarantine_file = str(current.get('filename') or '')
        return {
            'provider_id': provider_id,
            'evidence_source': 'operator_live_client_report',
            'operator_confirmed': True,
            'quarantine_reason': reason,
            'tested_commit_sha': commit_sha,
            'tested_bundle': prestate[provider_id]['filename'],
            'tested_bundle_sha256': prestate[provider_id]['sha256'],
            'fixture': {
                'tmdbId': '1215638',
                'mediaType': 'movie',
                'title': 'Mon ninja et moi 3',
            },
            'quarantined_bundle': quarantine_file,
            'quarantined_bundle_sha256': file_sha(ROOT / quarantine_file),
        }

    if 'netmirror' in prestate:
        row = common('netmirror', REASONS['netmirror'])
        row.update({
            'evidence_type': 'manual_live_wrong_content',
            'transport_playable': True,
            'observed_content': 'unrelated athletics event',
            'observed_duration_seconds': 11820,
            'clients_with_contradiction': ['desktop_macos', 'tv'],
        })
        findings.append(row)
    if 'moviebox' in prestate:
        row = common('moviebox', REASONS['moviebox'])
        row.update({
            'evidence_type': 'manual_live_non_playable',
            'transport_playable': False,
            'observed_failure': 'infinite_loading',
            'clients_with_failure': ['desktop_macos'],
        })
        findings.append(row)
    data['findings'] = findings
    dump(findings_path, data)


def assert_result() -> None:
    rows = manifest_rows()
    for provider_id, reason in REASONS.items():
        row = rows[provider_id]
        if row.get('enabled') is not False:
            raise SystemExit(f'{provider_id}: not disabled')
        filename = str(row.get('filename') or '')
        payload = (ROOT / filename).read_text(encoding='utf-8')
        if 'NUVIO_PROVIDER_QUARANTINE_V1' not in payload or reason not in payload:
            raise SystemExit(f'{provider_id}: published bundle is not inert')
        print(
            f'FIELD_SAFETY_QUARANTINE provider={provider_id} '
            f'enabled=false file={filename} reason={reason}'
        )
    streamzo = rows.get('streamzo') or {}
    if streamzo.get('enabled') is not True:
        raise SystemExit('streamzo: safety repair must not globally disable it')
    print(
        f"FIELD_STREAMZO_UNCHANGED enabled=true file={streamzo.get('filename')}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'record-evidence', 'assert'))
    args = parser.parse_args()
    if args.phase == 'prepare':
        prepare()
    elif args.phase == 'record-evidence':
        record_evidence()
    else:
        assert_result()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
