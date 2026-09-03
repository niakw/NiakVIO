#!/usr/bin/env python3
"""Block CodeQL 'Bad HTML filtering regexp' patterns at their NiakVIO sources."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    ROOT / "scripts/provider_base_store.py",
    ROOT / "scripts/provider_patches/global_catalogue_alias_recovery_v2.py",
)

BAD_PATTERNS = (
    re.compile(r"""\.replace\(\s*/<\[\^>\][+*]>/[a-z]*"""),
    re.compile(r"""\.replace\(\s*/<script\["""),
    re.compile(r"""\.replace\(\s*/<style\["""),
)


def findings(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    rows = []
    for pattern in BAD_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            rows.append(f"{path.relative_to(ROOT)}:{line}:{match.group(0)}")
    return rows


def published_paths() -> list[Path]:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    rows = manifest.get("scrapers") or []
    if len(rows) != 96:
        raise AssertionError(f"expected 96 manifest providers, got {len(rows)}")
    paths = [ROOT / str(row.get("filename") or "") for row in rows]
    if len({path.resolve() for path in paths}) != 96:
        raise AssertionError("published provider paths must be unique")
    for path in paths:
        if not path.is_file():
            raise AssertionError(f"missing published provider: {path}")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--published", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    for path in SOURCE_PATHS:
        failures.extend(findings(path))

    base_source = SOURCE_PATHS[0].read_text(encoding="utf-8")
    alias_source = SOURCE_PATHS[1].read_text(encoding="utf-8")
    if "function _htmlVisibleText(value)" not in base_source:
        failures.append("provider_base_store.py: missing deterministic HTML text scanner")
    if "function plainHtml(v)" not in alias_source:
        failures.append("global_catalogue_alias_recovery_v2.py: missing deterministic HTML text scanner")

    checked = 0
    if args.published:
        for path in published_paths():
            checked += 1
            failures.extend(findings(path))

    if failures:
        raise AssertionError("\n".join(failures))

    print(
        "PROVIDER_HTML_FILTER_SECURITY_OK "
        f"sources={len(SOURCE_PATHS)} published={checked} bad_html_filter_regex=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
