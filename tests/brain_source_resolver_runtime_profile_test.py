#!/usr/bin/env python3
"""The V2 resolver primitive is provider-agnostic and fail-closed."""
from __future__ import annotations
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"scripts/adaptive_runtime/runtime_repair.py"
spec=importlib.util.spec_from_file_location("source_resolver_runtime",SRC)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

source=r'''function txt(v){return String(v||"")}
async function text(url,opt){return ""}
function arrays(js){var out=[],re=/var\s+([a-z0-9_$]+)\s*=\s*\[([\s\S]*?)\s*\];/gim,m;while((m=re.exec(txt(js)))!==null){var vals=[],q=/["']([^"']+)["']/g,x;while((x=q.exec(m[2]))!==null){if(/^https?:\/\//i.test(x[1]))vals.push(x[1])}if(vals.length)out.push(vals)}return out}
async function direct(player,referer){return[]}
async function episodeJs(origin,body,groups,idx){for(var i=0;i<groups.length;i++){var player=groups[i][idx];if(!player)continue;var rows=await direct(player,origin+"/");}}
'''
patched,records=mod._apply_inline_token_resolver_contract(
    source.encode(),"same-origin-api-lien-j-l-v1"
)
text=patched.decode()
assert records and patched!=source.encode()
assert "||/^lien:/i.test(x[1])" in text
assert "epsJeton" in text and "/api/lien.php?j=" in text and "obj&&obj.u" in text
assert "NIAKVIO_SOURCE_RESOLVER_CONTRACT same-origin-api-lien-j-l-v1" in text
assert "anime-sama" not in text.casefold()
# Applying twice is a no-op and an unrelated source is never mutated.
again,again_records=mod._apply_inline_token_resolver_contract(
    patched,"same-origin-api-lien-j-l-v1"
)
assert again==patched and again_records==[]
plain,plain_records=mod._apply_inline_token_resolver_contract(
    b"async function unrelated(){return 1}","same-origin-api-lien-j-l-v1"
)
assert plain==b"async function unrelated(){return 1}" and plain_records==[]
try:
    mod._apply_inline_token_resolver_contract(source.encode(),"other")
except ValueError:
    pass
else:
    raise AssertionError("unknown resolver contract accepted")
with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as handle:
    handle.write(text)
    js=handle.name
check=subprocess.run(["node","--check",js],capture_output=True,text=True,check=False)
Path(js).unlink(missing_ok=True)
assert check.returncode==0,check.stderr
print("Brain source resolver runtime V2: provider-agnostic mutation, JS syntax and fail-closed anchors passed")
