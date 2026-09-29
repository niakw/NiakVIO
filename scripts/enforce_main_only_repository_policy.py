#!/usr/bin/env python3
"""Enforce NiakVIO's main-only human code-change policy.

Human/manual maintenance stays on main. Normal Brain Learning may create only
the review-only brain-repair/proposal branch. Explicit architecture FORCE is
the single proposal-review exception: after bounded materialization and targeted
validation it may publish one lease-guarded commit directly to main, never a
FORCE PR/branch. The persistent brain-learning/proposals ref remains sanitized
memory, not a code branch.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAIN_WORKFLOW = ROOT / ".github/workflows/brain-learning-lab.yml"
HYGIENE_WORKFLOW = ROOT / ".github/workflows/repository-hygiene.yml"
BRAIN_BRANCH_MAINTENANCE = ROOT / ".github/workflows/brain-branch-maintenance.yml"
BRAIN_PROPOSAL_BRANCH = "brain-repair/proposal"
LEGACY_FORBIDDEN_BRANCH = "brain-repair/proposals"
JOB_MARKER = "\n  publish-repair-proposal:\n"
FORCE_JOB_MARKER = "- name: Promote FORCE architecture directly on main"
FORCE_MAIN_PUSH = 'git push --force-with-lease=refs/heads/main:"$GITHUB_SHA" origin HEAD:main'


def normalize(*, apply: bool) -> list[str]:
    return []


def assert_policy() -> None:
    workflow = BRAIN_WORKFLOW.read_text(encoding="utf-8")
    if JOB_MARKER not in workflow:
        raise ValueError("scheduled Brain repair proposal job is missing")
    required = (
        "if: github.event_name == 'schedule'",
        "pull-requests: write",
        "contents: write",
        f"BRANCH: {BRAIN_PROPOSAL_BRANCH}",
        "gh pr create",
        "requiresHumanMerge",
    )
    for marker in required:
        if marker not in workflow:
            raise ValueError(f"Brain repair PR contract missing: {marker}")
    if "git push origin HEAD:main" in workflow:
        raise ValueError("Brain workflow may not publish normal Learning code directly to main")
    if workflow.count(FORCE_MAIN_PUSH) != 1:
        raise ValueError("Brain architecture FORCE must expose exactly one lease-guarded direct-main publication point")
    if FORCE_JOB_MARKER not in workflow:
        raise ValueError("Brain architecture FORCE direct-main job is missing")
    force_block = workflow.split(FORCE_JOB_MARKER, 1)[1].split("\n  continue-learning-slot:", 1)[0]
    for marker in (
        "needs.experiment.outputs.architecture_force",
        "FIELD_BRAIN_ARCH_FORCE_MAIN_PROMOTION",
        "-f publish_proposal=false",
        "architecture FORCE crossed provider/publication boundary",
        "architecture FORCE changed non-allowlisted paths",
        "architecture FORCE did not contain an executable structural change",
        FORCE_MAIN_PUSH,
    ):
        if marker not in force_block:
            raise ValueError(f"Brain architecture FORCE direct-main contract missing: {marker}")
    if LEGACY_FORBIDDEN_BRANCH in workflow:
        raise ValueError("legacy Brain repair branch name resurrected")

    for pattern in ("*.yml", "*.yaml"):
        for path in sorted((ROOT / ".github/workflows").glob(pattern)):
            text = path.read_text(encoding="utf-8")
            if LEGACY_FORBIDDEN_BRANCH in text:
                raise ValueError(f"legacy Brain repair branch referenced by {path.relative_to(ROOT)}")
            if BRAIN_PROPOSAL_BRANCH not in text:
                continue
            if path.resolve() == BRAIN_WORKFLOW.resolve():
                continue
            if path.resolve() == HYGIENE_WORKFLOW.resolve():
                continue
            if path.resolve() == BRAIN_BRANCH_MAINTENANCE.resolve():
                cleanup_contracts = (
                    (
                        f'REPAIR_BRANCH="{BRAIN_PROPOSAL_BRANCH}"',
                        'gh pr list',
                        '--head "$REPAIR_BRANCH"',
                        'git push origin --delete "$REPAIR_BRANCH"',
                    ),
                    (
                        f'"{BRAIN_PROPOSAL_BRANCH}"',
                        'for branch in',
                        'gh pr list',
                        '--head "$branch"',
                        'git push origin --delete "$branch"',
                    ),
                )
                if not any(all(marker in text for marker in contract) for contract in cleanup_contracts):
                    raise ValueError(
                        "Brain branch maintenance cleanup contract missing for repair proposal branch"
                    )
                forbidden_cleanup_markers = (
                    'gh pr create',
                    'HEAD:"$REPAIR_BRANCH"',
                    'git switch -C "$REPAIR_BRANCH"',
                    'HEAD:"$branch"',
                    'git switch -C "$branch"',
                )
                for marker in forbidden_cleanup_markers:
                    if marker in text:
                        raise ValueError(f"Brain branch maintenance may only delete repair branch: {marker}")
                continue
            raise ValueError(
                f"only scheduled Brain Learning may create the repair PR branch: {path.relative_to(ROOT)}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")

    changed = normalize(apply=args.apply)
    assert_policy()

    print(
        "FIELD_MAIN_ONLY_POLICY "
        f"manual_code_branches=0 brain_repair_pr_branch={BRAIN_PROPOSAL_BRANCH} "
        f"scheduled_only=true changed={len(changed)} "
        "force_architecture_main_only=true persistent_learning_ref=brain-learning/proposals"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
