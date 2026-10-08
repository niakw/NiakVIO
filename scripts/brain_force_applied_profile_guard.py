#!/usr/bin/env python3
"""Verify that a FORCE artifact installed every executable strategy gate.

Run after git apply on the promoter checkout, not merely on the generator's
temporary workspace. Registration-only changes are never an executable fix.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from brain_architecture_force_materializer import (
    NEW_REPAIR_PROFILE_SURFACES,
    select_blueprint,
    validate_blueprint_implementation,
)
from build_brain_architecture_proposal import fully_installed_repair_profiles

ROOT = Path(__file__).resolve().parents[1]


def verify(proposal: dict, report: dict, *, root: Path = ROOT) -> str:
    blueprint = select_blueprint(proposal)
    strategy = str(blueprint.get("strategyId") or "")
    if strategy != str(report.get("strategyId") or ""):
        raise ValueError("FORCE applied profile differs from generated blueprint")
    changed = [str(path) for path in (report.get("changedFiles") or [])]
    if not changed or int(report.get("editCount") or 0) <= 0:
        raise ValueError("FORCE executable patch absent")
    if blueprint.get("requiresNewExecutableRepairProfile") is not True:
        return strategy
    if not set(NEW_REPAIR_PROFILE_SURFACES).issubset(set(changed)):
        raise ValueError("FORCE artifact lost generated runtime or planner/Brain source")
    validate_blueprint_implementation(changed, blueprint, root=root)
    if strategy not in fully_installed_repair_profiles(root):
        raise ValueError("FORCE strategy not fully installed in all executable surfaces")
    return strategy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    report = json.loads(args.report.read_text(encoding="utf-8"))
    strategy = verify(proposal, report)
    print(f"FIELD_BRAIN_FORCE_APPLIED_PROFILE strategy={strategy} selector=verified planner=verified executor=verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
