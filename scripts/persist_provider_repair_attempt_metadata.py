#!/usr/bin/env python3
"""Persist Repair/FORCE attempt activity without weakening provider proof state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--status",type=Path,required=True)
    parser.add_argument("--brain",type=Path)
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--mode",choices=("repair","force"),required=True)
    parser.add_argument("--canonical-outcome",required=True)
    parser.add_argument("--candidate-gate-outcome",default="skipped")
    args=parser.parse_args()

    state=load(args.status)
    brain=load(args.brain) if args.brain and args.brain.is_file() else {}

    selected=sorted({
        canon(value)
        for value in brain.get("selectedProviders") or []
        if canon(value)
    })
    candidate=sorted({
        canon(value)
        for value in (
            list(brain.get("fixedInLabProviders") or [])
            + list(brain.get("acceptedProgramCompiledProviders") or [])
        )
        if canon(value)
    })
    deferred=sorted({
        canon(value)
        for value in brain.get("deferredLearningProviders") or []
        if canon(value)
    })
    accepted_count=int(brain.get("acceptedRepairCount") or 0)
    canonical=str(args.canonical_outcome or "").strip().casefold()
    gate=str(args.candidate_gate_outcome or "").strip().casefold()
    validated=candidate if canonical=="success" and gate=="success" else []

    state["lastRepairAttempt"]={
        "runId":str(args.run_id),
        "sourceCensusRunId":str(state.get("runId") or ""),
        "mode":args.mode,
        "selectedProviders":selected,
        "candidateProviders":candidate,
        "validatedProviders":validated,
        "acceptedRepairCount":accepted_count,
        "deferredToLearningSlotProviders":deferred,
        "noProgressReason":str(
            brain.get("noProgressReason")
            or ("canonical-"+canonical if canonical else "unknown")
        ),
        "timeBudgetExhausted":brain.get("timeBudgetExhausted") is True,
        "canonicalOutcome":canonical,
        "candidateGateOutcome":gate,
        "publicationAllowed":canonical=="success" and gate=="success",
    }
    args.status.write_text(
        json.dumps(state,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8",
    )
    print(
        "FIELD_REPAIR_ATTEMPT_METADATA "
        f"run={args.run_id} mode={args.mode} selected={len(selected)} "
        f"candidates={len(candidate)} validated={len(validated)} "
        f"outcome={canonical} gate={gate}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
