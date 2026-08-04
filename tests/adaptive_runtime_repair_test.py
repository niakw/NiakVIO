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
    source = provider.read_text(encoding="utf-8")
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(
        candidate, failing, source
    )
    assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(
        candidate, healthy, source
    )

    repaired, error = runtime_repair.create_repair_candidate(
        stage, candidate, "adaptive_runtime_recovery", 1
    )
    assert error is None, error
    assert repaired is not None
    target = stage / repaired["local_path"]
    assert target.is_file()
    generated = target.read_text(encoding="utf-8")
    assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V2" in generated
    assert repaired["runtime_repair"]["profile"] == ""
    assert repaired["runtime_repair"]["strategy"] == "adaptive_runtime_recovery"

    runner = r'''
const vm=require('vm');
const source=process.argv[2];
const responses={
  'https://demo.example/?s=Fixture%20Movie':'<a href="/film/fixture-movie">Fixture Movie 2020</a>',
  'https://demo.example/film/fixture-movie':'<iframe src="https://player.example/embed/a"></iframe><iframe src="https://second.example/e/b"></iframe>',
  'https://player.example/embed/a':'<source src="https://cdn.example/a/master.m3u8">',
  'https://second.example/e/b':'<script>var source="https://cdn2.example/b/video.mp4"</script>'
};
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,
  fetch:async(url)=>({
    ok:true,url:String(url),
    text:async()=>responses[String(url)]||'',
    json:async()=>({title:'Fixture Movie',release_date:'2020-01-01'})
  })
};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie',title:'Fixture Movie',year:2020})
  .then(rows=>console.log(JSON.stringify(rows)))
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
    rows = json.loads(process.stdout.strip())
    assert len(rows) == 2, rows
    by_url = {row["url"]: row for row in rows}
    first = by_url["https://cdn.example/a/master.m3u8"]
    second = by_url["https://cdn2.example/b/video.mp4"]
    assert first["headers"]["Referer"] == "https://player.example/embed/a"
    assert first["headers"]["Origin"] == "https://player.example"
    assert second["headers"]["Referer"] == "https://second.example/e/b"
    assert second["headers"]["Origin"] == "https://second.example"

print("adaptive runtime repair tests passed")
