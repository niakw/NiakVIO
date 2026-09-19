#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_player_fallback_v21_6.py"

spec = importlib.util.spec_from_file_location("v216", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V21.6 migration")
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
start = base.index("function _spv216PlayerFallbackEligible")
end = base.index("async function _resolveProviderValuePlan", start)
helper = base[start:end]

node = f'''
function _text(v) {{ return v == null ? "" : String(v); }}
function _directMedia(v) {{ return /\\.(?:m3u8|mp4)(?:[?#]|$)/i.test(String(v || "")); }}
function _playerLike(v) {{ return /\\/(?:embed|player|watch)(?:[/?#.-]|$)/i.test(String(v || "")); }}
function _streams(urls, referer) {{ return (urls || []).map(url => ({{url, headers:{{Referer:referer}}}})); }}
{helper}
const out = {{
  direct: _spv216PlayerFallbackEligible("https://media.invalid/master.m3u8"),
  embed: _spv216PlayerFallbackEligible("https://player.invalid/embed/abc"),
  queryPlayer: _spv216PlayerFallbackEligible("https://media.invalid/shell.php?videoid=42"),
  ordinaryDetail: _spv216PlayerFallbackEligible("https://catalog.invalid/anime/42-title"),
  ordinaryApi: _spv216PlayerFallbackEligible("https://api.invalid/detail?id=42"),
  streams: _spv216FallbackStreams([
    {{url:"https://player.invalid/embed/a", referer:"https://catalog.invalid/episode/1"}},
    {{url:"https://player.invalid/embed/a", referer:"https://catalog.invalid/episode/1"}},
    {{url:"https://catalog.invalid/detail/1", referer:"https://catalog.invalid/"}}
  ])
}};
process.stdout.write(JSON.stringify(out));
'''
proc = subprocess.run(["node", "-e", node], cwd=ROOT, check=True, capture_output=True, text=True)
out = json.loads(proc.stdout)
assert out["direct"] is True, out
assert out["embed"] is True, out
assert out["queryPlayer"] is True, out
assert out["ordinaryDetail"] is False, out
assert out["ordinaryApi"] is False, out
assert len(out["streams"]) == 1, out
assert out["streams"][0]["headers"]["Referer"] == "https://catalog.invalid/episode/1", out

resolver_start = base.index("async function _resolveProviderValuePlan")
resolver_end = base.index("async function _resolveSearchRequestPlan", resolver_start)
resolver = base[resolver_start:resolver_end]
for needle in (
    "const playerFallbacks = [];",
    "try {\n            payload = await _recipePayload(stepUrl, {}, stepSpec, values);",
    "if (_spv216PlayerFallbackEligible(stepUrl))",
    'playerFallbacks.push({ url: stepUrl, referer: fallbackReferer });',
    '"step_player_fallback"',
    "const fallbackStreams = _spv216FallbackStreams(playerFallbacks);",
):
    assert needle in resolver, needle
assert resolver.index("const fallbackStreams = _spv216FallbackStreams(playerFallbacks);") > resolver.index("if (!progressed) break;")

print("provider player fallback V21.6 tests passed")
