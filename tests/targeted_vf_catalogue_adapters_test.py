#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.provider_patches import frenchstream_dle_catalogue, streamzo_public_catalogue

BASE_PROVIDER = "module.exports={getStreams:async function(){return []}};\n"


def run_node(source: str, responses: dict, provider: str) -> dict:
    runner = r'''
const vm=require('vm');
const source=process.argv[2];
const responses=JSON.parse(process.argv[3]);
const calls=[];
function makeResponse(url,row){return {
  ok:row.status===undefined||row.status>=200&&row.status<300,
  status:row.status===undefined?200:row.status,
  url:row.finalUrl||url,
  headers:{get:(key)=>key.toLowerCase()==='content-type'?(row.type||'text/html'):null},
  text:async()=>typeof row.body==='string'?row.body:JSON.stringify(row.body||{}),
  json:async()=>typeof row.body==='string'?JSON.parse(row.body):row.body
}}
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,
 fetch:async(url,opts={})=>{url=String(url);calls.push({url,method:opts.method||'GET',body:opts.body||null,headers:opts.headers||{}});let key=(opts.method||'GET')+' '+url;let row=responses[key]||responses[url];if(!row)return makeResponse(url,{status:404,body:''});return makeResponse(url,row)}};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014,settings:{}})
 .then(rows=>console.log(JSON.stringify({rows,calls}))).catch(e=>{console.error(e);process.exit(1)});
'''
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "runner.cjs"
        path.write_text(runner, encoding="utf-8")
        process = subprocess.run(
            ["node", str(path), source, json.dumps(responses)],
            capture_output=True,
            text=True,
            timeout=20,
        )
    assert process.returncode == 0, f"{provider}: {process.stderr}"
    return json.loads(process.stdout.strip())


streamzo_source = streamzo_public_catalogue.apply(BASE_PROVIDER, {"base_url": "https://streamzo.fr"})
assert "NUVIO_STREAMZO_PUBLIC_CATALOGUE_V1" in streamzo_source
streamzo = run_node(
    streamzo_source,
    {
        "https://streamzo.fr/interstellar": {
            "body": '<article class="detail" data-film-id="23254"><button data-embed="/embed/vidnest.fun/23254">Lire</button></article>'
        },
        "https://streamzo.fr/api/mirrors/film/23254": {
            "type": "application/json",
            "body": {"mirrors": [{"url": "/embed/vidzy/23254"}]},
        },
    },
    "streamzo",
)
assert len(streamzo["rows"]) == 2, streamzo
assert {row["url"] for row in streamzo["rows"]} == {
    "https://streamzo.fr/embed/vidnest.fun/23254",
    "https://streamzo.fr/embed/vidzy/23254",
}
assert any(call["url"].endswith("/api/mirrors/film/23254") for call in streamzo["calls"])

french_source = frenchstream_dle_catalogue.apply(
    BASE_PROVIDER,
    {"hub_url": "https://www.fstream.org/", "base_url": "https://fs16.lol"},
)
assert "NUVIO_FRENCHSTREAM_DLE_CATALOGUE_V1" in french_source
french = run_node(
    french_source,
    {
        "https://www.fstream.org/": {"body": '<a href="https://fs16.lol/">adresse</a>'},
        "POST https://fs16.lol/engine/ajax/search.php": {
            "body": '<div class="search-item"><a href="/index.php?newsid=15971" alt="Interstellar 2014"><img alt="Interstellar"></a></div>'
        },
        "https://fs16.lol/?do=search&subaction=search&story=Interstellar": {"body": ""},
        "https://fs16.lol/index.php?newsid=15971": {
            "body": '<h1>Interstellar</h1><iframe src="https://vidzy.example/embed-123.html"></iframe>'
        },
    },
    "frenchstream",
)
assert len(french["rows"]) == 1, french
assert french["rows"][0]["url"] == "https://vidzy.example/embed-123.html"
post = next(call for call in french["calls"] if call["method"] == "POST")
assert post["body"] == "query=Interstellar&page=1"

print("targeted VF catalogue adapter tests passed")
