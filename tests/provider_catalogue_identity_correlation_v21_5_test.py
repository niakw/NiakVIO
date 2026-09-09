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
const wrongSeasonHtml = `
  <div onclick="location.href='/33333-alpha-show-saison-2.html'">Alpha Show</div>
  <div onclick="location.href='/44444-alpha-show-saison-1.html'">Alpha Show</div>
`;
const out = {{
  correlated: _spv205StrictProviderValues(correlatedHtml, "https://catalog.invalid/", {{title:"Alpha Show"}}, 1),
  fallback: _spv205StrictProviderValues(fallbackHtml, "https://catalog.invalid/", {{title:"Alpha Show"}}, 1),
  season: _spv205StrictProviderValues(wrongSeasonHtml, "https://catalog.invalid/", {{title:"Alpha Show"}}, 1)
}};
process.stdout.write(JSON.stringify(out));
'''
proc = subprocess.run(["node", "-e", node], cwd=ROOT, check=True, capture_output=True, text=True)
out = json.loads(proc.stdout)

assert out["correlated"]["id"] == "11111", out
assert out["correlated"]["slug"] == "11111-alpha-show-saison-1", out
assert out["fallback"]["id"] == "fallback-77", out
assert out["season"]["id"] == "44444", out
assert out["season"]["slug"] == "44444-alpha-show-saison-1", out

strict_start = base.index("function _spv205StrictProviderValues")
strict_end = base.index("function _spv205HttpValues", strict_start)
strict = base[strict_start:strict_end]
assert "if (!best.id && bestId) best.id = bestId;" in strict
assert "if (bestId) best.id = bestId;" not in strict

print("provider catalogue identity correlation V21.5 tests passed")
