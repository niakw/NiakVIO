#!/usr/bin/env python3
"""Shared runtime source drift must not discard unrelated Brain advisor priors.

Static import ownership is deliberately conservative; opaque or global Core
changes retain all-provider invalidation. This is source reachability only,
not positive stream or safe-mutation evidence.
"""
from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "family_drift_scope", ROOT / "scripts" / "select_provider_materialization_scope.py")
assert spec and spec.loader
scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)
initial = scope.ROOT

with tempfile.TemporaryDirectory(prefix="niakvio-brain-family-scope-") as tmp:
    scope.ROOT = Path(tmp)
    folder = scope.ROOT / "scripts" / "provider_patches"
    folder.mkdir(parents=True)
    (folder / "anime_wrapper.py").write_text(
        "from family_runtime_common import apply_runtime\n", encoding="utf-8")
    (folder / "neko_wrapper.py").write_text(
        "import family_runtime_common as shared\n", encoding="utf-8")
    (folder / "movie_wrapper.py").write_text(
        "from independent_movie_renderer import apply_runtime\n", encoding="utf-8")
    (folder / "dynamic_wrapper.py").write_text(
        "import importlib\nx=importlib.import_module('family_runtime_common')\n",
        encoding="utf-8")
    rows = {
      "provider_patches":{
        "anime-test":{"provider_lego_scripts":["scripts/provider_patches/anime_wrapper.py"]},
        "neko-test":{"provider_lego_scripts":["scripts/provider_patches/neko_wrapper.py"]},
        "movie-test":{"provider_lego_scripts":["scripts/provider_patches/movie_wrapper.py"]},
        "dynamic-test":{"provider_lego_scripts":["scripts/provider_patches/dynamic_wrapper.py"]},
      },
    }
    docs = {"provider-overrides.json": rows}
    family = "scripts/provider_patches/family_runtime_common.py"
    owners=scope.transitively_imported_shared_patch_owners(family,rows,rows)
    assert owners == {"anime-test","neko-test"},owners
    mode, providers, reasons = scope.classify([family],docs,docs)
    assert mode=="providers" and providers==["anime-test","neko-test"],(mode,providers,reasons)
    assert reasons==["patch:"+family+":anime-test,neko-test"],reasons
    # Direct patch ownership remains exact.
    mode, providers, _ = scope.classify(
        ["scripts/provider_patches/movie_wrapper.py"], docs, docs)
    assert mode=="providers" and providers==["movie-test"],(mode,providers)
    # Unowned, dynamically-imported, and global patches are NOT safely
    # attributable and must retain all-provider invalidation.
    for changed in ("scripts/provider_patches/unknown_renderer.py",
                    "scripts/provider_patches/global_stream_identity_v1.py"):
        mode, providers, reasons = scope.classify([changed],docs,docs)
        assert mode=="all" and not providers,(changed,mode,providers,reasons)
    # A mixed change can be globally unsafe even if one part is scoped.
    mode, providers, _ = scope.classify(
        [family,"scripts/provider_base_store.py"], docs, docs)
    assert mode=="all" and not providers,(mode,providers)

scope.ROOT = initial
print("FIELD_BRAIN_SHARED_RENDERER_DRIFT scoped_import_owners=2 unrelated_provider_preserved=true "
      "global_changes_fail_closed=true no_playback_proof=true")
