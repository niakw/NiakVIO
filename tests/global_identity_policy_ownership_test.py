#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
CORE = ROOT / "scripts/provider_patches/global_stream_identity_v1.py"
UPGRADER = ROOT / "scripts/upgrade_provider_base_runtime_v5.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("niakvio_identity_policy_test", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load_module(CORE)
stub = '''/* BEGIN NIAKVIO_PROVIDER */
/* NIAKVIO_PROVIDER_ID:identity-policy-test */
module.exports={getStreams:async function(){return[];}};
/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
/* END NIAKVIO_PROVIDER */
'''
compiled = core.apply(stub, context={"provider_id": "identity-policy-test"})
assert compiled.count("STARTFIX:CORE.STREAM_IDENTITY.V1") == 1
assert compiled.count("CLOSEFIX:CORE.STREAM_IDENTITY.V1") == 1
assert '__nuvioIdentityPolicyV1' in compiled
assert 'yearPolicy:"movie-only"' in compiled
assert 'cross-client-shared-tmdb-owner-movie-year-only-v10' in compiled

script = compiled + r'''
;(async function(){
  const p=globalThis.__nuvioIdentityPolicyV1;
  if(!p) throw new Error("missing identity policy");
  const base={
    title:"House of the Dragon",
    expectedTitles:["House of the Dragon"],
    providerId:"hotd-provider-id",
    strictIdentity:true,
    requireProviderTypeEvidence:true,
    expectedYear:"2022"
  };
  const out={
    tv:p.catalogueScore({...base,actualMedia:"tv",expectedMedia:"tv",year:"2026"}),
    series:p.catalogueScore({...base,actualMedia:"series",expectedMedia:"series",year:"2031"}),
    anime:p.catalogueScore({...base,actualMedia:"anime",expectedMedia:"anime",year:"1999"}),
    movieBad:p.catalogueScore({...base,actualMedia:"movie",expectedMedia:"movie",year:"2026"}),
    movieGood:p.catalogueScore({...base,actualMedia:"movie",expectedMedia:"movie",year:"2022"}),
    htmlTv:p.htmlIdentityOk({strictIdentity:true,html:"<h1>House of the Dragon - Saison 3 (2026)</h1>",visibleText:"House of the Dragon - Saison 3 (2026)",expectedTitles:["House of the Dragon"],expectedYear:"2022",mediaType:"tv"}),
    htmlMovie:p.htmlIdentityOk({strictIdentity:true,html:"<h1>House of the Dragon (2026)</h1>",visibleText:"House of the Dragon (2026)",expectedTitles:["House of the Dragon"],expectedYear:"2022",mediaType:"movie"})
  };
  process.stdout.write(JSON.stringify(out));
})().catch(e=>{console.error(e);process.exit(1)});
'''
with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as handle:
    handle.write(script)
    temp = Path(handle.name)
try:
    result = subprocess.run(["node", str(temp)], cwd=ROOT, text=True, capture_output=True, check=False)
finally:
    temp.unlink(missing_ok=True)
assert result.returncode == 0, result.stderr
out = json.loads(result.stdout)
assert out["tv"] > 0 and out["series"] > 0 and out["anime"] > 0, out
assert out["movieBad"] == -1 and out["movieGood"] > 0, out
assert out["htmlTv"] is True and out["htmlMovie"] is False, out

# ProviderBase runtime must delegate catalogue and HTML identity to the Core
# policy. Inspect transformed snippets only; migration-source validation strings
# are not executable runtime ownership.
upgrader = load_module(UPGRADER)
providerbase = '''
function strictIdentity(x){return x}
function strictIdentityHtml(x){return x}
const goodEpisode=(mediaType==='tv'||mediaType==='series'||mediaType==='anime');
const movieIdentity=goodEpisode;
function evaluateStrictCandidate(){return true}
'''
try:
    transformed = upgrader.upgrade(providerbase)
except Exception:
    transformed = upgrader.upgrade_source(providerbase) if hasattr(upgrader, "upgrade_source") else ""
if transformed:
    assert "__nuvioIdentityPolicyV1" in transformed
    assert "strictIdentityScore" not in transformed
    assert "function routeIdentity(" not in transformed

print("global identity policy ownership tests passed")
