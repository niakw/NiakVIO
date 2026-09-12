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

ANCHOR = 'def decode_static_obfuscated_strings(text: str) -> list[str]:\n'
HELPER = '''# NIAKVIO_DISCOVERY_AUTHORITATIVE_UPSTREAM_REGISTRY_V2\ndef load_discovery_config() -> dict[str, Any]:
    """Compose local policy/exclusions with the current external registry.

    External repositories are knowledge inputs only. This adapter intentionally
    converts the authoritative list schema into the historical `manifest_urls`
    shape consumed by the bounded discovery code without restoring upstream
    ownership to `sources.json`.
    """
    policy = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    registry = json.loads(UPSTREAMS_PATH.read_text(encoding="utf-8"))
    rows = registry.get("upstreams") if isinstance(registry, dict) else []
    if not isinstance(rows, list):
        raise ValueError("provider-upstreams.json: upstreams list required")

    upstreams: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("id") or "").strip()
        if not source_id:
            continue
        branch = str(row.get("branch") or "main").strip() or "main"
        manifest = str(row.get("manifest") or "manifest.json").strip().lstrip("/") or "manifest.json"
        repositories = []
        for key in ("repository", "fallback_repository"):
            repository = str(row.get(key) or "").strip().strip("/")
            if repository and repository not in repositories:
                repositories.append(repository)
        if not repositories:
            raise ValueError(f"provider-upstreams.json: {source_id} has no repository")
        upstreams[source_id] = {
            "manifest_urls": [
                f"https://raw.githubusercontent.com/{repository}/{branch}/{manifest}"
                for repository in repositories
            ],
            "repository": repositories[0],
            "fallback_repository": repositories[1] if len(repositories) > 1 else None,
            "branch": branch,
            "manifest": manifest,
        }

    if not upstreams:
        raise ValueError("provider-upstreams.json: no usable upstreams")
    exclusions = policy.get("exclusions") if isinstance(policy, dict) else {}
    return {
        "exclusions": exclusions if isinstance(exclusions, dict) else {},
        "upstreams": upstreams,
    }


def decode_static_obfuscated_strings(text: str) -> list[str]:
'''


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
        'f"https://raw.githubusercontent.com/{repository}/{branch}/{manifest}"',
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
