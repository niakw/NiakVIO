#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/provider_patches/vf_catalogue_recovery.py"

spec = importlib.util.spec_from_file_location("vf_catalogue_recovery", PATH)
if not spec or not spec.loader:
    raise RuntimeError(PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = PATH.read_text(encoding="utf-8")
assert '"implementationVersion": 4,' in source
assert "if(!a||(!wanted&&!original))return -100;" in source
assert "if(s>=80)rows.push" in source
assert "years.length&&years.indexOf(String(meta.year))<0" in source
assert "__nuvioMediaContext" in source
assert "tmdbMetadata" in source
assert "api.themoviedb.org" not in source
assert "TMDB_KEY" not in source

fixture = "async function getStreams(){return []}\n"
patched = module.apply(
    fixture,
    {
        "strategy": "html",
        "base_url": "https://catalogue.test",
        "provider_name": "Fixture",
        "types": ["movie", "tv"],
        "search_paths": ["/?s={query}"],
    },
)
assert "NUVIO_VF_CATALOGUE_RECOVERY_V1" in patched
assert '"implementationVersion":4' in patched
assert "__nuvioMediaContext" in patched
assert "tmdbMetadata" in patched
assert "api.themoviedb.org" not in patched
assert "TMDB_KEY" not in patched
assert "if(!a||(!wanted&&!original))return -100;" in patched
assert "if(s>=80)rows.push" in patched
# Unknown/unresolvable TMDb metadata can no longer score every search result via
# String.indexOf(\"\") and therefore cannot fabricate a stream for a missing film.
assert "a.indexOf(wanted)>=0" not in patched

print("VF catalogue identity hardening tests passed")
