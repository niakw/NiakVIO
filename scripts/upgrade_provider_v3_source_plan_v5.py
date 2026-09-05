#!/usr/bin/env python3
"""Provider v3 source-plan v5 local migration gate.

Ordinary reconstruction consumes only NiakVIO-owned ProviderBase + durable DATA +
owned Lego. Before reconstruction, this gate also keeps fixtures semantically
aligned, prevents generic homepage responses from becoming media-type proof, and
wires validated clean-v3 route Lego/current route DATA for the active batches.
"""
from __future__ import annotations

import json
from pathlib import Path

import upgrade_provider_v3_fixture_selection_v1 as fixture_selection
import upgrade_provider_v3_type_route_gate_v1 as type_route_gate
import upgrade_provider_v3_batch_routes_v1 as batch_routes
import upgrade_provider_v3_batch_routes_v2 as batch_routes_v2

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
    type_gate_changed = type_route_gate.patch()
    type_route_gate.validate()
    batch_routes_changed = batch_routes.patch()
    batch_routes.validate()
    batch_routes_v2_changed = batch_routes_v2.patch()
    batch_routes_v2.validate()

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
            "sources.json still contains external provider repositories; ordinary Provider v3 reconstruction must be NiakVIO-local"
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
        f"fixtureSelectionChanged={str(fixture_changed).lower()} "
        f"typeRouteGateChanged={str(type_gate_changed).lower()} "
        f"batchRoutesChanged={str(batch_routes_changed).lower()} "
        f"batchRoutesV2Changed={str(batch_routes_v2_changed).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
