#!/usr/bin/env python3
"""Verify that a FORCE artifact installed every executable strategy gate.

Run after git apply on the promoter checkout, not merely on the generator's
temporary workspace. Registration-only changes are never an executable fix.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from brain_architecture_force_materializer import (
    NEW_REPAIR_PROFILE_SURFACES,
    select_blueprint,
    validate_blueprint_implementation,
    validate_source_family_implementation,
    validate_changed_syntax,
    allowed_patterns,
    path_allowed,
    _source_family_artifact_paths,
)
from build_brain_architecture_proposal import fully_installed_repair_profiles

ROOT = Path(__file__).resolve().parents[1]


def verify(proposal: dict, report: dict, *, root: Path = ROOT) -> str:
    blueprint = select_blueprint(proposal, target_provider=str(report.get("targetProvider") or ""))
    strategy = str(blueprint.get("strategyId") or "")
    if strategy != str(report.get("strategyId") or ""):
        raise ValueError("FORCE applied profile differs from generated blueprint")
    changed = [str(path) for path in (report.get("changedFiles") or [])]
    if not changed or int(report.get("editCount") or 0) <= 0:
        raise ValueError("FORCE executable patch absent")
    if blueprint.get("requiresNewSourceFamilyLego") is True:
        if report.get("applied") is not True:
            raise ValueError("source-family FORCE not applied")
        expected = _source_family_artifact_paths({"blueprint": blueprint})
        if len(changed) != 3 or set(changed) != {expected["modulePath"], expected["runtimePath"], expected["testPath"]}:
            raise ValueError("source-family FORCE applied path set differs from compiler")
        digests = report.get("materializedSha256")
        if not isinstance(digests, dict) or set(digests) != set(changed):
            raise ValueError("source-family FORCE missing exact materialized byte digests")
        for path in changed:
            target = (root / path).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digests[path]:
                raise ValueError("source-family FORCE applied byte mismatch: " + path)
        validate_changed_syntax(changed, root=root)
        validate_source_family_implementation(changed, blueprint, root=root)
        return strategy
    if blueprint.get("requiresNewExecutableRepairProfile") is not True:
        return strategy
    if not set(NEW_REPAIR_PROFILE_SURFACES).issubset(set(changed)):
        raise ValueError("FORCE artifact lost generated runtime or planner/Brain source")
    validate_blueprint_implementation(changed, blueprint, root=root)
    if strategy not in fully_installed_repair_profiles(root):
        raise ValueError("FORCE strategy not fully installed in all executable surfaces")
    return strategy


def export_patch(report: dict, output: Path, *, root: Path = ROOT) -> None:
    """Package every exact reported path, not an obsolete shell path list."""
    from brain_force_rebase_guard import patch_changed_paths
    paths = report.get("changedFiles")
    if (report.get("applied") is not True or not isinstance(paths, list)
            or not paths or any(not isinstance(p, str) for p in paths)
            or len(paths) != len(set(paths))):
        raise ValueError("FORCE patch report has invalid paths or application state")
    cfg = json.loads((root / "engine_v2/config/brain-self-evolution.json").read_text("utf-8"))
    patterns = allowed_patterns(cfg)
    for path in paths:
        target = (root / path).resolve()
        if not path_allowed(path, patterns) or not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError("FORCE patch path outside allowlist: " + path)
    digests = report.get("materializedSha256")
    if not isinstance(digests, dict) or set(digests) != set(paths):
        raise ValueError("FORCE patch missing materialized byte digests")
    for path in paths:
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != digests[path]:
            raise ValueError("FORCE patch source differs from validated bytes: " + path)
    subprocess.run(["git", "add", "-N", "--", *paths], cwd=root, check=True)
    diff = subprocess.check_output(["git", "diff", "--binary", "HEAD", "--", *paths], cwd=root)
    if patch_changed_paths(diff.decode("utf-8")) != set(paths):
        raise ValueError("FORCE exported paths differ from validated report")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(diff)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--export-patch", type=Path)
    args = parser.parse_args()
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    report = json.loads(args.report.read_text(encoding="utf-8"))
    strategy = verify(proposal, report)
    if args.export_patch:
        export_patch(report, args.export_patch)
    blueprint = select_blueprint(proposal, target_provider=str(report.get("targetProvider") or ""))
    if blueprint.get("requiresNewSourceFamilyLego") is True:
        print(f"FIELD_BRAIN_FORCE_APPLIED_SOURCE_FAMILY strategy={strategy} bytes=verified parser=verified playback=false")
    else:
        print(f"FIELD_BRAIN_FORCE_APPLIED_PROFILE strategy={strategy} selector=verified planner=verified executor=verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
