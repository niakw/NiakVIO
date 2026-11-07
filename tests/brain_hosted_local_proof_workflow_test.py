#!/usr/bin/env python3
"""Guard the re-enabled main-only, local Qwen, sandbox proof path."""
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
source=(root/'.github/workflows/brain-hosted-repair-check.yml').read_text(encoding='utf-8')
assert "if: ${{ false }}" not in source, "hosted proof remains disabled"
assert "github.ref == 'refs/heads/main'" in source
assert "github.repository == 'niakw/NiakVIO'" in source
assert 'default: allanime' in source
assert 'tests/brain_hosted_representative_selection_test.py' in source
assert "options: [allanime, animekai, uhdmovies, mallumv]" in source
assert "animevostfr" not in source.split("workflow_dispatch:",1)[1].split("permissions:",1)[0]
assert "MANUAL_PROVIDER: ${{ inputs.provider || '' }}" in source
assert "select_brain_hosted_representative.py" in source
assert "brain_hosted_representative_selection_test.py" in source
assert 'FIELD_BRAIN_REPRESENTATIVE' in (root/'scripts/select_brain_hosted_representative.py').read_text(encoding='utf-8')
assert "TARGET_PROVIDER: ${{ inputs.provider || 'allanime' }}" not in source
assert "ref: ${{ steps.brain_pin.outputs.sha }}" in source
assert 'BRAIN_SHA=$sha' in source
assert '727e108132444b6e62a71939f9e742a8193577af' not in source
assert 'Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M' in source
assert '127.0.0.1:8080' in source
assert 'FIELD_BRAIN_LOCAL_SMOKE generated=true' in source
assert 'FIELD_BRAIN_LOCAL_SMOKE generated=false' in source
assert 'qwen25-coder-3b-q4-km-v1' in source
assert 'Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M' not in source
assert 'sha256sum -c -' in source and 'llama-b11140' in source
assert "NIAKVIO_REQUIRE_DECODE_PROOF: '1'" in source
# The preflight that informs the Brain must run the very same manifest/category
# fixtures as the sandbox that accepts or rejects the generated patch.
observe=source.split('name: Observe current provider execution before choosing editable functions',1)[1].split('name: Summarize bounded GraphQL evidence',1)[0]
assert "NIAKVIO_REQUIRE_DECODE_PROOF: '1'" in observe
recheck=source.split('name: Recheck transient missing content once after the browser observation',1)[1].split('name: Run bounded hosted repair and verification loop',1)[0]
assert "NIAKVIO_REQUIRE_DECODE_PROOF: '1'" in recheck
assert "NIAKVIO_FORCE_CPU_TIGHT_PROMPT: '1'" in source
assert "FIELD_BRAIN_GRAPHQL_CAUSAL_PREFLIGHT exact_unit_selection=true" in source
assert "NIAKVIO_FORCE_CPU_LONG_CALL: '1'" in source
assert "NIAKVIO_FORCE_CPU_OUTPUT_BUDGET: '1'" in source
loop_source=(root/'scripts/run_hosted_brain_repair_loop.py').read_text(encoding='utf-8')
assert "'--timeout-seconds', '300'" in loop_source
assert "'--force-provider-budget-seconds', '360'" in loop_source
assert 'test_force_rejected_unit_diversification.py' in source
assert 'test_live_function_context.py' in source
assert 'brain-llm/tests/test_force_cpu_tight_prompt.py' in source
assert 'FIELD_BRAIN_GRAPHQL_OBSERVATION' in source
assert 'python -m unittest discover -s brain-llm/tests' in source
assert 'audit_replay_provenance.py' in source
assert 'test_replay_provenance.py' in source
assert 'replay-program-inventory.json' in source
assert 'run_hosted_brain_repair_loop.py' in source
assert 'hosted-repair-check-${{ github.run_id }}' in source
assert "published" not in source.lower().split('name: require executed, materialized and decoded provider repair evidence',1)[1].split('name: retain bounded experiment evidence',1)[0], "proof step cannot publish provider code"
assert "materializedMutationObserved" in source and "executionObserved" in source
# The strict evaluator already requires new decoded-media improvement and
# no regression. A second ad-hoc all-fixtures-must-pass check would reject its
# validated partial improvement; record remaining debt instead.
assert "and not accepted[0].get('unresolvedFixtures')" not in source
assert "remaining_fixture_debt=" in source

assert "decodedProofRequired" in source and "improvedFixtures" in source
assert "acceptedProviderCount" in source and "publicationAuthority" in source
assert 'if: ${{ always() }}' in source
assert "FIELD_BRAIN_HOSTED_PRECHECK failure=" in source
assert "selected_provider or 'unselected'" in source
assert "'unavailableEvidenceReason': reason" in source
assert "'acceptedProviderCount': 0" in source
assert 'No strictly decoded, materialized Brain repair proved' in source
print("BRAIN_HOSTED_LOCAL_PROOF_WORKFLOW_OK local-inference exact-main strict decode no-provider-writes")
