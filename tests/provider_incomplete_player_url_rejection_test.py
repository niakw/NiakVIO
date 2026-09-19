#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from provider_base_store import build_clean_provider_seed, build_provider_data_model, compose_provider_bundle

model=build_provider_data_model(
    "demo",
    {"name":"Demo","supportedTypes":["movie"]},
    known_site="https://provider.example",
    provider_model={"strategy":"html_scraper","officialSite":"https://provider.example","routes":["/?s={query}"],"routeProofVersion":5},
)
source=compose_provider_bundle("demo",build_clean_provider_seed("demo"),model).decode("utf-8")
source += r'''
console.log(JSON.stringify({
  incompleteMovie:_crawlEligible("https://player.autoembed.cc/embed/movie/"),
  incompleteTv:_crawlEligible("https://player.example/player/tv"),
  completeMovie:_crawlEligible("https://player.autoembed.cc/embed/movie/157336"),
  completeQuery:_crawlEligible("https://player.example/embed/movie?id=157336"),
  direct:_crawlEligible("https://cdn.example/video.m3u8")
}));
'''
with tempfile.TemporaryDirectory() as td:
    path=Path(td)/"probe.js"
    path.write_text(source,encoding="utf-8")
    proc=subprocess.run(["node",str(path)],capture_output=True,text=True,check=True,cwd=ROOT)
row=__import__("json").loads(proc.stdout.strip().splitlines()[-1])
assert row["incompleteMovie"] is False,row
assert row["incompleteTv"] is False,row
assert row["completeMovie"] is True,row
assert row["completeQuery"] is True,row
assert row["direct"] is True,row
print("provider incomplete player URL rejection passed")
