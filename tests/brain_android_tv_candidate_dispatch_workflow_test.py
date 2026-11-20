#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/brain-android-tv-emulator-feedback.yml").read_text(encoding="utf-8")

for needle in (
    "actions: write",
    "Dispatch one source-pinned Brain candidate experiment",
    "native-candidate-tv-",
    "status=skipped_candidate_source",
    "candidate dispatch is bounded to exactly one provider/fixture",
    "candidate route provenance mismatch",
    "brain-native-candidate-experiments.json",
    "tested-source/automation/brain-native-candidate-experiments.json",
    "candidateOnly",
    "generatedByBrain",
    "providerMutationAuthority",
    "native-corpus-device-targeted.yml",
    '-f source_sha="$NIAKVIO_BRAIN_CANDIDATE_SOURCE_SHA"',
    "-f candidate_rematerialize=true",
    "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29",
    "persisted_experiment=true",
    "persist_brain_native_hls_followup.py",
    "followupCoreExperiment",
    "candidate_type",
    "native-hls-master-receipt-v30",
    "NIAKVIO_PROVIDER_NATIVE_HLS_ROOT_RECEIPT_V30",
    "Dispatch once the distinct Brain V30 Core receipt candidate",
    "FIELD_BRAIN_V30_DISPATCH status=dispatched",
    "publication=false",
):
    assert needle in workflow, needle

route = workflow.index("Route the exact TV replay through Brain as diagnosis only")
dispatch = workflow.index("Dispatch one source-pinned Brain candidate experiment")
upload = workflow.index("Upload bounded Brain TV next-action plan")
persist = workflow.index("Persist non-authoritative Brain TV diagnostic memory on main")
assert route < upload < persist < dispatch
assert workflow.count("Dispatch one source-pinned Brain candidate experiment") == 1
assert "NIAKVIO_BRAIN_CANDIDATE_SOURCE_SHA=$(git rev-parse HEAD)" in workflow
assert 'candidate_source_sha="$(git rev-parse HEAD)"' in workflow
assert "brain_candidate_experiment_json" not in workflow[dispatch:]
assert "_apply_native_brain_origin_priority_candidate" in workflow[persist:dispatch]
v30 = workflow.index("Dispatch once the distinct Brain V30 Core receipt candidate")
assert persist < v30 < dispatch
assert workflow.count("Dispatch once the distinct Brain V30 Core receipt candidate") == 1
assert "steps.verdict.outputs.candidate_type == 'native-blocking-player-origin-priority'" in workflow
assert "brainCandidateHlsRootReceipt" in (ROOT / "scripts/materialize_provider_v3_one.py").read_text()
assert "native-hls-master-receipt-v30" in (ROOT / "scripts/persist_brain_native_candidate_verdict.py").read_text()

# Closing the loop on a failing, exact-byte official TV candidate must not rely
# solely on workflow_run chaining (which can silently stop at GitHub depth).
native = (ROOT / ".github/workflows/native-corpus-device-targeted.yml").read_text(encoding="utf-8")
for needle in (
    "brain-candidate-feedback:",
    "needs: [resolve, native-corpus]",
    "Dispatch exact completed TV candidate verdict without workflow_run chaining",
    "native-candidate-tv-",
    "candidateRematerialize == true",
    "candidate_run_id=",
    "candidate_source_sha=",
    'gh workflow run brain-android-tv-emulator-feedback.yml',
):
    assert needle in native, needle
assert native.index("Upload isolated candidate evidence (never production proof)") < native.index("brain-candidate-feedback:")
privileged = native[native.index("  brain-candidate-feedback:"):native.index("  cross-runtime-gate:")]
assert "      actions: write" in privileged
assert "      contents: read" in privileged
assert "actions/checkout@" not in privileged
assert "        env:" in privileged
assert "  native-corpus:\n" in native
build_section = native[native.index("  native-corpus:\n"):native.index("  brain-candidate-feedback:\n")]
assert "      actions: write" not in build_section

for needle in (
    "workflow_dispatch:",
    "candidate_run_id:",
    "candidate_source_sha:",
    "Verify upstream native execution provenance before loading artifacts",
    'gh api "repos/$GITHUB_REPOSITORY/actions/runs/$NATIVE_RUN_ID"',
    "FIELD_BRAIN_NATIVE_SOURCE_ATTESTED",
    "recover-missed-candidate:",
    "status=no_unlearned_candidate",
    "FIELD_BRAIN_CANDIDATE_RECOVERY",
    "Persist isolated Brain candidate verdict",
    "candidateAttempts",
):
    # candidateAttempts is a schema element of the verifier, not the workflow.
    if needle != "candidateAttempts":
        assert needle in workflow, needle
assert workflow.count("  ingest:\n") == 1
assert workflow.count("  recover-missed-candidate:\n") == 1
assert "FIELD_BRAIN_V30_RECOVERY status=dispatched_negative_feedback" in workflow
assert "candidateFollowUpExperiments // []" in workflow
assert 'and .candidateVerdict == "candidate_zero_stream"' in workflow
assert "and .candidateRestoredObserved == true" in workflow
assert "candidate_run_id=\"$candidate_run_id\"" in workflow
assert "candidate_source_sha=\"$candidate_source_sha\"" in workflow
assert "and .head_branch == \"main\" and .name == \"NATIVE - Device Corpus Tests\"" in workflow
assert workflow.index("FIELD_BRAIN_V30_RECOVERY status=dispatched_negative_feedback") < workflow.index("  ingest:")

assert workflow.index("Verify upstream native execution provenance") < workflow.index("Detect isolated Brain candidate replay")
assert 'github.event_name == \'workflow_dispatch\'' in workflow
assert "github.event.workflow_run.head_sha" in workflow
assert 'status=dispatched run=$candidate_run_id' in workflow
assert '      actions: write' in workflow[workflow.index("  recover-missed-candidate:"):workflow.index("  ingest:")]

# Negative verdicts must be routed on their original official-TV source bytes,
# with only the exact CI-validated Brain gitlink. No provider retry on this path.
for needle in (
    'ref: ${{ env.NATIVE_SOURCE_SHA }}',
    'ref: ${{ steps.brain_pin.outputs.sha }}',
    "automation/brain-pinned-source.json",
    "Resolve source-pinned pre-candidate observation for negative learning",
    "Checkout exact original provider bytes for post-candidate learning",
    "Route executed candidate negative through Brain once without rerunning V29",
    "candidateBrainReroutes",
    "before-candidate/automation/brain-native-candidate-experiments.json",
    "FIELD_BRAIN_CANDIDATE_NEXT",
    "post-candidate route must be one diagnostic-only non-repeat plan",
    "validatedRepair",
    "modelExecuted",
    "publicationAuthority",
    "providerMutationAuthority",
):
    assert needle in workflow, needle
assert workflow.index("Persist isolated Brain candidate verdict") < workflow.index("Route executed candidate negative through Brain")
assert workflow.index("Route executed candidate negative through Brain") < workflow.index("Persist non-authoritative Brain TV diagnostic memory on main")
assert "if: ${{ steps.candidate.outputs.is_candidate != 'true' && hashFiles(" in workflow
assert "modelExecuted" in workflow[workflow.index("Route executed candidate negative through Brain"):workflow.index("Route the exact TV replay through Brain")]
print("Brain Android TV source-pinned candidate dispatch workflow contract passed")
