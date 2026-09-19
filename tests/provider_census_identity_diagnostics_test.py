#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_provider_quick_yield import _identity_diagnostics, classify_debug_stage

probe={"streams":[{
    "row":{"url":"https://cdn.example/video.mkv?token=secret","title":"The Colony","filename":"The.Colony.AKA.Tides.2021.mkv"},
    "media":{"kind":"matroska","status":206,"error":None},
    "identity":{"status":"contradiction","reason":"fixture_duration_mismatch"},
    "metadata_identity":{"status":"match","reason":"expected_title_alias"},
    "duration_identity":{"status":"contradiction","reason":"fixture_duration_mismatch","ratio":0.4},
}]}
rows=_identity_diagnostics(probe)
assert rows==[{
    "host":"cdn.example",
    "title":"The Colony",
    "filename":"The.Colony.AKA.Tides.2021.mkv",
    "identity_status":"contradiction",
    "identity_reason":"fixture_duration_mismatch",
    "metadata_status":"match",
    "metadata_reason":"expected_title_alias",
    "duration_status":"contradiction",
    "duration_reason":"fixture_duration_mismatch",
    "duration_ratio":0.4,
    "media_kind":"matroska",
    "media_status":206,
    "media_error":"",
}]
assert "token=secret" not in repr(rows)
# Network classification is causal: an incidental failure before a later
# successful provider request must not poison the entire probe.
debug_mixed_http={
    "model":{"supported_types":["movie"],"has_api_recipe":False,"route_count":1,"source_runtime_family":"catalogue-html"},
    "fetches":[
        {"url":"https://provider.example/optional-asset","status":404},
        {"url":"https://provider.example/detail","status":200},
    ],
}
assert classify_debug_stage(task,probe_zero,debug_mixed_http)=="provider_network_zero_result"

debug_mixed_exception={
    "model":{"supported_types":["movie"],"has_api_recipe":False,"route_count":1,"source_runtime_family":"catalogue-html"},
    "fetches":[
        {"url":"https://old-alias.example/search","status":0,"error":"TypeError"},
        {"url":"https://provider.example/search","status":200},
    ],
}
assert classify_debug_stage(task,probe_zero,debug_mixed_exception)=="provider_network_zero_result"

debug_terminal_http={
    "model":{"supported_types":["movie"],"has_api_recipe":False,"route_count":1,"source_runtime_family":"catalogue-html"},
    "fetches":[
        {"url":"https://provider.example/search","status":200},
        {"url":"https://provider.example/player","status":403},
    ],
}
assert classify_debug_stage(task,probe_zero,debug_terminal_http)=="provider_network_http_error"

debug_terminal_exception={
    "model":{"supported_types":["movie"],"has_api_recipe":False,"route_count":1,"source_runtime_family":"catalogue-html"},
    "fetches":[
        {"url":"https://provider.example/search","status":200},
        {"url":"https://provider.example/player","status":0,"error":"AbortError"},
    ],
}
assert classify_debug_stage(task,probe_zero,debug_terminal_exception)=="provider_network_exception"

probe_source=(ROOT/"scripts/nuvio_tv_probe_tmdb_ci.cjs").read_text(encoding="utf-8")
assert "const terminal = meaningful[meaningful.length - 1]" in probe_source
assert "providerFetches.some((row) => Number(row.status) >= 400)" not in probe_source
assert "providerFetches.some((row) => row.error)" not in probe_source

print("provider census identity diagnostics passed")


# A provider-local Lego may execute even when the reconstructed static DATA has
# no generic route. Once provider HTTP actually happened, the diagnostic must
# report the network outcome instead of mislabelling it as a pre-network gate.
task={"semantic_type":"movie"}
probe_zero={"raw_stream_count":0,"identity_contradiction_count":0}
debug_http={
    "model":{"supported_types":["movie"],"has_api_recipe":False,"route_count":0,"source_runtime_family":"catalogue-html"},
    "fetches":[{"url":"https://provider.example/search?q=x","status":403}],
}
assert classify_debug_stage(task,probe_zero,debug_http)=="provider_network_http_error"

debug_none={
    "model":{"supported_types":["movie"],"has_api_recipe":False,"route_count":0,"source_runtime_family":"catalogue-html"},
    "fetches":[],
}
assert classify_debug_stage(task,probe_zero,debug_none)=="gate_runtime_plan_missing"
