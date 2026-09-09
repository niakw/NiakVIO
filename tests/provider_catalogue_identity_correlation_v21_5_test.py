#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_catalogue_identity_correlation_v21_5.py"

spec = importlib.util.spec_from_file_location("v215", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V21.5 migration")
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

base = module.BASE.read_text(encoding="utf-8")
helper_start = base.index("function _spv205SeasonSignal")
helper_end = base.index("function _spv205HttpValues", helper_start)
helper = base[helper_start:helper_end]

node = f'''
function _text(v) {{ return v == null ? "" : String(v); }}
function _htmlVisibleText(v) {{
  return _text(v).replace(/<[^>]+>/g, " ").replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&");
}}
function _norm(v) {{
  return _text(v).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}}
function _slug(v) {{ return _norm(v).replace(/\\s+/g, "-"); }}
function _spv4Titles(meta) {{ return meta && meta.title ? [meta.title] : []; }}
function _spv4TitleScore(title, meta) {{
  const actual = _norm(title);
  const expected = _norm(meta && meta.title);
  if (!actual || !expected) return 0;
  if (actual === expected) return 240;
  if (actual.includes(expected) || expected.includes(actual)) return 110;
  let score = 0;
  for (const token of expected.split(/\\s+/).filter(v => v.length >= 3)) {{
    if (actual.includes(token)) score += 18;
  }}
  return score;
}}
function _spv4JsonRows(value, out) {{ return out || []; }}
function _spv18ProviderIdFromJson() {{ return ""; }}
function _spv4Scalar(v) {{ return v == null ? "" : String(v); }}
{helper}

const correlatedHtml = `
  <div class="search-item" onclick="location.href='/11111-alpha-show-saison-1.html'">
    <div class="search-title">Alpha Show</div>
  </div>
  <div class="noise" data-id="22222"></div>
  <div class="noise" data-id="22222"></div>
  <div class="noise" data-id="22222"></div>
`;
const fallbackHtml = `
  <div data-id="fallback-77"></div>
  <span data-id="fallback-77"></span>
`;
const seasonHtml = `
  <div class="search-item" onclick="location.href='/33333-alpha-show-saison-2.html'">
    <div class="search-title">Alpha Show</div>
  </div>
  <div class="search-item" onclick="location.href='/44444-alpha-show-saison-1.html'">
    <div class="search-title">Alpha Show</div>
  </div>
`;
const out = {{
  catalogue: _spv215CatalogueProviderValues(correlatedHtml, "https://catalog.invalid/", {{title:"Alpha Show"}}, 1, "tv"),
  laterStep: _spv205StrictProviderValues(correlatedHtml, "https://catalog.invalid/", {{title:"Alpha Show"}}, 1, "tv"),
  fallback: _spv215CatalogueProviderValues(fallbackHtml, "https://catalog.invalid/", {{title:"Alpha Show"}}, 1, "tv"),
  season: _spv215CatalogueProviderValues(seasonHtml, "https://catalog.invalid/", {{title:"Alpha Show"}}, 1, "tv")
}};
process.stdout.write(JSON.stringify(out));
'''
proc = subprocess.run(["node", "-e", node], cwd=ROOT, check=True, capture_output=True, text=True)
out = json.loads(proc.stdout)

# Initial catalogue response: same-record title+onclick identity is authoritative.
assert out["catalogue"]["id"] == "11111", out
assert out["catalogue"]["slug"] == "11111-alpha-show-saison-1", out
# Later response: unchanged V20.5/V21.1 strict selector keeps response-wide id learning.
assert out["laterStep"]["id"] == "22222", out
# Initial response without a correlated row still gets the historical fallback.
assert out["fallback"]["id"] == "fallback-77", out
# Same-record season evidence selects the requested season.
assert out["season"]["id"] == "44444", out
assert out["season"]["slug"] == "44444-alpha-show-saison-1", out

assert "function _spv205StrictProviderValues(value, base, meta, season, mediaType)" in base
assert "function _spv215CatalogueProviderValues(value, base, meta, season, mediaType)" in base

resolver_start = base.index("async function _resolveProviderValuePlan")
resolver_end = base.index("async function _resolveSearchRequestPlan", resolver_start)
resolver = base[resolver_start:resolver_end]
assert resolver.count("providerValues = _spv215CatalogueProviderValues(") == 1
assert "const nextProviderValues = _spv205StrictProviderValues(" in resolver
assert "const nextProviderValues = _spv215CatalogueProviderValues(" not in resolver

print("provider catalogue identity correlation V21.5 tests passed")
