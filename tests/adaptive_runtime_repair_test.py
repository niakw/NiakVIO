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
    assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4" in generated
    assert 'language:"fr"' not in generated
    assert repaired["runtime_repair"]["profile"] == ""
    assert repaired["runtime_repair"]["strategy"] == "adaptive_runtime_recovery"

    stale_candidate = json.loads(json.dumps(repaired))
    stale_candidate["key"] = "test:demo"
    stale_candidate.pop("runtime_repair", None)
    stale_candidate["metadata"]["baseUrl"] = "https://new-demo.example"
    assert any(
        row.get("profile") == "adaptive_runtime_recovery"
        for row in stale_candidate["local_patches"]
        if isinstance(row, dict)
    )
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(
        stale_candidate, failing, generated
    )
    refreshed, refresh_error = runtime_repair.create_repair_candidate(
        stage, stale_candidate, "adaptive_runtime_recovery", 2
    )
    assert refresh_error is None, refresh_error
    assert refreshed is not None
    refreshed_source = (stage / refreshed["local_path"]).read_text(encoding="utf-8")
    assert "https://new-demo.example" in refreshed_source
    assert "https://demo.example" not in refreshed_source
    assert refreshed_source.count("NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4") == 1

    current_candidate = json.loads(json.dumps(refreshed))
    current_candidate["key"] = "test:demo"
    current_candidate.pop("runtime_repair", None)
    current_source = (stage / current_candidate["local_path"]).read_text(encoding="utf-8")
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(
        current_candidate, failing, current_source
    )
    unchanged, unchanged_error = runtime_repair.create_repair_candidate(
        stage, current_candidate, "adaptive_runtime_recovery", 3
    )
    assert unchanged is None
    assert unchanged_error == "structural_profile_made_no_change"

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
    body:'<iframe src="https://player.example/embed/a"></iframe><iframe src="https://second.example/e/b"></iframe><iframe src="https://third.example/player/c"></iframe>'
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
  },
  'https://third.example/player/c':{
    url:'https://third.example/player/c',
    type:'text/html',
    body:'<script>fetch("/api/sources/55").then(r=>r.json())</script>'
  },
  'https://third.example/api/sources/55':{
    url:'https://third.example/api/sources/55',
    type:'application/json',
    body:'{"source":"https://cdn3.example/token/opaque"}'
  },
  'https://cdn3.example/token/opaque':{
    url:'https://cdn3.example/final/no-extension',
    type:'application/vnd.apple.mpegurl',
    body:''
  }
};
function headers(row){return {
  get:(key)=>key.toLowerCase()==='content-type'?(row.type||'text/html'):key.toLowerCase()==='content-disposition'?(row.disposition||null):key.toLowerCase()==='set-cookie'?((row.cookies||[])[0]||null):null,
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
      json:async()=>JSON.parse(row.body||'{"title":"Fixture Movie","release_date":"2020-01-01"}')
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
    assert len(rows) == 3, rows
    assert all("language" not in row for row in rows), rows
    by_url = {row["url"]: row for row in rows}
    first = by_url["https://cdn.example/redirected/master"]
    second = by_url["https://cdn2.example/b/video.mp4"]
    third = by_url["https://cdn3.example/final/no-extension"]
    assert first["isDirect"] is True
    assert third["isDirect"] is True
    assert first["headers"]["Referer"] == "https://player.example/embed/a"
    assert first["headers"]["Origin"] == "https://player.example"
    assert second["headers"]["Referer"] == "https://second.example/e/b"
    assert second["headers"]["Origin"] == "https://second.example"
    assert third["headers"]["Referer"] == "https://third.example/api/sources/55"
    assert third["headers"]["Origin"] == "https://third.example"
    player_call = next(call for call in calls if call["url"] == "https://player.example/embed/a")
    assert "session=abc" in player_call["headers"].get("Cookie", "")
    assert any(call["url"] == "https://third.example/api/sources/55" for call in calls)

    native_provider = stage / "providers" / "native-demo.js"
    native_provider.write_text(
        'module.exports={getStreams:async function(){return [{name:"native",url:"https://native.example/token",headers:{Referer:"https://native.example/watch/1"}}]}};\n',
        encoding="utf-8",
    )
    native_candidate = json.loads(json.dumps(candidate))
    native_candidate["key"] = "test:native-demo"
    native_candidate["canonical_id"] = "native"
    native_candidate["upstream_id"] = "native"
    native_candidate["local_path"] = "providers/native-demo.js"
    native_candidate["metadata"]["id"] = "native-demo"
    native_candidate["metadata"]["name"] = "Native Demo"
    native_candidate["metadata"]["baseUrl"] = "https://native.example"
    native_repaired, native_error = runtime_repair.create_repair_candidate(
        stage, native_candidate, "adaptive_runtime_recovery", 1
    )
    assert native_error is None, native_error
    assert native_repaired is not None
    native_generated = (stage / native_repaired["local_path"]).read_text(encoding="utf-8")
    native_runner = r'''
const vm=require('vm');
const source=process.argv[2];
const calls=[];
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,
  fetch:async(url,options={})=>{calls.push(String(url));return {ok:true,status:200,url:'https://native.example/final/opaque',headers:{get:(k)=>k.toLowerCase()==='content-type'?'video/mp4':null,getSetCookie:()=>[]},text:async()=>''};}
};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie',title:'Fixture Movie',year:2020})
 .then(rows=>console.log(JSON.stringify({rows,calls}))).catch(e=>{console.error(e);process.exit(1)});
'''
    native_runner_path = stage / "native-opaque-test.cjs"
    native_runner_path.write_text(native_runner, encoding="utf-8")
    native_process = subprocess.run(
        ["node", str(native_runner_path), native_generated],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert native_process.returncode == 0, native_process.stderr
    native_payload = json.loads(native_process.stdout.strip())
    assert len(native_payload["rows"]) == 1, native_payload
    assert native_payload["rows"][0]["url"] == "https://native.example/final/opaque"
    assert native_payload["rows"][0]["isDirect"] is True
    assert native_payload["rows"][0]["name"] == "native"
    assert native_payload["calls"] == ["https://native.example/token"]

print("adaptive runtime repair tests passed")
