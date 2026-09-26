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
    "NIAKVIO_BRAIN_LLM_GUIDANCE=$GITHUB_WORKSPACE/$final",
    "Prepare Fast-Handoff cached Brain LLM guidance",
    "--negative-memory brain-learning-input/previous.json",
    "--negative-memory automation/brain-repair-memory.json",
    "FAST_MISSING_PROVIDERS: ${{ steps.brain_llm_fast_cache.outputs.missing_providers }}",
    "FIELD_BRAIN_LLM_FAST_CACHE",
    "fallback=cached-or-deterministic",
    "Download and verify official llama.cpp binary when needed",
    "llama-b11140-bin-ubuntu-x64.tar.gz",
    "460c45fa8a9ebc36c9b08e3a15c06dbdbeb312c6308599521c84d9e7f92a268b",
    "sha256sum -c -",
):
    assert required in llm, required

for required in (
    "--llm-batch brain-sandbox/brain-llm/batch.jsonl",
    "g.schemaVersion !== 2",
    "'experiment','experimentFingerprint'",
    "--workers 2",
    "max_tokens=768",
    "max_tokens=512",
    '--max-tokens "$max_tokens"',
    "-c 8192 -np 2",
    'effective_filter="${FAST_MISSING_PROVIDERS:-}"',
    "guidance.cached.json",
    "guidance.generated.json",
    "FIELD_BRAIN_LLM_GUIDANCE_FINAL",
):
    assert required in workflow, required

assert "key: llama-cpp-b11140-ubuntu-x64" not in llm, "executable llama.cpp binary must not be restored from actions/cache"

arch = workflow[workflow.index("- name: Open or refresh Brain architecture PR"):]
assert "git add -A" not in arch, "architecture PR must not stage transient Learning outputs"
assert "git add engine_v2/learning/architecture-proposal.json engine_v2/learning/architecture-proposal.md" in arch
assert "git add engine_v2/config/brain-policy.json" in arch
assert "git add scripts/brain_layers tests engine_v2/scripts engine_v2/config .github/workflows" in arch

print("Brain LLM Learning workflow interpolation contract passed")
