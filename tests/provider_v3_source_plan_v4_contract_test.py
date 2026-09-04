#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from materialize_provider_v3_all import _identity_mode_from_plan  # noqa: E402
from provider_base_store import (  # noqa: E402
    build_clean_provider_seed,
    build_provider_data_model,
    compose_provider_bundle,
)

GOWARU_REF = "c3ce6f43a1ba8ccf2f3838b5cd9db40745c33fa2"
REQUIRED_GOWARU = {
    "animesama-co",
    "animesultra",
    "animevostfr",
    "dulourd",
    "mugiwarastream",
    "papadustream",
    "sekai",
    "voiranime-homes",
    "voiranime-rip",
    "vostfree",
}


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


def make_bundle(family: str, routes: list[str]) -> bytes:
    base = build_clean_provider_seed("synthetic")
    assert b"NIAKVIO_PROVIDER_BASE_SOURCE_PLAN_V4" in base
    model = build_provider_data_model(
        "synthetic",
        {"id": "synthetic", "name": "Synthetic", "supportedTypes": ["tv"]},
        known_site="https://site.test",
        provider_model={
            "knownSite": "https://site.test",
            "officialSite": "https://site.test",
            "strategy": "mixed_embed_resolver",
            "routes": routes,
            "sourceRuntimeFamily": family,
            "identityInput": {
                "mode": "catalog_search",
                "requiresTmdbBeforeRun": True,
                "requiredFields": ["title", "year", "mediaType"],
            },
        },
    )
    return compose_provider_bundle("synthetic", base, model)


def test_post_form_reader() -> None:
    bundle = make_bundle("catalogue-form-html-embed", ["/template-php/defaut/fetch.php"])
    harness = r'''
const calls=[];
function response(url,body,type){return{ok:true,status:200,url,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?(type||"text/html"):""},text:async()=>body,json:async()=>JSON.parse(body)}}
globalThis.__nuvioMediaContext={tmdbId:"1",tmdbNamespace:"tv",tmdbMetadata:{name:"Example Show",first_air_date:"2020-01-01"}};
globalThis.fetch=async function(input,init){const url=String(input);init=init||{};calls.push({url,method:init.method||"GET",body:init.body||""});if(url.includes("fetch.php"))return response(url,'<a class="va-search-result" href="/example-show/"><span>Example Show</span></a>');if(url.endsWith("/example-show/"))return response(url,'<iframe src="https://cdn.test/example.m3u8"></iframe>');throw new Error("unexpected "+url)};
(async()=>{const p=require(BUNDLE_PATH);const streams=await p.getStreams("1","tv",1,2);console.log(JSON.stringify({streams,calls}))})().catch(e=>{console.error(e);process.exit(1)});
'''
    data = run_node(bundle, harness)
    assert data["streams"] and data["streams"][0]["url"] == "https://cdn.test/example.m3u8"
    first = data["calls"][0]
    assert first["method"] == "POST", first
    assert "query=Example%20Show" in first["body"], first


def test_metadata_gate() -> None:
    bundle = make_bundle("catalogue-form-html-embed", ["/template-php/defaut/fetch.php"])
    harness = r'''
let calls=0;globalThis.fetch=async function(){calls++;throw new Error("provider network must stay gated")};
(async()=>{const p=require(BUNDLE_PATH);const streams=await p.getStreams("1","tv",1,2);console.log(JSON.stringify({streams,calls}))})().catch(e=>{console.error(e);process.exit(1)});
'''
    data = run_node(bundle, harness)
    assert data == {"streams": [], "calls": 0}, data


def test_get_search_reader() -> None:
    bundle = make_bundle("wordpress-search-episode", ["/?s={query}"])
    harness = r'''
const calls=[];
function response(url,body){return{ok:true,status:200,url,headers:{get:()=>"text/html"},text:async()=>body,json:async()=>JSON.parse(body)}}
globalThis.__nuvioMediaContext={tmdbId:"1",tmdbNamespace:"tv",tmdbMetadata:{name:"Example Show",first_air_date:"2020-01-01"}};
globalThis.fetch=async function(input,init){const url=String(input);calls.push(url);if(url.includes("?s=Example%20Show"))return response(url,'<a href="/animes/example-show/">Example Show</a>');if(url.endsWith("/animes/example-show/"))return response(url,'<a href="/animes/example-show/saison-1/episode-2/">Episode 2</a>');if(url.includes("/episode-2/"))return response(url,'<iframe src="https://cdn.test/example-2.m3u8"></iframe>');throw new Error("unexpected "+url)};
(async()=>{const p=require(BUNDLE_PATH);const streams=await p.getStreams("1","tv",1,2);console.log(JSON.stringify({streams,calls}))})().catch(e=>{console.error(e);process.exit(1)});
'''
    data = run_node(bundle, harness)
    assert data["streams"] and data["streams"][0]["url"] == "https://cdn.test/example-2.m3u8", data


def main() -> int:
    assert _identity_mode_from_plan(["/?do=search&subaction=search&story={query}"], None) == "catalog_search"
    assert _identity_mode_from_plan(["/template-php/defaut/fetch.php"], None) == "catalog_search"
    assert _identity_mode_from_plan(["/{slug}"], None) == "catalog_search"

    knowledge = json.loads((ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8"))
    assert knowledge.get("gowaruSourceRef") == GOWARU_REF
    providers = knowledge.get("providers") or {}
    for provider_id in REQUIRED_GOWARU:
        row = providers.get(provider_id) or {}
        model = row.get("model") or {}
        assert model.get("sourceKnowledgeRef") == GOWARU_REF, provider_id
        assert model.get("routes"), provider_id
        assert str(model.get("sourceRuntimeFamily") or "unknown") != "unknown", provider_id

    test_post_form_reader()
    test_metadata_gate()
    test_get_search_reader()
    print("PROVIDER_V3_SOURCE_PLAN_V4_CONTRACT_OK gowaru=10 synthetic_runtime=3 metadata_gate=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
