#!/usr/bin/env python3
"""Provider v3 source-plan v5 local migration gate.

The old v4 helper was a one-shot migration that also knew about external provider
repositories. Provider v3 is now NiakVIO-owned: ordinary reconstruction must only
consume ProviderBase + durable NiakVIO DATA + owned Lego. This gate therefore
performs no network I/O and no external-repository pinning.

It also keeps the live fixture matrix semantically aligned before any reconstruction
starts (for example anime-specialized movie providers use an anime feature film,
not an unrelated live-action movie).
"""
from __future__ import annotations

import json
from pathlib import Path

import upgrade_provider_v3_fixture_selection_v1 as fixture_selection

ROOT = Path(__file__).resolve().parents[1]
BASE_STORE = ROOT / "scripts" / "provider_base_store.py"
SOURCES = ROOT / "sources.json"

REQUIRED_MARKERS = (
    "NIAKVIO_PROVIDER_BASE_SOURCE_PLAN_V4",
    "NIAKVIO_PROVIDER_BASE_RUNTIME_V5",
    "NIAKVIO_PROVIDER_BASE_RUNTIME_V6",
    "NIAKVIO_PROVIDER_BASE_RUNTIME_V7",
)


def main() -> int:
    fixture_changed = fixture_selection.patch()
    fixture_selection.validate()

    base_text = BASE_STORE.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_MARKERS if marker not in base_text]
    if missing:
        raise AssertionError("ProviderBase runtime/source-plan markers missing: " + ",".join(missing))

    config = json.loads(SOURCES.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise AssertionError("sources.json must be an object")
    upstreams = config.get("upstreams")
    if isinstance(upstreams, dict) and upstreams:
        raise AssertionError(
            "sources.json still contains external provider repositories; "
            "ordinary Provider v3 reconstruction must be NiakVIO-local"
        )

    serialized = json.dumps(config, ensure_ascii=False).casefold()
    forbidden = (
        "gowaru-nuvio-providers",
        "yoruix/nuvio-providers",
        "nuvioplugin/all-in-one-nuvio",
        "d3adlyrocket/all-in-one-nuvio",
    )
    leaked = [value for value in forbidden if value in serialized]
    if leaked:
        raise AssertionError("sources.json leaked external provider registry identifiers: " + ",".join(leaked))

    print(
        "PROVIDER_V3_SOURCE_PLAN_V5_LOCAL_OK "
        f"markers={len(REQUIRED_MARKERS)} externalProviderRepositories=0 network=0 "
        f"fixtureSelectionChanged={str(fixture_changed).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
