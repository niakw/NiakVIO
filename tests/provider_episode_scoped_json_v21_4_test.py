#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_episode_scoped_json_v21_4.py"

spec = importlib.util.spec_from_file_location("v214", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V21.4 migration")
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
start = base.index("function _spv214EpisodeNumber")
end = base.index("function _spv211ProviderIdAllowed", start)
helper = base[start:end]

node = f'''
function _text(v) {{ return v == null ? "" : String(v); }}
{helper}
const payload = {{
  vf: {{
    "1": {{ServerA:"https://player.invalid/ep1-vf",ServerB:"https://player.invalid/ep1b-vf"}},
    "2": {{ServerA:"https://player.invalid/ep2-vf"}}
  }},
  vostfr: {{
    "1": {{ServerA:"https://player.invalid/ep1-vo"}},
    "2": {{ServerA:"https://player.invalid/ep2-vo"}}
  }},
  info: {{
    "1": {{title:"Episode One"}},
    "2": {{title:"Episode Two"}}
  }}
}};
const tagged = [
  {{episode_number:1,url:"https://player.invalid/tag-1"}},
  {{episode_number:2,url:"https://player.invalid/tag-2"}}
];
const qualities = {{"1080":"https://cdn.invalid/1080.m3u8","720":"https://cdn.invalid/720.m3u8"}};
const out = {{
  ep1: _spv214EpisodeScopedValue(payload,"anime",1,0),
  ep2: _spv214EpisodeScopedValue(payload,"tv",2,0),
  missing: _spv214EpisodeScopedValue(payload,"tv",9,0),
  movie: _spv214EpisodeScopedValue(payload,"movie",1,0),
  tagged2: _spv214EpisodeScopedValue(tagged,"tv",2,0),
  qualities: _spv214EpisodeScopedValue(qualities,"tv",1,0)
}};
process.stdout.write(JSON.stringify(out));
'''
proc = subprocess.run(["node", "-e", node], cwd=ROOT, check=True, capture_output=True, text=True)
out = json.loads(proc.stdout)

expected_payload = {
    "vf": {
        "1": {"ServerA": "https://player.invalid/ep1-vf", "ServerB": "https://player.invalid/ep1b-vf"},
        "2": {"ServerA": "https://player.invalid/ep2-vf"},
    },
    "vostfr": {
        "1": {"ServerA": "https://player.invalid/ep1-vo"},
        "2": {"ServerA": "https://player.invalid/ep2-vo"},
    },
    "info": {
        "1": {"title": "Episode One"},
        "2": {"title": "Episode Two"},
    },
}
expected_tagged = [
    {"episode_number": 1, "url": "https://player.invalid/tag-1"},
    {"episode_number": 2, "url": "https://player.invalid/tag-2"},
]
expected_qualities = {
    "1080": "https://cdn.invalid/1080.m3u8",
    "720": "https://cdn.invalid/720.m3u8",
}

serialized_ep1 = json.dumps(out["ep1"], sort_keys=True)
assert "ep1-vf" in serialized_ep1 and "ep1-vo" in serialized_ep1, out
assert "ep2-vf" not in serialized_ep1 and "ep2-vo" not in serialized_ep1, out
serialized_ep2 = json.dumps(out["ep2"], sort_keys=True)
assert "ep2-vf" in serialized_ep2 and "ep2-vo" in serialized_ep2, out
assert "ep1-vf" not in serialized_ep2 and "ep1-vo" not in serialized_ep2, out
# Every real episode table fails closed for an absent requested episode; the
# remaining object can contain only unrelated/non-episode metadata branches.
assert "player.invalid" not in json.dumps(out["missing"], sort_keys=True), out
assert out["movie"] == expected_payload, out
assert out["tagged2"] == [expected_tagged[1]], out
assert out["qualities"] == expected_qualities, out

resolver_start = base.index("async function _resolveProviderValuePlan")
resolver_end = base.index("async function _resolveSearchRequestPlan", resolver_start)
resolver = base[resolver_start:resolver_end]
boundary = resolver.index("const scopedPayloadValue =")
extraction = resolver[boundary:]
for forbidden in (
    "_extractUrls(payload.value, payload.base)",
    "_jsonUrls(payload.value)",
    "_sourceUrls(payload.value, payload.base)",
    "_spv18ValueUrls(payload.value, payload.base, [])",
    "_spv205HttpValues(payload.value, payload.base, [])",
):
    assert forbidden not in extraction, forbidden

print("provider episode-scoped JSON V21.4 tests passed")
