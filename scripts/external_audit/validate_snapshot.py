#!/usr/bin/env python3
"""Fail closed unless every external audit export is complete and exact-SHA fresh."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("OUT", "audit/ai-external"))
TARGET = os.environ.get("AUDITED_SHA", "").strip()
SOURCES = ("sonar", "deepsource", "codescene")
REQUIRED_FILES = {
    "sonar": ("status.json", "issues.json", "analyses.json"),
    "deepsource": ("status.json", "findings.json"),
    "codescene": ("status.json", "analysis-latest.json", "files.json"),
}


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid or missing JSON: {path}: {type(exc).__name__}") from exc


def main() -> int:
    errors: list[str] = []
    if not TARGET:
        errors.append("AUDITED_SHA is empty")

    refresh_path = ROOT / "refresh-request.json"
    try:
        refresh = load(refresh_path)
    except ValueError as exc:
        refresh = {}
        errors.append(str(exc))

    refresh_target = str(refresh.get("target_sha") or "") if isinstance(refresh, dict) else ""
    if TARGET and refresh_target != TARGET:
        errors.append(f"refresh target mismatch expected={TARGET} actual={refresh_target or 'missing'}")
    services = refresh.get("services") if isinstance(refresh, dict) else {}
    if not isinstance(services, dict):
        services = {}
        errors.append("refresh-request services must be an object")

    status_summary: list[str] = []
    for source in SOURCES:
        service = services.get(source) if isinstance(services.get(source), dict) else {}
        fresh = service.get("fresh") is True
        latest_sha = str(service.get("latest_sha") or service.get("repository_latest_sha_after") or "")
        if not fresh:
            errors.append(
                f"{source}: external analysis is not fresh for target {TARGET}; "
                f"latest={latest_sha or 'unknown'} notes={service.get('notes') or []}"
            )

        status_path = ROOT / source / "status.json"
        try:
            status = load(status_path)
        except ValueError as exc:
            status = {}
            errors.append(str(exc))
        if not isinstance(status, dict) or status.get("ok") is not True:
            errors.append(f"{source}: exporter status is not ok: {status.get('errors') if isinstance(status, dict) else status}")

        for name in REQUIRED_FILES[source]:
            path = ROOT / source / name
            if not path.is_file() or path.stat().st_size < 3:
                errors.append(f"{source}: required export missing/empty: {name}")

        count = status.get("finding_count", status.get("file_count", "?")) if isinstance(status, dict) else "?"
        status_summary.append(f"{source}:fresh={str(fresh).lower()}:count={count}")

    print("FIELD_EXTERNAL_AUDIT_SNAPSHOT " + " ".join(status_summary) + f" target={TARGET or 'missing'}")
    if errors:
        raise SystemExit("external audit snapshot invalid:\n" + "\n".join(f"- {item}" for item in errors))
    print("FIELD_EXTERNAL_AUDIT_SNAPSHOT_OK true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
