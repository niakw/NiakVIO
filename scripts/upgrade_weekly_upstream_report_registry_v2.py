#!/usr/bin/env python3
"""Migrate weekly upstream reporting to the authoritative upstream registry."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "report_new_upstream_providers.py"
MARKER = "NIAKVIO_WEEKLY_REPORT_AUTHORITATIVE_UPSTREAM_REGISTRY_V2"

OLD_ROOT = 'ROOT = Path(__file__).resolve().parents[1]\n'
NEW_ROOT = 'ROOT = Path(__file__).resolve().parents[1]\nUPSTREAMS_PATH = ROOT / "engine_v2" / "config" / "provider-upstreams.json"\n'

OLD_BUILD = '''def build_report(stage: dict[str, Any], catalog: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:\n    upstreams = sources.get("upstreams") if isinstance(sources.get("upstreams"), dict) else {}\n    allowed_sources = set(upstreams)\n    if len(allowed_sources) != 3:\n        raise ValueError(f"expected exactly 3 configured upstream repositories, got {len(allowed_sources)}")\n'''
NEW_BUILD = '''# NIAKVIO_WEEKLY_REPORT_AUTHORITATIVE_UPSTREAM_REGISTRY_V2\ndef authoritative_upstreams() -> dict[str, dict[str, Any]]:\n    registry = load_json(UPSTREAMS_PATH)\n    rows = registry.get("upstreams") if isinstance(registry.get("upstreams"), list) else []\n    upstreams: dict[str, dict[str, Any]] = {}\n    for row in rows:\n        if not isinstance(row, dict):\n            continue\n        source_id = str(row.get("id") or "").strip()\n        repository = str(row.get("repository") or "").strip().strip("/")\n        if not source_id or not repository:\n            continue\n        upstreams[source_id] = {\n            "repository": repository,\n            "fallback_repository": str(row.get("fallback_repository") or "").strip().strip("/") or None,\n            "branch": str(row.get("branch") or "main").strip() or "main",\n            "manifest": str(row.get("manifest") or "manifest.json").strip().lstrip("/") or "manifest.json",\n        }\n    if len(upstreams) != 3:\n        raise ValueError(f"expected exactly 3 configured upstream repositories, got {len(upstreams)}")\n    return upstreams\n\n\ndef build_report(stage: dict[str, Any], catalog: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:\n    # `sources` remains policy/exclusion input only. External repository ownership\n    # lives exclusively in engine_v2/config/provider-upstreams.json.\n    _ = sources\n    upstreams = authoritative_upstreams()\n    allowed_sources = set(upstreams)\n'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    before = text
    if "UPSTREAMS_PATH =" not in text:
        if OLD_ROOT not in text:
            raise AssertionError("weekly report ROOT anchor missing")
        text = text.replace(OLD_ROOT, NEW_ROOT, 1)
    if MARKER not in text:
        if text.count(OLD_BUILD) != 1:
            raise AssertionError(f"weekly report build anchor count={text.count(OLD_BUILD)}")
        text = text.replace(OLD_BUILD, NEW_BUILD, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return text != before


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        'UPSTREAMS_PATH = ROOT / "engine_v2" / "config" / "provider-upstreams.json"',
        "def authoritative_upstreams()",
        'registry.get("upstreams")',
        'upstreams = authoritative_upstreams()',
        '"fallback_repository"',
    ):
        if needle not in value:
            raise AssertionError(f"weekly report registry V2 missing {needle}")
    if 'upstreams = sources.get("upstreams")' in value:
        raise AssertionError("weekly report still treats sources.json as upstream authority")


def main() -> int:
    changed = patch()
    print(f"WEEKLY_REPORT_REGISTRY_V2_OK changed={str(changed).lower()} authoritative=engine_v2/config/provider-upstreams.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
