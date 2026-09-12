#!/usr/bin/env python3
"""Provider v3 source-plan v5 local migration gate.

Ordinary reconstruction consumes only NiakVIO-owned ProviderBase + durable DATA +
owned Core blocks. Before reconstruction, this gate also keeps fixtures semantically
aligned, prevents generic homepage responses from becoming media-type proof, wires
validated clean-v3 route data, hardens proof-v5 dataflow, and applies proven
provider-family/runtime migrations required by the current candidate.
"""
from __future__ import annotations

import json
from pathlib import Path

import upgrade_provider_v3_fixture_selection_v1 as fixture_selection
import upgrade_provider_v3_type_route_gate_v1 as type_route_gate
import upgrade_provider_v3_batch_routes_v1 as batch_routes
import upgrade_provider_v3_batch_routes_v2 as batch_routes_v2
import upgrade_route_proof_dataflow_safety_v2 as route_dataflow_safety
import upgrade_kehflix_terminal_domain_v1 as kehflix_terminal
import upgrade_signed_player_api_v1 as signed_player_api
import upgrade_provider_auxiliary_metadata_filter_v1 as auxiliary_metadata_filter
import upgrade_provider_terminal_media_block_v1 as terminal_media_block
import upgrade_provider_disabled_fast_advance_v1 as disabled_fast_advance
import upgrade_provider_adaptive_live_retry_v1 as adaptive_live_retry

ROOT = Path(__file__).resolve().parents[1]
BASE_STORE = ROOT / "scripts" / "provider_base_store.py"
SOURCES = ROOT / "sources.json"
PROOF = ROOT / "scripts" / "provider_route_proof.py"

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
    auxiliary_metadata_changed = auxiliary_metadata_filter.patch()
    auxiliary_metadata_filter.validate()
    terminal_media_block_changed = terminal_media_block.patch()
    terminal_media_block.validate()
    disabled_fast_advance_changed = disabled_fast_advance.patch()
    disabled_fast_advance.validate()
    adaptive_live_retry_changed = adaptive_live_retry.patch()
    adaptive_live_retry.validate()

    proof_text = PROOF.read_text(encoding="utf-8") if PROOF.is_file() else ""
    route_safety_changed = False
    if "PROVIDER_ROUTE_PROOF_REQUEST_SPEC_V1" in proof_text:
        route_safety_changed = route_dataflow_safety.patch_proof()
        route_safety_changed = route_dataflow_safety.patch_recovery() or route_safety_changed
        route_dataflow_safety.validate()

    overrides = kehflix_terminal.load(kehflix_terminal.OVERRIDES)
    knowledge = kehflix_terminal.load(kehflix_terminal.KNOWLEDGE)
    kehflix_overrides_changed = kehflix_terminal.patch_overrides(overrides)
    kehflix_knowledge_changed = kehflix_terminal.patch_knowledge(knowledge)
    kehflix_terminal.validate(overrides, knowledge)
    if kehflix_overrides_changed:
        kehflix_terminal.write(kehflix_terminal.OVERRIDES, overrides)
    if kehflix_knowledge_changed:
        kehflix_terminal.write(kehflix_terminal.KNOWLEDGE, knowledge)
    signed_player_changed = signed_player_api.patch()

    base_text = BASE_STORE.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_MARKERS if marker not in base_text]
    if missing:
        raise AssertionError("ProviderBase runtime/source-plan markers missing: " + ",".join(missing))
    if signed_player_api.MARKER not in base_text:
        raise AssertionError("signed-player runtime marker missing after migration")

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
        f"batchRoutesV2Changed={str(batch_routes_v2_changed).lower()} "
        f"auxiliaryMetadataChanged={str(auxiliary_metadata_changed).lower()} "
        f"terminalMediaBlockChanged={str(terminal_media_block_changed).lower()} "
        f"disabledFastAdvanceChanged={str(disabled_fast_advance_changed).lower()} "
        f"adaptiveLiveRetryChanged={str(adaptive_live_retry_changed).lower()} "
        f"routeSafetyChanged={str(route_safety_changed).lower()} "
        f"kehflixTerminalChanged={str(kehflix_overrides_changed or kehflix_knowledge_changed).lower()} "
        f"signedPlayerChanged={str(signed_player_changed).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
