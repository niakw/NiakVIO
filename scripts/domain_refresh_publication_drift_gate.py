#!/usr/bin/env python3
"""Decide whether Domain Refresh can replay an atomic publication onto a newer main.

Only non-executable evidence/documentation drift is allowed. Any change to
provider bytes, manifest, CORE, Brain code, release inputs, or authority DATA
requires a new full resolution from the latest source SHA. This is deliberately
more conservative than a general git rebase.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

SAFE_FILES = {
    "MEMORY.md",
    "PROVIDER_CENSUS_STATUS.md",
    "automation/brain-repair-memory.json",
    "automation/brain-llm-force-memory.json",
    "automation/brain-repair-experience.json",
    "automation/provider-census-status.json",
    "automation/provider-brain-repair-latest.json",
    "automation/provider-fast-repair-summary.json",
    "automation/provider-repair-learn-handoff-v1.json",
    "automation/provider-census-sharded-latest.json",
    "automation/provider-learning-handoff.json",
    # Census publications are generated evidence, never provider source DATA.
    "automation/provider-census-proof-history.json",
    "automation/provider-repair-batch-plan-latest.json",
    "automation/provider-waf-browser-session-latest.json",
}

# Timestamped census/WAF session artifacts are evidence only. Never accept a
# generic automation/*.json glob: provider-overrides and authority DATA live there.
SAFE_ARTIFACT_PATTERNS = (
    re.compile(r"^automation/provider-census-sharded-[0-9]{8,20}\.json$"),
    re.compile(r"^automation/provider-waf-browser-session-[0-9]{8,20}\.json$"),
)

# Each retained hosted JSON is a source-SHA-qualified, immutable experiment.
# Only newly ADDED entries can be treated as non-executable drift.
HOSTED_EVIDENCE_ARCHIVE = re.compile(
    r"^automation/hosted-repair-evidence/[0-9]{8,14}"
    r"(?:-(?:evaluation|http-observation|mutations|player-markup))?\.json$"
)



def classify_drift(paths: list[str]) -> tuple[bool, list[str]]:
    """Permit evidence-only rebase, reject provider/runtime edits.

    Input from git diff --name-status preserves archive addition vs overwrite.
    A legacy path-only row is conservatively interpreted as modified.
    """
    unsafe: list[str] = []
    for raw in paths:
        row = raw.strip()
        if not row:
            continue
        if "\t" in row:
            status, path = row.split("\t", 1)
            if status not in {"A", "M"}:
                unsafe.append(row)
                continue
        else:
            status, path = "M", row
        path = path.replace("\\", "/")
        if path in SAFE_FILES or any(p.fullmatch(path) for p in SAFE_ARTIFACT_PATTERNS):
            continue
        if path.startswith("docs/") and path.endswith(".md"):
            continue
        if status == "A" and HOSTED_EVIDENCE_ARCHIVE.fullmatch(path):
            continue
        unsafe.append(row)
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
