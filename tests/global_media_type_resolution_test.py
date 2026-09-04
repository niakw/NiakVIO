#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("global_media_type_resolution_v1", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = r'''\n"use strict";\nasync function getStreams(tmdbId, mediaType, season, episode) {\n  const ctx = globalThis.__nuvioMediaContext || {};\n  return [{\n    tmdbId, mediaType, season, episode,\n    canonicalMediaType: ctx.canonicalMediaType || "",\n    providerMediaType: ctx.providerMediaType || mediaType,\n    degraded: ctx.tmdbResolutionDegraded === true\n  }];\n}\nmodule.exports = { getStreams };\n'''

ZERO_BASE = r'''\n"use strict";\nasync function getStreams() { return []; }\nmodule.exports = { getStreams };\n'''


def run_case(source: str, runner: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        provider = tmp_path / "provider.cjs"
        test = tmp_path / "test.cjs"
        provider.write_text(source, encoding="utf-8")
        test.write_text(
            "global.TMDB_API_KEY='0123456789abcdef0123456789abcdef';\n" + runner,
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(test), str(provider)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


mixed = mod.apply(BASE, options={"semantic_types": ["tv", "anime"]})
assert "api.themoviedb.org/3/" in mixed
assert "www.themoviedb.org/" not in mixed
assert '"tmdbKeyCipher":' not in mixed
assert '"tmdbKeySalt":' not in mixed
assert "external_source=imdb_id" in mixed
assert "alternative_titles" in mixed
assert "language=fr-FR" in mixed
assert 'var providerEvent=invocationEvent(originalArgs);' in mixed
assert 'if(providerEvent!=="launch")return [];' in mixed
assert 'if(!hasProviderOutput(value))return [];' in mixed

run_case(mixed, r'''\nlet calls = 0;\nglobal.fetch = async (url) => {\n  calls++;\n  const value=String(url);\n  if (!value.includes("api.themoviedb.org/3/tv/280049")) throw new Error("wrong TMDB endpoint "+value);\n  if (!value.includes("api_key=0123456789abcdef0123456789abcdef")) throw new Error("runtime TMDB API key missing");\n  return { ok:true, status:200, json:async()=>({\n    id:280049, genres:[{id:16,name:"Animation"}], original_language:"ja",\n    origin_country:["JP"], keywords:{results:[{name:"anime"}]}\n  }) };\n};\nconst provider=require(process.argv[2]);\n(async()=>{\n  const value=await provider.getStreams("280049","series",1,11);\n  if(!Array.isArray(value)||!value.length||value[0].canonicalMediaType!=="anime"||value[0].mediaType!=="tv")\n    throw new Error("anime semantic/TV transport split failed: "+JSON.stringify(value));\n  const again=await provider.getStreams("280049","series",1,12);\n  if(!Array.isArray(again)||!again.length||again[0].canonicalMediaType!=="anime"||again[0].mediaType!=="tv")\n    throw new Error("anime cache/transport lost");\n  if(calls!==1)throw new Error("TMDB lookup was not cached: "+calls);\n})().catch(e=>{console.error(e);process.exit(1)});\n''')

run_case(mixed, r'''\nlet calls=0;\nglobal.__nuvioProviderEvent='discovery';\nglobal.fetch=async()=>{calls++;throw new Error('network forbidden')};\nconst provider=require(process.argv[2]);\n(async()=>{\n  const value=await provider.getStreams('280049','series',1,1);\n  if(!Array.isArray(value)||value.length!==0)throw new Error('non-launch must return []');\n  if(calls!==0)throw new Error('non-launch touched network');\n})().catch(e=>{console.error(e);process.exit(1)});\n''')

deferred_zero = mod.apply(ZERO_BASE, options={"semantic_types": ["movie", "tv"]})
run_case(deferred_zero, r'''\nlet calls=0;\nglobal.fetch=async()=>{calls++;throw new Error('TMDB must not run for zero output')};\nconst provider=require(process.argv[2]);\n(async()=>{\n  const value=await provider.getStreams('1396','series',1,1);\n  if(!Array.isArray(value)||value.length!==0)throw new Error('zero output changed');\n  if(calls!==0)throw new Error('zero output caused TMDB work');\n})().catch(e=>{console.error(e);process.exit(1)});\n''')

tv_only = mod.apply(BASE, options={"semantic_types": ["tv"]})
run_case(tv_only, r'''\nlet calls=0;\nglobal.fetch=async(url)=>{\n  calls++;\n  if(!String(url).includes('/tv/1396?'))throw new Error('unexpected TMDB endpoint '+url);\n  return{ok:true,status:200,json:async()=>({\n    id:1396,genres:[{id:18,name:'Drama'}],original_language:'en',\n    origin_country:['US'],keywords:{results:[]}\n  })};\n};\nconst provider=require(process.argv[2]);\n(async()=>{\n  const value=await provider.getStreams('1396','series',1,1);\n  if(!Array.isArray(value)||!value.length||value[0].mediaType!=='tv')throw new Error('ordinary TV output rejected');\n  if(calls!==1)throw new Error('positive output must be verified exactly once');\n})().catch(e=>{console.error(e);process.exit(1)});\n''')

run_case(tv_only, r'''\nglobal.fetch=async()=>({ok:true,status:200,json:async()=>({\n  id:30984,genres:[{id:16,name:'Animation'}],original_language:'ja',\n  origin_country:['JP'],keywords:{results:[{name:'anime'}]}\n})});\nconst provider=require(process.argv[2]);\n(async()=>{\n  const value=await provider.getStreams('30984','series',1,7);\n  if(!Array.isArray(value)||value.length!==0)throw new Error('TV-only provider leaked anime');\n})().catch(e=>{console.error(e);process.exit(1)});\n''')

run_case(tv_only, r'''\nglobal.fetch=async()=>{throw new Error('TMDB unavailable')};\nconst provider=require(process.argv[2]);\n(async()=>{\n  const value=await provider.getStreams('62425','series',2,1);\n  if(!Array.isArray(value)||!value.length||value[0].mediaType!=='tv'||value[0].degraded!==true)\n    throw new Error('TV fail-open fallback failed: '+JSON.stringify(value));\n})().catch(e=>{console.error(e);process.exit(1)});\n''')

print('global media resolver: runtime-only TMDB credentials, launch gate, canonical/transport split and deferred verification passed')
