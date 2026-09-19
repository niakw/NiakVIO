#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/allanime_site_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["allanime"]

assert "NIAKVIO_ALLANIME_GRAPHQL_RUNTIME_V2" in src
for needle in (
    "https://api.allanime.day/api",
    "https://allanime.day",
    "VaildTranslationTypeEnumType",
    "sourceUrls",
    "tobeparsed",
    "Xot36i3lK3:v1",
    "AES-CTR",
    "clock.json",
    "function decodeSource",
    "function directPlayable",
    "https://ww2.aniwatch.fit",
    "siteFallback",
    '-episode-"+episodes[ei]+"-"+modes[mi].suffix',
    "function fetchSitePage(page)",
    "function siteCandidates(html,page)",
    'typeof _extractUrls==="function"',
    'typeof _spv241ExplicitPlayerPayloadUrls==="function"',
    "rows=await _crawlDirectMedia(candidates,doc.url,3)",
    "rows=await _crawlDirectMedia([doc.url],doc.url,3)",
    'provider:"allanime",resolve:resolve',
):
    assert needle in src, needle

assert ov["provider_lego_scripts"]==["scripts/provider_patches/allanime_site_runtime_v1.py"]
assert ov["source_runtime_family"]=="graphql-source-clock"
assert ov["learned_routes"]==["/api","/apivtwo/clock.json"]
assert ov["reconstruction_state"]=="provider-local-current-api"

js=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0].replace("CONFIG_PLACEHOLDER","{}")
subprocess.run(["node","-e","new Function(process.argv[1]);",js],check=True)

print("AllAnime GraphQL + observed site fallback runtime contract passed")
