#!/usr/bin/env python3
"""Decide whether Domain Refresh can replay an atomic publication onto a newer main.

Only non-executable evidence/documentation drift is allowed. Any change to
provider bytes, manifest, CORE, Brain code, release inputs, or authority DATA
requires a new full resolution from the latest source SHA. This is deliberately
more conservative than a general git rebase.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SAFE_FILES = {
    "MEMORY.md",
    "PROVIDER_CENSUS_STATUS.md",
    "automation/brain-repair-memory.json",
    "automation/brain-repair-experience.json",
    "automation/provider-census-status.json",
    "automation/provider-brain-repair-latest.json",
    "automation/provider-fast-repair-summary.json",
    "automation/provider-repair-learn-handoff-v1.json",
    "automation/provider-census-sharded-latest.json",
    "automation/provider-learning-handoff.json",
}


def classify_drift(paths: list[str]) -> tuple[bool, list[str]]:
    unsafe: list[str] = []
    for raw in paths:
        path = raw.strip().replace("\\", "/")
        if not path:
            continue
        if path in SAFE_FILES or (path.startswith("docs/") and path.endswith(".md")):
            continue
        unsafe.append(path)
    return not unsafe, sorted(set(unsafe))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drift-file", required=True)
    args = parser.parse_args()
    paths = Path(args.drift_file).read_text(encoding="utf-8").splitlines()
    safe, unsafe = classify_drift(paths)
    if safe:
        print("FIELD_DOMAIN_RACE_REBASE_SAFE evidence_only=true")
    else:
        print("FIELD_DOMAIN_RACE_REBASE_BLOCKED executable_or_publication_drift=" + ",".join(unsafe[:30]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
