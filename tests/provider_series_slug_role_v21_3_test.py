#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_series_slug_role_v21_3.py"

spec = importlib.util.spec_from_file_location("v213", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V21.3 migration")
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
start = base.index("function _spv213SlugCarriesEpisodeIdentity")
end = base.index("function _spv211ProviderIdAllowed", start)
helper = base[start:end]

node = f'''
function _text(v) {{ return v == null ? "" : String(v); }}
{helper}
const steps = [
  {{route:"/series/{{slug}}/"}},
  {{route:"/episode/{{slug}}-{{season}}-episode-{{episode}}/"}}
];
const done = new Set([0]);
const out = {{
  preserveSeries: _spv213StableSeriesSlug("neutral-series", "neutral-series-1-episode-54", "anime", steps, done, 0),
  preserveSeriesTv: _spv213StableSeriesSlug("neutral-series", "neutral-series-season-1-episode-54", "tv", steps, done, 0),
  movieCandidate: _spv213StableSeriesSlug("neutral-movie", "neutral-movie-1-episode-54", "movie", steps, done, 0),
  terminalEpisodeHandoff: _spv213StableSeriesSlug("neutral-series", "neutral-series-1-episode-54", "anime", [{{route:"/series/{{slug}}/"}},{{route:"/watch/{{slug}}"}}], done, 0),
  cleanerCandidate: _spv213StableSeriesSlug("neutral-series-1-episode-54", "neutral-series", "anime", steps, done, 0)
}};
process.stdout.write(JSON.stringify(out));
'''
proc = subprocess.run(["node", "-e", node], cwd=ROOT, check=True, capture_output=True, text=True)
out = json.loads(proc.stdout)
assert out["preserveSeries"] == "neutral-series", out
assert out["preserveSeriesTv"] == "neutral-series", out
assert out["movieCandidate"] == "neutral-movie-1-episode-54", out
assert out["terminalEpisodeHandoff"] == "neutral-series-1-episode-54", out
assert out["cleanerCandidate"] == "neutral-series", out

# Historical V20.4/20.5 assertions deliberately remain true after the additive guard.
assert "providerId: nextProviderValues.id || values.providerId" in base
assert "providerSlug: nextProviderValues.slug || values.providerSlug" in base

print("provider series slug role V21.3 tests passed")
