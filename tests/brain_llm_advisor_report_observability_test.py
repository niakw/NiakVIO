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
