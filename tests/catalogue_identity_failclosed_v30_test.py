#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
PATCH = SCRIPTS / "provider_patches" / "global_stream_identity_v1.py"
spec = importlib.util.spec_from_file_location("identity_v30", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

base = '''
"use strict";
async function getStreams(){ return []; }
module.exports={getStreams};
'''
patched = mod.apply(base, options={}, context={"provider_id":"anime-sama"})

runner = r'''
require(process.argv[2]);
const p=global.__nuvioIdentityPolicyV1;
if(!p||typeof p.catalogueScore!=="function")throw new Error("identity policy missing");
const common={expectedTitles:["Children of Men","Les Fils de l'homme"],expectedMedia:"movie",expectedYear:"2006",actualMedia:"movie",year:"2006",providerId:"opaque-provider-id"};
function score(title){return Number(p.catalogueScore(Object.assign({},common,{title})));}
const out={lag:score("LAG"),mikails:score("Les Mikails"),fr:score("Les Fils de l'homme"),en:score("Children of Men"),extended:score("Children of Men Extended")};
if(!(out.lag<0))throw new Error("LAG false positive: "+JSON.stringify(out));
if(!(out.mikails<0))throw new Error("Les Mikails false positive: "+JSON.stringify(out));
if(!(out.fr>0&&out.en>0&&out.extended>0))throw new Error("legitimate title rejected: "+JSON.stringify(out));
console.log(JSON.stringify(out));
'''

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    provider = root / "provider.js"
    test = root / "test.js"
    provider.write_text(patched, encoding="utf-8")
    test.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True, timeout=10)

source = PATCH.read_text(encoding="utf-8")
anime = (SCRIPTS / "provider_patches" / "anime_sama_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_CATALOGUE_TITLE_FAIL_CLOSED_V30" in source
assert "if(!identityMatched)return-1" in source
assert "NIAKVIO_ANIME_SAMA_SEARCH_IDENTITY_V30" in anime
assert "searchSlugIdentityOk(title,s)" in anime
print("catalogue identity fail-closed v30 test passed")
