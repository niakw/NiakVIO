#!/usr/bin/env python3
"""Rollback promoted Provider DATA when final-bundle verification fails.

A provider may qualify in the candidate probe but regress after finalization. Such a
provider is deferred to Learn, so its failed final DATA must not remain authority in
the workspace/artifact. Preserve the pre-finalization candidate/evidence state and
restore it atomically before continuing to N+1.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "reconstruct_provider_v3_batch_diagnostic.py"
MARKER = "PROVIDER_V3_DEFER_FINALIZATION_ROLLBACK_V2"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    old_finalize = '''        finalize_provider(
            provider_id,
            provider,
            knowledge,
            overrides,
            evaluation,
            completion_state,
            origin_evidence,
        )
'''
    new_finalize = '''        # PROVIDER_V3_DEFER_FINALIZATION_ROLLBACK_V2
        # Snapshot the candidate/evidence state immediately before promotion.
        # If the rebuilt final bundle regresses, defer to Learn and restore this
        # exact state instead of leaving broken promoted DATA in the artifact.
        pre_finalize_static_row = copy.deepcopy(static_row)
        pre_finalize_patch = copy.deepcopy(patch)
        finalize_provider(
            provider_id,
            provider,
            knowledge,
            overrides,
            evaluation,
            completion_state,
            origin_evidence,
        )
'''
    text = once(text, old_finalize, new_finalize, "pre-finalization-snapshot")

    old_failure = '''            else:
                final_proof["deferToLearn"] = True
                final_proof["deferReason"] = "final-bundle-verification-failed"
                deferred_to_learn.append({
'''
    new_failure = '''            else:
                final_proof["deferToLearn"] = True
                final_proof["deferReason"] = "final-bundle-verification-failed"
                # Candidate proof is useful to Learn, but failed promoted DATA is
                # not publication/reconstruction authority. Restore N before N+1.
                providers[provider_id] = pre_finalize_static_row
                if isinstance(patches, dict):
                    if pre_finalize_patch:
                        patches[provider_id] = pre_finalize_patch
                    else:
                        patches.pop(provider_id, None)
                static_row = providers[provider_id]
                patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
                write(knowledge_path, knowledge)
                write(overrides_path, overrides)
                final_proof["promotedDataRolledBack"] = True
                deferred_to_learn.append({
'''
    text = once(text, old_failure, new_failure, "failed-final-rollback")

    old_deferred = '''                    "reason": "final-bundle-verification-failed",
                    "candidateValidatedTypes": list(evaluation.get("validatedTypes") or []),
'''
    new_deferred = '''                    "reason": "final-bundle-verification-failed",
                    "promotedDataRolledBack": True,
                    "candidateValidatedTypes": list(evaluation.get("validatedTypes") or []),
'''
    text = once(text, old_deferred, new_deferred, "rollback-report-marker")

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str) -> None:
    required = (
        MARKER,
        "pre_finalize_static_row = copy.deepcopy(static_row)",
        "pre_finalize_patch = copy.deepcopy(patch)",
        "providers[provider_id] = pre_finalize_static_row",
        "patches[provider_id] = pre_finalize_patch",
        'patches.pop(provider_id, None)',
        'final_proof["promotedDataRolledBack"] = True',
        '"promotedDataRolledBack": True',
        "write(knowledge_path, knowledge)",
        "write(overrides_path, overrides)",
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"defer finalization rollback missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_DEFER_FINALIZATION_ROLLBACK_V2_OK "
        f"changed={str(changed).lower()} failed_final=rollback_candidate_state continue_next=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
