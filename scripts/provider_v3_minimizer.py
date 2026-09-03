#!/usr/bin/env python3
"""Provider v3 JavaScript minimizer workbench.

This is intentionally audit/preview-only. It never mutates providers/ and does not
participate in reconstruction or publication. The first phase inventories the exact
96 generated Provider JS files, structural markers and whitespace/comment budget so a
future token-aware compactor can be enabled only after semantic-equivalence gates exist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = ROOT / "providers"
MANIFEST = ROOT / "manifest.json"
MARKERS = (
    "BEGIN NIAKVIO_PROVIDER",
    "END NIAKVIO_PROVIDER",
    "STARTFIX:",
    "CLOSEFIX:",
    "FIXDATA:",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
)
ASI_SENSITIVE = re.compile(r"(?m)^\s*(return|throw|break|continue|yield|await)\b")
LINE_COMMENT = re.compile(r"//[^\n]*")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def audit_text(text: str) -> dict:
    encoded = text.encode("utf-8")
    lines = text.splitlines()
    indentation = sum(len(line) - len(line.lstrip(" \t")) for line in lines)
    trailing = sum(len(line) - len(line.rstrip(" \t")) for line in lines)
    blank = sum(1 for line in lines if not line.strip())
    comments = LINE_COMMENT.findall(text) + BLOCK_COMMENT.findall(text)
    return {
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "lines": len(lines),
        "blank_lines": blank,
        "indentation_bytes": indentation,
        "trailing_space_bytes": trailing,
        "comment_bytes": sum(len(value.encode("utf-8")) for value in comments),
        "template_literal_tokens": text.count(chr(96)),
        "asi_sensitive_lines": len(ASI_SENSITIVE.findall(text)),
        "markers": {marker: text.count(marker) for marker in MARKERS},
    }


def provider_files() -> list[Path]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    filenames = [
        str(row.get("filename") or "").strip()
        for row in (manifest.get("scrapers") or [])
        if str(row.get("filename") or "").strip()
    ]
    if len(filenames) != 96 or len(set(filenames)) != 96:
        raise SystemExit(
            f"expected 96 unique manifest provider filenames, got {len(filenames)} / {len(set(filenames))}"
        )
    files: list[Path] = []
    for filename in filenames:
        path = (ROOT / filename).resolve()
        if PROVIDERS.resolve() not in path.parents:
            raise SystemExit(f"manifest provider path escapes providers/: {filename}")
        if not path.is_file():
            raise SystemExit(f"manifest provider asset missing: {filename}")
        files.append(path)
    return files


def portfolio_report() -> dict:
    files = provider_files()
    rows = []
    totals = {
        "bytes": 0,
        "lines": 0,
        "blank_lines": 0,
        "indentation_bytes": 0,
        "trailing_space_bytes": 0,
        "comment_bytes": 0,
        "template_literal_tokens": 0,
        "asi_sensitive_lines": 0,
    }
    for path in files:
        audit = audit_text(path.read_text(encoding="utf-8"))
        rows.append({"file": path.name, **audit})
        for key in totals:
            totals[key] += int(audit[key])
    return {
        "schema_version": 1,
        "mode": "audit-only",
        "production_enabled": False,
        "provider_count": len(files),
        "terser_allowed": False,
        "transformations_enabled": [],
        "future_safe_transform_contract": [
            "preserve every newline until ASI-equivalence is proven",
            "preserve comments and all Provider v3 managed markers",
            "never rename identifiers",
            "never reorder/fold expressions",
            "never change string, template or regex literal bytes",
            "require parse + structural + runtime equivalence before any publication",
        ],
        "totals": totals,
        "providers": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = portfolio_report()
    if report["provider_count"] != 96:
        raise SystemExit(f"expected 96 generated providers, got {report['provider_count']}")
    if any(
        row["markers"]["BEGIN NIAKVIO_PROVIDER"] != 1
        or row["markers"]["END NIAKVIO_PROVIDER"] != 1
        or row["markers"]["NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"] != 1
        for row in report["providers"]
    ):
        raise SystemExit("Provider v3 structural marker inventory failed")

    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        resolved = args.output.resolve()
        providers_root = PROVIDERS.resolve()
        if resolved == providers_root or providers_root in resolved.parents:
            raise SystemExit("minimizer audit may never write inside providers/")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(payload, encoding="utf-8")

    if args.json:
        print(payload, end="")
    else:
        totals = report["totals"]
        print(
            "FIELD_PROVIDER_V3_MINIMIZER_AUDIT "
            f"providers={report['provider_count']} bytes={totals['bytes']} "
            f"indentation_bytes={totals['indentation_bytes']} "
            f"trailing_space_bytes={totals['trailing_space_bytes']} "
            f"comment_bytes={totals['comment_bytes']} "
            f"templates={totals['template_literal_tokens']} "
            f"asi_sensitive_lines={totals['asi_sensitive_lines']} "
            "production_enabled=false terser_allowed=false"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
