#!/usr/bin/env python3
"""Classify external audit findings into maintained source vs derived evidence.

Raw Sonar/DeepSource/CodeScene exports remain untouched.  This script creates a
release-oriented view so generated Provider JS does not multiply one maintained
Core issue across every published bundle.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

DERIVED_PREFIXES = ("providers/", "native-hub46/")
HISTORICAL_PREFIXES = ("provider-old/", "upstream-lkg/")
EVIDENCE_PREFIXES = ("audit/", "automation/evidence/", "health-output/")
MAINTAINED_PREFIXES = (
    ".github/",
    "engine_v2/",
    "provider-bases/",
    "scripts/",
    "tests/",
)

# Exact reviewed scanner false positives.  Keep this intentionally narrow: the
# rule remains active everywhere else.
REVIEWED_FALSE_POSITIVES = {
    (
        "deepsource",
        "SCT-A000",
        "scripts/provider_patches/global_media_type_resolution_v1.py",
    ): "TMDB response field names movie_results/tv_results are schema keys, not credentials or secrets.",
}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def norm_path(value: object) -> str:
    path = str(value or "").strip().replace("\\", "/")
    if ":" in path and not path.startswith(("http://", "https://")):
        left, right = path.split(":", 1)
        if "/" not in left and "/" in right:
            path = right
    return path.lstrip("./")


def scope(path: str) -> str:
    if path.startswith(DERIVED_PREFIXES):
        return "generated"
    if path.startswith(HISTORICAL_PREFIXES):
        return "historical"
    if path.startswith(EVIDENCE_PREFIXES) or path.startswith("automation/"):
        return "evidence"
    if path.startswith(MAINTAINED_PREFIXES):
        return "maintained"
    return "maintained"  # root config/source files are maintained by default.


def sonar_rows(root: Path) -> Iterable[dict[str, Any]]:
    payload = load_json(root / "sonar" / "issues.json", {})
    rows = payload.get("issues", []) if isinstance(payload, dict) else payload
    for raw in rows if isinstance(rows, list) else []:
        if not isinstance(raw, dict):
            continue
        component = norm_path(raw.get("component") or raw.get("filePath") or raw.get("path"))
        yield {
            "source": "sonar",
            "rule": str(raw.get("rule") or ""),
            "severity": str(raw.get("severity") or raw.get("impactSeverity") or "").upper(),
            "path": component,
            "line": raw.get("line") or ((raw.get("textRange") or {}).get("startLine") if isinstance(raw.get("textRange"), dict) else None),
            "message": str(raw.get("message") or ""),
        }


def deepsource_rows(root: Path) -> Iterable[dict[str, Any]]:
    payload = load_json(root / "deepsource" / "findings.json", [])
    rows = payload
    if isinstance(payload, dict):
        rows = payload.get("results") or payload.get("findings") or payload.get("data") or []
    for raw in rows if isinstance(rows, list) else []:
        if not isinstance(raw, dict):
            continue
        rule = str(raw.get("issueCode") or raw.get("issue_code") or raw.get("code") or raw.get("rule") or "")
        yield {
            "source": "deepsource",
            "rule": rule,
            "severity": str(raw.get("severity") or "").upper(),
            "path": norm_path(raw.get("path") or raw.get("filePath")),
            "line": raw.get("beginLine") or raw.get("line"),
            "message": str(raw.get("message") or raw.get("title") or raw.get("description") or ""),
        }


def codescene_rows(root: Path) -> Iterable[dict[str, Any]]:
    payload = load_json(root / "codescene" / "analysis-latest.json", {})
    candidates: list[Any] = []
    if isinstance(payload, dict):
        for key in ("defects", "findings", "issues", "warnings"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates.extend(value)
    for raw in candidates:
        if not isinstance(raw, dict):
            continue
        yield {
            "source": "codescene",
            "rule": str(raw.get("rule") or raw.get("category") or raw.get("type") or ""),
            "severity": str(raw.get("severity") or "").upper(),
            "path": norm_path(raw.get("path") or raw.get("file") or raw.get("file_path")),
            "line": raw.get("line"),
            "message": str(raw.get("message") or raw.get("description") or raw.get("name") or ""),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="audit/ai-external")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = Path(args.root)

    rows = [*sonar_rows(root), *deepsource_rows(root), *codescene_rows(root)]
    unresolved: list[dict[str, Any]] = []
    reviewed: list[dict[str, Any]] = []
    scoped = Counter()
    sources = Counter()

    for row in rows:
        row["scope"] = scope(row["path"])
        scoped[row["scope"]] += 1
        sources[row["source"]] += 1
        key = (row["source"], row["rule"], row["path"])
        reason = REVIEWED_FALSE_POSITIVES.get(key)
        if reason and row["scope"] == "maintained":
            row["review"] = "false_positive"
            row["review_reason"] = reason
            reviewed.append(row)
        elif row["scope"] == "maintained":
            unresolved.append(row)

    report = {
        "schema_version": 1,
        "raw_findings": len(rows),
        "by_source": dict(sorted(sources.items())),
        "by_scope": dict(sorted(scoped.items())),
        "maintained_unresolved_count": len(unresolved),
        "maintained_reviewed_count": len(reviewed),
        "maintained_unresolved": unresolved,
        "maintained_reviewed": reviewed,
        "policy": {
            "generated_provider_js": "raw evidence retained; security gated by exact-byte publication tests",
            "historical": "archive/reference only",
            "evidence": "diagnostic/reference only",
            "maintained": "release blocking unless corrected or exact reviewed false positive",
        },
    }
    (root / "maintained-source.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# External audit — maintained source",
        "",
        f"Raw findings retained: **{len(rows)}**",
        f"Maintained unresolved: **{len(unresolved)}**",
        f"Maintained reviewed false positives: **{len(reviewed)}**",
        "",
        "## Scope",
        "",
    ]
    for name, count in sorted(scoped.items()):
        lines.append(f"- `{name}`: {count}")
    if unresolved:
        lines += ["", "## Unresolved maintained findings", ""]
        for row in unresolved[:200]:
            lines.append(f"- `{row['source']}` `{row['rule']}` `{row['path']}:{row.get('line') or '?'}'` — {row['message']}")
    if reviewed:
        lines += ["", "## Reviewed false positives", ""]
        for row in reviewed:
            lines.append(f"- `{row['source']}` `{row['rule']}` `{row['path']}:{row.get('line') or '?'}'` — {row['review_reason']}")
    (root / "maintained-source.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        "FIELD_EXTERNAL_AUDIT_SCOPE "
        f"raw={len(rows)} maintained_unresolved={len(unresolved)} "
        f"maintained_reviewed={len(reviewed)} generated={scoped['generated']} "
        f"historical={scoped['historical']} evidence={scoped['evidence']}"
    )
    if args.strict and unresolved:
        raise SystemExit(f"external audit has {len(unresolved)} unresolved maintained-source findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
