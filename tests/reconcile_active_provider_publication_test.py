#!/usr/bin/env python3
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "reconcile_active_provider_publication",
    ROOT/"scripts"/"reconcile_active_provider_publication.py",
)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ids=mod.active_global_ids(ROOT)
assert ids, "active Global provider set must be non-empty"
assert len(ids)==len(set(ids)), "active Global IDs must be unique"
assert "chillflix" in ids, ids
print(f"ACTIVE_PUBLICATION_FIXED_POINT_SCOPE_OK providers={len(ids)}")
