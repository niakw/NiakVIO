#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
text = BASE.read_text(encoding="utf-8")

required = (
    "NIAKVIO_PROVIDER_EPISODE_IDENTITY_GUARD_V22_1",
    "function _spv221EpisodeTableState(html, base, season, episode)",
    "detailEpisodeMarker.marked && !detailEpisodeMarker.matches",
    "episodeTableState.marked && !episodeTableState.matches",
    "episodeTableState.marked && !(detailEpisodeMarker.marked && detailEpisodeMarker.matches)",
)
for needle in required:
    assert needle in text, needle

start = text.index("function _spv22EpisodeMarker")
end = text.index("async function _spv22ResolveEpisodeHop", start)
snippet = text[start:end]

runner = r'''
function _text(value){return String(value==null?"":value)}
function _embeddedText(value){return _text(value)}
function _absolute(value,base){try{return new URL(value,base).toString()}catch(_){return""}}
SNIPPET
function check(value,msg){if(!value)throw new Error(msg)}
const exact=_spv22EpisodeMarker("https://example.test/watch?season=2&episode=10",2,10);
check(exact.marked&&exact.matches,"query season/episode exact did not match "+JSON.stringify(exact));
const wrong=_spv22EpisodeMarker("https://example.test/watch?season=2&episode=10",2,11);
check(wrong.marked&&!wrong.matches,"wrong requested episode accepted "+JSON.stringify(wrong));
const reversed=_spv22EpisodeMarker("https://example.test/watch?episode=10&season=2",2,10);
check(reversed.marked&&reversed.matches,"reversed query order did not match "+JSON.stringify(reversed));
const html='<a href="/anime?season=2&episode=9">E9</a><a href="/anime?season=2&episode=10">E10</a>';
const state=_spv221EpisodeTableState(html,"https://example.test/show",2,10);
check(state.marked&&state.matches,"matching table not recognized "+JSON.stringify(state));
const miss=_spv221EpisodeTableState('<a href="/anime?season=2&episode=9">E9</a>',"https://example.test/show",2,10);
check(miss.marked&&!miss.matches,"missing requested episode did not fail closed "+JSON.stringify(miss));
console.log("EPISODE_IDENTITY_V22_1_OK");
'''.replace("SNIPPET", snippet)

with tempfile.TemporaryDirectory() as tmp:
    js = Path(tmp) / "episode-guard.js"
    js.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(js)], check=True, timeout=5)

print("provider episode identity guard v22.1 contract passed")
