#!/usr/bin/env python3
"""Deterministic crypto/runtime contract for the clean-v3 VidRock Lego."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))
PATCH = ROOT / "scripts/provider_patches/vidrock_runtime_v1.py"


def load_patch():
    spec = importlib.util.spec_from_file_location("vidrock_runtime_crypto_test_module", PATCH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_node(wrapper: str) -> dict:
    key_hex = "7f3e9c2a8b5d1f4e6a9c3b7d2e5f8a1c4b6d9e2f5a8c1b4d7e9f2a5c8b1d4e7f"
    movie_url = "https://cdn.example.test/movie/master.m3u8"
    tv_url = "https://cdn.example.test/tv/master.m3u8"
    node = f"""
const crypto=require('crypto');
const key=Buffer.from({json.dumps(key_hex)},'hex');
function token(plain,tamper=false){{
  const iv=Buffer.from('00112233445566778899aabb','hex');
  const c=crypto.createCipheriv('aes-256-gcm',key,iv);
  const ct=Buffer.concat([c.update(Buffer.from(plain,'utf8')),c.final()]);
  const tag=c.getAuthTag(); if(tamper) tag[0]^=1;
  return Buffer.concat([iv,ct,tag]).toString('base64').replace(/\\+/g,'-').replace(/\\//g,'_').replace(/=+$/,'');
}}
const movieToken=token({json.dumps(movie_url)});
const tvToken=token({json.dumps(tv_url)});
const badToken=token('https://cdn.example.test/bad/master.m3u8',true);
const calls=[];
globalThis.getStreams=async function(){{return []}};
globalThis.fetch=async function(url,opts){{
  url=String(url); calls.push({{url,headers:(opts&&opts.headers)||{{}}}});
  if(url==='https://vidrock.ru/api/movie/157336') return {{ok:true,status:200,json:async()=>({{Atlas:{{url:movieToken}}}})}};
  if(url==='https://vidrock.ru/api/tv/1396/1/1') return {{ok:true,status:200,json:async()=>({{Atlas:{{url:tvToken}}}})}};
  if(url==='https://vidrock.ru/api/movie/999') return {{ok:true,status:200,json:async()=>({{Atlas:{{url:badToken}}}})}};
  if(url==={json.dumps(movie_url)}) return {{ok:true,status:200,text:async()=> '#EXTM3U\\n#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=1920x1080\\nmovie.m3u8\\n'}};
  if(url==={json.dumps(tv_url)}) return {{ok:true,status:200,text:async()=> '#EXTM3U\\n#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=1280x720\\ntv.m3u8\\n'}};
  throw new Error('unexpected fetch '+url);
}};
{wrapper}
(async()=>{{
  const movie=await globalThis.getStreams('157336','movie');
  const tv=await globalThis.getStreams('1396','tv',1,1);
  const tampered=await globalThis.getStreams('999','movie');
  const imdb=await globalThis.getStreams('tt0816692','movie');
  process.stdout.write(JSON.stringify({{movie,tv,tampered,imdb,calls}}));
}})().catch(e=>{{console.error(e);process.exit(1)}});
"""
    completed = subprocess.run(
        ["node", "-e", node], cwd=ROOT, capture_output=True, text=True, timeout=30, check=False
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


def main() -> int:
    module = load_patch()
    assert module.MANAGED_FIX_ID == "PROVIDER.VIDROCK.RUNTIME.V1"
    assert module.MARKER == "NIAKVIO_VIDROCK_RUNTIME_V1"
    payload = {
        "base": "https://vidrock.ru",
        "keyHex": "7f3e9c2a8b5d1f4e6a9c3b7d2e5f8a1c4b6d9e2f5a8c1b4d7e9f2a5c8b1d4e7f",
        "origin": "https://vidrock.net",
        "referer": "https://vidrock.net/",
        "userAgent": "NiakVIO-VidRock-Test",
        "serverOrder": ["Atlas", "Luna", "Orion", "Astra", "Nova"],
        "maxStreams": 5,
    }
    wrapper = module.WRAPPER.replace(
        "CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
    result = run_node(wrapper)
    assert len(result["movie"]) == 1, result
    assert result["movie"][0]["url"] == "https://cdn.example.test/movie/master.m3u8"
    assert result["movie"][0]["quality"] == "1080p"
    assert result["movie"][0]["headers"]["Origin"] == "https://vidrock.net"
    assert len(result["tv"]) == 1, result
    assert result["tv"][0]["url"] == "https://cdn.example.test/tv/master.m3u8"
    assert result["tv"][0]["quality"] == "720p"
    assert result["tampered"] == [], "authentication-tag corruption must fail closed"
    assert result["imdb"] == [], "non-numeric raw id must fail before provider network"
    urls = [row["url"] for row in result["calls"]]
    assert "https://vidrock.ru/api/movie/157336" in urls
    assert "https://vidrock.ru/api/tv/1396/1/1" in urls
    assert not any("tt0816692" in url for url in urls)
    print("VIDROCK_RUNTIME_CRYPTO_OK movie=1 tv=1 tag_tamper=fail_closed imdb_network=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
