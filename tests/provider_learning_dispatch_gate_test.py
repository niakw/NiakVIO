#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_learning_dispatch_gate.py"
spec = importlib.util.spec_from_file_location("dispatch_gate", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def brain(signature="sig-a", profile="chain_terminal_extractor_v1", harness=None):
    return {
        "deferredLearningProviders": ["demo", "harness"],
        "harnessDifferentialProviders": list(harness or []),
        "waves": [{
            "batches": [{
                "brain": {
                    "plans": {
                        "demo-key": {
                            "providerId": "demo",
                            "failureClass": "chain_terminal_gap",
                            "signature": signature,
                            "repairScope": "provider",
                            "repairType": "targeted_runtime",
                            "learningDisposition": "invent-new-strategy",
                            "allowedProfiles": [profile],
                            "experimentVariant": 4,
                            "experimentGeneration": 2,
                            "llmAdvisorStrategy": "",
                            "llmAdvisorProfile": "",
                            "llmAdvisorExperimentFingerprint": "",
                        },
                        "harness-key": {
                            "providerId": "harness",
                            "failureClass": "route_proven_gap",
                            "signature": "harness-sig",
                            "repairScope": "harness-compatibility",
                            "repairType": "harness_differential",
                            "learningDisposition": "harness-fix-required-before-provider-learning",
                            "allowedProfiles": [],
                        },
                    }
                }
            }]
        }],
    }


first = module.select(brain(harness=["harness"]), {"providers": {}}, ["demo", "harness"])
assert first["eligibleProviders"] == ["demo"], first
assert first["harnessDifferentialExcludedProviders"] == ["harness"], first
fp = first["eligible"][0]["fingerprint"]
assert len(fp) == 64

ledger = module.mark_dispatched(
    {"schemaVersion": 1, "providers": {}},
    first,
    repair_run_id="repair-1",
    learning_run_id="learn-1",
)
assert ledger["providers"]["demo"]["lastDispatchedFingerprint"] == fp
assert ledger["providers"]["demo"]["dispatchCount"] == 1

repeat = module.select(brain(harness=["harness"]), ledger, ["demo", "harness"])
assert repeat["eligibleProviders"] == [], repeat
assert repeat["suppressedRepeatProviders"] == ["demo"], repeat

changed = module.select(brain(signature="sig-b", harness=["harness"]), ledger, ["demo"])
assert changed["eligibleProviders"] == ["demo"], changed
assert changed["eligible"][0]["fingerprint"] != fp

# Retry bookkeeping alone cannot re-authorize a previously dispatched method.
# A new generation/variant is not a new causal strategy.
ordinal_only = brain(harness=["harness"])
ordinal_plan = ordinal_only["waves"][0]["batches"][0]["brain"]["plans"]["demo-key"]
ordinal_plan["experimentVariant"] = 200
ordinal_plan["experimentGeneration"] = 300
assert module.plan_fingerprint("demo", ordinal_plan) == fp
ordinal_repeat = module.select(ordinal_only, ledger, ["demo"])
assert ordinal_repeat["eligibleProviders"] == [], ordinal_repeat
assert ordinal_repeat["suppressedRepeatProviders"] == ["demo"], ordinal_repeat

# Removing the counters also preserves causal identity for older plan schemas.
ordinal_plan.pop("experimentVariant")
ordinal_plan.pop("experimentGeneration")
assert module.plan_fingerprint("demo", ordinal_plan) == fp

changed_method = module.select(
    brain(profile="player_media_extractor_v1", harness=["harness"]),
    ledger,
    ["demo"],
)
assert changed_method["eligibleProviders"] == ["demo"], changed_method
assert changed_method["eligible"][0]["fingerprint"] != fp

# History, not only the last value, owns anti-replay. A -> B -> A must not
# auto-dispatch A again.
ledger_b = module.mark_dispatched(
    ledger,
    changed_method,
    repair_run_id="repair-2",
    learning_run_id="learn-2",
)
assert len(ledger_b["providers"]["demo"]["dispatchedFingerprints"]) == 2
replayed_a = module.select(brain(harness=["harness"]), ledger_b, ["demo"])
assert replayed_a["eligibleProviders"] == [], replayed_a
assert replayed_a["suppressedRepeatProviders"] == ["demo"], replayed_a

# Legacy last-only ledgers remain safe after schema migration.
legacy = {
    "providers": {
        "demo": {
            "lastDispatchedFingerprint": fp,
            "dispatchCount": 1,
        }
    }
}
legacy_repeat = module.select(brain(harness=["harness"]), legacy, ["demo"])
assert legacy_repeat["eligibleProviders"] == [], legacy_repeat

execution_plan = {
    "executions": [
        {
            "lane": "BRAIN_LEARNING",
            "owner": "BRAIN_LEARNING",
            "repairScope": "learning",
            "capabilityStrategy": "unknown",
            "transportSignature": "not-applicable",
            "dispatchAllowed": True,
            "providers": ["learn-only"],
        },
        {
            "lane": "CORE_CLIENT_LEARNING",
            "owner": "CORE_CLIENT_TRANSPORT",
            "repairScope": "harness-compatibility",
            "capabilityStrategy": "html_scraper",
            "transportSignature": "browser-profile-only-both-networks",
            "strategyBlueprint": "native_tls_browser_differential_v1",
            "dispatchAllowed": True,
            "providers": ["harness-only"],
        },
    ]
}
plan_first = module.select_execution_plan(
    execution_plan,
    {"providers": {}},
    lane="BRAIN_LEARNING",
    requested=["learn-only"],
)
assert plan_first["eligibleProviders"] == ["learn-only"], plan_first

# An omitted filter means the whole lane, but an explicitly supplied empty
# (e.g. invalid-only) filter must fail closed rather than selecting everyone.
unfiltered = module.select_execution_plan(
    execution_plan, {"providers": {}}, lane="BRAIN_LEARNING",
)
assert unfiltered["eligibleProviders"] == ["learn-only"], unfiltered
invalid_only = module.select_execution_plan(
    execution_plan, {"providers": {}}, lane="BRAIN_LEARNING", requested=[],
)
assert invalid_only["eligibleProviders"] == [], invalid_only
assert module._requested("bad/path", brain()) == []
assert module._requested("", brain()) == ["demo", "harness"]

# Exercise the CLI, where a user-supplied invalid value is sanitized to [].
with tempfile.TemporaryDirectory() as tmp:
    directory = Path(tmp)
    plan_file = directory / "plan.json"
    brain_file = directory / "brain.json"
    ledger_file = directory / "ledger.json"
    output_file = directory / "selection.json"
    plan_file.write_text(json.dumps(execution_plan), encoding="utf-8")
    brain_file.write_text(json.dumps(brain()), encoding="utf-8")
    ledger_file.write_text('{"providers":{}}', encoding="utf-8")
    for command, source_flag, source in (
        ("select", "--brain", brain_file),
        ("select-plan", "--plan", plan_file),
    ):
        args = [
            sys.executable, str(SCRIPT), command,
            source_flag, str(source),
            "--ledger", str(ledger_file),
            "--providers", "bad/path",
            "--output", str(output_file),
        ]
        if command == "select-plan":
            args.extend(["--lane", "BRAIN_LEARNING"])
        subprocess.run(args, check=True, capture_output=True, text=True)
        result = json.loads(output_file.read_text(encoding="utf-8"))
        assert result["eligibleProviders"] == [], (command, result)

plan_ledger = module.mark_dispatched({"providers": {}}, plan_first, repair_run_id="auto-1")
plan_repeat = module.select_execution_plan(
    execution_plan,
    plan_ledger,
    lane="BRAIN_LEARNING",
    requested=["learn-only"],
)
assert plan_repeat["eligibleProviders"] == [], plan_repeat
assert plan_repeat["suppressedRepeatProviders"] == ["learn-only"], plan_repeat

harness_plan = module.select_execution_plan(
    execution_plan,
    {"providers": {}},
    lane="CORE_CLIENT_LEARNING",
    requested=["harness-only"],
)
assert harness_plan["eligibleProviders"] == ["harness-only"], harness_plan

missing = {
    "deferredLearningProviders": ["unknown"],
    "waves": [{"batches": [{"brain": {"plans": {
        "x": {
            "providerId": "unknown",
            "failureClass": "unknown_failure",
            "signature": "unknown-sig",
            "allowedProfiles": [],
        }
    }}}]}],
}
closed = module.select(missing, {"providers": {}}, ["unknown"])
assert closed["eligibleProviders"] == [], closed
assert closed["suppressedMissingFingerprintProviders"] == ["unknown"], closed

print("Provider Learning causal dispatch gate tests passed")
