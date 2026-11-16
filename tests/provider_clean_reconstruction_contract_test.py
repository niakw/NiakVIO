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
sys.path.insert(0, str(ROOT / "scripts"))
from current_provider_scope import projection_active_provider_count
from current_provider_scope import projection_active_provider_ids
from current_provider_scope import projection_active_provider_rows
from current_provider_scope import projection_disabled_provider_count

SCRIPTS=ROOT/"scripts"
sys.path.insert(0,str(SCRIPTS))

import provider_base_store as base_store

provenance=json.loads((ROOT/"PROVENANCE.json").read_text(encoding="utf-8"))
rows=provenance.get("providers")
store=provenance.get("provider_base_store")
assert isinstance(rows,dict)
assert isinstance(store,dict)

active_ids=projection_active_provider_ids()
entries=projection_active_provider_rows()
provider_ids=[base_store.canonical_id(str(row["id"])) for row in entries]
assert set(provider_ids)==active_ids, (len(provider_ids),len(active_ids))
assert len(set(provider_ids))==len(provider_ids)

assert base_store.INITIAL_RECONSTRUCTION_SCOPE==96
assert base_store.CLEAN_RECONSTRUCTION_AUTHORING_VERSION>=3
assert base_store.CLEAN_RECONSTRUCTION_SOURCE=="niakvio-clean-reconstruction-v3"
assert store.get("provider_count")==projection_active_provider_count()
assert store.get("clean_reconstructed")==projection_active_provider_count()
assert store.get("reconstruction_required")==0
assert store.get("published_legacy_code_may_seed_new_base") is False
assert store.get("upstream_code_may_seed_new_base") is False
assert store.get("git_history_code_may_seed_new_base") is False
if "provider_js_seed_used" in store:
    assert store.get("provider_js_seed_used") is False
if "upstream_js_seed_used" in store:
    assert store.get("upstream_js_seed_used") is False

expected=base_store.build_clean_provider_seed("ignored")
expected_text=expected.decode("utf-8", errors="strict")
v34_helper="function _spv34RouteMediaCompatible(route, mediaType) {"
assert expected_text.count(v34_helper)==1, (
    "ProviderBase common runtime must define the V34 route/media compatibility helper exactly once",
    expected_text.count(v34_helper),
)
assert expected_text.count("NIAKVIO_PROVIDER_ROUTE_MEDIA_COMPAT_V34")==1, (
    "ProviderBase common runtime must bind the V34 route/media compatibility gate exactly once",
    expected_text.count("NIAKVIO_PROVIDER_ROUTE_MEDIA_COMPAT_V34"),
)
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

assert len(seen_paths) == projection_active_provider_count()
assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected_sha for path in seen_paths)

coverage=base_store.validate_all()
assert coverage["checked"]==projection_active_provider_count(), coverage
assert coverage["clean_reconstructed"]==projection_active_provider_count(), coverage
assert coverage["reconstruction_required"]==0, coverage
assert coverage["disabled_visible"]==projection_disabled_provider_count(), coverage

materializer=(SCRIPTS/"materialize_provider_v3_all.py").read_text(encoding="utf-8")
store_materializer=(SCRIPTS/"materialize_provider_base_v3_store.py").read_text(encoding="utf-8")
identity_compat=(SCRIPTS/"materialize_provider_base_identity_only.py").read_text(encoding="utf-8")
base_store_source=(SCRIPTS/"provider_base_store.py").read_text(encoding="utf-8")
repair_legacy_source=base_store_source.split("def repair_legacy_bases()",1)[1].split("def repair_derived_base_tails()",1)[0]
repair_derived_source=base_store_source.split("def repair_derived_base_tails()",1)[1].split("def migrate_existing()",1)[0]
assert "projection_active_provider_rows()" in repair_legacy_source
assert "manifest.get(\"scrapers\")" not in repair_legacy_source
assert "projection_active_provider_rows()" in repair_derived_source
assert "manifest.get(\"scrapers\")" not in repair_derived_source
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

for token in (
    "SOURCE_MIGRATION_PATHS",
    "_source_migration_snapshot",
    "ProviderBase source migrations are not fixed-point on checked-in authority",
    'ROOT / "scripts" / "provider_base_store.py"',
    'ROOT / "scripts" / "apply_provider_overrides.py"',
    'ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py"',
    'ROOT / "scripts" / "provider_patches" / "mugiwarastream_packed_runtime_v1.py"',
):
    assert token in store_materializer, f"canonical ProviderBase materializer lost source fixed-point guard: {token}"
assert store_materializer.index("sanitize_provider_v3_execution_routes_v1.py") < store_materializer.index("before = _source_migration_snapshot()")
assert store_materializer.index("before = _source_migration_snapshot()") < store_materializer.index("upgrade_provider_base_runtime_v5.py")
assert 'store["provider_media_transport"] = "canonical-anime-v32"' in store_materializer
assert 'store["html_search_identity_coverage"] = "v33"' in store_materializer
assert 'store["dle_episode_variant_coverage"] = "v34"' in store_materializer

assert "materialize_provider_base_v3_store.py" in manual
assert "materialize_provider_v3_all.py" in manual
assert "python scripts/reconcile_provider_static_authority.py --apply" in manual
assert manual.index("python scripts/reconcile_provider_static_authority.py --apply") < manual.index("python scripts/enrich_provider_v3_static_knowledge.py")
assert "python tests/provider_static_authority_france_only_test.py" in manual
assert "verify_provider_v3_reverse_rebuild.py" in manual

# The historical identity-only entry point must not retain independent
# reconstruction authority. In particular, it may not regress to the old
# Global-only cardinality or replay runtime-v5 without the cumulative current
# ProviderBase preparation owned by the canonical store materializer.
assert "materialize_provider_base_v3_store.py" in identity_compat
assert "active_provider_count" not in identity_compat
assert "upgrade_provider_base_runtime_v5.py" not in identity_compat
assert "manifest.json" not in identity_compat
assert "IDENTITY_ONLY_PROVIDER_BASE_COMPAT" in identity_compat

assert "materialize_provider_v3_all.py" not in routine
assert "verify_provider_v3_reverse_rebuild.py" not in routine
assert "run_brain_learning_queue.py" in learn

# The initial published-stage builder is already local and must not receive
# discover_candidates.py-specific CLI flags.
published_stage=learn.split("      - name: Build isolated current provider stage",1)[1].split("      - name:",1)[0]
assert "build_published_provider_stage.py --stage staging" in published_stage
assert "args+=(--local-catalog-only)" not in published_stage
# Fast-Handoff reconstruction must derive ProviderBase from local structured authority.
learn_stage=learn.split("      - name: Build clean ProviderBase reconstruction stage",1)[1].split("      - name:",1)[0]
assert "--clean-reconstruction" in learn_stage
assert "--provider" in learn_stage
assert "--local-catalog-only" in learn_stage
assert learn_stage.index("--provider") < learn_stage.index("--local-catalog-only")
assert "ProviderBase is derived from NiakVIO-owned structured authority" in learn_stage

print(
    "PROVIDER_V3_CLEAN_RECONSTRUCTION_OK "
    f"providers={len(provider_ids)} common_base_sha={expected_sha[:16]} "
    "legacy_seed=false upstream_seed=false"
)
