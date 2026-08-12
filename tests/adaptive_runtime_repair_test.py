#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "adaptive_runtime"))
sys.path.insert(1, str(ROOT / "scripts"))

import runtime_repair  # noqa: E402

with tempfile.TemporaryDirectory() as directory:
    stage = Path(directory)
    provider = stage / "providers" / "demo.js"
    provider.parent.mkdir(parents=True)
    provider.write_text(
        "module.exports={getStreams:async function(){return []}};\n",
        encoding="utf-8",
    )
    candidate = {
        "key": "test:demo",
        "canonical_id": "demo",
        "upstream_id": "demo",
        "source": "test",
        "local_path": "providers/demo.js",
        "metadata": {
            "id": "demo",
            "name": "Demo",
            "baseUrl": "https://demo.example",
            "supportedTypes": ["movie"],
        },
        "local_patches": [],
    }
    failing = {
        "status": "no_streams",
        "tests": [{"failure_class": "content_lookup_completed_no_streams"}],
        "evidence": {"streams_returned": 0, "streams_playable": 0},
    }
    healthy = {
        "status": "healthy",
        "tests": [],
        "evidence": {"streams_returned": 1, "streams_playable": 1},
    }
    healthy_with_secondary_gap = {
        "status": "healthy",
        "tests": [{"failure_class": "content_lookup_completed_no_streams", "streams_playable": 0}],
        "evidence": {"streams_returned": 1, "streams_playable": 1},
    }
    healthy_without_playable_proof = {
        "status": "healthy",
        "tests": [{"failure_class": "content_lookup_completed_no_streams", "streams_playable": 0}],
        "evidence": {"streams_returned": 0, "streams_playable": 0},
    }
    source = provider.read_text(encoding="utf-8")
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(
        candidate, failing, source
    )
    assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(
        candidate, healthy, source
    )
    assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(
        candidate, healthy_with_secondary_gap, source
    )
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(
        candidate, healthy_without_playable_proof, source
    )

    repaired, error = runtime_repair.create_repair_candidate(
        stage, candidate, "adaptive_runtime_recovery", 1
    )
    assert error is None, error
    assert repaired is not None
    target = stage / repaired["local_path"]
    assert target.is_file()
    generated = target.read_text(encoding="utf-8")
    assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V3" in generated
    assert 'language:"fr"' not in generated
    assert repaired["runtime_repair"]["profile"] == ""
    assert repaired["runtime_repair"]["strategy"] == "adaptive_runtime_recovery"

    runner = r'''
const vm=require('vm');
const source=process.argv[2];
const calls=[];
const responses={
  'https://demo.example/?s=Fixture%20Movie':{
    url:'https://demo.example/search/final',
    type:'text/html',
    body:'<a href="../film/fixture-movie">Fixture Movie 2020</a>',
    cookies:['session=abc; Path=/']
  },
  'https://demo.example/film/fixture-movie':{
    url:'https://demo.example/film/fixture-movie',
    type:'text/html',
    body:'<iframe src="https://player.example/embed/a"></iframe><iframe src="https://second.example/e/b"></iframe>'
  },
  'https://player.example/embed/a':{
    url:'https://player.example/embed/a',
    type:'text/html',
    body:'<source src="https://cdn.example/media/token">',
    cookies:['player=xyz; Path=/']
  },
  'https://cdn.example/media/token':{
    url:'https://cdn.example/redirected/master',
    type:'application/vnd.apple.mpegurl',
    body:''
  },
  'https://second.example/e/b':{
    url:'https://second.example/e/b',
    type:'text/html',
    body:'<script>var source="https://cdn2.example/b/video.mp4"</script>'
  }
};
function headers(row){return {
  get:(key)=>key.toLowerCase()==='content-type'?(row.type||'text/html'):key.toLowerCase()==='set-cookie'?((row.cookies||[])[0]||null):null,
  getSetCookie:()=>row.cookies||[]
}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,
  fetch:async(url,options={})=>{
    const key=String(url); calls.push({url:key,headers:options.headers||{}});
    const row=responses[key]||{url:key,type:'text/html',body:''};
    return {
      ok:true,status:200,url:row.url||key,headers:headers(row),
      text:async()=>row.body||'',
      json:async()=>({title:'Fixture Movie',release_date:'2020-01-01'})
    };
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie',title:'Fixture Movie',year:2020})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(error=>{console.error(error);process.exit(1)});
'''
    runner_path = stage / "nested-player-test.cjs"
    runner_path.write_text(runner, encoding="utf-8")
    process = subprocess.run(
        ["node", str(runner_path), generated],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert process.returncode == 0, process.stderr
    payload = json.loads(process.stdout.strip())
    rows = payload["rows"]
    calls = payload["calls"]
    assert len(rows) == 2, rows
    assert all("language" not in row for row in rows), rows
    by_url = {row["url"]: row for row in rows}
    first = by_url["https://cdn.example/redirected/master"]
    second = by_url["https://cdn2.example/b/video.mp4"]
    assert first["headers"]["Referer"] == "https://player.example/embed/a"
    assert first["headers"]["Origin"] == "https://player.example"
    assert first["isDirect"] is False  # media proof came from Content-Type, not extension.
    assert second["headers"]["Referer"] == "https://second.example/e/b"
    assert second["headers"]["Origin"] == "https://second.example"
    player_call = next(call for call in calls if call["url"] == "https://player.example/embed/a")
    assert "session=abc" in player_call["headers"].get("Cookie", "")

print("adaptive runtime repair tests passed")
