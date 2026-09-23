#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"scripts/brain_repair_runtime.py").read_text(encoding="utf-8")

start=source.index("sanitized_plans = {")
end=source.index('report["brain"] = {',start)
block=source[start:end]

for field in (
    '"llmAdvisorApplied": row.get("llmAdvisorApplied") is True',
    '"llmAdvisorRescue": row.get("llmAdvisorRescue") is True',
    '"llmAdvisorStrategy": row.get("llmAdvisorStrategy")',
    '"llmAdvisorProfile": row.get("llmAdvisorProfile")',
    '"llmAdvisorConfidence": row.get("llmAdvisorConfidence")',
):
    assert field in block, field

assert '"llmGuidance": planner_llm_guidance()' in source
print("Brain LLM advisor report observability contract passed")

portfolio=(ROOT/"scripts/run_provider_brain_repair.py").read_text(encoding="utf-8")
pstart=portfolio.index("def sanitized_brain(")
pend=portfolio.index("def persist_accepted_programs(",pstart)
pblock=portfolio[pstart:pend]
for field in (
    '"llmAdvisorApplied": row.get("llmAdvisorApplied") is True',
    '"llmAdvisorRescue": row.get("llmAdvisorRescue") is True',
    '"llmAdvisorStrategy": row.get("llmAdvisorStrategy")',
    '"llmAdvisorProfile": row.get("llmAdvisorProfile")',
    '"llmAdvisorConfidence": row.get("llmAdvisorConfidence")',
):
    assert field in pblock, field
