#!/usr/bin/env python3
from pathlib import Path
import json

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

print("AllWish recovered runtime contract passed")
