#!/usr/bin/env python3
"""Canonical Provider v3 reconstruction contract.

The durable reconstruction source is one NiakVIO-owned common ProviderBase v3
skeleton plus structured DATA and owned Lego. Legacy/upstream/published Provider
JavaScript may be observed as knowledge but can never seed reconstruction.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/"scripts"
sys.path.insert(0,str(SCRIPTS))

import provider_base_store as base_store

manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
provenance=json.loads((ROOT/"PROVENANCE.json").read_text(encoding="utf-8"))
rows=provenance.get("providers")
store=provenance.get("provider_base_store")
assert isinstance(rows,dict)
assert isinstance(store,dict)

entries=[
    row for row in manifest.get("scrapers") or []
    if isinstance(row,dict) and base_store.canonical_id(str(row.get("id") or ""))
]
provider_ids=[base_store.canonical_id(str(row["id"])) for row in entries]
assert len(provider_ids)==96, len(provider_ids)
assert len(set(provider_ids))==96

assert base_store.INITIAL_RECONSTRUCTION_SCOPE==96
assert base_store.CLEAN_RECONSTRUCTION_AUTHORING_VERSION>=3
assert base_store.CLEAN_RECONSTRUCTION_SOURCE=="niakvio-clean-reconstruction-v3"
assert store.get("provider_count")==96
assert store.get("clean_reconstructed")==96
assert store.get("reconstruction_required")==0
assert store.get("published_legacy_code_may_seed_new_base") is False
assert store.get("upstream_code_may_seed_new_base") is False
assert store.get("git_history_code_may_seed_new_base") is False
if "provider_js_seed_used" in store:
    assert store.get("provider_js_seed_used") is False
if "upstream_js_seed_used" in store:
    assert store.get("upstream_js_seed_used") is False

expected=base_store.build_clean_provider_seed("ignored")
expected_sha=hashlib.sha256(expected).hexdigest()
seen_paths=set()
for pid in provider_ids:
    row=rows.get(pid)
    assert isinstance(row,dict), pid
    assert base_store.is_clean_reconstructed(row), pid
    assert row.get("clean_reconstruction_required") is False
    assert row.get("clean_reconstruction_verified") is True
    assert int(row.get("clean_reconstruction_authoring_version") or 0)>=base_store.CLEAN_RECONSTRUCTION_AUTHORING_VERSION
    assert row.get("base_source")==base_store.CLEAN_RECONSTRUCTION_SOURCE

    relative=str(row.get("base_filename") or "")
    path=ROOT/relative
    assert relative.startswith("provider-bases/") and path.is_file(), (pid,relative)
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==str(row.get("base_sha256") or ""), pid
    # ProviderBase v3 is intentionally common and provider-neutral.
    assert raw==expected, pid
    base_store.assert_clean_provider_base(raw,pid)
    seen_paths.add(relative)

assert len(seen_paths)==96
assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected_sha for path in seen_paths)

materializer=(SCRIPTS/"materialize_provider_v3_all.py").read_text(encoding="utf-8")
store_materializer=(SCRIPTS/"materialize_provider_base_v3_store.py").read_text(encoding="utf-8")
manual=(ROOT/".github/workflows/provider-v3-reconstruct-all.yml").read_text(encoding="utf-8")
routine=(ROOT/".github/workflows/sync.yml").read_text(encoding="utf-8")
learn=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

for required in (
    "build_clean_provider_seed",
    "build_provider_data_model",
    "compose_provider_bundle",
    "include_global_core=True",
):
    assert required in materializer, required
for forbidden in (
    "published provider",
    "legacy_provider_js_executed_for_reconstruction=True",
    "upstream_code_executed_for_reconstruction=True",
):
    assert forbidden not in store_materializer

assert "materialize_provider_base_v3_store.py" in manual
assert "materialize_provider_v3_all.py" in manual
assert "verify_provider_v3_reverse_rebuild.py" in manual
assert "materialize_provider_v3_all.py" not in routine
assert "verify_provider_v3_reverse_rebuild.py" not in routine
assert "run_brain_learning_queue.py" in learn

print(
    "PROVIDER_V3_CLEAN_RECONSTRUCTION_OK "
    f"providers={len(provider_ids)} common_base_sha={expected_sha[:16]} "
    "legacy_seed=false upstream_seed=false"
)
