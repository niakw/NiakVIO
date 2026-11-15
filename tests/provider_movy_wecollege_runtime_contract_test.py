#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))

from provider_patches.movy_wecollege_runtime_v1 import (  # noqa: E402
    DEFAULT_ENDPOINTS,
    MARKER,
    apply,
)
from register_movy_wecollege_runtime_v1 import (  # noqa: E402
    LEGO,
    MARKER as ORACLE_MARKER,
    apply_document,
    validate_document,
)

assert [x["path"] for x in DEFAULT_ENDPOINTS] == [
    "miami/sources",
    "boise/sources",
    "nashville/sources",
]

fixture = {
    "provider_patches": {
        "movy": {
            "notes": [],
            "learned_routes": ["/movie/{tmdbId}", "/tv/{tmdbId}"],
        }
    },
    "provider_capabilities": {"movy": {}},
}
assert apply_document(fixture) is True
validate_document(fixture)
row = fixture["provider_patches"]["movy"]
assert LEGO in row["provider_lego_scripts"]
assert row["capability"] == "api_stream_resolver"
assert row["official_api"] == "https://api.wecollege.net"
assert row["identity_input"]["requires_tmdb_before_run"] is True
assert "imdbId" in row["identity_input"]["required_fields"]
assert ORACLE_MARKER in json.dumps(row)

# Verify the provider Lego renders the shared family rather than embedding a
# one-title fixture or a captured terminal URL.
base = """/* STARTFIX:PROVIDER.MOVY.WECOLLEGE.WINGS.V1 */\n/* CLOSEFIX:PROVIDER.MOVY.WECOLLEGE.WINGS.V1 */\n"""
rendered = apply(base)
assert MARKER in rendered
assert "https://api.wecollege.net" in rendered
assert "miami/sources" in rendered
assert "boise/sources" in rendered
assert "nashville/sources" in rendered
assert '"doubleEncodeTitle":true' in rendered
assert "401905" not in rendered
assert "213375" not in rendered
assert "goldenkite.top" not in rendered
assert "warmsquare.top" not in rendered

print("MOVY_WECOLLEGE_RUNTIME_CONTRACT_OK family=wings-v1 endpoints=3 fixtures=0")
