#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_media_identity_guard_v21_2.py"

spec = importlib.util.spec_from_file_location("v212", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V21.2 migration")
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
start = base.index("function _spv211RegexEscape")
end = base.index("function _spv205StrictProviderValues", start)
helper = base[start:end]

# Deliberately DO NOT define _slug or _spv4Titles here. Historical V20.5 tests
# execute this resolver in isolation, so V21-owned helpers must be sufficient.
node = f'''
function _text(v) {{ return v == null ? "" : String(v); }}
function _spv4TitleScore(title, meta) {{
  function localSlug(v) {{ return _text(v).normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, ""); }}
  const actual = localSlug(title); let best = 0;
  const titles = [meta && meta.title].concat((meta && meta.aliases) || []);
  for (const wanted of titles.map(localSlug).filter(Boolean)) {{
    if (actual === wanted) best = Math.max(best, 240);
    else if (actual.includes(wanted) || wanted.includes(actual)) best = Math.max(best, 110);
  }}
  return best;
}}
function _spv205SeasonSignal(raw, season) {{
  const text = _text(raw).toLowerCase();
  const wanted = Number(season);
  const m = text.match(/(?:saison|season)[\\s._-]*0*(\\d{{1,3}})\\b/i);
  return m ? (Number(m[1]) === wanted ? 80 : -120) : 0;
}}
{helper}
const meta = {{title:"Neutral Series", aliases:["Neutral Series TV"], year:2020}};
const out = {{
  exactTv: _spv211CandidateIdentityScore("Neutral Series", "/anime/42-neutral-series.html", meta, "anime", 1),
  numericInstallmentTv: _spv211CandidateIdentityScore("Neutral Series 0", "/anime/94-neutral-series-0.html", meta, "anime", 1),
  seasonTv: _spv211CandidateIdentityScore("Neutral Series Saison 1", "/anime/42-neutral-series-saison-1.html", meta, "tv", 1),
  movieYearOk: _spv211CandidateIdentityScore("Neutral Movie 2020", "/film/neutral-movie-2020", {{title:"Neutral Movie", year:2020}}, "movie", 0),
  movieYearBad: _spv211CandidateIdentityScore("Neutral Movie 2019", "/film/neutral-movie-2019", {{title:"Neutral Movie", year:2020}}, "movie", 0),
  trackingG: _spv211ProviderIdAllowed("measurement_id", "G-X5Q6XKMG6W"),
  providerNumeric: _spv211ProviderIdAllowed("entryid", "4711")
}};
process.stdout.write(JSON.stringify(out));
'''
proc = subprocess.run(["node", "-e", node], cwd=ROOT, check=True, capture_output=True, text=True)
out = json.loads(proc.stdout)
assert out["exactTv"] >= 200, out
assert out["numericInstallmentTv"] <= -10000, out
assert out["seasonTv"] > 0, out
assert out["movieYearOk"] > 0, out
assert out["movieYearBad"] <= -10000, out
assert out["trackingG"] is False, out
assert out["providerNumeric"] is True, out

scorer_start = base.index("function _spv211CandidateIdentityScore")
scorer_end = base.index("function _spv211ProviderIdAllowed", scorer_start)
scorer = base[scorer_start:scorer_end]
assert "_slug(" not in scorer, scorer
assert "_spv4Titles(" not in scorer, scorer

print("provider media identity guard V21.2 self-contained compatibility tests passed")
