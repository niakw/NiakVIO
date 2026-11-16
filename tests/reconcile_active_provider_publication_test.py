#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "reconcile_active_provider_publication",
    ROOT/"scripts"/"reconcile_active_provider_publication.py",
)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Publication scope must follow current repository authority, never a historical
# provider witness.  Importing the reconciler adds scripts/ to sys.path.
from current_provider_scope import active_provider_ids

ids=mod.active_global_ids(ROOT)
expected=active_provider_ids()
assert ids, "active Global provider set must be non-empty"
assert len(ids)==len(set(ids)), "active Global IDs must be unique"
assert set(ids)==expected, (
    f"active publication scope drift actual={sorted(ids)} "
    f"expected={sorted(expected)}"
)
assert str((ROOT/"scripts").resolve()) in {str(Path(p).resolve()) for p in sys.path if p}, "sibling imports must work under importlib execution"
source=(ROOT/"scripts"/"reconcile_active_provider_publication.py").read_text(encoding="utf-8")
assert "reconcile_materialization_from_active_bundles(apply=True)" in source
assert "union_rebound=" in source
print(f"ACTIVE_PUBLICATION_FIXED_POINT_SCOPE_OK providers={len(ids)} derived_scope=true union_materialization_rebind=true")
