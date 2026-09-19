#!/usr/bin/env python3
"""Build the consolidated external-audit status files."""

from __future__ import annotations

import datetime
import json
import os
import pathlib

root = pathlib.Path(os.environ.get("OUT", "audit/ai-external"))
root.mkdir(parents=True, exist_ok=True)

statuses = []
for name in ("sonar", "deepsource", "codescene"):
    try:
        statuses.append(
            json.loads((root / name / "status.json").read_text(encoding="utf-8"))
        )
    except Exception:
        statuses.append(
            {"source": name, "ok": False, "errors": ["status unavailable"]}
        )

lines = [
    "# External code-audit status",
    "",
    f"Generated from `{os.environ.get('REPO_SLUG', 'niakw/NiakVIO')}` at commit `{os.environ.get('AUDITED_SHA', '')}`.",
    "",
    "| Source | Status | Findings/files | Access | Notes |",
    "|---|---:|---:|---|---|",
]

for status in statuses:
    count = status.get("finding_count", status.get("file_count", "—"))
    notes = "; ".join(status.get("errors") or []) or "OK"
    lines.append(
        f"| {status.get('source', '?')} | "
        f"{'OK' if status.get('ok') else 'PARTIAL/ERROR'} | "
        f"{count} | {status.get('access_mode', '?')} | {notes} |"
    )

lines.extend(
    [
        "",
        "## AI reading order",
        "",
        "1. Read `STATUS.md`.",
        "2. Read each source `summary.md` when available.",
        "3. Open raw JSON/text for exact fields/context.",
        "",
        "> Evidence only: no external autofix is applied automatically.",
    ]
)
(root / "STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

manifest = {
    "repository": os.environ.get("REPO_SLUG", "niakw/NiakVIO"),
    "sha": os.environ.get("AUDITED_SHA"),
    "run_id": os.environ.get("GITHUB_RUN_ID"),
    "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
(root / "manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)
