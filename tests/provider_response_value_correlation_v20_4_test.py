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

proof = module.PROOF.read_text(encoding="utf-8")
base = module.BASE.read_text(encoding="utf-8")

namespace: dict[str, object] = {}
exec(
    "import re\n"
    "import urllib.parse\n"
    "def canonical(value): return str(value or '').strip().casefold()\n"
    "def unique(values, limit=256):\n"
    " out=[]\n"
    " for raw in values:\n"
    "  value=str(raw or '').strip()\n"
    "  if value and value not in out: out.append(value)\n"
    "  if len(out)>=limit: break\n"
    " return out\n"
    "PROVIDER_VALUE_KEYS={'id','slug'}\n"
    "BODY_TITLE_KEYS={'q','query','search','title','keyword','story','name'}\n"
    "BODY_SEASON_KEYS={'s','season','season_number','seasonid','season_id'}\n"
    "BODY_EPISODE_KEYS={'e','ep','episode','episode_number','episodeid','episode_id'}\n"
    "BODY_MEDIA_KEYS={'type','mediatype','media_type','media','category','kind'}\n"
    "BODY_TMDB_KEYS={'id','tmdb','tmdbid','tmdb_id','movie','tv'}\n"
    "BODY_YEAR_KEYS={'year','releaseyear','release_year'}\n"
    "SEMANTIC_TYPES={'movie','tv','anime'}\n"
    + proof[proof.index("def _request_scalar_placeholder("):proof.index("def derive_request_spec(")],
    namespace,
)
fixture = {
    "title": "Neutral Series",
    "aliases": ["Neutral-Series"],
    "tmdbId": "95479",
    "mediaType": "anime",
    "season": 1,
    "episode": 1,
}
helper = namespace["_urlencoded_text_body_spec"]
body, substitutions, residue = helper("query=Neutral%20Series&page=1", fixture, set())
assert residue == [], residue
assert body == {"query": "{query}", "page": "1"}, body

body, substitutions, residue = helper("query=Neutral%20Series%20Saison%201&page=1", fixture, set())
assert residue == [], residue
assert body == {"query": "{query} Saison {season}", "page": "1"}, body
assert any(row.get("placeholder") == "{query} Saison {season}" for row in substitutions), substitutions

body, substitutions, residue = helper("query=Neutral%20Series&opaque=Neutral%20Series", fixture, set())
assert body is None
assert any(row.get("location") == "body:opaque" for row in residue), residue

start = base.index("function _spv204ResponseProviderValues")
end = base.index("async function _resolveProviderValuePlan", start)
helper_js = base[start:end]
node = f'''
function _text(v) {{ return v == null ? "" : String(v); }}
function _spv20ProviderValuesFromJson() {{ return {{id:"", slug:""}}; }}
function _spv20ProviderValuesFromHtml() {{ return {{id:"catalog-slug", slug:"catalog-slug"}}; }}
{helper_js}
const html = '<a href="/?mode=0&trid=4711">A</a><a href="/?mode=1&trid=4711">B</a>';
const pair = _spv204ResponseProviderValues(html, 'https://example.invalid/', {{title:'Neutral Series'}});
process.stdout.write(JSON.stringify(pair));
'''
proc = subprocess.run(["node", "-e", node], check=True, capture_output=True, text=True)
pair = json.loads(proc.stdout)
assert pair["id"] == "4711", pair
assert pair["slug"] == "catalog-slug", pair

assert "let values = Object.assign({}, baseValues" in base
assert "providerId: nextProviderValues.id || values.providerId" in base
assert "providerSlug: nextProviderValues.slug || values.providerSlug" in base

print("provider response-value correlation V20.4 tests passed")
