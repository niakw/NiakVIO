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
    "candidateOnly",
    "generatedByBrain",
    "providerMutationAuthority",
    "native-corpus-device-targeted.yml",
    '-f source_sha="$NATIVE_SOURCE_SHA"',
    "-f candidate_rematerialize=true",
    "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29",
    '-f brain_candidate_experiment_json="$experiment"',
    "publication=false",
):
    assert needle in workflow, needle

route = workflow.index("Route the exact TV replay through Brain as diagnosis only")
dispatch = workflow.index("Dispatch one source-pinned Brain candidate experiment")
upload = workflow.index("Upload bounded Brain TV next-action plan")
persist = workflow.index("Persist non-authoritative Brain TV diagnostic memory on main")
assert route < dispatch < upload < persist
assert workflow.count("Dispatch one source-pinned Brain candidate experiment") == 1
print("Brain Android TV source-pinned candidate dispatch workflow contract passed")
