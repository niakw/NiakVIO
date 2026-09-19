#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
URL_LITERAL_RE = re.compile(r"https?://[^\"'\s}]+")

def literal_url_hosts(value: str) -> set[str]:
    return {host for raw in URL_LITERAL_RE.findall(value) if (host := urlsplit(raw).hostname)}

sys.path.insert(0, str(ROOT / "scripts" / "adaptive_runtime"))
sys.path.insert(1, str(ROOT / "scripts"))

import runtime_repair  # noqa: E402


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


with tempfile.TemporaryDirectory() as directory:
    stage = Path(directory)
    provider = stage / "providers" / "demo.js"
    provider.parent.mkdir(parents=True)
    provider.write_text("module.exports={getStreams:async function(){return []}};\n", encoding="utf-8")
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
    healthy = {"status": "healthy", "tests": [], "evidence": {"streams_returned": 1, "streams_playable": 1}}
    healthy_without_playable = {
        "status": "healthy",
        "tests": [{"failure_class": "content_lookup_completed_no_streams", "streams_playable": 0}],
        "evidence": {"streams_returned": 0, "streams_playable": 0},
    }
    source = provider.read_text(encoding="utf-8")
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(candidate, failing, source)
    assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(candidate, healthy, source)
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(candidate, healthy_without_playable, source)

    repaired, error = runtime_repair.create_repair_candidate(stage, candidate, "adaptive_runtime_recovery", 1)
    assert error is None, error
    assert repaired is not None
    generated = (stage / repaired["local_path"]).read_text(encoding="utf-8")
    assert "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5" in generated
    assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4" not in generated
    assert '"runtimeRevision":"generic-core-v3"' in generated
    assert 'language:"fr"' not in generated
    assert repaired["runtime_repair"]["profile"] == ""
    assert repaired["runtime_repair"]["strategy"] == "adaptive_runtime_recovery"
    assert repaired["runtime_repair"]["revision"] == 5

    # A later domain migration must replace the V5 wrapper before peer inference;
    # the obsolete base must not leak back as a generated endpoint peer.
    stale_candidate = json.loads(json.dumps(repaired))
    stale_candidate["key"] = "test:demo"
    stale_candidate.pop("runtime_repair", None)
    stale_candidate["metadata"]["baseUrl"] = "https://new-demo.example"
    refreshed, refresh_error = runtime_repair.create_repair_candidate(stage, stale_candidate, "adaptive_runtime_recovery", 2)
    assert refresh_error is None, refresh_error
    assert refreshed is not None
    refreshed_source = (stage / refreshed["local_path"]).read_text(encoding="utf-8")
    refreshed_hosts = literal_url_hosts(refreshed_source)
    assert "new-demo.example" in refreshed_hosts
    assert "demo.example" not in refreshed_hosts
    assert refreshed_source.count("NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5") == 1

    current_candidate = json.loads(json.dumps(refreshed))
    current_candidate["key"] = "test:demo"
    current_candidate.pop("runtime_repair", None)
    unchanged, unchanged_error = runtime_repair.create_repair_candidate(stage, current_candidate, "adaptive_runtime_recovery", 3)
    assert unchanged is None
    assert unchanged_error == "structural_profile_made_no_change"

    # The historical V4 migrator must ignore the distinct V5 marker, even when
    # provenance still contains the generic adaptive profile name.
    reapply = load("reapply_overrides_for_v5_test", ROOT / "scripts" / "reapply_published_overrides.py")
    legacy_provenance = {"local_patches": [{
        "type": "patch_profile", "profile": "adaptive_runtime_recovery", "phase": "runtime",
        "options": {"provider_name": "Demo", "base_url": "https://new-demo.example", "types": ["movie"]},
    }]}
    persisted, migration_records = reapply.reapply_adaptive_runtime_revision(refreshed_source.encode(), legacy_provenance)
    assert persisted.decode() == refreshed_source
    assert migration_records == []

    # Generic nested-player recovery: strong MIME is accepted, opaque MIME is
    # accepted, and a media-looking .mp4 must be network-verified before return.
    runner = r'''
const vm=require('vm');
const source=process.argv[2];
const calls=[];
const responses={
  'https://new-demo.example/?s=Fixture%20Movie':{url:'https://new-demo.example/search/final',type:'text/html',body:'<a href="../film/fixture-movie">Fixture Movie 2020</a>',cookies:['session=abc; Path=/']},
  'https://new-demo.example/film/fixture-movie':{url:'https://new-demo.example/film/fixture-movie',type:'text/html',body:'<iframe src="https://player.example/embed/a"></iframe><iframe src="https://second.example/e/b"></iframe><iframe src="https://third.example/player/c"></iframe>'},
  'https://player.example/embed/a':{url:'https://player.example/embed/a',type:'text/html',body:'<source src="https://cdn.example/media/token">',cookies:['player=xyz; Path=/']},
  'https://cdn.example/media/token':{url:'https://cdn.example/redirected/master',type:'application/vnd.apple.mpegurl',body:''},
  'https://second.example/e/b':{url:'https://second.example/e/b',type:'text/html',body:'<script>var source="https://cdn2.example/b/video.mp4"</script>'},
  'https://cdn2.example/b/video.mp4':{url:'https://cdn2.example/b/video.mp4',type:'video/mp4',body:''},
  'https://third.example/player/c':{url:'https://third.example/player/c',type:'text/html',body:'<script>fetch("/api/sources/55").then(r=>r.json())</script>'},
  'https://third.example/api/sources/55':{url:'https://third.example/api/sources/55',type:'application/json',body:'{"source":"https://cdn3.example/token/opaque"}'},
  'https://cdn3.example/token/opaque':{url:'https://cdn3.example/final/no-extension',type:'application/vnd.apple.mpegurl',body:''}
};
function headers(row){return {get:(key)=>key.toLowerCase()==='content-type'?(row.type||'text/html'):key.toLowerCase()==='content-disposition'?(row.disposition||null):key.toLowerCase()==='set-cookie'?((row.cookies||[])[0]||null):null,getSetCookie:()=>row.cookies||[]}}
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  fetch:async(url,options={})=>{const key=String(url);calls.push({url:key,headers:options.headers||{}});const row=responses[key]||{url:key,type:'text/html',body:''};return {ok:true,status:200,url:row.url||key,headers:headers(row),text:async()=>row.body||'',json:async()=>JSON.parse(row.body||'{"title":"Fixture Movie","release_date":"2020-01-01"}')}}
};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie',title:'Fixture Movie',year:2020}).then(rows=>console.log(JSON.stringify({rows,calls}))).catch(error=>{console.error(error);process.exit(1)});
'''
    runner_path = stage / "nested-player-test.cjs"
    runner_path.write_text(runner, encoding="utf-8")
    process = subprocess.run(["node", str(runner_path), refreshed_source], capture_output=True, text=True, timeout=20)
    assert process.returncode == 0, process.stderr
    payload = json.loads(process.stdout.strip())
    rows = payload["rows"]
    calls = payload["calls"]
    assert len(rows) == 3, rows
    by_url = {row["url"]: row for row in rows}
    assert set(by_url) == {
        "https://cdn.example/redirected/master",
        "https://cdn2.example/b/video.mp4",
        "https://cdn3.example/final/no-extension",
    }, rows
    assert all(row["isDirect"] is True for row in rows)
    assert by_url["https://cdn.example/redirected/master"]["headers"]["Referer"] == "https://player.example/embed/a"
    assert by_url["https://cdn2.example/b/video.mp4"]["headers"]["Referer"] == "https://second.example/e/b"
    assert by_url["https://cdn3.example/final/no-extension"]["headers"]["Referer"] == "https://third.example/api/sources/55"
    assert any(call["url"] == "https://cdn2.example/b/video.mp4" for call in calls), "extension-only media was not probed"

    native_provider = stage / "providers" / "native-demo.js"
    native_provider.write_text('module.exports={getStreams:async function(){return [{name:"native",url:"https://native.example/token",headers:{Referer:"https://native.example/watch/1"}}]}};\n', encoding="utf-8")
    native_candidate = json.loads(json.dumps(candidate))
    native_candidate.update({"key": "test:native-demo", "canonical_id": "native", "upstream_id": "native", "local_path": "providers/native-demo.js"})
    native_candidate["metadata"].update({"id": "native-demo", "name": "Native Demo", "baseUrl": "https://native.example"})
    native_repaired, native_error = runtime_repair.create_repair_candidate(stage, native_candidate, "adaptive_runtime_recovery", 1)
    assert native_error is None, native_error
    native_generated = (stage / native_repaired["local_path"]).read_text(encoding="utf-8")
    native_runner = r'''
const vm=require('vm');const source=process.argv[2],calls=[];
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,fetch:async(url)=>{calls.push(String(url));return {ok:true,status:200,url:'https://native.example/final/opaque',headers:{get:(k)=>k.toLowerCase()==='content-type'?'video/mp4':null,getSetCookie:()=>[]},text:async()=>''}}};sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie',title:'Fixture Movie',year:2020}).then(rows=>console.log(JSON.stringify({rows,calls}))).catch(e=>{console.error(e);process.exit(1)});
'''
    native_runner_path = stage / "native-opaque-test.cjs"
    native_runner_path.write_text(native_runner, encoding="utf-8")
    native_process = subprocess.run(["node", str(native_runner_path), native_generated], capture_output=True, text=True, timeout=20)
    assert native_process.returncode == 0, native_process.stderr
    native_payload = json.loads(native_process.stdout.strip())
    assert len(native_payload["rows"]) == 1, native_payload
    assert native_payload["rows"][0]["url"] == "https://native.example/final/opaque"
    assert native_payload["rows"][0]["name"] == "native"
    assert native_payload["calls"] == ["https://native.example/token"]

print("adaptive runtime repair tests passed")
