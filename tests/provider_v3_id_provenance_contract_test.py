#!/usr/bin/env python3
"""Ambiguous provider {id} must never be fabricated from TMDB for catalogue plans."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "provider_base_store.py"
spec = importlib.util.spec_from_file_location("provider_base_store", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def bundle(mode: str, route: str, strategy: str = "api_stream_resolver") -> str:
    base = mod.build_clean_provider_seed("synthetic")
    model = mod.build_provider_data_model(
        "synthetic",
        {"name": "Synthetic", "supportedTypes": ["movie", "tv"]},
        known_site="https://api.example.test",
        provider_model={
            "strategy": strategy,
            "officialApi": "https://api.example.test",
            "officialSite": "https://api.example.test",
            "routes": [route],
            "identityInput": {
                "mode": mode,
                "requiresTmdbBeforeRun": mode != "tmdb_direct",
                "requiredFields": ["tmdbId", "mediaType"],
            },
        },
    )
    return mod.compose_provider_bundle("synthetic", base, model).decode("utf-8")


RUNNER = r"""
const provider=require(process.argv[2]);
const expected=process.argv[3];
const calls=[];
global.fetch=async(url)=>{
  url=String(url);calls.push(url);
  return{
    ok:true,status:200,url,
    headers:{get:()=> 'application/json'},
    json:async()=>({url:'https://cdn.example.test/video.m3u8'}),
    text:async()=> '{"url":"https://cdn.example.test/video.m3u8"}'
  };
};
(async()=>{
  const rows=await provider.getStreams('157336','movie');
  if(expected==='none'){
    if(calls.length!==0)throw new Error('catalogue plan fabricated network call: '+calls.join(','));
    if(!Array.isArray(rows)||rows.length!==0)throw new Error('catalogue ambiguous-id plan must stay empty');
  }else{
    if(calls.length<1)throw new Error('expected explicit/direct route call');
    if(calls[0]!==expected)throw new Error('unexpected route '+calls[0]+' expected '+expected);
    if(!Array.isArray(rows)||rows.length<1)throw new Error('valid direct route lost');
  }
})().catch(e=>{console.error(e);process.exit(1)});
"""


def run(source: str, expected: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(source, encoding="utf-8")
        runner.write_text(RUNNER, encoding="utf-8")
        result = subprocess.run(
            ["node", str(runner), str(provider), expected],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


# Provider/session/file ids obtained after a search are not TMDB ids.
run(bundle("catalog_search", "/api/resolve?id={id}"), "none")

# Explicit provenance remains executable even in a catalogue-capable model.
run(
    bundle("catalog_search", "/api/resolve?tmdb={tmdbId}"),
    "https://api.example.test/api/resolve?tmdb=157336",
)

# Direct providers retain backwards-compatible implicit {id}=TMDB behavior.
run(
    bundle("tmdb_direct", "/api/resolve?id={id}"),
    "https://api.example.test/api/resolve?id=157336",
)

# A bare /player route may only synthesize ?id=TMDB for tmdb_direct providers.
run(bundle("catalog_search", "/player", strategy="iframe_player"), "none")

print("provider v3 id provenance contract passed")
