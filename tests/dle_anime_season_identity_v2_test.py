#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PATCHES = SCRIPTS / "provider_patches"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PATCHES))
SOURCE = PATCHES / "dle_anime_runtime_v1.py"

spec = importlib.util.spec_from_file_location("dle_anime_runtime_v1", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert "function seasonSignal(row,season)" in module.WRAPPER
assert "function episodeNode(data,season,episode)" in module.WRAPPER
assert "q.season>1&&!node.seasonVerified&&!hit._seasonVerified" in module.WRAPPER

CONFIG = {
    "base": "https://anime.example",
    "provider": "season-test",
    "name": "Season Test",
    "userAgent": "NiakVIO-Test",
    "maxStreams": 6,
}


def run(search_html_by_query: dict[str, str], api_payload_by_id: dict[str, object]) -> list[dict]:
    wrapper = module.WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(CONFIG, ensure_ascii=False, separators=(",", ":")),
    )
    js = f"""
const searchByQuery={json.dumps(search_html_by_query)};
const apiById={json.dumps(api_payload_by_id)};
global.fetch=async function(url, init={{}}){{
  const u=String(url);
  if(u.includes('/engine/ajax/search.php')){{
    const body=String(init.body||'');
    const query=decodeURIComponent((body.match(/(?:^|&)query=([^&]*)/)||[])[1]||'');
    const text=Object.prototype.hasOwnProperty.call(searchByQuery,query)?searchByQuery[query]:'';
    return {{ok:true,status:200,url:u,text:async()=>text}};
  }}
  if(u.includes('/engine/ajax/manga_episodes_api.php')){{
    const id=(u.match(/[?&]id=([^&]+)/)||[])[1]||'';
    return {{ok:true,status:200,url:u,text:async()=>JSON.stringify(apiById[decodeURIComponent(id)]||{{}})}};
  }}
  throw new Error('unexpected fetch '+u);
}};
{wrapper}
const resolver=global.__niakvioProviderRuntimeResolverV1;
if(!resolver) throw new Error('resolver missing');
resolver.resolve([{{tmdbId:'280049',mediaType:'anime',season:2,episode:12,title:'Hell Mode'}}],{{}})
  .then(rows=>console.log(JSON.stringify(rows)))
  .catch(err=>{{console.error(err&&err.stack||String(err));process.exit(1)}});
"""
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "season-test.cjs"
        path.write_text(js, encoding="utf-8")
        result = subprocess.run(
            ["node", str(path)],
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip() or "[]")


s1 = '<a href="https://anime.example/show?id=111">Hell Mode Saison 1</a>'
s2 = '<a href="https://anime.example/show?id=222">Hell Mode Saison 2</a>'
rows = run(
    {
        "Hell Mode saison 2": s1 + s2,
        "Hell Mode season 2": s1 + s2,
        "Hell Mode": s1 + s2,
    },
    {
        "111": {"vostfr": {"12": ["https://cdn.example/s1e12.m3u8"]}},
        "222": {"vostfr": {"12": ["https://cdn.example/s2e12.m3u8"]}},
    },
)
assert rows, rows
assert rows[0]["url"] == "https://cdn.example/s2e12.m3u8", rows
assert rows[0]["language"] == "VOSTFR", rows

# Fail closed: if a season-2 request only finds an unlabelled page whose API is
# episode-only (no season scope), never silently return its E12 as S02E12.
unknown = '<a href="https://anime.example/show?id=333">Hell Mode</a>'
rows = run(
    {
        "Hell Mode saison 2": unknown,
        "Hell Mode season 2": unknown,
        "Hell Mode": unknown,
    },
    {
        "333": {"vostfr": {"12": ["https://cdn.example/ambiguous-e12.m3u8"]}},
    },
)
assert rows == [], rows

print("DLE season identity regression test passed: S02E12 cannot fall back to ambiguous S01E12")
