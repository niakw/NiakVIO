#!/usr/bin/env python3
"""The cross-source reverse matrix remains read-only and honest."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
workflow=(ROOT/'.github/workflows/brain-multi-topology-reverse.yml').read_text(encoding='utf-8')
expected={"4khdhub","allanime","animevostfr","moviesmod","yflix","flemmix"}
assert {line.split('provider: ',1)[1].split(',')[0].strip() for line in workflow.splitlines()
        if '- { provider: ' in line}==expected
assert "ref: ${{ github.sha }}" in workflow
assert 'NIAKVIO_REQUIRE_DECODE_PROOF' in workflow
assert 'python tests/brain_strict_fixture_category_test.py' in workflow
assert "'scripts/evaluate_brain_llm_force_candidates.py'" in workflow
assert 'publicationAuthority' in workflow and 'False' in workflow
assert 'providerMutationAllowed' in workflow
assert 'candidateDecodedIdentityProven' in workflow
assert 'fixtureCoverageIncomplete' in workflow
assert 'BRAIN_REVERSE_FIXTURE_COVERAGE' in workflow
assert 'missingFixtureCategories' in workflow
assert 'expectedFixtureCount' in workflow
assert 'audit_brain_harness_differential.py' in workflow
assert 'tests/brain_harness_differential_test.py' in workflow
assert 'sameByteHarnessDifferential' in workflow
assert 'harnessDifferentialChecked' in workflow
assert 'worker_zero_nuvio_provider_request' in workflow
assert '--stage health-output/reverse-topology/live-preflight/stage' in workflow
assert '--health health-output/reverse-topology/live-preflight/health/health-results.json' in workflow
assert 'health-output/reverse-topology/${{ matrix.provider }}-harness.json' in workflow
assert 'if host in {"api.themoviedb.org","www.themoviedb.org","image.tmdb.org"}:' in [
    line.strip() for line in workflow.splitlines()
]
assert 'max-parallel: 3' in workflow
for banned in ('NIAKVIO_ALLOW_PAID_API=1','plan_batch_from_checkout.py',
               'publish_niakvio_force_mutations.py','--apply','git push','gh workflow run'):
    assert banned not in workflow,banned
print('BRAIN_MULTI_TOPOLOGY_REVERSE_WORKFLOW_OK read-only 6 independent current-byte witnesses')

# Lifecycle-disabled historical representatives are not live Repair targets.
assert 'id: eligibility' in workflow
assert 'FIELD_BRAIN_REVERSE_SCOPE' in workflow
assert workflow.count("if: steps.eligibility.outputs.eligible == 'true'") >= 2
assert "if: always() && steps.eligibility.outputs.eligible == 'true'" in workflow
assert "lifecycle-disabled-or-not-current" in workflow
print('BRAIN_MULTI_TOPOLOGY_LIFECYCLE_SCOPE_OK disabled targets are not re-probed')
