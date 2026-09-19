#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.provider_v3_minimizer import minimize_text
src=(ROOT/"scripts/provider_patches/allanime_site_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["allanime"]

assert "NIAKVIO_ALLANIME_GRAPHQL_RUNTIME_V3" in src
for needle in (
    "https://api.mkissa.net/api",
    "https://mkissa.to",
    "https://cdn.mkissa.net/all/mk/_app/immutable",
    "https://api.allanime.day/api",
    "https://allanime.day",
    "VaildTranslationTypeEnumType",
    "sourceUrls",
    "tobeparsed",
    "f4662f4b7510b26795dd53ef824a0bf1740fbbc5d1273fab18222ac831bca8d0",
    "d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec",
    "aaReq",
    "partB",
    "AES-GCM",
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
assert ov["source_runtime_family"]=="allanime-mkissa-aaReq-gcm-plus-legacy-ctr-v5"
assert ov["learned_routes"]==["/api","/apivtwo/clock.json"]
assert ov["reconstruction_state"]=="provider-local-current-api-dual"
opts=ov["provider_lego_options"]["scripts/provider_patches/allanime_site_runtime_v1.py"]
assert opts["currentApi"]=="https://api.mkissa.net/api"
assert opts["currentOrigin"]=="https://mkissa.to"

js=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0].replace("CONFIG_PLACEHOLDER","{}")
assert "if(!out.length)out=await siteFallback(meta,q);" in js
minimized=minimize_text(js).text
assert "\n" not in minimized and "\r" not in minimized
subprocess.run(["node","-e","new Function(process.argv[1]);",minimized],check=True)
subprocess.run(["node","-e","new Function(process.argv[1]);",js],check=True)

print("AllAnime GraphQL + observed site fallback runtime contract passed")
