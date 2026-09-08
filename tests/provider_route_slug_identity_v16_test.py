#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
proof_path = ROOT / "scripts" / "provider_route_proof.py"
spec = importlib.util.spec_from_file_location("provider_route_proof_v16_test", proof_path)
assert spec and spec.loader
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)

fixture = {
    "tmdbId": "95479",
    "mediaType": "anime",
    "title": "Example Anime",
    "season": 1,
    "episode": 1,
}
hints = [{"key": "slug", "value": "example-anime"}]
fetch = {
    "url": "https://provider.example/catalogue/example-anime/episodes/saison1",
    "final_url": "https://provider.example/catalogue/example-anime/episodes/saison1",
    "method": "GET",
    "proof_headers": {"accept": "text/html"},
    "body_kind": "none",
    "body_values": {},
}
route, meta = proof.derive_observed_route(fetch, {"fixture": fixture}, hints)

# V18 represented all provider-native values as {id}. V20 keeps exact response
# provenance and therefore preserves slug separately. The test remains valid on
# both pre-V20 and post-V20 owners because other workflows can execute it before
# the V20 migration is applied.
proof_text = proof_path.read_text(encoding="utf-8")
slug_typed = "NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20" in proof_text
expected_placeholder = "{slug}" if slug_typed else "{id}"
assert route == f"/catalogue/{expected_placeholder}/episodes/saison1", (route, meta)
assert meta.get("providerValueCorrelation") is True, meta
assert any(row.get("placeholder") == expected_placeholder for row in meta.get("substitutions") or []), meta

id_hints = [{"key": "id", "value": "abc123"}]
id_fetch = dict(fetch)
id_fetch["url"] = id_fetch["final_url"] = "https://provider.example/title/abc123"
id_route, id_meta = proof.derive_observed_route(id_fetch, {"fixture": fixture}, id_hints)
assert id_route == "/title/{id}", (id_route, id_meta)
assert any(row.get("placeholder") == "{id}" for row in id_meta.get("substitutions") or []), id_meta

print("provider route correlated identity placeholder tests passed")
