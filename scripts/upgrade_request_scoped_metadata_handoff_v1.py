#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
TEST = ROOT / "tests/global_media_type_resolution_test.py"
MARKER = "NUVIO_REQUEST_SCOPED_METADATA_HANDOFF_V1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    src = CORE.read_text(encoding="utf-8")

    helper_anchor = 'function objectRequest(a){return a&&typeof a==="object"&&!Array.isArray(a)}\n'
    helper = r'''function objectRequest(a){return a&&typeof a==="object"&&!Array.isArray(a)}
/* NUVIO_REQUEST_SCOPED_METADATA_HANDOFF_V1 */
function matchingIncomingContext(a){
  try{
    if(!g||!g.__nuvioMediaContext||typeof g.__nuvioMediaContext!=="object")return null;
    var ctx=g.__nuvioMediaContext,first=a&&a[0],obj=objectRequest(first),q=obj?first:null;
    var input=obj?s(q.mediaType||q.type||q.category||"movie"):s(a&&a[1]||"movie");
    var namespace=namespaceOf(input),raw=obj?s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id):s(first),source=sourceIdentity(raw);
    if(source.kind==="tmdb"){
      if(s(ctx.tmdbId)!==source.id)return null;
    }else if(source.kind==="imdb"){
      if(s(ctx.imdbId).toLowerCase()!==source.id)return null;
    }else return null;
    var ctxNamespace=s(ctx.tmdbNamespace).toLowerCase();
    if(ctxNamespace&&ctxNamespace!==namespace)return null;
    var metadata=ctx.tmdbMetadata;
    if(!metadata||typeof metadata!=="object")return null;
    var declaredId=s(metadata.__nuvioTmdbId||metadata.id);
    if(source.kind==="tmdb"&&declaredId&&declaredId!==source.id)return null;
    return{
      tmdbId:s(ctx.tmdbId),imdbId:s(ctx.imdbId).toLowerCase(),
      tmdbNamespace:ctxNamespace||namespace,tmdbMetadata:metadata
    };
  }catch(_){return null}
}
'''
    if MARKER not in src:
        src = replace_once(src, helper_anchor, helper, "incoming context helper")

    src = replace_once(src, "async function resolve(a){", "async function resolve(a,incomingContext){", "resolve signature")
    src = replace_once(
        src,
        '  var metadata=obj&&(q.tmdbMetadata||q.tmdb_metadata||q.metadata||q);',
        '  var metadata=(obj&&(q.tmdbMetadata||q.tmdb_metadata||q.metadata||q))||(incomingContext&&incomingContext.tmdbMetadata)||null;',
        "resolve metadata handoff",
    )
    src = replace_once(src, "function provisional(a){", "function provisional(a,incomingContext){", "provisional signature")
    src = replace_once(
        src,
        "    tmdbMetadata:null,\n    canonicalMediaType:type,",
        "    tmdbMetadata:incomingContext&&incomingContext.tmdbMetadata||null,\n    canonicalMediaType:type,",
        "provisional metadata handoff",
    )
    src = replace_once(
        src,
        '      if(g){priorController=g.__nuvioProviderAbortController||null;priorDone=g.__nuvioProviderInvocationDone||null}\n      if(g&&Object.prototype.hasOwnProperty.call(g,"__nuvioMediaContext"))delete g.__nuvioMediaContext;',
        '      if(g){priorController=g.__nuvioProviderAbortController||null;priorDone=g.__nuvioProviderInvocationDone||null}\n      var incomingContext=matchingIncomingContext(originalArgs);\n      if(g&&Object.prototype.hasOwnProperty.call(g,"__nuvioMediaContext"))delete g.__nuvioMediaContext;',
        "capture incoming context before cleanup",
    )
    src = replace_once(src, "      var a=provisional(originalArgs);", "      var a=provisional(originalArgs,incomingContext);", "provisional invocation")
    if "preResolved=await resolve(originalArgs,incomingContext);" not in src:
        count = src.count("preResolved=await resolve(originalArgs);")
        if count != 1:
            raise AssertionError(f"pre-resolve call count={count}")
        src = src.replace("preResolved=await resolve(originalArgs);", "preResolved=await resolve(originalArgs,incomingContext);", 1)
    if "verified=preResolved||await resolve(originalArgs,incomingContext);" not in src:
        src = replace_once(
            src,
            "verified=preResolved||await resolve(originalArgs);",
            "verified=preResolved||await resolve(originalArgs,incomingContext);",
            "post-output resolve",
        )

    required = [
        MARKER,
        "var incomingContext=matchingIncomingContext(originalArgs);",
        "var a=provisional(originalArgs,incomingContext);",
        "preResolved=await resolve(originalArgs,incomingContext);",
        "verified=preResolved||await resolve(originalArgs,incomingContext);",
        "tmdbMetadata:incomingContext&&incomingContext.tmdbMetadata||null",
    ]
    for token in required:
        if token not in src:
            raise AssertionError(f"missing Core metadata handoff token: {token}")
    CORE.write_text(src, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    test_marker = "# REQUEST_SCOPED_METADATA_HANDOFF_V1_TEST"
    if test_marker not in test:
        extra = r'''

# REQUEST_SCOPED_METADATA_HANDOFF_V1_TEST
context_base = mod.apply(BASE, options={"semantic_types": ["movie", "tv"]})
run_case(context_base, r'''
let calls=0;
global.fetch=async(url)=>{calls++;throw new Error('matching request metadata should avoid TMDB network: '+url)};
global.__nuvioMediaContext={
  tmdbId:'157336',tmdbNamespace:'movie',
  tmdbMetadata:{title:'Interstellar',original_title:'Interstellar',release_date:'2014-11-07'}
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('157336','movie');
  if(!Array.isArray(value)||!value.length)throw new Error('matching context suppressed output');
  if(calls!==0)throw new Error('matching context caused network '+calls);
})().catch(e=>{console.error(e);process.exit(1)});
''')

metadata_echo_base = mod.apply('''
"use strict";
async function getStreams(tmdbId, mediaType) {
  const ctx=globalThis.__nuvioMediaContext||{};
  const meta=ctx.tmdbMetadata||{};
  return [{url:"https://media.example/ok.m3u8", seenTitle:String(meta.title||meta.name||"")}];
}
module.exports={getStreams};
''', options={"semantic_types": ["movie", "tv"]})
run_case(metadata_echo_base, r'''
let calls=0;
global.fetch=async(url)=>{
  calls++;
  if(!String(url).includes('/movie/157336?'))throw new Error('unexpected endpoint '+url);
  return {ok:true,status:200,json:async()=>({id:157336,title:'Interstellar',genres:[{id:12,name:'Adventure'}],original_language:'en',keywords:{keywords:[]}})};
};
global.__nuvioMediaContext={tmdbId:'1396',tmdbNamespace:'tv',tmdbMetadata:{id:1396,name:'Breaking Bad',genres:[{id:18,name:'Drama'}],original_language:'en'}};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('157336','movie');
  if(!Array.isArray(value)||!value.length)throw new Error('stale-context case suppressed output');
  if(value[0].seenTitle)throw new Error('stale metadata leaked into request: '+JSON.stringify(value));
  if(calls!==1)throw new Error('stale context should require current TMDB verification: '+calls);
})().catch(e=>{console.error(e);process.exit(1)});
''')
'''
        # The nested Python raw string above is intentionally built with a placeholder
        # delimiter below to avoid quoting ambiguity.
        extra = extra.replace("r'''\nlet calls=0;", "'''\nlet calls=0;").replace("\n''')\n\nmetadata_echo_base", "\n''')\n\nmetadata_echo_base", 1)
        # Rebuild with ordinary triple-double-quoted Python source instead; this keeps
        # the generated test human-readable and py_compile-safe.
        extra = '''\n\n# REQUEST_SCOPED_METADATA_HANDOFF_V1_TEST\ncontext_base = mod.apply(BASE, options={"semantic_types": ["movie", "tv"]})\nrun_case(context_base, """\nlet calls=0;\nglobal.fetch=async(url)=>{calls++;throw new Error('matching request metadata should avoid TMDB network: '+url)};\nglobal.__nuvioMediaContext={tmdbId:'157336',tmdbNamespace:'movie',tmdbMetadata:{title:'Interstellar',original_title:'Interstellar',release_date:'2014-11-07'}};\nconst provider=require(process.argv[2]);\n(async()=>{\n  const value=await provider.getStreams('157336','movie');\n  if(!Array.isArray(value)||!value.length)throw new Error('matching context suppressed output');\n  if(calls!==0)throw new Error('matching context caused network '+calls);\n})().catch(e=>{console.error(e);process.exit(1)});\n""")\n\nmetadata_echo_base = mod.apply("""\n\\"use strict\\";\nasync function getStreams(tmdbId, mediaType) {\n  const ctx=globalThis.__nuvioMediaContext||{};\n  const meta=ctx.tmdbMetadata||{};\n  return [{url:\\"https://media.example/ok.m3u8\\", seenTitle:String(meta.title||meta.name||\\"\\")}];\n}\nmodule.exports={getStreams};\n""", options={"semantic_types": ["movie", "tv"]})\nrun_case(metadata_echo_base, """\nlet calls=0;\nglobal.fetch=async(url)=>{\n  calls++;\n  if(!String(url).includes('/movie/157336?'))throw new Error('unexpected endpoint '+url);\n  return {ok:true,status:200,json:async()=>({id:157336,title:'Interstellar',genres:[{id:12,name:'Adventure'}],original_language:'en',keywords:{keywords:[]}})};\n};\nglobal.__nuvioMediaContext={tmdbId:'1396',tmdbNamespace:'tv',tmdbMetadata:{id:1396,name:'Breaking Bad',genres:[{id:18,name:'Drama'}],original_language:'en'}};\nconst provider=require(process.argv[2]);\n(async()=>{\n  const value=await provider.getStreams('157336','movie');\n  if(!Array.isArray(value)||!value.length)throw new Error('stale-context case suppressed output');\n  if(value[0].seenTitle)throw new Error('stale metadata leaked into request: '+JSON.stringify(value));\n  if(calls!==1)throw new Error('stale context should require current TMDB verification: '+calls);\n})().catch(e=>{console.error(e);process.exit(1)});\n""")\n'''
        test += extra
        TEST.write_text(test, encoding="utf-8")

    print("REQUEST_SCOPED_METADATA_HANDOFF_V1_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
