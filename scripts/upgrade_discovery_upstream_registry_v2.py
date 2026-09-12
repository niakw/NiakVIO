#!/usr/bin/env python3
"""Migrate candidate discovery to the authoritative provider upstream registry.

`sources.json` is the NiakVIO catalogue/policy document and no longer owns external
provider repository declarations. Those declarations live in
`engine_v2/config/provider-upstreams.json`. The discovery path must compose both
sources instead of assuming the historical `sources.json['upstreams']` shape.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "discover_candidates.py"
MARKER = "NIAKVIO_DISCOVERY_AUTHORITATIVE_UPSTREAM_REGISTRY_V2"

OLD_CONST = 'SOURCES_PATH = ROOT / "sources.json"\nDEFAULT_STAGE = ROOT / "staging"\n'
NEW_CONST = 'SOURCES_PATH = ROOT / "sources.json"\nUPSTREAMS_PATH = ROOT / "engine_v2" / "config" / "provider-upstreams.json"\nDEFAULT_STAGE = ROOT / "staging"\n'

OLD_LOAD = '    config = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))\n    exclusions = config.get("exclusions", {})\n'
NEW_LOAD = '    config = load_discovery_config()\n    exclusions = config.get("exclusions", {})\n'

ANCHOR = '''def load_manifest_snapshot'''
HELPER = '''# NIAKVIO_DISCOVERY_AUTHORITATIVE_UPSTREAM_REGISTRY_V2\ndef load_discovery_config() -> dict[str, Any]:\n    \"\"\"Compose local policy/exclusions with the current external registry.\n\n    External repositories are knowledge inputs only. This adapter intentionally\n    converts the authoritative list schema into the historical `manifest_urls`\n    shape consumed by the bounded discovery code without restoring upstream\n    ownership to `sources.json`.\n    \"\"\"\n    policy = json.loads(SOURCES_PATH.read_text(encoding=\"utf-8\"))\n    registry = json.loads(UPSTREAMS_PATH.read_text(encoding=\"utf-8\"))\n    rows = registry.get(\"upstreams\") if isinstance(registry, dict) else []\n    if not isinstance(rows, list):\n        raise ValueError(\"provider-upstreams.json: upstreams list required\")\n\n    upstreams: dict[str, dict[str, Any]] = {}\n    for row in rows:\n        if not isinstance(row, dict):\n            continue\n        source_id = str(row.get(\"id\") or \"\").strip()\n        if not source_id:\n            continue\n        branch = str(row.get(\"branch\") or \"main\").strip() or \"main\"\n        manifest = str(row.get(\"manifest\") or \"manifest.json\").strip().lstrip(\"/\") or \"manifest.json\"\n        repositories = []\n        for key in (\"repository\", \"fallback_repository\"):\n            repository = str(row.get(key) or \"\").strip().strip(\"/\")\n            if repository and repository not in repositories:\n                repositories.append(repository)\n        if not repositories:\n            raise ValueError(f\"provider-upstreams.json: {source_id} has no repository\")\n        upstreams[source_id] = {\n            \"manifest_urls\": [\n                f\"https://raw.githubusercontent.com/{repository}/{branch}/{manifest}\"\n                for repository in repositories\n            ],\n            \"repository\": repositories[0],\n            \"fallback_repository\": repositories[1] if len(repositories) > 1 else None,\n            \"branch\": branch,\n            \"manifest\": manifest,\n        }\n\n    if not upstreams:\n        raise ValueError(\"provider-upstreams.json: no usable upstreams\")\n    exclusions = policy.get(\"exclusions\") if isinstance(policy, dict) else {}\n    return {\n        \"exclusions\": exclusions if isinstance(exclusions, dict) else {},\n        \"upstreams\": upstreams,\n    }\n\n\ndef load_manifest_snapshot'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    before = text
    if "UPSTREAMS_PATH =" not in text:
        if OLD_CONST not in text:
            raise AssertionError("discovery constants anchor missing")
        text = text.replace(OLD_CONST, NEW_CONST, 1)
    if MARKER not in text:
        if ANCHOR not in text:
            raise AssertionError("discovery helper anchor missing")
        text = text.replace(ANCHOR, HELPER, 1)
    if OLD_LOAD in text:
        text = text.replace(OLD_LOAD, NEW_LOAD, 1)
    elif NEW_LOAD not in text:
        raise AssertionError("discovery config load anchor missing")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return text != before


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        'UPSTREAMS_PATH = ROOT / "engine_v2" / "config" / "provider-upstreams.json"',
        'registry.get("upstreams")',
        'for key in ("repository", "fallback_repository")',
        '"https://raw.githubusercontent.com/{repository}/{branch}/{manifest}"',
        'config = load_discovery_config()',
    ):
        if needle not in value:
            raise AssertionError(f"discovery upstream V2 missing {needle}")
    if 'config = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))\n    exclusions = config.get("exclusions", {})' in value:
        raise AssertionError("legacy sources.json upstream load remains active")


def main() -> int:
    changed = patch()
    print(f"DISCOVERY_UPSTREAM_REGISTRY_V2_OK changed={str(changed).lower()} authoritative=engine_v2/config/provider-upstreams.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
