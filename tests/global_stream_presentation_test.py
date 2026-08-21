#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHES = ROOT / "scripts" / "provider_patches"


def load(name: str):
    path = PATCHES / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


facts = load("purstream_stream_facts_v1.py")
presentation = load("global_stream_presentation_v1.py")

legacy = """module.exports={getStreams:async()=>[{name:'Purstream | 4k | Dual-Audio',title:'🎬 Interstellar - 2014\\n🔥 4k | 🔊 Dual-Audio\\n🎯 HLS • HEVC | 🎧 AAC • 169 min • BLU-RAY',size:'🎬 Interstellar - 2014\\n🔥 4k | 🔊 Dual-Audio\\n🎯 HLS • HEVC | 🎧 AAC • 169 min • BLU-RAY',description:'🎬 Interstellar - 2014\\n🔥 4k | 🔊 Dual-Audio\\n🎯 HLS • HEVC | 🎧 AAC • 169 min • BLU-RAY',url:'https://media.example/master.m3u8',quality:'',language:'',format:'m3u8',headers:{Referer:'https://purstream.example/'}}]};\n"""
with_facts = facts.apply(legacy)
assert "NUVIO_PURSTREAM_STREAM_FACTS_V1" in with_facts
patched = presentation.apply(with_facts, context={"provider_id": "purstream"})
assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in patched
assert patched == presentation.apply(patched, context={"provider_id": "purstream"})


def run(source: str, fetch_impl: str, call: str) -> object:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(source, encoding="utf-8")
        runner.write_text(
            "global.fetch=" + fetch_impl + ";\n"
            "const p=require(" + json.dumps(str(provider)) + ");\n"
            + call
            + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(runner)], text=True, capture_output=True, check=False, timeout=15)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip())


tmdb_ok = r"""async function(url){
  if(!String(url).includes('api.themoviedb.org')) throw new Error('presentation must not fetch playback URLs');
  return {ok:true,status:200,json:async()=>({id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169,release_dates:{results:[{iso_3166_1:'FR',release_dates:[{certification:'-12'}]}]}})};
}"""
row = run(
    patched,
    tmdb_ok,
    "p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert row["url"] == "https://media.example/master.m3u8"
assert row["headers"] == {"Referer": "https://purstream.example/"}
assert row["quality"] == "2160p", row
assert row["language"] == "Dual Audio", row
assert row["codec"] == "HEVC", row
assert row["audio"] == "AAC", row
assert row["duration"] == 169, row
assert row["sourceType"] == "BLU-RAY", row
assert row["ageRating"] == "-12", row
assert row["title"] == "Purstream", row
assert row["size"].startswith("【4K】 【BLU-RAY】 🌐 Dual Audio 🎞 HEVC"), row
for token in ("【4K】", "【BLU-RAY】", "🌐 Dual Audio", "🎞 HEVC", "🔊 AAC", "⏱ 2h49", "🔞 -12", "Interstellar • 2014"):
    assert token in row["description"], (token, row)
assert "Unknown" not in row["description"]

# Empty provider output must not start an optional TMDB request that can outlive
# the provider route and make native evidence look incomplete.
empty = "module.exports={getStreams:async()=>[]};\n"
empty_patched = presentation.apply(empty, context={"provider_id": "movieshunt"})
empty_result = run(
    empty_patched,
    "async function(){global.__tmdbCalls=(global.__tmdbCalls||0)+1;throw new Error('must not run')}",
    "p.getStreams({tmdbId:'1233413',mediaType:'movie',title:'Sinners',year:2025}).then(v=>console.log(JSON.stringify({streams:v,calls:global.__tmdbCalls||0})))",
)
assert empty_result == {"streams": [], "calls": 0}, empty_result

# Resolution alone never invents Blu-ray provenance.
plain = "module.exports={getStreams:async()=>[{name:'Cineby',url:'https://media.example/video.mp4',quality:'1080p'}]};\n"
plain_patched = presentation.apply(plain, context={"provider_id": "cineby"})
plain_row = run(
    plain_patched,
    "async function(){throw new Error('tmdb offline')}",
    "p.getStreams({mediaType:'movie',title:'Example',year:2026}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert plain_row["quality"] == "1080p"
assert "sourceType" not in plain_row
assert "BLU-RAY" not in plain_row["description"]
assert "【1080P】" in plain_row["description"]
assert "Example • 2026" in plain_row["description"]

# Optional TMDB failure must never drop or mutate playback material.
unknown = "module.exports={getStreams:async()=>[{name:'Movix',url:'https://media.example/u.m3u8',description:'Unknown',headers:{Origin:'https://movix.example'}}]};\n"
unknown_patched = presentation.apply(unknown, context={"provider_id": "movix"})
unknown_row = run(
    unknown_patched,
    "async function(){throw new Error('offline')}",
    "p.getStreams({tmdbId:'999',mediaType:'movie',title:'Fallback title',year:2026}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert unknown_row["url"] == "https://media.example/u.m3u8"
assert unknown_row["headers"] == {"Origin": "https://movix.example"}
assert "Unknown" not in unknown_row["description"]
assert "Fallback title • 2026" in unknown_row["description"]

print("global stream presentation + Purstream factual contract tests passed")
