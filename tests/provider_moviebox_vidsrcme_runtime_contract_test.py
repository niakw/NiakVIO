#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/moviebox_vidsrcme_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["moviebox"]
lego="scripts/provider_patches/moviebox_vidsrcme_runtime_v1.py"

assert "NIAKVIO_MOVIEBOX_VIDSRCME_RUNTIME_V1" in src
assert '"/vs_src.php?type="+encodeURIComponent(q.type)+"&id="+encodeURIComponent(q.id)' in src
assert 'typeof _crawlDirectMedia==="function"' in src
assert 'await _crawlDirectMedia([src],c.referer,3)' in src
assert 'x.provider="moviebox"' in src
assert 'terminalResolution": "vidsrcme-src-direct-or-bounded-crawl"' in src
assert ov["provider_lego_scripts"]==[lego]
assert ov["provider_lego_options"][lego]["base"]=="https://vidsrcme.ru"
assert ov["route_data_state"]=="repair"
assert ov["repair_disposition"]["quarantined"] is False

ledger=(ROOT/"automation/USER-PROVIDER-EVIDENCE-LEDGER.md").read_text(encoding="utf-8")
assert "MovieBox manual positive" in ledger
assert "sagaciousslumber" in ledger

print("MovieBox vidsrcme embed-terminal runtime contract passed")
