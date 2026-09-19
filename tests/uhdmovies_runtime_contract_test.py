#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/"scripts/provider_patches/uhdmovies_runtime_v1.py").read_text(encoding="utf-8")
for marker in [
    "NIAKVIO_UHDMOVIES_RUNTIME_V1",
    "function findPosts",
    'b+"/?s="+encodeURIComponent(m.title)',
    "function parseForm",
    'h.Cookie=token+"="+values[i]',
    "function redirectedDirect",
    "function followDownload",
    'new URL(u).searchParams.get("url")',
    "function driveSeed",
    'provider:"uhdmovies"',
]:
    assert marker in p, marker
over=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))
row=over["provider_patches"]["uhdmovies"]
assert row["published_types"]==["movie"]
assert "scripts/provider_patches/uhdmovies_runtime_v1.py" in row["provider_lego_scripts"]
print("UHDMovies runtime contract passed")
