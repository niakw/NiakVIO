#!/usr/bin/env python3
"""Enforce NiakVIO's main-only human code-change policy.

Human/manual maintenance stays on main. The only code-review branch a workflow
may create is brain-repair/proposal, and only the scheduled Brain Learning job
may create it after materializing validated sandbox evidence. The persistent
brain-learning/proposals ref remains sanitized memory, not a code branch.
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
        raise ValueError("Brain workflow may not publish learned code directly to main")
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
                cleanup_markers = (
                    f'REPAIR_BRANCH="{BRAIN_PROPOSAL_BRANCH}"',
                    'gh pr list',
                    '--head "$REPAIR_BRANCH"',
                    'git push origin --delete "$REPAIR_BRANCH"',
                )
                for marker in cleanup_markers:
                    if marker not in text:
                        raise ValueError(f"Brain branch maintenance cleanup contract missing: {marker}")
                forbidden_cleanup_markers = (
                    'gh pr create',
                    'HEAD:"$REPAIR_BRANCH"',
                    'git switch -C "$REPAIR_BRANCH"',
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
        "persistent_learning_ref=brain-learning/proposals"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
