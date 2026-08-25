#!/usr/bin/env python3
"""Materialize Core-wide runtime portability and systemic Brain safeguards."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLY_TARGET = ROOT / "scripts/apply_provider_overrides.py"
BRAIN_TARGET = ROOT / "engine_v2/scripts/diagnose-native-reader.mjs"

RUNTIME_CONST = 'GLOBAL_RUNTIME_COMPAT = "scripts/provider_patches/global_runtime_compat_v1.py"'
PRESENTATION_CONST = 'GLOBAL_STREAM_PRESENTATION = "scripts/provider_patches/global_stream_presentation_v1.py"'
RUNTIME_MARKER = '    "NUVIO_GLOBAL_RUNTIME_COMPAT_V1",\n'
PRESENTATION_MARKER = '    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",\n'
RUNTIME_SCOPE = '"scope": "global_runtime_compat"'
RUNTIME_ANCHOR = '''        # Presentation is a Core-wide finalization layer, not a provider capability.
'''
RUNTIME_BLOCK = '''        # Runtime portability is a Core concern. Apply it to every reconstructed
        # provider after provider-specific network/playback recovery but before any
        # stream wrapper. It only normalizes JS host semantics (URL/fetch/timers).
        before = text
        text = _apply_patch_script(text, provider_id, GLOBAL_RUNTIME_COMPAT, {}, None)
        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_RUNTIME_COMPAT,
                "phase": phase,
                "scope": "global_runtime_compat",
            })

'''

BRAIN_IMPORT_ANCHOR = "import { BRAIN_CONTROL_PLANE_VERSION, planRepair } from '../src/repair-brain.mjs';\n"
BRAIN_IMPORT = "import { classifySystemicExtraction, extractionExecutionKey } from '../src/runtime-systemic.mjs';\n"
BRAIN_EXTRACTION_ANCHOR = '''const extractionHealthy = enabledDeclaredResults.filter((row) => row.count > 0);
const ignoredDisabledExtractionFailures = declaredResultRows.filter((row) => !row.enabled && row.count === 0);
'''
BRAIN_EXTRACTION_REPLACEMENT = '''const extractionHealthy = enabledDeclaredResults.filter((row) => row.count > 0);
const ignoredDisabledExtractionFailures = declaredResultRows.filter((row) => !row.enabled && row.count === 0);
const systemicExtraction = classifySystemicExtraction(enabledDeclaredResults);
const systemicExtractionKeys = systemicExtraction.systemicExecutionKeys;
const systemicExtractionFailures = extractionFailures.filter((row) => systemicExtractionKeys.has(extractionExecutionKey(row)));
const providerExtractionFailures = extractionFailures.filter((row) => !systemicExtractionKeys.has(extractionExecutionKey(row)));
'''

BRAIN_PLAN_MAP_OLD = "const extractionPlans = evidence.complete ? extractionFailures.map((row) => {"
BRAIN_PLAN_MAP_NEW = "const extractionPlans = evidence.complete ? providerExtractionFailures.map((row) => {"
BRAIN_PLANS_ANCHOR = '''}) : [];
const plans = [...readerPlans, ...extractionPlans];

const providerLoadIssues ='''
BRAIN_PLANS_REPLACEMENT = '''}) : [];
const systemicExtractionPlans = evidence.complete ? systemicExtractionFailures.map((row) => {
  const signature = `${row.requestType}:runtime_contract_drift:${String(row.client || 'unknown').toLowerCase()}:${row.fixture}`;
  const plan = planRepair({
    invoked: true,
    contractDrift: true,
    signature,
    request: { mediaType: row.requestType },
  }, { signature, maxHypotheses: 3 });
  return {
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: -1,
    state: 'empty', failureClass: 'runtime_contract_drift', failureDomain: 'client_runtime',
    providerMutationEligible: false, coreOrManifestProposalAllowed: true,
    failureStage: 'provider_runtime_compat', returnedCount: 0, signature,
    action: plan.action, exitReason: plan.exitReason,
    hypotheses: plan.hypotheses.map((hypothesis) => ({
      id: hypothesis.id,
      capabilities: [...(hypothesis.capabilities || [])],
      actions: [...(hypothesis.actions || [])],
    })),
  };
}) : [];
const plans = [...readerPlans, ...extractionPlans];

const providerLoadIssues ='''

BRAIN_OBS_MAP_OLD = "const extractionObservations = extractionFailures.map((row) => ({"
BRAIN_OBS_MAP_NEW = "const extractionObservations = providerExtractionFailures.map((row) => ({"
BRAIN_OBS_ANCHOR = '''const extractionHealthyObservations = extractionHealthy.map((row) => ({
'''
BRAIN_SYSTEMIC_OBS = '''const systemicExtractionObservations = systemicExtractionFailures.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, index: -1,
  state: 'empty', failureClass: 'runtime_contract_drift', failureDomain: 'client_runtime',
  providerMutationEligible: false, failureStage: 'provider_runtime_compat',
  httpStatus: 0, errorCode: '', host: '', durationSeconds: null, loadBytes: 0, loadDurationMs: 0,
  returnedCount: 0, observationLayer: 'runtime',
}));
'''
BRAIN_OBSERVATIONS_OLD = "const observations = [...playerObservations, ...extractionObservations, ...runtimeSentinelObservations];"
BRAIN_OBSERVATIONS_NEW = "const observations = [...playerObservations, ...extractionObservations, ...systemicExtractionObservations, ...runtimeSentinelObservations];"

BRAIN_OUTCOME_OLD = '''  if (row.count > 0) current.extractionHealthy += 1;
  else {
    current.extractionFailures += 1;
    current.failures += 1;
    current.providerEligibleFailures += 1;
    current.failureClasses.media_extraction_gap = Number(current.failureClasses.media_extraction_gap || 0) + 1;
  }
'''
BRAIN_OUTCOME_NEW = '''  if (row.count > 0) current.extractionHealthy += 1;
  else {
    current.extractionFailures += 1;
    current.failures += 1;
    if (systemicExtractionKeys.has(extractionExecutionKey(row))) {
      current.clientRuntimeFailures += 1;
      current.failureClasses.runtime_contract_drift = Number(current.failureClasses.runtime_contract_drift || 0) + 1;
    } else {
      current.providerEligibleFailures += 1;
      current.failureClasses.media_extraction_gap = Number(current.failureClasses.media_extraction_gap || 0) + 1;
    }
  }
'''

BRAIN_PAYLOAD_ANCHOR = '''  extractionFailures: extractionFailures.length,
  ignoredDisabledExtractionFailures: ignoredDisabledExtractionFailures.length,
'''
BRAIN_PAYLOAD_REPLACEMENT = '''  extractionFailures: extractionFailures.length,
  providerExtractionFailures: providerExtractionFailures.length,
  clientRuntimeExtractionFailures: systemicExtractionFailures.length,
  systemicExtractionGroups: systemicExtraction.systemicGroups.length,
  ignoredDisabledExtractionFailures: ignoredDisabledExtractionFailures.length,
'''
BRAIN_PAYLOAD_OBS_ANCHOR = '''  extractionHealthyObservations,
  providerLoadObservations,
'''
BRAIN_PAYLOAD_OBS_REPLACEMENT = '''  extractionHealthyObservations,
  systemicExtractionGroups: systemicExtraction.systemicGroups,
  clientRuntimeExtractionPlans: systemicExtractionPlans,
  providerLoadObservations,
'''
BRAIN_POLICY_ANCHOR = '''    clientRuntimeFailureLearningAllowed: false,
    runtimeErrorSentinelLearningAllowed: false,
'''
BRAIN_POLICY_REPLACEMENT = '''    clientRuntimeFailureLearningAllowed: false,
    clientRuntimeExtractionLearningAllowed: false,
    coreRuntimeCompatibilityProposalAllowed: evidence.complete && systemicExtractionFailures.length > 0,
    runtimeErrorSentinelLearningAllowed: false,
'''
BRAIN_CONSOLE_OLD = '''  `provider_eligible_failures=${payload.providerEligibleReaderFailures} extraction_failures=${payload.extractionFailures} ` +
  `client_runtime_failures=${payload.clientRuntimeReaderFailures} runtime_sentinels=${payload.runtimeErrorSentinelObserved} ` +
'''
BRAIN_CONSOLE_NEW = '''  `provider_eligible_failures=${payload.providerEligibleReaderFailures} extraction_failures=${payload.extractionFailures} ` +
  `provider_extraction_failures=${payload.providerExtractionFailures} systemic_extraction_failures=${payload.clientRuntimeExtractionFailures} ` +
  `client_runtime_failures=${payload.clientRuntimeReaderFailures} runtime_sentinels=${payload.runtimeErrorSentinelObserved} ` +
'''


def replace_once(text: str, old: str, new: str, label: str, changed: list[str]) -> str:
    if new in text:
        return text
    if old not in text:
        raise ValueError(f"{label} anchor missing")
    changed.append(label)
    return text.replace(old, new, 1)


def normalize_apply(text: str) -> tuple[str, list[str]]:
    changed: list[str] = []
    if RUNTIME_CONST not in text:
        if PRESENTATION_CONST not in text:
            raise ValueError("runtime constant anchor missing")
        text = text.replace(PRESENTATION_CONST, PRESENTATION_CONST + "\n" + RUNTIME_CONST, 1)
        changed.append("runtime_compat_constant")
    if RUNTIME_MARKER not in text:
        if PRESENTATION_MARKER not in text:
            raise ValueError("runtime tail marker anchor missing")
        text = text.replace(PRESENTATION_MARKER, RUNTIME_MARKER + PRESENTATION_MARKER, 1)
        changed.append("runtime_compat_tail_marker")
    if RUNTIME_SCOPE not in text:
        if RUNTIME_ANCHOR not in text:
            raise ValueError("runtime application anchor missing")
        text = text.replace(RUNTIME_ANCHOR, RUNTIME_BLOCK + RUNTIME_ANCHOR, 1)
        changed.append("pre_presentation_runtime_compat")
    return text, changed


def assert_apply_contract(text: str) -> None:
    if text.count(RUNTIME_CONST) != 1 or text.count(RUNTIME_SCOPE) != 1 or text.count(RUNTIME_MARKER) != 1:
        raise ValueError("global runtime compatibility Core layer must exist exactly once")
    runtime = text.find(RUNTIME_SCOPE)
    presentation = text.find('"scope": "global_stream_presentation"')
    branding = text.find('"scope": "global_provider_branding"')
    if runtime < 0 or presentation < 0 or branding < 0 or not (runtime < presentation < branding):
        raise ValueError("Core tail order must be runtime compatibility -> presentation -> branding")


def normalize_brain(text: str) -> tuple[str, list[str]]:
    changed: list[str] = []
    if BRAIN_IMPORT not in text:
        text = replace_once(text, BRAIN_IMPORT_ANCHOR, BRAIN_IMPORT_ANCHOR + BRAIN_IMPORT, "brain_systemic_import", changed)
    if "const systemicExtraction = classifySystemicExtraction(enabledDeclaredResults);" not in text:
        text = replace_once(text, BRAIN_EXTRACTION_ANCHOR, BRAIN_EXTRACTION_REPLACEMENT, "brain_systemic_partition", changed)
    text = replace_once(text, BRAIN_PLAN_MAP_OLD, BRAIN_PLAN_MAP_NEW, "brain_provider_plan_partition", changed)
    if "const systemicExtractionPlans = evidence.complete" not in text:
        text = replace_once(text, BRAIN_PLANS_ANCHOR, BRAIN_PLANS_REPLACEMENT, "brain_runtime_plans", changed)
    text = replace_once(text, BRAIN_OBS_MAP_OLD, BRAIN_OBS_MAP_NEW, "brain_provider_observation_partition", changed)
    if "const systemicExtractionObservations = systemicExtractionFailures.map" not in text:
        text = replace_once(text, BRAIN_OBS_ANCHOR, BRAIN_SYSTEMIC_OBS + BRAIN_OBS_ANCHOR, "brain_runtime_observations", changed)
    text = replace_once(text, BRAIN_OBSERVATIONS_OLD, BRAIN_OBSERVATIONS_NEW, "brain_observation_union", changed)
    text = replace_once(text, BRAIN_OUTCOME_OLD, BRAIN_OUTCOME_NEW, "brain_outcome_attribution", changed)
    text = replace_once(text, BRAIN_PAYLOAD_ANCHOR, BRAIN_PAYLOAD_REPLACEMENT, "brain_payload_counts", changed)
    text = replace_once(text, BRAIN_PAYLOAD_OBS_ANCHOR, BRAIN_PAYLOAD_OBS_REPLACEMENT, "brain_payload_runtime_plans", changed)
    text = replace_once(text, BRAIN_POLICY_ANCHOR, BRAIN_POLICY_REPLACEMENT, "brain_runtime_policy", changed)
    text = replace_once(text, BRAIN_CONSOLE_OLD, BRAIN_CONSOLE_NEW, "brain_console_counts", changed)
    return text, changed


def assert_brain_contract(text: str) -> None:
    required = (
        BRAIN_IMPORT.strip(),
        "classifySystemicExtraction(enabledDeclaredResults)",
        "providerExtractionFailures = extractionFailures.filter",
        "systemicExtractionFailures = extractionFailures.filter",
        "failureDomain: 'client_runtime'",
        "providerMutationEligible: false, coreOrManifestProposalAllowed: true",
        "clientRuntimeExtractionLearningAllowed: false",
        "coreRuntimeCompatibilityProposalAllowed:",
    )
    missing = [value for value in required if value not in text]
    if missing:
        raise ValueError("Brain systemic runtime contract missing: " + ", ".join(missing))
    if "const extractionPlans = evidence.complete ? extractionFailures.map" in text:
        raise ValueError("Brain still treats every zero-stream result as provider-mutable")


def normalize_files(*, apply: bool) -> list[str]:
    changes: list[str] = []
    apply_source = APPLY_TARGET.read_text(encoding="utf-8")
    apply_normalized, apply_changes = normalize_apply(apply_source)
    assert_apply_contract(apply_normalized)
    changes.extend(f"apply:{item}" for item in apply_changes)
    if apply and apply_normalized != apply_source:
        APPLY_TARGET.write_text(apply_normalized, encoding="utf-8")

    brain_source = BRAIN_TARGET.read_text(encoding="utf-8")
    brain_normalized, brain_changes = normalize_brain(brain_source)
    assert_brain_contract(brain_normalized)
    changes.extend(f"brain:{item}" for item in brain_changes)
    if apply and brain_normalized != brain_source:
        BRAIN_TARGET.write_text(brain_normalized, encoding="utf-8")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        raise SystemExit("choose exactly one of --apply or --check")
    changes = normalize_files(apply=args.apply)
    if args.check and changes:
        raise SystemExit("Core runtime compatibility normalization required: " + ", ".join(changes))
    print(f"FIELD_CORE_RUNTIME_COMPAT changed={len(changes)} runtime=global brain_systemic_guard=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
