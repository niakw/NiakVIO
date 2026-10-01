#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"scripts"/"response_variant_hints.cjs"
runner=r"""
const {extractResponseVariantHints}=require(process.argv[1]);
const coflix={status:true,message:Array.from({length:9},(_,i)=>({server_link:"https://srv"+(i+1)+".example/e/"+(i+1),version:"VF"}))};
const papa='<h3>480p Download Links</h3> "link":"https://filemoon.test/e/1" '+
 '<h3>720p Download Links</h3> "link":"https://vidzy.test/e/2" '+
 '<h3>720p Download Links</h3> "link":"https://uqload.test/e/3" '+
 '<h3>1080p Download Links</h3> "link":"https://doply.test/e/4" '+
 '<h3>1080p Download Links</h3> "link":"https://sandratableother.test/e/5" '+
 '<h3>2160p 4K Download Links</h3> "link":"https://multiup.test/e/6"';
const nav='<a href="https://example.test/about">About</a><img src="https://cdn.example/poster.jpg">';
console.log(JSON.stringify({
 coflix:extractResponseVariantHints(coflix,{baseUrl:"https://coflix.test/ajax/player"}),
 papa:extractResponseVariantHints(papa,{baseUrl:"https://papa.test/movie/x"}),
 nav:extractResponseVariantHints(nav,{baseUrl:"https://example.test/"})
}));
"""
proc=subprocess.run(["node","-e",runner,str(MODULE)],cwd=ROOT,text=True,capture_output=True,check=True)
data=json.loads(proc.stdout)
assert data["coflix"]["declared_player_candidate_count"]==9,data
assert len(data["coflix"]["declared_player_hosts"])==9,data
assert data["papa"]["declared_player_candidate_count"]==6,data
assert data["papa"]["declared_quality_heights"]==[480,720,1080,2160],data
assert data["nav"]["declared_player_candidate_count"]==0,data
serialized=json.dumps(data)
assert "/e/1" not in serialized and "https://filemoon.test/e/1" not in serialized,data
worker=(ROOT/"scripts"/"provider_worker.cjs").read_text(encoding="utf-8")
assert "extractResponseVariantHints" in worker
assert "declared_player_candidate_count" in worker
print("provider response variant fan-out diagnostics passed")
