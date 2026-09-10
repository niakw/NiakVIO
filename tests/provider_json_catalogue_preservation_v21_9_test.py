#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_json_catalogue_preservation_v21_9.py"

spec = importlib.util.spec_from_file_location("v219", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V21.9 migration")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.patch_base()
module.validate_base()
base = module.BASE.read_text(encoding="utf-8")

start = base.index("function _spv219JsonProviderValues")
end = base.index("function _spv215CatalogueProviderValues", start)
helper_js = base[start:end]

node = f'''
function _spv4JsonRows(v) {{
  if (Array.isArray(v)) return v;
  if (v && Array.isArray(v.results)) return v.results;
  return v && typeof v === "object" ? [v] : [];
}}
function _spv4Scalar(v) {{ return v == null ? "" : String(v); }}
function _spv211CandidateIdentityScore(label, href, meta) {{
  const norm = x => String(x || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  return norm(label) === norm(meta && meta.title) ? 200 : 0;
}}
function _spv211ProviderIdAllowed(key, value) {{
  return /^(?:id|ID|_id|media_id|post_id|anime_id|movie_id|series_id|show_id)$/.test(String(key || "")) && /^[A-Za-z0-9._~-]{{1,160}}$/.test(String(value || ""));
}}
{helper_js}
const slugOnly = _spv219JsonProviderValues(
  {{results:[{{anime:"Neutral Series",slug:"neutral-series"}}]}},
  {{title:"Neutral Series"}}, 1, "tv"
);
const both = _spv219JsonProviderValues(
  {{results:[{{title:"Neutral Movie",id:"4711",slug:"neutral-movie"}}]}},
  {{title:"Neutral Movie"}}, 1, "movie"
);
const unrelated = _spv219JsonProviderValues(
  {{results:[{{title:"Other Work",id:"999",slug:"other-work"}}]}},
  {{title:"Neutral Movie"}}, 1, "movie"
);
process.stdout.write(JSON.stringify({{slugOnly,both,unrelated}}));
'''
proc = subprocess.run(["node", "-e", node], check=True, capture_output=True, text=True)
result = json.loads(proc.stdout)
assert result["slugOnly"] == {"id": "", "slug": "neutral-series"}, result
assert result["both"] == {"id": "4711", "slug": "neutral-movie"}, result
assert result["unrelated"] == {"id": "", "slug": ""}, result

resolver_start = base.index("async function _resolveProviderValuePlan")
resolver_end = base.index("async function _resolveSearchRequestPlan", resolver_start)
resolver = base[resolver_start:resolver_end]
assert "providerValues = _spv219JsonProviderValues(JSON.parse(rawSearchValue), meta, season, mediaType);" in resolver
assert "const catalogueProviderValues = _spv215CatalogueProviderValues(" in resolver
assert 'id: providerValues.id || catalogueProviderValues.id || ""' in resolver
assert 'slug: providerValues.slug || catalogueProviderValues.slug || ""' in resolver
assert 'catalogueProviderValues.slug || providerValues.slug' not in resolver
assert "_spv20ProviderValuesFromJson(JSON.parse(rawSearchValue), meta)" not in resolver

print("provider JSON/catalogue preservation V21.9 tests passed: strict JSON remains authoritative")
