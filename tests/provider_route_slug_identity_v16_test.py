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
assert route == "/catalogue/{slug}/episodes/saison1", (route, meta)
assert meta.get("providerValueCorrelation") is True, meta
assert any(row.get("placeholder") == "{slug}" for row in meta.get("substitutions") or []), meta

id_hints = [{"key": "id", "value": "abc123"}]
id_fetch = dict(fetch)
id_fetch["url"] = id_fetch["final_url"] = "https://provider.example/title/abc123"
id_route, id_meta = proof.derive_observed_route(id_fetch, {"fixture": fixture}, id_hints)
assert id_route == "/title/{id}", (id_route, id_meta)
assert any(row.get("placeholder") == "{id}" for row in id_meta.get("substitutions") or []), id_meta

print("provider route slug identity v16 tests passed")
