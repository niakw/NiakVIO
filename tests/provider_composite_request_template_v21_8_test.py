#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "upgrade_provider_composite_request_template_v21_8.py"

spec = importlib.util.spec_from_file_location("v218", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.patch_worker(); module.patch_proof(); module.patch_recovery(); module.patch_materializer(); module.patch_base()
module.validate_worker(); module.validate_proof(); module.validate_recovery(); module.validate_materializer(); module.validate_base()

# Reload the actually patched proof module.
proof_spec = importlib.util.spec_from_file_location("proof_v218", module.PROOF)
assert proof_spec is not None and proof_spec.loader is not None
proof = importlib.util.module_from_spec(proof_spec)
proof_spec.loader.exec_module(proof)

movie_fixture = {
    "tmdbId": 123,
    "title": "Sample Film",
    "year": 2024,
    "mediaType": "movie",
}
movie_fetch = {
    "method": "POST",
    "body_kind": "json",
    "body_values": {"q": "Sample.Film.2024"},
    "proof_headers": {"Content-Type": "application/json"},
}
movie_spec, movie_meta = proof.derive_request_spec(movie_fetch, {"fixture": movie_fixture})
assert movie_meta["requestSpecReusable"] is True, movie_meta
assert movie_spec is not None
assert movie_spec["body"]["q"] == "{queryDots}.{year}", movie_spec

series_fixture = {
    "tmdbId": 456,
    "title": "Sample Show",
    "year": 2020,
    "mediaType": "tv",
    "season": 1,
    "episode": 2,
}
series_fetch = {
    "method": "POST",
    "body_kind": "form",
    "body_values": {"q": "Sample.Show.S01E02", "page_index": 0},
    "proof_headers": {},
}
series_spec, series_meta = proof.derive_request_spec(series_fetch, {"fixture": series_fixture})
assert series_meta["requestSpecReusable"] is True, series_meta
assert series_spec is not None
assert series_spec["body"]["q"] == "{queryDots}.S{season2}E{episode2}", series_spec

# A close but wrong episode identity must not be frozen as static executable DATA.
wrong_fetch = {
    "method": "POST",
    "body_kind": "json",
    "body_values": {"q": "Sample.Show.S99E99"},
    "proof_headers": {},
}
wrong_spec, wrong_meta = proof.derive_request_spec(wrong_fetch, {"fixture": series_fixture})
assert wrong_spec is None, wrong_spec
assert wrong_meta["requestSpecReusable"] is False, wrong_meta
assert any(row.get("location") == "body:q" for row in wrong_meta["requestSpecResidue"]), wrong_meta

# Redacted/session material stays fail-closed even when the title query itself is deterministic.
redacted_fetch = {
    "method": "POST",
    "body_kind": "form",
    "body_values": {"q": "Sample.Show.S01E02", "page_token": "<redacted>"},
    "proof_headers": {},
}
redacted_spec, redacted_meta = proof.derive_request_spec(redacted_fetch, {"fixture": series_fixture})
assert redacted_spec is None, redacted_spec
assert redacted_meta["requestSpecReusable"] is False, redacted_meta
assert any(row.get("location") == "body:page_token" for row in redacted_meta["requestSpecResidue"]), redacted_meta

# Exercise the actual patched JavaScript scalar expander, not a Python reimplementation.
base = module.BASE.read_text(encoding="utf-8")
start = base.index("function _recipeExpandScalar(value, values) {")
end = base.index("function _recipeExpandObject", start)
helper = base[start:end]
js = r'''
function _text(value) { return value == null ? "" : String(value); }
''' + helper + r'''
const values = {query:"Sample Film", year:"2024", season:1, episode:2, providerId:"", tmdbId:"123", media:"movie", source:null};
console.log(JSON.stringify([
  _recipeExpandScalar("{queryDots}.{year}", values),
  _recipeExpandScalar("{queryDots}.S{season2}E{episode2}", values)
]));
'''
proc = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True, check=True)
expanded = json.loads(proc.stdout.strip())
assert expanded == ["Sample.Film.2024", "Sample.Film.S01E02"], expanded

# Recovery must treat the new composite placeholders as search identity.
recovery = module.RECOVERY.read_text(encoding="utf-8")
assert '"{queryDots}"' in recovery
assert "ROUTE_RECOVERY_COMPOSITE_SEARCH_TEMPLATE_V21_8" in recovery

print("provider composite request template V21.8 tests passed")
