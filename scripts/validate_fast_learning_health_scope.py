#!/usr/bin/env python3
"""Validate a Fast-Handoff Learning health report against its selected scope."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_","-")


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--handoff",type=Path,required=True)
    p.add_argument("--health",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()

    handoff=load(args.handoff)
    health=load(args.health)
    expected={cid(x) for x in handoff.get("providers") or [] if cid(x)}
    if not expected:
        raise SystemExit("fast handoff has no providers")
    rows=[row for row in health.get("results") or [] if isinstance(row,dict)]
    actual={cid(row.get("canonical_id") or row.get("providerId") or row.get("id")) for row in rows}
    actual.discard("")
    missing=sorted(expected-actual)
    extra=sorted(actual-expected)
    if missing or extra:
        raise SystemExit(f"targeted health scope mismatch missing={missing} extra={extra}")
    if int(health.get("candidate_count") or len(rows)) != len(expected):
        raise SystemExit("targeted health candidate_count mismatch")
    if any(not str(row.get("status") or "").strip() for row in rows):
        raise SystemExit("targeted health contains rows without status")

    payload={
        "schemaVersion":1,
        "providerCount":len(expected),
        "providers":sorted(expected),
        "statuses":{cid(row.get("canonical_id")):str(row.get("status") or "") for row in rows},
        "fullCatalogueCoverageRequired":False,
        "policy":"Fast-Handoff validates exact selected providers; scheduled/full Learning owns global daily coverage.",
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"FIELD_FAST_LEARNING_HEALTH_SCOPE providers={len(expected)} ids={','.join(sorted(expected))}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
