#!/usr/bin/env python3
"""Verify generated Brain JavaScript samples original/localized TMDB title aliases fairly."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote_plus

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "adaptive_runtime"))
from runtime_recovery_generator import apply  # noqa: E402

with tempfile.TemporaryDirectory(prefix="brain-alias-test-") as work:
    wd = Path(work)
    generated = apply(
        "module.exports={getStreams:async function(){return []}};\n",
        {
            "provider_name": "Synthetic Catalogue",
            "base_url": "https://demo.example",
            "search_paths": ["/?s={query}"] + [f"/search{i}?q={{query}}" for i in range(1, 18)],
            "types": ["movie"],
            "alias_search": True,
            "max_pages": 12,
            "max_embeds": 4,
            "timeout_ms": 2000,
        },
    )
    source = wd / "source.cjs"
    source.write_text(generated, encoding="utf-8")
    runner = r'''
const fs=require('fs'),vm=require('vm'),source=fs.readFileSync(process.argv[2],'utf8'),calls=[];
const meta={title:'Titre local',original_title:'Original Title',release_date:'2026-01-01',alternative_titles:{titles:[]}};
const ctx={
 module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
 fetch:async function(u){
   const url=String(u);calls.push(url);
   const isTmdb=url.includes('api.themoviedb.org');
   return {ok:true,status:200,url,headers:{get:k=>k.toLowerCase()==='content-type'?(isTmdb?'application/json':'text/html'):null},
     json:async()=>meta,text:async()=>isTmdb?JSON.stringify(meta):'<html>No matching detail</html>'};
 }
};
ctx.globalThis=ctx;
vm.runInNewContext(source,ctx,{timeout:5000});
ctx.module.exports.getStreams({tmdbId:'123',mediaType:'movie',title:'Titre local',year:2026})
 .then(rows=>process.stdout.write(JSON.stringify({rows,calls})))
 .catch(e=>{console.error(e);process.exit(1)});
'''
    js = wd / "runner.cjs"
    js.write_text(runner, encoding="utf-8")
    task = subprocess.run(["node", str(js), str(source)], capture_output=True, text=True, timeout=25)
    assert task.returncode == 0, task.stderr
    output = json.loads(task.stdout.strip())
    searches = [unquote_plus(x) for x in output["calls"] if "demo.example" in x]
    assert 2 <= len(searches) <= 12, searches
    assert any("Titre local" in x for x in searches), searches
    assert any("Original Title" in x for x in searches), "aliases starved by first search path: " + repr(searches)
    assert output["rows"] == [], "absence of matching content cannot fabricate media"

print("Brain localized/original title alias fair-share execution passed")
