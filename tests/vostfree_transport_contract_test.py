#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/vostfree_dle_uqload_runtime_v1.py").read_text(encoding="utf-8")

assert "NIAKVIO_VOSTFREE_DLE_UQLOAD_RUNTIME_V1" in src
assert 'var semantic=s((obj&&obj.semanticType)||ctx.semanticType||"").toLowerCase();' in src
assert 'if(semantic==="anime"||(type==="tv"&&!semantic))type="anime";' in src
assert 'if(type!=="anime")return null;' in src
assert 'c.site+"/index.php?do=search"' in src
assert 'action_select_season' not in src
assert 'provider:"vostfree",resolve:resolve' in src

print("Vostfree anime TV transport contract passed")
