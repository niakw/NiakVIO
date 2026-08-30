#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
TEST = ROOT / "tests/global_media_type_resolution_test.py"
KEY_CONTRACT = ROOT / "tests/provider_tmdb_runtime_key_contract_test.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def patch_resolver() -> None:
    text = RESOLVER.read_text(encoding="utf-8")

    old_doc = '''No NiakVIO credential is embedded. The resolver first reuses a runtime/provider
TMDB credential when one already exists; otherwise it may classify TV-shaped
requests from the public TMDB title page. Object-style requests can also carry
trusted metadata directly. Ambiguous TV/anime metadata failure is fail-closed.
TMDB identity is namespaced: anime-series share the TMDB TV namespace.
'''
    new_doc = '''TMDB API metadata is authoritative when available. The build may embed an
obfuscated runtime-only TMDB v3 API key generated from the repository secret;
the plaintext key is never committed and is never passed into provider business
logic. Object-style requests can also carry trusted TMDB metadata directly.

A conclusive TMDB classification still enforces provider semantic capabilities.
Only infrastructure failure (timeout/network/auth/rate-limit/5xx/unparseable
response) degrades to a fail-open transport/semantic fallback so one metadata
outage cannot suppress the entire provider catalogue. No public HTML scraping is
used as a classification substitute.
'''
    text = replace_once(text, old_doc, new_doc, "resolver docstring")

    text = replace_once(
        text,
        "import json\nfrom typing import Any\n",
        "import json\nfrom pathlib import Path\nfrom typing import Any\n",
        "resolver imports",
    )

    anchor = 'MARKER = "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1"\n\n\n'
    helper = '''MARKER = "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1"
ROOT = Path(__file__).resolve().parents[2]
RUNTIME_KEY_PATH = ROOT / "runtime" / "tmdb-runtime-key.json"


def _runtime_key_payload() -> dict[str, Any]:
    try:
        value = json.loads(RUNTIME_KEY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict) or int(value.get("version") or 0) != 1:
        return {}
    salt = str(value.get("salt") or "").strip()
    cipher = value.get("cipher")
    if not salt or not isinstance(cipher, list) or not cipher:
        return {}
    cleaned: list[int] = []
    for item in cipher:
        try:
            number = int(item)
        except (TypeError, ValueError):
            return {}
        if number < 0 or number > 255:
            return {}
        cleaned.append(number)
    return {"tmdbKeySalt": salt, "tmdbKeyCipher": cleaned}


'''
    text = replace_once(text, anchor, helper, "resolver runtime key helper")

    old_payload = '''    payload = {
        "timeoutMs": max(900, min(int(cfg.get("timeout_ms", 1800)), 5000)),
        "providerTimeoutMs": max(5_000, min(int(cfg.get("provider_timeout_ms", 25_000)), 120_000)),
        "semanticTypes": semantic_types,
        "revision": "tmdb-first-provider-entity-gate-v5-bounded-execution",
    }
'''
    new_payload = '''    payload = {
        "timeoutMs": max(900, min(int(cfg.get("timeout_ms", 1800)), 5000)),
        "providerTimeoutMs": max(5_000, min(int(cfg.get("provider_timeout_ms", 25_000)), 120_000)),
        "semanticTypes": semantic_types,
        "revision": "tmdb-api-authoritative-fail-open-infra-v6",
        **_runtime_key_payload(),
    }
'''
    text = replace_once(text, old_payload, new_payload, "resolver payload")

    start = text.index("function localKey(){")
    end = text.index("var mediaCache=Object.create(null);", start)
    local_key = r'''function embeddedKey(){
  var salt=s(c.tmdbKeySalt),cipher=rows(c.tmdbKeyCipher);
  if(!salt||!cipher.length)return"";
  var material=salt+"|NiakVIO/TMDB/v1",seed=2166136261>>>0;
  for(var i=0;i<material.length;i++){seed^=material.charCodeAt(i);seed=Math.imul(seed,16777619)>>>0}
  var out="";
  for(var j=0;j<cipher.length;j++){
    seed^=(seed<<13);seed>>>=0;seed^=(seed>>>17);seed>>>=0;seed^=(seed<<5);seed>>>=0;
    out+=String.fromCharCode((Number(cipher[j])&255)^(seed&255));
  }
  return out;
}
function localKey(){
  try{if(g&&s(g.TMDB_API_KEY))return s(g.TMDB_API_KEY)}catch(_){}
  try{if(typeof TMDB_API_KEY!=="undefined"&&s(TMDB_API_KEY))return s(TMDB_API_KEY)}catch(_){}
  try{return embeddedKey()}catch(_){return""}
}
function localToken(){
  try{if(g&&s(g.TMDB_ACCESS_TOKEN))return s(g.TMDB_ACCESS_TOKEN)}catch(_){}
  try{if(typeof TMDB_ACCESS_TOKEN!=="undefined"&&s(TMDB_ACCESS_TOKEN))return s(TMDB_ACCESS_TOKEN)}catch(_){}
  return "";
}
'''
    text = text[:start] + local_key + text[end:]

    start = text.index("async function tmdb(namespaceValue,tmdbId){")
    end = text.index("function objectRequest(a)", start)
    api_logic = r'''async function tmdb(namespaceValue,tmdbId){
  var namespace=namespaceValue==="movie"?"movie":"tv",id=s(tmdbId),cacheKey=namespace+":"+id,key=localKey(),token=localToken();
  if(!/^\d+$/.test(id)||!g||typeof g.fetch!=="function")return{state:"unavailable",metadata:null};
  if(Object.prototype.hasOwnProperty.call(mediaCache,cacheKey))return await mediaCache[cacheKey];
  var pending=(async function(){
    if(!key&&!token)return{state:"unavailable",metadata:null};
    try{
      var u="https://api.themoviedb.org/3/"+namespace+"/"+encodeURIComponent(id)+"?append_to_response=keywords&language=en-US";
      if(key)u+="&api_key="+encodeURIComponent(key);
      var h={Accept:"application/json"};if(token)h.Authorization="Bearer "+token;
      var api=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});
      if(!api)return{state:"unavailable",metadata:null};
      if(api.status===404)return{state:"not_found",metadata:null};
      if(!api.ok||typeof api.json!=="function")return{state:"unavailable",metadata:null};
      var value=await api.json();
      if(!value||typeof value!=="object"||Number(value.id||0)<=0)return{state:"unavailable",metadata:null};
      value.__nuvioTmdbNamespace=namespace;
      value.__nuvioTmdbId=id;
      return{state:"ok",metadata:value};
    }catch(_){return{state:"unavailable",metadata:null}}
  })();
  mediaCache[cacheKey]=pending;
  var value=await pending;
  mediaCache[cacheKey]=value;
  return value;
}
function fallbackType(input,semantic){
  var raw=s(input||"movie").toLowerCase(),transport=alias(input);
  if(raw==="anime")return"anime";
  if(transport==="tv"&&semantic.indexOf("tv")<0&&semantic.indexOf("anime")>=0)return"anime";
  if(raw==="movie"&&semantic.indexOf("movie")<0&&semantic.indexOf("anime")>=0)return"anime";
  return transport;
}
async function canonicalResolution(id,input,metadata,season,episode,semantic){
  var candidates=namespaceCandidates(input,season,episode,semantic),raw=s(input||"movie").toLowerCase();
  if(hasTmdbMetadata(metadata)){
    var declared=s(metadata&&metadata.__nuvioTmdbNamespace).toLowerCase();
    var namespace=declared==="movie"?"movie":candidates[0];
    var type=animeMeta(metadata)?"anime":namespace;
    if(raw==="anime"&&type!=="anime")return null;
    return{type:type,namespace:namespace,metadata:metadata,authoritative:true,degraded:false};
  }
  var unavailable=false;
  for(var i=0;i<candidates.length;i++){
    var namespace=candidates[i],probe=await tmdb(namespace,id);
    if(!probe||probe.state==="unavailable"){unavailable=true;continue}
    if(probe.state==="not_found")continue;
    var m=probe.metadata,type=animeMeta(m)?"anime":namespace;
    if(raw==="anime"&&type!=="anime")continue;
    return{type:type,namespace:namespace,metadata:m,authoritative:true,degraded:false};
  }
  if(unavailable){
    var fallback=fallbackType(input,semantic),fallbackNamespace=namespaceOf(input);
    return{type:fallback,namespace:fallbackNamespace,metadata:null,authoritative:false,degraded:true};
  }
  return null;
}
'''
    text = text[:start] + api_logic + text[end:]

    # Keep the existing semantic capability gate. It is authoritative for a valid
    # TMDB answer and fallbackType() deliberately chooses an admitted semantic type
    # when metadata infrastructure is unavailable.
    text = text.replace(
        'canonicalMediaType:type,\n    nuvioInputMediaType:input',
        'canonicalMediaType:type,\n    tmdbResolutionDegraded:resolved.degraded===true,\n    nuvioInputMediaType:input',
        1,
    )

    # Public HTML parser helpers are now dead code; remove them so future changes
    # cannot accidentally reintroduce scraping into the critical path.
    html_start = text.find("function htmlAnime(h){")
    anime_start = text.find("function animeMeta(m){", html_start)
    if html_start >= 0 and anime_start > html_start:
        text = text[:html_start] + text[anime_start:]
    public_start = text.find("function htmlDecode(v){")
    meta_start = text.find("function hasTmdbMetadata(m){", public_start)
    if public_start >= 0 and meta_start > public_start:
        text = text[:public_start] + text[meta_start:]
    text = text.replace('  if(typeof m.__nuvioPublicHtml==="string")return htmlAnime(m.__nuvioPublicHtml);\n', "")

    if "www.themoviedb.org/" in text:
        raise RuntimeError("public TMDB HTML fallback still present")
    for required in (
        "tmdb-api-authoritative-fail-open-infra-v6",
        "tmdbKeyCipher",
        'state:"unavailable"',
        "fallbackType(input,semantic)",
        "tmdbResolutionDegraded",
    ):
        if required not in text:
            raise RuntimeError(f"resolver missing {required}")

    RESOLVER.write_text(text, encoding="utf-8")


def write_tests() -> None:
    content = r'''#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("global_media_type_resolution_v1", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = r"""
"use strict";
async function getStreams(tmdbId, mediaType, season, episode) {
  const ctx = globalThis.__nuvioMediaContext || {};
  return [{ tmdbId, mediaType, season, episode, degraded: ctx.tmdbResolutionDegraded === true }];
}
module.exports = { getStreams };
"""

def run_case(source: str, runner: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        provider = tmp_path / "provider.cjs"
        test = tmp_path / "test.cjs"
        provider.write_text(source, encoding="utf-8")
        test.write_text(runner, encoding="utf-8")
        result = subprocess.run(["node", str(test), str(provider)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr

mixed = mod.apply(BASE, options={"semantic_types": ["tv", "anime"]})
assert "api.themoviedb.org/3/" in mixed
assert "www.themoviedb.org/" not in mixed
assert "tmdbKeyCipher" in mixed

run_case(mixed, r"""
let calls = 0;
global.fetch = async (url) => {
  calls++;
  if (!String(url).includes("api.themoviedb.org/3/tv/280049")) throw new Error("wrong TMDB endpoint "+url);
  if (!String(url).includes("api_key=")) throw new Error("embedded TMDB API key missing");
  return { ok:true, status:200, json:async()=>({
    id:280049, genres:[{id:16,name:"Animation"}], original_language:"ja",
    origin_country:["JP"], keywords:{results:[{name:"anime"}]}
  }) };
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("280049","series",1,11);
  if(!value.length||value[0].mediaType!=="anime")throw new Error("Hell Mode was not refined to anime");
  const again=await provider.getStreams("280049","series",1,12);
  if(!again.length||again[0].mediaType!=="anime")throw new Error("anime cache lost");
  if(calls!==1)throw new Error("TMDB lookup was not cached");
})().catch(e=>{console.error(e);process.exit(1)});
""")

tv_only = mod.apply(BASE, options={"semantic_types": ["tv"]})
run_case(tv_only, r"""
global.fetch=async()=>({ok:true,status:200,json:async()=>({
  id:30984,genres:[{id:16,name:"Animation"}],original_language:"ja",
  origin_country:["JP"],keywords:{results:[{name:"anime"}]}
})});
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("30984","series",1,7);
  if(!Array.isArray(value)||value.length!==0)throw new Error("TV-only provider must reject TMDB-proven anime");
})().catch(e=>{console.error(e);process.exit(1)});
""")

anime_only = mod.apply(BASE, options={"semantic_types": ["anime"]})
run_case(anime_only, r"""
global.fetch=async()=>({ok:true,status:200,json:async()=>({
  id:1396,genres:[{id:18,name:"Drama"}],original_language:"en",origin_country:["US"],keywords:{results:[]}
})});
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("1396","series",1,1);
  if(!Array.isArray(value)||value.length!==0)throw new Error("Anime-only provider must reject TMDB-proven ordinary TV");
})().catch(e=>{console.error(e);process.exit(1)});
""")

run_case(tv_only, r"""
global.fetch=async()=>{throw new Error("TMDB unavailable")};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("62425","series",2,1);
  if(!value.length||value[0].mediaType!=="tv"||value[0].degraded!==true)throw new Error("TV fallback must stay executable on TMDB outage");
})().catch(e=>{console.error(e);process.exit(1)});
""")

run_case(anime_only, r"""
global.fetch=async()=>{throw new Error("TMDB unavailable")};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("280049","series",1,11);
  if(!value.length||value[0].mediaType!=="anime"||value[0].degraded!==true)throw new Error("Anime provider must fail open on metadata outage");
})().catch(e=>{console.error(e);process.exit(1)});
""")

movie_only = mod.apply(BASE, options={"semantic_types": ["movie"]})
run_case(movie_only, r"""
global.fetch=async()=>{throw new Error("TMDB unavailable")};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("157336","movie",null,null);
  if(!value.length||value[0].mediaType!=="movie"||value[0].degraded!==true)throw new Error("Movie fallback failed");
})().catch(e=>{console.error(e);process.exit(1)});
""")

# Conclusive API identity remains authoritative on ordinary TV.
run_case(mixed, r"""
global.fetch=async(url)=>{
  if(!String(url).includes("/tv/62425"))throw new Error("Dark Matter left TV namespace");
  return{ok:true,status:200,json:async()=>({
    id:62425,genres:[{id:18,name:"Drama"}],original_language:"en",origin_country:["CA"],keywords:{results:[]}
  })};
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("62425","series",2,1);
  if(!value.length||value[0].mediaType!=="tv"||value[0].degraded)throw new Error("Dark Matter TV classification failed");
})().catch(e=>{console.error(e);process.exit(1)});
""")

print("global media resolver: TMDB API authoritative, semantic safeguard preserved, infra fail-open verified")
'''
    TEST.write_text(content, encoding="utf-8")


def patch_key_contract() -> None:
    text = KEY_CONTRACT.read_text(encoding="utf-8")
    if "RUNTIME_KEY_PATH" not in text:
        insert = '''
RUNTIME_KEY_PATH = ROOT / "runtime" / "tmdb-runtime-key.json"
runtime_key = json.loads(RUNTIME_KEY_PATH.read_text(encoding="utf-8"))
assert runtime_key.get("version") == 1
assert isinstance(runtime_key.get("salt"), str) and runtime_key["salt"]
assert isinstance(runtime_key.get("cipher"), list) and runtime_key["cipher"]
assert all(isinstance(value, int) and 0 <= value <= 255 for value in runtime_key["cipher"])
assert "api_key" not in runtime_key and "token" not in runtime_key

resolver_source = (ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py").read_text(encoding="utf-8")
assert "tmdbKeyCipher" in resolver_source
assert "api.themoviedb.org/3/" in resolver_source
assert "www.themoviedb.org/" not in resolver_source
'''
        marker = 'failures: list[str] = []\n'
        text = replace_once(text, marker, marker + insert + "\n", "runtime key contract insertion")
    KEY_CONTRACT.write_text(text, encoding="utf-8")


def main() -> int:
    patch_resolver()
    write_tests()
    patch_key_contract()
    print("FIELD_TMDB_RESOLVER_FIX status=ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
