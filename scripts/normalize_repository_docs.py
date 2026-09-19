#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Normalize durable repository documentation references.

Generated/provider result sections are owned by their dedicated synchronizers.
This normalizer only repairs static architecture references that must follow the
permanent workflow surface on main.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CORE_PUBLISH_FREEZE = ROOT / "automation" / "CORE-PUBLISH-FREEZE"

REPLACEMENTS = {
    "| `engine-regression-offline.yml` | non-régressions moteur hors réseau |":
        "| `core-media-finalize-main.yml` | fixed-point Core, non-régressions Engine v2 et intégrité de publication |",
}
FORBIDDEN = (
    "engine-regression-offline.yml",
    "provider-rebuild-offline.yml",
)


def normalized(text: str) -> str:
    result = text
    for old, new in REPLACEMENTS.items():
        result = result.replace(old, new)
    return result


def enforce_core_publish_freeze() -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    if os.environ.get("GITHUB_WORKFLOW") != "NiakVIO Core media finalizer":
        return
    if CORE_PUBLISH_FREEZE.is_file():
        raise SystemExit("Core publication freeze is active; refusing stale/future Core finalizer")


def main() -> int:
    enforce_core_publish_freeze()

    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error("choose exactly one of --apply or --check")

    current = README.read_text(encoding="utf-8")
    expected = normalized(current)
    remaining = [value for value in FORBIDDEN if value in expected]
    if remaining:
        raise SystemExit("retired README workflow references remain: " + ", ".join(remaining))

    changed = current != expected
    if args.check and changed:
        raise SystemExit("repository documentation normalization required")
    if args.apply and changed:
        README.write_text(expected, encoding="utf-8")

    print(f"FIELD_REPOSITORY_DOCS changed={int(changed)} retired_workflow_refs=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
