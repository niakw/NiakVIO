#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_base_store import (  # noqa: E402
    build_clean_provider_seed,
    build_provider_data_model,
    compose_provider_bundle,
)


def run_node(bundle: bytes, harness: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "provider.js"
        path.write_bytes(bundle)
        script = harness.replace("BUNDLE_PATH", json.dumps(str(path)))
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise AssertionError(result.stdout + "\n" + result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if not lines:
            raise AssertionError("node harness produced no JSON")
        return json.loads(lines[-1])


def make_direct_recipe_bundle() -> bytes:
    base = build_clean_provider_seed("synthetic-direct")
    model = build_provider_data_model(
        "synthetic-direct",
        {
            "id": "synthetic-direct",
            "name": "Synthetic Direct",
            "supportedTypes": ["movie", "tv"],
        },
        known_site="https://resolver.test",
        provider_model={
            "knownSite": "https://resolver.test",
            "officialSite": "https://resolver.test",
            "officialApi": "https://resolver.test",
            "strategy": "direct_media",
            "routes": [
                "https://resolver.test/api.php?tmdb={tmdbId}&type={media}",
                "https://resolver.test/api.php?tmdb={tmdbId}&type={media}&season={season}&episode={episode}",
            ],
            "sourceRuntimeFamily": "tmdb-direct-api",
            "apiRecipe": {
                "recipeKind": "typed-resolver-api",
                "allowGenericFallback": False,
                "movieRoute": "https://resolver.test/api.php?tmdb={tmdbId}&type=movie",
                "episodeRoute": "https://resolver.test/api.php?tmdb={tmdbId}&type=tv&season={season}&episode={episode}",
                "movieRequest": {"method": "GET"},
                "episodeRequest": {"method": "GET"},
            },
            "identityInput": {
                "mode": "tmdb_direct",
                "requiresTmdbBeforeRun": False,
                "requiredFields": ["tmdbId", "mediaType"],
            },
        },
    )
    return compose_provider_bundle("synthetic-direct", base, model)


def test_numeric_tmdb_survives_without_metadata() -> None:
    bundle = make_direct_recipe_bundle()
    assert b"NIAKVIO_PROVIDER_RAW_TMDB_ROUTE_IDENTITY_V19" in bundle
    harness = r'''
const calls=[];
function response(url,body){return{ok:true,status:200,url,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?"text/plain":""},text:async()=>body,json:async()=>JSON.parse(body)}}
globalThis.fetch=async function(input){const url=String(input);calls.push(url);return response(url,"https://cdn.test/interstellar.m3u8")};
(async()=>{const p=require(BUNDLE_PATH);const streams=await p.getStreams("157336","movie");console.log(JSON.stringify({streams,calls}))})().catch(e=>{console.error(e);process.exit(1)});
'''
    data = run_node(bundle, harness)
    assert data["calls"] == ["https://resolver.test/api.php?tmdb=157336&type=movie"], data
    assert data["streams"] and data["streams"][0]["url"] == "https://cdn.test/interstellar.m3u8", data


def test_non_tmdb_identity_fails_closed_without_empty_request() -> None:
    bundle = make_direct_recipe_bundle()
    harness = r'''
let calls=0;globalThis.fetch=async function(){calls++;throw new Error("typed resolver must not receive an empty TMDB request")};
(async()=>{const p=require(BUNDLE_PATH);const streams=await p.getStreams("tt0816692","movie");console.log(JSON.stringify({streams,calls}))})().catch(e=>{console.error(e);process.exit(1)});
'''
    data = run_node(bundle, harness)
    assert data == {"streams": [], "calls": 0}, data


def main() -> int:
    test_numeric_tmdb_survives_without_metadata()
    test_non_tmdb_identity_fails_closed_without_empty_request()
    print("PROVIDER_RAW_TMDB_ROUTE_IDENTITY_OK numeric_tmdb_preserved=1 metadata_optional=1 imdb_empty_request=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
