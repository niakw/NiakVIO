#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
path = ROOT / "scripts" / "render_provider_census_status_from_state.py"
spec = importlib.util.spec_from_file_location("render_provider_census_status_from_state_test", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

state = {
    "runId": "repair-run",
    "triggerSha": "abcdef1234567890",
    "harnessEvidenceRunId": "waf-run",
    "providers": [
        {
            "provider": "green",
            "status": "FULL OK",
            "color": "🟢",
            "declaredLanes": ["movie"],
            "currentVerifiedLanes": ["movie"],
            "historicalProof": ["movie: Interstellar"],
            "candidateProof": [],
            "routeProof": [],
            "searchProgress": [],
            "evidenceDepth": [],
            "harnessTransportClass": "",
            "latestLaneVerdicts": ["movie=OK"],
            "dominantIssue": "none",
            "action": "protect",
            "testedThisRun": False,
        },
        {
            "provider": "waf",
            "status": "HARNESS MISMATCH",
            "color": "🟧",
            "declaredLanes": ["movie"],
            "currentVerifiedLanes": [],
            "historicalProof": [],
            "candidateProof": [],
            "routeProof": ["2 live routes / movie"],
            "searchProgress": ["movie: 4 works tested"],
            "evidenceDepth": ["movie=lookup_only"],
            "harnessTransportClass": "native-policy-reachable",
            "latestLaneVerdicts": ["movie=no_streams/provider_waf_challenge"],
            "dominantIssue": "provider_waf_challenge",
            "action": "replay with representative native transport",
            "testedThisRun": False,
        },
    ],
    "counts": {"FULL OK": 1, "HARNESS MISMATCH": 1},
    "symptomaticProviders": ["waf"],
    "brainQueue": ["waf"],
    "repairQueue": [],
    "environmentQueue": ["waf"],
    "harnessQueue": ["waf"],
    "lastRepairAttempt": {
        "runId": "force-run",
        "selectedProviders": ["waf"],
        "candidateProviders": [],
        "validatedProviders": [],
        "deferredToLearningSlotProviders": ["waf"],
        "acceptedRepairCount": 0,
        "noProgressReason": "time_budget_exhausted_during_batch",
        "timeBudgetExhausted": True,
        "publicationAllowed": False,
    },
}
text = mod.render(state)
assert "🟢 1 FULL OK" in text, text
assert "FULL tested **0/1**" in text, text
assert "PARTIAL tested **0/0**" in text, text
assert "carried prior playback evidence" in text, text
assert "FULL OK** — all declared lanes have retained verified playback evidence" in text, text
assert "PARTIAL OK** — at least one lane has retained verified playback evidence" in text, text
assert "carried rows were not revalidated on this census SHA" in text, text
assert "current verified playback" not in text, text
assert "🟧 1 HARNESS MISMATCH" in text, text
assert "Repair census run repair-run" in text, text
assert "transport overlay waf-run" in text, text
assert "Latest Repair/FORCE attempt: **run force-run**" in text, text
assert "Learning debt recorded **1**" in text, text
assert "time_budget_exhausted_during_batch" in text, text
assert "automated repair queue: **0**" in text, text
assert "harness/environment queue: **1**" in text, text
assert "| **waf** | 🟧 **HARNESS MISMATCH** | carried |" in text, text
assert "native-policy-reachable" in text, text
assert "transport evidence only" in text, text

# Authority-gated dispatch counts are not network-health counts.
transport_rows = (
    [{"status": "HARNESS MISMATCH", "authorityRepairEligible": False, "testedThisRun": False}] * 8
    + [{"status": "HARNESS/ENV BLOCKED", "authorityRepairEligible": False, "testedThisRun": False}] * 7
    + [{"status": "PROVIDER NETWORK BLOCKED", "authorityRepairEligible": False, "testedThisRun": True}] * 7
    + [{"status": "PROVIDER NETWORK BLOCKED", "authorityRepairEligible": True, "testedThisRun": True}]
    + [{"status": "FULL OK", "authorityRepairEligible": False, "testedThisRun": True}]
)
notice = mod.transport_status_notice(transport_rows)
assert "rows (not dispatch queues): **23**" in notice, notice
assert "census-tested: **8** · carried: **15** · authority-blocked: **22**" in notice, notice
assert "rows (not dispatch queues): **0**" in mod.transport_status_notice([])
assert "census-tested: **0** · carried: **1** · authority-blocked: **0**" in mod.transport_status_notice([{"status": "CLIENT TRANSPORT GAP"}])
assert "Transport-status rows (not dispatch queues): **1**" in text, text

print("provider census authoritative-state markdown contract passed")
