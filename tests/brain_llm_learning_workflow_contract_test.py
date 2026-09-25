#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

start = workflow.index("- name: Checkout private NiakVIO chat memory read-only")
end = workflow.index("- name: Run adaptive Learning provider queue", start)
llm = workflow[start:end]

assert "\\${" not in llm, "Brain LLM workflow contains escaped GitHub/shell interpolation"
for required in (
    "token: ${{ secrets.NIAKVIO_PRIVATE_READ_TOKEN }}",
    "PROVIDER_FILTER: ${{ steps.learning-slot.outputs.provider_filter }}",
    "LLM_NEEDED: ${{ steps.brain_llm_route.outputs.llm_needed }}",
    "LLM_AVAILABLE: ${{ steps.brain_llm_server.outputs.available }}",
    'if [ -n "${PROVIDER_FILTER:-}" ]; then',
    'if [ "${LLM_NEEDED:-false}" != "true" ] || [ "${LLM_AVAILABLE:-false}" = "true" ]; then',
    '"${args[@]}"',
    "NIAKVIO_BRAIN_LLM_GUIDANCE=$GITHUB_WORKSPACE/brain-sandbox/brain-llm/guidance.json",
    "Prepare Fast-Handoff cached Brain LLM guidance",
    "--negative-memory brain-learning-input/previous.json",
    "FAST_MISSING_PROVIDERS: ${{ steps.brain_llm_fast_cache.outputs.missing_providers }}",
    "FIELD_BRAIN_LLM_FAST_CACHE",
    "fallback=cached-or-deterministic",
    "llama-cpp-b11140-ubuntu-x64",
    "llama-b11140-bin-ubuntu-x64.tar.gz",
):
    assert required in llm, required

for required in (
    "--llm-batch brain-sandbox/brain-llm/batch.jsonl",
    "g.schemaVersion !== 2",
    "'experiment','experimentFingerprint'",
    "--workers 2",
    "--max-tokens 768",
    "-c 8192 -np 2",
    'effective_filter="${FAST_MISSING_PROVIDERS:-}"',
    "guidance.cached.json",
    "guidance.generated.json",
    "FIELD_BRAIN_LLM_GUIDANCE_FINAL",
):
    assert required in workflow, required

print("Brain LLM Learning workflow interpolation contract passed")
