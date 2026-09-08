#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_response_value_correlation_v20_4.py"

spec = importlib.util.spec_from_file_location("v204", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V20.4 migration")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.patch_worker()
module.patch_proof()
module.patch_recovery()
module.patch_materializer()
module.patch_base()
module.validate_worker()
module.validate_proof()
module.validate_recovery()
module.validate_materializer()
module.validate_base()

proof_spec = importlib.util.spec_from_file_location("provider_route_proof_v204_test", module.PROOF)
if proof_spec is None or proof_spec.loader is None:
    raise SystemExit("unable to load patched provider_route_proof")
proof = importlib.util.module_from_spec(proof_spec)
proof_spec.loader.exec_module(proof)

fixture = {
    "title": "Neutral Series",
    "aliases": ["Neutral-Series"],
    "tmdbId": "95479",
    "mediaType": "anime",
    "season": 1,
    "episode": 1,
    "year": 2020,
}
task = {"fixture": fixture}

form_fetch = {
    "method": "POST",
    "body_kind": "form",
    "body_values": {"query": "Neutral Series", "page": "1"},
    "proof_headers": {"content-type": "application/x-www-form-urlencoded"},
}
form_spec, form_meta = proof.derive_request_spec(form_fetch, task, [])
assert form_meta["requestSpecReusable"] is True, form_meta
assert form_spec["bodyKind"] == "form", form_spec
assert form_spec["body"] == {"query": "{query}", "page": "1"}, form_spec

season_form = dict(form_fetch)
season_form["body_values"] = {"query": "Neutral Series Saison 1", "page": "1"}
season_spec, season_meta = proof.derive_request_spec(season_form, task, [])
assert season_meta["requestSpecReusable"] is True, season_meta
assert season_spec["body"] == {"query": "{query} Saison {season}", "page": "1"}, season_spec

body, substitutions, residue = proof._urlencoded_text_body_spec(
    "query=Neutral%20Series%20Saison%201&page=1", fixture, set()
)
assert residue == [], residue
assert body == {"query": "{query} Saison {season}", "page": "1"}, body
assert any(row.get("placeholder") == "{query} Saison {season}" for row in substitutions), substitutions

unsafe_fetch = dict(form_fetch)
unsafe_fetch["body_values"] = {"query": "Neutral Series", "opaque": "Neutral Series"}
unsafe_spec, unsafe_meta = proof.derive_request_spec(unsafe_fetch, task, [])
assert unsafe_spec is None
assert any(row.get("location") == "body:opaque" for row in unsafe_meta["requestSpecResidue"]), unsafe_meta

episode_fetch = {
    "url": "https://example.invalid/episode/neutral-series-1-episode-1/",
    "final_url": "https://example.invalid/episode/neutral-series-1-episode-1/",
    "method": "GET",
    "body_kind": "none",
    "body_values": {},
    "proof_headers": {},
}
route, route_meta = proof.derive_observed_route(
    episode_fetch,
    task,
    [{"key": "slug", "value": "neutral-series"}],
)
assert route == "/episode/{slug}-{season}-episode-{episode}/", (route, route_meta)
assert route_meta["providerValueCorrelation"] is True, route_meta
assert route_meta["reusable"] is True, route_meta

base = module.BASE.read_text(encoding="utf-8")
start = base.index("function _spv204ResponseProviderValues")
end = base.index("async function _resolveProviderValuePlan", start)
helper_js = base[start:end]
node = f'''
function _text(v) {{ return v == null ? "" : String(v); }}
function _spv20ProviderValuesFromJson() {{ return {{id:"", slug:""}}; }}
function _spv20ProviderValuesFromHtml() {{ return {{id:"catalog-slug", slug:"catalog-slug"}}; }}
{helper_js}
const html = '<iframe src="/?trembed=0&trid=4711&trtype=2"></iframe>' +
             '<iframe src="/?trembed=1&trid=4711&trtype=2"></iframe>';
const pair = _spv204ResponseProviderValues(html, 'https://example.invalid/', {{title:'Neutral Series'}});
process.stdout.write(JSON.stringify(pair));
'''
proc = subprocess.run(["node", "-e", node], check=True, capture_output=True, text=True)
pair = json.loads(proc.stdout)
assert pair["id"] == "4711", pair
assert pair["slug"] == "catalog-slug", pair

recovery = module.RECOVERY.read_text(encoding="utf-8")
assert module.RECOVERY_MARKER in recovery
assert '"requestSpecResidue": copy.deepcopy' in recovery
assert '"proofBodyValues": copy.deepcopy(fetch.get("body_values") or {})' in recovery

assert "let values = Object.assign({}, baseValues" in base
assert "providerId: nextProviderValues.id || values.providerId" in base
assert "providerSlug: nextProviderValues.slug || values.providerSlug" in base

print("provider response-value correlation V20.4 tests passed")
