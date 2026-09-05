#!/usr/bin/env python3
"""Defer bounded provider-specific failures to Learn instead of stopping a repair slice."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "reconstruct_provider_v3_batch_diagnostic.py"
MARKER = "PROVIDER_V3_DEFER_TO_LEARN_V1"


def sub1(text: str, pattern: str, replacement: str, label: str) -> str:
    new, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return new


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    text = text.replace(
        '    refused_provider: str | None = None\n',
        '    # PROVIDER_V3_DEFER_TO_LEARN_V1\n'
        '    # Provider-scoped repair exhaustion is evidence for Learn, not a slice blocker.\n'
        '    deferred_to_learn: list[dict[str, Any]] = []\n',
        1,
    )

    text = sub1(
        text,
        r'''        if not isinstance\(static_row, dict\):\n.*?            break\n\n        model =''',
        '''        if not isinstance(static_row, dict):
            deferred_to_learn.append({"index": absolute_index, "providerId": provider_id, "reason": "missing-static-knowledge"})
            rows.append({
                "index": absolute_index, "providerId": provider_id,
                "result": "defer-to-learn", "completionState": "defer-to-learn",
                "learnRequired": True, "deferReason": "missing-static-knowledge",
                "advancedAfterDefer": True, "refusedToAdvance": False,
                "finalBundleVerified": False,
            })
            print(f"FIELD_PROVIDER_BATCH_PROVIDER_DEFER index={absolute_index} provider={provider_id} reason=missing-static-knowledge advancing_next=true learn=true", flush=True)
            continue

        model =''',
        "missing-static-defer",
    )

    text = sub1(
        text,
        r'''        if not candidate_filename:\n.*?            break\n        for task in provider\["tasks"\]:''',
        '''        if not candidate_filename:
            deferred_to_learn.append({"index": absolute_index, "providerId": provider_id, "reason": "candidate-materialization-failed"})
            rows.append({
                "index": absolute_index, "providerId": provider_id,
                "result": "defer-to-learn", "completionState": "defer-to-learn",
                "learnRequired": True, "deferReason": "candidate-materialization-failed",
                "advancedAfterDefer": True, "refusedToAdvance": False,
                "finalBundleVerified": False,
            })
            print(f"FIELD_PROVIDER_BATCH_PROVIDER_DEFER index={absolute_index} provider={provider_id} reason=candidate-materialization-failed advancing_next=true learn=true", flush=True)
            continue
        for task in provider["tasks"]:''',
        "candidate-materialization-defer",
    )

    text = sub1(
        text,
        r'''        if completion_state is None:\n            hard_failures\.append\(provider_id\).*?            break\n\n        finalize_provider\(''',
        '''        if completion_state is None:
            deferred_to_learn.append({
                "index": absolute_index,
                "providerId": provider_id,
                "reason": "repair-exhausted",
                "missingTypes": list(evaluation.get("missingTypes") or []),
                "validatedTypes": list(evaluation.get("validatedTypes") or []),
                "providerRequestCount": int(evaluation.get("providerRequestCount") or 0),
                "liveValidatedRouteCount": int(evaluation.get("liveValidatedRouteCount") or 0),
                "repairHistory": repair_history,
            })
            rows.append({
                **evaluation,
                "index": absolute_index,
                "providerId": provider_id,
                "result": "defer-to-learn",
                "completionState": "defer-to-learn",
                "originEvidence": origin_evidence,
                "candidateBundleFile": candidate_filename,
                "candidateBundleSha256": candidate.get("sha256"),
                "repairHistory": repair_history,
                "learnRequired": True,
                "deferReason": "repair-exhausted",
                "advancedAfterDefer": True,
                "refusedToAdvance": False,
                "finalBundleVerified": False,
            })
            print(
                "FIELD_PROVIDER_BATCH_PROVIDER_DEFER "
                f"index={absolute_index} provider={provider_id} repair_exhausted=true "
                f"missing={','.join(evaluation.get('missingTypes') or []) or 'unknown'} "
                f"validated={','.join(evaluation.get('validatedTypes') or []) or 'none'} "
                f"advancing_next={str(absolute_index < EXPECTED).lower()} learn=true",
                flush=True,
            )
            continue

        finalize_provider(''',
        "repair-exhausted-defer",
    )

    text = text.replace(
        '''            if final_proof.get("verified"):
                final_verified.append(provider_id)
            else:
                hard_failures.append(provider_id)
                refused_provider = provider_id
''',
        '''            if final_proof.get("verified"):
                final_verified.append(provider_id)
            else:
                final_proof["deferToLearn"] = True
                final_proof["deferReason"] = "final-bundle-verification-failed"
                deferred_to_learn.append({
                    "index": absolute_index,
                    "providerId": provider_id,
                    "reason": "final-bundle-verification-failed",
                    "candidateValidatedTypes": list(evaluation.get("validatedTypes") or []),
                    "candidateMissingTypes": list(evaluation.get("missingTypes") or []),
                    "finalProof": final_proof,
                })
''',
        1,
    )

    text = text.replace(
        '            "result": "ok" if final_proof.get("verified") else completion_state,\n',
        '            "result": "ok" if final_proof.get("verified") else ("defer-to-learn" if final_proof.get("deferToLearn") else completion_state),\n',
        1,
    )
    text = text.replace(
        '''            "advancedForDiagnostics": refused_provider is None,
            "refusedToAdvance": refused_provider is not None,
''',
        '''            "learnRequired": bool(final_proof.get("deferToLearn")),
            "deferReason": final_proof.get("deferReason"),
            "advancedAfterDefer": bool(final_proof.get("deferToLearn")),
            "refusedToAdvance": False,
''',
        1,
    )
    text = text.replace(
        '''        if refused_provider is not None:
            break

    report = {
''',
        '''        if final_proof.get("deferToLearn"):
            print(
                f"FIELD_PROVIDER_BATCH_PROVIDER_DEFER index={absolute_index} provider={provider_id} reason={final_proof.get('deferReason')} advancing_next=true learn=true",
                flush=True,
            )

    report = {
''',
        1,
    )

    text = text.replace('        "schemaVersion": 2,\n', '        "schemaVersion": 3,\n', 1)
    text = text.replace('        "method": "provider-v3-bounded-repair-first-gate",\n', '        "method": "provider-v3-bounded-repair-first-defer-to-learn",\n', 1)
    text = text.replace(
        '        "refuseAdvanceAfterUnresolved": True,\n',
        '        "refuseAdvanceAfterUnresolved": False,\n'
        '        "continueAfterRepairExhausted": True,\n'
        '        "providerScopedFailuresDeferToLearn": True,\n',
        1,
    )
    text = text.replace(
        '        "refusedProvider": refused_provider,\n',
        '        "refusedProvider": None,\n'
        '        "deferredToLearnCount": len(deferred_to_learn),\n'
        '        "deferredToLearn": deferred_to_learn,\n',
        1,
    )
    text = text.replace(
        '''        f"hard_failures={len(hard_failures)} terminal={len(terminal_only)} "
        f"final_verified={len(final_verified)} refused={refused_provider or 'none'}",
''',
        '''        f"hard_failures={len(hard_failures)} deferred={len(deferred_to_learn)} "
        f"terminal={len(terminal_only)} final_verified={len(final_verified)} refused=none",
''',
        1,
    )

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str) -> None:
    required = (
        MARKER,
        'deferred_to_learn: list[dict[str, Any]] = []',
        '"result": "defer-to-learn"',
        '"continueAfterRepairExhausted": True',
        '"providerScopedFailuresDeferToLearn": True',
        '"deferredToLearnCount": len(deferred_to_learn)',
        'FIELD_PROVIDER_BATCH_PROVIDER_DEFER',
        '"refuseAdvanceAfterUnresolved": False',
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"defer-to-learn contract missing: {needle}")
    for forbidden in ('refused_provider = provider_id', 'f"refusing_next='):
        if forbidden in text:
            raise AssertionError(f"blocking provider rule survived: {forbidden}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_DEFER_TO_LEARN_V1_OK "
        f"changed={str(changed).lower()} repair_first=true bounded=true "
        "provider_failure=defer-to-learn continue_next=true publication_gate=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
