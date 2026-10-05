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
    '"llmAdvisorSourceFailureClass": row.get("llmAdvisorSourceFailureClass")',
    '"llmAdvisorFailureCompatibility": row.get("llmAdvisorFailureCompatibility")',
    '"llmAdvisorExperimentFingerprint": row.get("llmAdvisorExperimentFingerprint")',
    '"llmAdvisorExperiment": copy.deepcopy(',
    '"baseExperimentExhausted": row.get("baseExperimentExhausted") is True',
    '"strategyEscalated": row.get("strategyEscalated") is True',
    '"explorationChainEnabled": row.get("explorationChainEnabled") is True',
    '"explorationModeEnabled": row.get("explorationModeEnabled") is True',
    '"postExhaustionCandidateProfiles": [',
    '"postExhaustionSourceFailureClass": row.get("postExhaustionSourceFailureClass")',
):
    assert field in block, field

assert '"llmGuidance": planner_llm_guidance()' in source
planner=(ROOT/"engine_v2/scripts/plan-repairs.mjs").read_text(encoding="utf-8")
assert "explorationChainEnabled: input.explorationChain === true" in planner
assert "postExhaustionCandidateProfiles" in planner
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
    '"llmAdvisorSourceFailureClass": row.get("llmAdvisorSourceFailureClass")',
    '"llmAdvisorFailureCompatibility": row.get("llmAdvisorFailureCompatibility")',
    '"llmAdvisorExperimentFingerprint": row.get("llmAdvisorExperimentFingerprint")',
    '"llmAdvisorExperiment": copy.deepcopy(',
    '"baseExperimentExhausted": row.get("baseExperimentExhausted") is True',
    '"strategyEscalated": row.get("strategyEscalated") is True',
    '"explorationChainEnabled": row.get("explorationChainEnabled") is True',
    '"explorationModeEnabled": row.get("explorationModeEnabled") is True',
    '"postExhaustionCandidateProfiles": [',
    '"postExhaustionSourceFailureClass": row.get("postExhaustionSourceFailureClass")',
):
    assert field in pblock, field
