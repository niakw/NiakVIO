#!/usr/bin/env python3
"""Enforce NiakVIO's main-only code-change policy.

The persistent ``brain-learning/proposals`` ref is sanitized learning memory, not
a code-review branch. Brain repair proposals remain artifacts only: no workflow
may create ``brain-repair/proposals`` or a temporary repair PR. The repository
hygiene workflow is the sole exception allowed to mention the forbidden ref,
because it only deletes it.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAIN_WORKFLOW = ROOT / ".github/workflows/brain-learning-lab.yml"
FORBIDDEN_BRANCH = "brain-repair/proposals"
JOB_MARKER = "\n  publish-repair-proposal:\n"
HYGIENE_WORKFLOW = ROOT / ".github/workflows/repository-hygiene.yml"


def normalize(*, apply: bool) -> list[str]:
    changed: list[str] = []
    text = BRAIN_WORKFLOW.read_text(encoding="utf-8")
    if JOB_MARKER in text:
        changed.append("brain-learning-lab:publish-repair-proposal")
        if apply:
            text = text.split(JOB_MARKER, 1)[0].rstrip() + "\n"
            BRAIN_WORKFLOW.write_text(text, encoding="utf-8")
    return changed


def assert_policy() -> None:
    workflow = BRAIN_WORKFLOW.read_text(encoding="utf-8")
    if JOB_MARKER in workflow:
        raise ValueError("Brain repair proposal job still exists")
    for pattern in ("*.yml", "*.yaml"):
        for path in sorted((ROOT / ".github/workflows").glob(pattern)):
            text = path.read_text(encoding="utf-8")
            if FORBIDDEN_BRANCH not in text:
                continue
            if path.resolve() == HYGIENE_WORKFLOW.resolve():
                if f"git push origin --delete \"$branch\"" not in text:
                    raise ValueError("repository hygiene mentions forbidden branch without a deletion-only implementation")
                continue
            raise ValueError(f"temporary Brain repair branch can still be created by {path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")

    changed = normalize(apply=args.apply)
    if args.apply:
        assert_policy()
    elif args.check:
        if changed:
            raise SystemExit("main-only workflow normalization required: " + ", ".join(changed))
        assert_policy()

    print(
        "FIELD_MAIN_ONLY_POLICY "
        f"temporary_repair_branches=0 temporary_repair_prs=0 changed={len(changed)} "
        "persistent_learning_ref=brain-learning/proposals"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
