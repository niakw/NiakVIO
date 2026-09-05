#!/usr/bin/env python3
"""Preserve live-validated Provider DATA when the final rebuilt bundle regresses.

A Provider can improve its route/DATA model and still fail the final reconstructed
bundle probe for a separate runtime/materialization reason. In that case:
- keep the improved live-validated execution DATA;
- never keep failed-live routes as executable routeData;
- demote provider qualification/publication authority;
- preserve the failure as Learn evidence and continue to N+1.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "scripts" / "reconstruct_provider_v3_batch_diagnostic.py"
VALIDATOR = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_PRESERVE_VALIDATED_DATA_ON_FINAL_FAILURE_V3"
VALIDATOR_MARKER_V1 = "PROVIDER_V3_FAILED_LIVE_NOT_EXECUTION_DATA_V1"
VALIDATOR_MARKER = "PROVIDER_V3_FAILED_LIVE_NOT_EXECUTION_DATA_V2"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_validator() -> bool:
    text = VALIDATOR.read_text(encoding="utf-8")
    if VALIDATOR_MARKER in text:
        validate_validator(text)
        return False

    changed = False
    if VALIDATOR_MARKER_V1 in text:
        text = text.replace(VALIDATOR_MARKER_V1, VALIDATOR_MARKER, 1)
        changed = True
    else:
        old = '''        execution_plan_rows = [
            row for row in stable_candidate_rows
            if row.get("attemptEvidence")
            or row.get("validationState") == "live-validated"
        ]
'''
        new = '''        # PROVIDER_V3_FAILED_LIVE_NOT_EXECUTION_DATA_V2
        # A route that was actually traversed and failed is useful negative
        # evidence, but it is not executable Provider source DATA. Keep blocked
        # routes (auth/rate/policy can be environmental), keep live-validated
        # routes, and keep failed-live rows only in candidate/diagnostic evidence.
        execution_plan_rows = [
            row for row in stable_candidate_rows
            if row.get("validationState") != "failed-live"
            and (
                row.get("attemptEvidence")
                or row.get("validationState") == "live-validated"
            )
        ]
'''
        text = once(text, old, new, "execution-plan-failed-live-filter")
        changed = True

    # Keep the machine-readable recognition contract aligned with the actual
    # execution DATA. A generic attempted non-2xx is no longer retained after a
    # qualified live traversal when it is classified failed-live; only terminal
    # blocked/unreachable plans survive because those failures may be environmental.
    if '"executionPlanRetainsFailedLive"' not in text:
        old_meta = '        "executionPlanRetainsAttemptedNon2xx": True,\n'
        new_meta = '''        "executionPlanRetainsAttemptedNon2xx": completion_state in {"terminal-blocked", "terminal-unreachable"},
        "executionPlanRetainsFailedLive": False,
        "blockedNon2xxPlanPreserved": completion_state in {"terminal-blocked", "terminal-unreachable"},
'''
        text = once(text, old_meta, new_meta, "failed-live-recognition-metadata")
        changed = True

    VALIDATOR.write_text(text, encoding="utf-8")
    validate_validator(text)
    return changed


def patch_batch() -> bool:
    text = BATCH.read_text(encoding="utf-8")
    if MARKER in text:
        validate_batch(text)
        return False

    helper_anchor = '''def main() -> int:
'''
    helper = '''# PROVIDER_V3_PRESERVE_VALIDATED_DATA_ON_FINAL_FAILURE_V3
def _demote_unverified_finalization(
    static_row: dict[str, Any],
    patch: dict[str, Any],
    evaluation: dict[str, Any],
) -> None:
    """Keep improved route/DATA, but remove provider-success authority."""
    state = "validated-data-retained-final-bundle-unverified"
    model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
    knowledge_row = static_row.get("knowledge") if isinstance(static_row.get("knowledge"), dict) else {}

    recognition = model.get("routeRecognition") if isinstance(model.get("routeRecognition"), dict) else {}
    recognition["status"] = state
    recognition["completionState"] = state
    recognition["finalBundleVerified"] = False
    recognition["learnRequired"] = True
    recognition["providerQualified"] = False
    recognition["publicationAuthority"] = False
    recognition["validatedRouteDataRetained"] = True
    recognition["validatedTypesBeforeFinalFailure"] = list(evaluation.get("validatedTypes") or [])
    model["routeRecognition"] = recognition

    repair = model.get("repairObservation") if isinstance(model.get("repairObservation"), dict) else {}
    repair["finalBundleVerified"] = False
    repair["learnRequired"] = True
    repair["validatedRouteDataRetained"] = True
    repair["finalFailureState"] = state
    model["repairObservation"] = repair

    recognized = knowledge_row.get("recognizedContract") if isinstance(knowledge_row.get("recognizedContract"), dict) else {}
    recognized["completionState"] = state
    recognized["finalBundleVerified"] = False
    recognized["learnRequired"] = True
    recognized["providerQualified"] = False
    recognized["publicationAuthority"] = False
    recognized["validatedRouteDataRetained"] = True
    knowledge_row["recognizedContract"] = recognized

    live_gate = patch.get("live_route_gate") if isinstance(patch.get("live_route_gate"), dict) else {}
    live_gate["completion_state"] = state
    live_gate["final_bundle_verified"] = False
    live_gate["learn_required"] = True
    live_gate["provider_qualified"] = False
    live_gate["publication_authority"] = False
    live_gate["validated_route_data_retained"] = True
    patch["live_route_gate"] = live_gate

    static_row["model"] = model
    static_row["knowledge"] = knowledge_row


def main() -> int:
'''
    text = once(text, helper_anchor, helper, "batch-demotion-helper")

    old_failure = '''            else:
                final_proof["deferToLearn"] = True
                final_proof["deferReason"] = "final-bundle-verification-failed"
                deferred_to_learn.append({
'''
    new_failure = '''            else:
                final_proof["deferToLearn"] = True
                final_proof["deferReason"] = "final-bundle-verification-failed"
                # The DATA repair itself may be correct even when the rebuilt JS
                # still regresses. Keep the improved validated routeData, demote
                # provider qualification/publication authority, and send the
                # remaining runtime/materialization problem to Learn.
                _demote_unverified_finalization(static_row, patch, evaluation)
                write(knowledge_path, knowledge)
                write(overrides_path, overrides)
                final_proof["validatedDataRetained"] = True
                final_proof["providerAuthorityDemoted"] = True
                deferred_to_learn.append({
'''
    text = once(text, old_failure, new_failure, "final-failure-preserve-data")

    old_report = '''                    "reason": "final-bundle-verification-failed",
                    "candidateValidatedTypes": list(evaluation.get("validatedTypes") or []),
'''
    new_report = '''                    "reason": "final-bundle-verification-failed",
                    "validatedDataRetained": True,
                    "providerAuthorityDemoted": True,
                    "candidateValidatedTypes": list(evaluation.get("validatedTypes") or []),
'''
    text = once(text, old_report, new_report, "final-failure-report")

    BATCH.write_text(text, encoding="utf-8")
    validate_batch(text)
    return True


def validate_validator(text: str) -> None:
    for needle in (
        VALIDATOR_MARKER,
        'row.get("validationState") != "failed-live"',
        'row.get("validationState") == "live-validated"',
        '"executionPlanRetainsFailedLive": False',
        '"blockedNon2xxPlanPreserved": completion_state in {"terminal-blocked", "terminal-unreachable"}',
    ):
        if needle not in text:
            raise AssertionError(f"validator preserve-DATA contract missing: {needle}")


def validate_batch(text: str) -> None:
    for needle in (
        MARKER,
        "def _demote_unverified_finalization(",
        'state = "validated-data-retained-final-bundle-unverified"',
        'recognition["publicationAuthority"] = False',
        'recognized["publicationAuthority"] = False',
        'live_gate["publication_authority"] = False',
        'final_proof["validatedDataRetained"] = True',
        'final_proof["providerAuthorityDemoted"] = True',
        '"validatedDataRetained": True',
        '"providerAuthorityDemoted": True',
    ):
        if needle not in text:
            raise AssertionError(f"batch preserve-DATA contract missing: {needle}")
    for forbidden in (
        "providers[provider_id] = pre_finalize_static_row",
        'final_proof["promotedDataRolledBack"] = True',
    ):
        if forbidden in text:
            raise AssertionError(f"validated DATA rollback survived: {forbidden}")


def main() -> int:
    validator_changed = patch_validator()
    batch_changed = patch_batch()
    print(
        "PROVIDER_V3_PRESERVE_VALIDATED_DATA_ON_FINAL_FAILURE_V3_OK "
        f"validator_changed={str(validator_changed).lower()} "
        f"batch_changed={str(batch_changed).lower()} "
        "failed_live_execution_data=false failed_live_metadata=false "
        "blocked_non2xx_plan=terminal-only validated_data_retained=true "
        "provider_authority_demoted=true learn=true continue_next=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
