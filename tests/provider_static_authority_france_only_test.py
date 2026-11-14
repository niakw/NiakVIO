#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts/reconcile_provider_static_authority.py"
spec=importlib.util.spec_from_file_location("reconcile_provider_static_authority_france",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.active_provider_rows=lambda:[
    {"id":"global-a","enabled":True,"filename":"providers/global-a.js"},
]
mod.france_only_catalog_rows=lambda root=None:[
    {"id":"fr-a","enabled":True,"filename":"providers/fr-a.js"},
    {"id":"fr-disabled","enabled":False,"filename":"provider-disabled/fr-disabled.js"},
]
rows=mod.active_current_rows()
assert [mod.canonical_id(row.get("id")) for row in rows]==["global-a","fr-a"],rows

mod.france_only_catalog_rows=lambda root=None:[
    {"id":"global-a","enabled":True,"filename":"providers/collision.js"},
]
try:
    mod.active_current_rows()
except ValueError as exc:
    assert "collides" in str(exc)
else:
    raise AssertionError("France-only/Global collision was accepted")

print("provider static authority covers Global + France-only current catalogue")
