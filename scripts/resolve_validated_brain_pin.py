#!/usr/bin/env python3
"""Resolve the single validated Brain-LLM revision paired with this NiakVIO commit."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "automation" / "brain-pinned-source.json"


def resolve_validated_brain_pin(root: Path = ROOT) -> str:
    pin_path = root / "automation" / "brain-pinned-source.json"
    raw = json.loads(pin_path.read_text(encoding="utf-8"))
    if raw.get("schemaVersion") != 1:
        raise RuntimeError("validated Brain pin schema mismatch")
    if raw.get("role") != "validated-external-brain-gitlink":
        raise RuntimeError("validated Brain pin role mismatch")
    if raw.get("repository") != "niakw/NiakVIO-Brain-LLM":
        raise RuntimeError("validated Brain repository mismatch")
    if raw.get("submodule") != "brain-llm":
        raise RuntimeError("validated Brain submodule mismatch")
    sha = str(raw.get("sha") or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError("validated Brain SHA missing")
    if raw.get("brainCiConclusion") != "success":
        raise RuntimeError("validated Brain CI is not successful")
    if raw.get("brainSecurityConclusion") != "success":
        raise RuntimeError("validated Brain security inventory is not successful")
    if raw.get("proofAuthority") is not False or raw.get("publicationAuthority") is not False:
        raise RuntimeError("Brain source provenance cannot grant proof/publication authority")

    entry = subprocess.check_output(
        ["git", "ls-tree", "HEAD", "--", "brain-llm"],
        cwd=root,
        text=True,
    ).strip()
    match = re.fullmatch(r"160000 commit ([0-9a-f]{40})\tbrain-llm", entry)
    if not match:
        raise RuntimeError(f"brain-llm is not an exact gitlink: {entry!r}")
    if match.group(1) != sha:
        raise RuntimeError(
            f"validated Brain pin/gitlink drift: pin={sha} gitlink={match.group(1)}"
        )
    return sha


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--env-output", type=Path)
    parser.add_argument("--env-name", default="BRAIN_SHA")
    args = parser.parse_args()

    sha = resolve_validated_brain_pin()
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"sha={sha}\n")
    if args.env_output:
        name = str(args.env_name or "BRAIN_SHA").strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", name):
            raise ValueError("invalid environment output name")
        with args.env_output.open("a", encoding="utf-8") as handle:
            handle.write(f"{name}={sha}\n")
    print(
        "FIELD_BRAIN_VALIDATED_PIN "
        f"sha={sha} source=validated-gitlink proof_authority=false publication=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
