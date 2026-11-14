#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))
PATCH = ROOT / "scripts/provider_patches/webflix_runtime_v1.py"

spec = importlib.util.spec_from_file_location("webflix_runtime_v1", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = '"use strict";\nmodule.exports={getStreams:async()=>[]};\n'
patched = module.apply(source, {"base": "https://webflix.art"})

for required in (
    "NIAKVIO_WEBFLIX_RUNTIME_V1",
    "/api/fastflux?type=movie&tmdb_id=",
    "/api/series-season-discovery?tmdb_id=",
    "/api/fastflux?type=episode&tmdb_id=",
    "discovery.tmdb_id",
    "Number(row.season)===q.season",
    "Number(row.episode)===q.episode",
    "__niakvioWebflixRuntimeV1",
):
    assert required in patched, required

for forbidden in (
    "capsolver",
    "2captcha",
    "turnstile",
    "157336",
    "1396",
    "interstellar",
    "breaking-bad",
):
    assert forbidden not in patched.casefold(), forbidden

overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
patch = overrides["provider_patches"]["webflix"]
assert patch["capability"] == "api_stream_resolver"
assert patch["provider_lego_scripts"] == ["scripts/provider_patches/webflix_runtime_v1.py"]
assert patch["identity_input"]["mode"] == "tmdb_direct"
routes = patch["learned_routes"]
assert len(routes) == 3
assert all("{tmdbId}" in route for route in routes)

print("WEBFLIX_RUNTIME_CONTRACT_OK routes=3 challenge_solver=false")


for required in (
    "/api/player-embed/vidzy-path?kind=movie&tmdbId=",
    "/api/v/z/",
    "Webflix - Vidzy",
    "direct-mp4-or-tmdb-signed-vidzy-hls",
):
    assert required in text, required
