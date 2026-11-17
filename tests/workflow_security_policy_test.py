#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github' / 'workflows'
SHA = re.compile(r'^[0-9a-f]{40}$', re.IGNORECASE)
USES = re.compile(r'^\s*(?:-\s*)?uses:\s*([^\s#]+)', re.MULTILINE)
errors: list[str] = []

for path in sorted([*WORKFLOWS.glob('*.yml'), *WORKFLOWS.glob('*.yaml')]):
    text = path.read_text(encoding='utf-8')
    rel = path.relative_to(ROOT)
    if re.search(r'^\s*pull_request_target\s*:', text, re.MULTILINE):
        errors.append(f'{rel}: pull_request_target is forbidden')
    if re.search(r'^\s*permissions\s*:\s*write-all\s*$', text, re.MULTILINE):
        errors.append(f'{rel}: permissions write-all is forbidden')
    if 'permissions:' not in text:
        errors.append(f'{rel}: explicit permissions are required')
    if 'npm install --ignore-scripts --no-audit --no-fund --package-lock=false' in text:
        errors.append(f'{rel}: unpinned npm fallback is forbidden; use npm ci with package-lock.json')
    if (
        re.search(r'^\s*workflow_run\s*:', text, re.MULTILINE)
        and re.search(r'^\s*contents\s*:\s*write\s*$', text, re.MULTILINE)
        and 'github.event.workflow_run.head_repository.full_name == github.repository' not in text
    ):
        errors.append(f'{rel}: workflow_run writer must require the source run to belong to this repository')
    for match in USES.finditer(text):
        value = match.group(1).strip('"\'')
        if value.startswith('./'):
            continue
        if value.startswith('docker://'):
            if '@sha256:' not in value:
                errors.append(f'{rel}: Docker action/image must be digest-pinned: {value}')
            continue
        if '@' not in value:
            errors.append(f'{rel}: action/ref missing immutable pin: {value}')
            continue
        _action, ref = value.rsplit('@', 1)
        if not SHA.fullmatch(ref):
            errors.append(f'{rel}: external action must use full commit SHA: {value}')

release_candidate = (WORKFLOWS / 'release-candidate-validation.yml').read_text(encoding='utf-8')
for marker in (
    'dispatch github-actions-gate.yml -f "inputs[expected_sha]=${TARGET_SHA}"',
    'dispatch codeql.yml -f "inputs[expected_sha]=${TARGET_SHA}"',
    'dispatch security-final-gate.yml -f "inputs[expected_sha]=${TARGET_SHA}"',
    'dispatch external-code-audit.yml -f "inputs[ref]=${TARGET_SHA}" -F \'inputs[publish]=false\'',
    "'security-final-gate.yml',",
    'security=codeql+final-gate+external',
):
    if marker not in release_candidate:
        errors.append(f'release-candidate-validation.yml: exact-SHA final security certification missing {marker}')
if "github.event_name == 'workflow_dispatch' && github.run_id" not in release_candidate:
    errors.append('release-candidate-validation.yml: exact final certification dispatch must use an isolated run_id concurrency group')
if "cancel-in-progress: ${{ github.event_name != 'workflow_dispatch' }}" not in release_candidate:
    errors.append('release-candidate-validation.yml: exact final certification dispatch must never be cancelled')

# Every workflow_dispatch launched by release-candidate validation is exact-SHA
# proof. It must not share a cancellable main/ref concurrency slot with routine
# push/schedule/PR runs; otherwise a later automatic event can destroy the
# authoritative certification while it is in flight.
for filename in (
    'github-actions-gate.yml',
    'provider-non-regression.yml',
    'core-stream-metadata-contract.yml',
    'canonical-media-types.yml',
    'provider-overrides-gate.yml',
    'codeql.yml',
    'security-final-gate.yml',
    'external-code-audit.yml',
    'native-mobile-android-reader.yml',
    'native-mobile-ios-reader.yml',
    'native-desktop-reader-acceptance.yml',
):
    dispatched = (WORKFLOWS / filename).read_text(encoding='utf-8')
    if "github.event_name == 'workflow_dispatch' && github.run_id" not in dispatched:
        errors.append(f'{filename}: exact workflow_dispatch certification must use an isolated run_id concurrency group')
    if filename != 'codeql.yml' and "cancel-in-progress: ${{ github.event_name != 'workflow_dispatch' }}" not in dispatched:
        errors.append(f'{filename}: exact workflow_dispatch certification must never be cancelled')

security_gate = (WORKFLOWS / 'security-final-gate.yml').read_text(encoding='utf-8')
if 'exact 92-provider scan' in security_gate or 'expected=92' in security_gate or 'len(rows) != 92' in security_gate:
    errors.append('security-final-gate.yml: published provider count must be derived from current projection authority, never hard-coded')
if 'expected=len(rows)' not in security_gate:
    errors.append('security-final-gate.yml: exhaustive scan must derive expected count from published rows')
if "if checked != expected:" not in security_gate:
    errors.append('security-final-gate.yml: exhaustive scan completion check is required')
if security_gate.count('from current_provider_scope import projection_visible_provider_rows') < 1:
    errors.append('security-final-gate.yml: byte-level security scan must use Global+France visible projection authority')
if 'active_rows=projection_active_provider_rows()' not in security_gate:
    errors.append('security-final-gate.yml: CodeQL release scope must use active Global+France projection authority')
if "canonical_id not in active_ids" not in security_gate:
    errors.append('security-final-gate.yml: inactive provenance must not widen CodeQL release-reachable ProviderBase scope')
for required_path in ("vf/manifest.json", "provider_catalog.json", "scripts/current_provider_scope.py"):
    if f"- '{required_path}'" not in security_gate:
        errors.append(f"security-final-gate.yml: Global+France security trigger missing {required_path}")

if "FIELD_CODEQL_FULL_WORKFLOW state=completed:success" not in security_gate or \
        "Wait for complete CodeQL workflow on exact tested main SHA" not in security_gate or \
        "actions: read" not in security_gate:
    errors.append('security-final-gate.yml: block on complete successful CodeQL matrix, not just first analysis')
if "ref: ${{ github.sha }}" not in security_gate:
    errors.append('security-final-gate.yml: security gate must checkout the exact triggering SHA')
if "github.event_name == 'workflow_dispatch' && github.run_id || github.ref" not in security_gate:
    errors.append('security-final-gate.yml: exact release dispatches must use an isolated concurrency group')
if "cancel-in-progress: ${{ github.event_name != 'workflow_dispatch' }}" not in security_gate:
    errors.append('security-final-gate.yml: exact workflow_dispatch certification must never be cancelled')
for required_path in (
    "scripts/provider_base_store.py",
    "scripts/add_provider.py",
    "scripts/probe_provider_runtime_parity.py",
    "tests/provider_bulk_spa_route_discovery_test.py",
):
    if f"- '{required_path}'" not in security_gate:
        errors.append(f"security-final-gate.yml: missing security trigger for {required_path}")

if "python tests/provider_bulk_spa_route_discovery_test.py" not in security_gate:
    errors.append("security-final-gate.yml: malformed SPA route regression must block final security certification")

if "path.startswith(('provider-disabled/','provider-old/'))" not in security_gate:
    errors.append('security-final-gate.yml: stale disabled/archive alerts must remain outside release-reachable blocking scope')

codeql = (WORKFLOWS / 'codeql.yml').read_text(encoding='utf-8')
if codeql.count('- provider-disabled/**') < 2:
    errors.append('codeql.yml: provider-disabled/** must be excluded from maintained Python and JS Core analysis')
if 'startswith("provider-disabled/")' not in codeql:
    errors.append('codeql.yml: alert cleanup must be scoped to provider-disabled/** only')
# A stale legacy analysis configuration must not be recreated just to retire
# an old alert. The dedicated cleanup workflow deletes only that obsolete
# configuration after a clean exact-SHA maintained JS Core analysis.
if 'CodeQL · JS Legacy Category Reconciliation' in codeql or \
        'category: ".github/workflows/codeql.yml:analyze"' in codeql:
    errors.append('codeql.yml: obsolete monolithic JS category must not be recreated')
retire = (WORKFLOWS / 'retire-stale-codeql-2531.yml').read_text(encoding='utf-8')
if 'delete_stale_codeql_2531_configuration.py' not in retire:
    errors.append('retire-stale-codeql-2531.yml: bounded stale-configuration cleanup is required')
if 'retire_stale_codeql_2531.py' in retire:
    errors.append('retire-stale-codeql-2531.yml: direct stale-alert PATCH retirement must not be automatic')
cleanup = (ROOT / 'scripts' / 'retire_stale_codeql_2531.py').read_text(encoding='utf-8')
stale_config_cleanup = (ROOT / 'scripts' / 'delete_stale_codeql_2531_configuration.py').read_text(encoding='utf-8')
for marker in (
    'legacy_js_categories',
    'confirm_delete=true',
    'Exact-main maintained JS Core CodeQL analysis not found',
    'Unresolved current JS Core High/Critical alert remains',
    'evidence_only_drift',
):
    if marker not in stale_config_cleanup:
        errors.append(f'delete_stale_codeql_2531_configuration.py: missing bounded cleanup marker {marker}')
for marker in (
    'verify_current_source()',
    'scan_source_sha()',
    'evidence_only_drift',
    'code-scanning/analyses',
    'scope:core',
    '"PATCH"',
    'dismissed_reason',
    'dismissed_comment',
):
    if marker not in cleanup:
        errors.append(f'retire_stale_codeql_2531.py: missing fail-closed marker {marker}')
if "Bulk dismissal requested by the repository owner" in codeql:
    errors.append('codeql.yml: blanket CodeQL alert dismissal is forbidden')

security_audit = (WORKFLOWS / 'security-audit-now.yml').read_text(encoding='utf-8')
source_marker = 'CodeQL · javascript-typescript · source'
source_pos = security_audit.find(source_marker)
source_tail = security_audit[source_pos:source_pos + 900] if source_pos >= 0 else ''
if '- provider-disabled/**' not in source_tail or '- provider-old/**' not in source_tail:
    errors.append('security-audit-now.yml: one-shot source CodeQL must exclude disabled/archive provider snapshots')


brain_learning = (WORKFLOWS / 'brain-learning-lab.yml').read_text(encoding='utf-8')
if 'path: .brain-llm-runtime/llama-prebuilt' in brain_learning:
    errors.append('brain-learning-lab.yml: executable llama.cpp binaries must never be restored from actions/cache')
if 'steps.brain_llm_llama_cache.outputs.cache-hit' in brain_learning:
    errors.append('brain-learning-lab.yml: executable llama.cpp download must not depend on an actions/cache hit')
if '460c45fa8a9ebc36c9b08e3a15c06dbdbeb312c6308599521c84d9e7f92a268b' not in brain_learning:
    errors.append('brain-learning-lab.yml: pinned llama.cpp b11140 Ubuntu x64 archive digest is required')
if 'sha256sum -c -' not in brain_learning:
    errors.append('brain-learning-lab.yml: downloaded llama.cpp executable archive must be verified before extraction')

# A skipped hosted producer cannot upload the artifact expected by its
# workflow_run consumer. Preserve failed-run diagnostics and manual replay.
hosted_evidence = (WORKFLOWS / 'brain-hosted-evidence-report.yml').read_text(encoding='utf-8')
if "github.event.workflow_run.conclusion != 'skipped'" not in hosted_evidence:
    errors.append('brain-hosted-evidence-report.yml: skipped producer must not trigger artifact download')

if errors:
    raise SystemExit('workflow security policy failed:\n- ' + '\n- '.join(errors))
print('workflow security policy tests passed')