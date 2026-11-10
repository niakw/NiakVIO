#!/usr/bin/env python3
"""Live episode probes must respect semantic provider capability, not Nuvio transport aliases."""
from __future__ import annotations

import importlib.util
from pathlib import Path

source = Path(__file__).resolve().parents[1] / "scripts" / "tv_regression_matrix.py"
spec = importlib.util.spec_from_file_location("tv_regression_matrix", source)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

anime_only = {
    "supportedTypes": ["anime", "tv"],  # tv is transport-only compatibility
    "canonicalSupportedTypes": ["anime"],
}
assert module.canonical_types(anime_only) == {"anime"}
assert "tv" not in module.canonical_types(anime_only)

tv_only = {"supportedTypes": ["tv"]}
assert module.canonical_types(tv_only) == {"tv"}

mixed = {"supportedTypes": ["anime", "tv", "movie"]}
assert module.canonical_types(mixed) == {"anime", "tv", "movie"}

print("FIELD_TV_LIVE_MATRIX_SEMANTIC_SCOPE semantic_tv_only=true anime_transport_alias_excluded=true")
