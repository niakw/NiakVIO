#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_response_value_correlation_v20_5.py"

spec = importlib.util.spec_from_file_location("v205", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V20.5 migration")
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
recovery = module.RECOVERY.read_text(encoding="utf-8")

assert "for row in correlated[:8]" in recovery
assert "for row in correlated[:4]" not in recovery
assert "const valueSteps = (plan.steps || []).slice(0, 8);" in base
assert "const completedSteps = new Set();" in base
assert "step_deferred" in base
assert "if (!progressed) break;" in base
assert '                ][:8],\n                "semanticTypes"' in base
assert '                ][:4],\n                "semanticTypes"' not in base
assert "..._spv205HttpValues(payload.value, payload.base, [])" in base

start = base.index("function _spv205SeasonSignal")
end = base.index("function _spv204ResponseProviderValues", start)
helper_js = base[start:end]
node = f'''
function _text(v) {{ return v == null ? "" : String(v); }}
function _htmlVisibleText(v) {{ return _text(v).replace(/<[^>]+>/g, " "); }}
function _spv4TitleScore(label, meta) {{
  const a = _text(label).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const b = _text(meta && meta.title).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  if (a === b) return 200;
  if (a.includes(b) || b.includes(a)) return 120;
  let score = 0;
  for (const word of b.split(/\\s+/)) if (word.length > 2 && a.includes(word)) score += 20;
  return score;
}}
function _spv18ProviderIdFromJson() {{ return ""; }}
function _spv4JsonRows(v) {{ return Array.isArray(v) ? v : [v]; }}
function _spv4Scalar(v) {{ return v == null ? "" : String(v); }}
{helper_js}
const search = '<a href="/catalog/neutral-series-saison-3/">Neutral Series Saison 3</a>' +
               '<a href="/catalog/neutral-series-saison-1/">Neutral Series Saison 1</a>';
const slugOnly = _spv205StrictProviderValues(search, 'https://example.invalid/', {{title:'Neutral Series'}}, 1);
const episode = '<iframe src="/?mode=0&entryid=4711&type=2"></iframe>' +
                '<iframe src="/?mode=1&entryid=8122&type=2"></iframe>';
const idOnly = _spv205StrictProviderValues(episode, 'https://example.invalid/', {{title:'Neutral Series'}}, 1);
const widget = '<div onclick="location.href=\\'/1497198-neutral-series-saison-1-2020.html\\'">Neutral Series Saison 1</div>';
const numericWidget = _spv205StrictProviderValues(widget, 'https://example.invalid/', {{title:'Neutral Series'}}, 1);
const urls = _spv205HttpValues({{
  vf: {{ '1': {{ ServerA: 'https://player.invalid/embed/abc', token: 'https://evil.invalid/private' }} }},
  poster: 'https://img.invalid/poster.jpg'
}}, 'https://example.invalid/', []);
process.stdout.write(JSON.stringify({{slugOnly,idOnly,numericWidget,urls}}));
'''
proc = subprocess.run(["node", "-e", node], check=True, capture_output=True, text=True)
result = json.loads(proc.stdout)
assert result["slugOnly"] == {"id": "", "slug": "neutral-series-saison-1"}, result
assert result["idOnly"]["id"] == "4711", result
assert result["idOnly"]["slug"] == "", result
assert result["numericWidget"]["id"] == "1497198", result
assert result["urls"] == ["https://player.invalid/embed/abc"], result

window = base[base.index(module.MARKER):base.index("async function _resolveSearchRequestPlan", base.index(module.MARKER))].casefold()
for forbidden in ("animesama", "animevostfr", "french-manga", "jujutsu", "vidzy", "purstream"):
    assert forbidden not in window, forbidden

print("provider response-value correlation V20.5 tests passed")
