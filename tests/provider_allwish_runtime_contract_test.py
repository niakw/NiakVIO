#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/allwish_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["allwish"]

assert "NIAKVIO_ALLWISH_RUNTIME_V1" in src
assert '"/filter?keyword="+encodeURIComponent(query)' in src
assert 'replace(/\\/ep-\\d+' in src
assert 'await _crawlDirectMedia([url],url,c.depth)' in src
assert '__niakvioProviderRuntimeResolverV1={provider:"allwish",resolve:resolve}' in src
assert "fetch.nexabloom.top" in (ROOT/"automation/USER-PROVIDER-EVIDENCE-LEDGER.md").read_text(encoding="utf-8")

lego="scripts/provider_patches/allwish_runtime_v1.py"
assert ov["official_site"]=="https://all-wish.me"
assert ov["provider_lego_scripts"]==[lego]
assert ov["provider_lego_options"][lego]["base"]=="https://all-wish.me"
assert "/filter?keyword={query}" in ov["learned_routes"]
assert "/watch/{slug}/ep-{episode}" in ov["learned_routes"]
assert ov["route_data_state"]=="repair"

sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("allwish_runtime_v1",ROOT/lego)
assert spec and spec.loader
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
row=next(r for r in manifest["scrapers"] if str(r.get("id","")).casefold()=="allwish")
bundle=(ROOT/row["filename"]).read_text(encoding="utf-8")
patched=module.apply(bundle,ov["provider_lego_options"][lego])
assert "NIAKVIO_ALLWISH_RUNTIME_V1" in patched
with tempfile.TemporaryDirectory(prefix="niakvio-allwish-contract-") as td:
    candidate=Path(td)/"allwish.js"
    candidate.write_text(patched,encoding="utf-8")
    checked=subprocess.run(
        ["node","--check",str(candidate)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert checked.returncode==0, checked.stderr or checked.stdout

print("AllWish recovered runtime contract passed")
