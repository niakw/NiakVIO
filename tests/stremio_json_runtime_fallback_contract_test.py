#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
common = (ROOT / "scripts" / "provider_patches" / "stremio_json_runtime_common.py").read_text(encoding="utf-8")
desiflix = (ROOT / "scripts" / "provider_patches" / "desiflix_runtime_v1.py").read_text(encoding="utf-8")

assert "function bases(){" in common
assert "fallbackBases" in common
assert "for(var b=0;b<bs.length;b++)" in common
assert "fetchJson(endpoint(q,ids[i],base),base)" in common
assert "fallback_bases[:4]" in common
assert '"https://manifest.desitvhub.eu.org"' in desiflix
assert '"https://desiflix.stremioaddon.workers.dev"' in desiflix
assert desiflix.index('"https://manifest.desitvhub.eu.org"') < desiflix.index('"https://desiflix.stremioaddon.workers.dev"')

print("STREMIO_JSON_RUNTIME_FALLBACK_OK primary_first=true bounded=4 desiflix_legacy_fallback=true")
