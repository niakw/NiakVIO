#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/native_catalogue_recovery_budget_v1.py"

spec = importlib.util.spec_from_file_location("native_catalogue_recovery_budget", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

fixture = r'''/* unrelated TMDB helper before */
;(function(){var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";})();

/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:abc */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
async function recover(q,knownMeta,deadline){if(["movie","tv","anime"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];var m=knownMeta||await meta(q);if(!m.titles.length||Date.now()>=deadline)return[];var guessed=[],found=[],searches=[];m.titles.forEach(function(t){guessed.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)found=found.concat([])}var candidates=unique(found.concat(guessed)).slice(0,c.maxCandidates);for(var j=0;j<candidates.length&&Date.now()<deadline;j++){}return[]}
function install(o,k){if(!o||typeof o[k]!=="function")return false;var native=o[k];var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+c.budgetMs;try{v=await native.apply(this,arguments)}catch(_){v=[]}return recover(q,null,deadline)};o[k]=wrap;return true}
})(typeof globalThis!=="undefined"?globalThis:this,{"budgetMs":45000,"maxCandidates":8});

/* unrelated TMDB helper after */
;(function(){var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";})();
'''

patched = module.apply(fixture)
assert "NUVIO_NATIVE_CATALOGUE_RECOVERY_BUDGET_V1" in patched
assert patched.count('function nativeRecoveryHost(){try{return typeof g.__native_fetch==="function"}') == 1
assert "searchCap=nativeRuntime?2:2147483647" in patched
assert "candidateCap=nativeRuntime?2:c.maxCandidates" in patched
assert "i<searchCap" in patched
assert "slice(0,candidateCap)" in patched
assert "nativeRecoveryHost()?Math.min(c.budgetMs,12000):c.budgetMs" in patched
# The two unrelated helpers plus the catalogue helper itself remain present.
assert patched.count('var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";') == 3
assert module.apply(patched) == patched

# Providers without the catalogue fallback are untouched.
plain = "module.exports={getStreams:async()=>[]};\n"
assert module.apply(plain) == plain

print("native catalogue recovery budget tests passed")
