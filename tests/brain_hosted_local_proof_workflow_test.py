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
assert "ref: ${{ steps.brain_pin.outputs.sha }}" in source
assert 'BRAIN_SHA=$sha' in source
assert '727e108132444b6e62a71939f9e742a8193577af' not in source
assert 'Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M' in source
assert '127.0.0.1:8080' in source
assert 'sha256sum -c -' in source and 'llama-b11140' in source
assert "NIAKVIO_REQUIRE_DECODE_PROOF: '1'" in source
assert "NIAKVIO_FORCE_CPU_TIGHT_PROMPT: '1'" in source
loop_source=(root/'scripts/run_hosted_brain_repair_loop.py').read_text(encoding='utf-8')
assert "'--timeout-seconds', '180'" in loop_source
assert "'--force-provider-budget-seconds', '360'" in loop_source
assert 'run_hosted_brain_repair_loop.py' in source
assert 'hosted-repair-check-${{ github.run_id }}' in source
assert "published" not in source.lower().split('name: require executed, materialized and decoded provider repair evidence',1)[1].split('name: retain bounded experiment evidence',1)[0], "proof step cannot publish provider code"
assert "materializedMutationObserved" in source and "executionObserved" in source
assert "decodedProofRequired" in source and "improvedFixtures" in source
assert "acceptedProviderCount" in source and "publicationAuthority" in source
assert 'if: ${{ always() }}' in source
assert 'No strictly decoded, materialized Brain repair proved' in source
print("BRAIN_HOSTED_LOCAL_PROOF_WORKFLOW_OK local-inference exact-main strict decode no-provider-writes")
