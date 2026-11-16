#!/usr/bin/env python3
"""Fail closed when an onboarding artifact is stale against executable main drift.

Single/bulk onboarding validates a transaction on one immutable base SHA. The
validated patch may be replayed only across documentation/control-trigger drift.
Any executable, provider, catalogue, test or workflow change requires the
onboarding transaction to be regenerated on current main.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

NEUTRAL_FILES = {
    "MEMORY.md",
    "README.md",
    "README.fr.md",
    "PROVIDER_CENSUS_STATUS.md",
}

NEUTRAL_PREFIXES = (
    "docs/",
    ".github/triggers/",
)


def normalize_path(value: str) -> str:
    return value.strip().replace("\\", "/").lstrip("./")


def is_neutral_path(value: str) -> bool:
    path = normalize_path(value)
    if not path:
        return True
    if path in NEUTRAL_FILES:
        return True
    return any(path.startswith(prefix) for prefix in NEUTRAL_PREFIXES)


def classify_paths(paths: Iterable[str]) -> tuple[list[str], list[str]]:
    neutral: list[str] = []
    blocking: list[str] = []
    for raw in paths:
        path = normalize_path(raw)
        if not path:
            continue
        (neutral if is_neutral_path(path) else blocking).append(path)
    return sorted(set(neutral)), sorted(set(blocking))


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout.strip()


def changed_paths(base: str, head: str) -> list[str]:
    git("merge-base", "--is-ancestor", base, head)
    out = git("diff", "--name-only", "--diff-filter=ACDMRTUXB", base, head, "--")
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    paths = changed_paths(args.base, args.head)
    neutral, blocking = classify_paths(paths)
    if blocking:
        print(
            "FIELD_PROVIDER_ONBOARDING_STALE "
            f"base={args.base} head={args.head} blocking={len(blocking)} "
            f"neutral={len(neutral)}"
        )
        for path in blocking:
            print(f"BLOCKING_ONBOARDING_DRIFT {path}")
        raise SystemExit(
            "validated onboarding artifact is stale after executable/repository drift"
        )

    print(
        "FIELD_PROVIDER_ONBOARDING_NEUTRAL_DRIFT "
        f"base={args.base} head={args.head} neutral={len(neutral)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
