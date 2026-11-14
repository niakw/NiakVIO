#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT / "scripts").resolve()))

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

materialize = load_module(
    "provider_identity_alias_materialize_test",
    ROOT / "scripts" / "materialize_provider_v3_all.py",
)
base_store = load_module(
    "provider_identity_alias_base_store_test",
    ROOT / "scripts" / "provider_base_store.py",
)

legacy = {
    "identity_input": {
        "mode": "tmdb_title_year",
        "requires_tmdb_before_run": True,
        "required_fields": ["tmdbId", "mediaType", "title", "year"],
    }
}
normalized = materialize.identity_input(legacy, ["/search?q={query}"], None)
assert normalized["mode"] == "catalog_search", normalized
assert normalized["requiresTmdbBeforeRun"] is True, normalized
assert normalized["requiredFields"] == ["tmdbId", "mediaType", "title", "year"], normalized

base = base_store._normalize_identity_input({
    "mode": "tmdb_title_year",
    "requiresTmdbBeforeRun": True,
    "requiredFields": ["title", "year", "mediaType"],
})
assert base["mode"] == "catalog_search", base
assert base["requiresTmdbBeforeRun"] is True, base

for value in ("tmdb_direct", "catalog_search", "external_id"):
    assert base_store._normalize_identity_input({"mode": value})["mode"] == value

overrides = (ROOT / "provider-overrides.json").read_text(encoding="utf-8")
assert '"tmdb_title_year"' not in overrides, "active overrides must be canonicalized after migration"
assert '"internet-archive"' in overrides

print("Provider legacy identity alias migration contract passed")
