#!/usr/bin/env python3
"""All durable ProviderBase preparation migrations must be byte-idempotent on main."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from materialize_provider_base_v3_store import prepare_runtime  # noqa: E402


def git_surface() -> tuple[str, str]:
    diff = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--binary", "--", "scripts"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "scripts"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    return diff, untracked


before = git_surface()
prepare_runtime()
after = git_surface()

assert after == before, (
    "ProviderBase preparation migrations must already be at a fixed point; "
    "running prepare_runtime() changed tracked/untracked scripts",
    {"before": before, "after": after},
)

print("provider base migration fixed-point contract passed")
