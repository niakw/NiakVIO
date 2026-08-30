#!/usr/bin/env python3
"""Fail closed until every current provider has a v2 clean reconstruction proof."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "provider_base_store_clean_contract",
    SCRIPTS / "provider_base_store.py",
)
assert spec is not None and spec.loader is not None
base_store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_store)

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
provenance = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
rows = provenance.get("providers")
assert isinstance(rows, dict)

provider_ids = [
    base_store.canonical_id(str(row.get("id") or ""))
    for row in manifest.get("scrapers") or []
    if isinstance(row, dict) and str(row.get("id") or "").strip()
]
assert len(provider_ids) == len(set(provider_ids)), "manifest provider ids must be unique"
provider_count = len(provider_ids)
assert provider_count > 0, "canonical provider catalogue must not be empty"

store = provenance.get("provider_base_store")
assert isinstance(store, dict)
assert store.get("provider_count") == provider_count
initial_scope = int(store.get("initial_reconstruction_scope") or 0)
assert 0 < initial_scope <= provider_count
assert store.get("migration_scope") == "all-current-providers"
assert store.get("published_legacy_code_may_seed_new_base") is False
assert store.get("upstream_code_may_seed_new_base") is False
assert store.get("git_history_code_may_seed_new_base") is False
if "runtime_role" in store:
    assert store.get("runtime_role") == "reader-only"
    assert store.get("runtime_route_discovery") is False

required = []
clean = []
for provider_id in provider_ids:
    row = rows.get(provider_id)
    assert isinstance(row, dict), f"{provider_id}: missing provenance"
    if base_store.requires_clean_reconstruction(row):
        required.append(provider_id)
        assert row.get("clean_reconstruction_required") is True, f"{provider_id}: v2 reconstruction flag missing"
        assert row.get("legacy_provider_base_role") in {
            "compatibility-lkg-only",
            "superseded-by-clean-candidate",
        }, f"{provider_id}: invalid legacy base role"
        assert row.get("legacy_provider_js_role") == "knowledge-only-for-reconstruction"
        assert row.get("legacy_provider_js_executed_for_reconstruction") is False
    else:
        clean.append(provider_id)
        assert row.get("clean_reconstruction_required") is False
        assert row.get("clean_reconstruction_verified") is True
        assert row.get("clean_reconstruction_authoring_version", 0) >= 2

# This migration intentionally resets trust for every pre-v2 base, including
# AniZone/DVDPlay. The assertion should shrink only as providers acquire an
# explicit v2 clean reconstruction proof on future proposal merges.
current_v2 = [
    provider_id
    for provider_id in provider_ids
    if base_store.is_clean_reconstructed(rows.get(provider_id))
]
assert set(clean) == set(current_v2)
assert len(required) + len(clean) == provider_count
assert store.get("reconstruction_required") == len(required)
assert store.get("clean_reconstructed") == len(clean)

# At the introduction of v2 every provider that existed at that time was
# untrusted for seeding. Future providers may be born directly as clean v2
# reconstructions, so current catalogue size must never be frozen here.
if not current_v2:
    assert len(required) == provider_count

pending_row = {
    "base_source": base_store.CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE,
    "clean_reconstruction_candidate": True,
    "clean_reconstruction_verified": False,
    "clean_reconstruction_authoring_version": 2,
}
assert base_store.is_clean_reconstruction_candidate(pending_row) is True
assert base_store.requires_clean_reconstruction(pending_row) is True

discover = (SCRIPTS / "discover_candidates.py").read_text(encoding="utf-8")
promoter = (SCRIPTS / "promote_candidates.py").read_text(encoding="utf-8")
base_store_source = (SCRIPTS / "provider_base_store.py").read_text(encoding="utf-8")
assert 'row.setdefault("clean_reconstruction_marked_at", marked_at)' in base_store_source
assert 'store.update({' in base_store_source
assert '"runtimeRole": "reader"' in base_store_source
assert '"runtimeDiscovery": False' in base_store_source
assert 'function _expandLearnedRoute' in base_store_source
assert 'function _runtimePlanAvailable' in base_store_source
assert 'if (!_runtimePlanAvailable()) return [];' in base_store_source
assert '"/search?q=" + query' not in base_store_source
assert '"/search/" + query' not in base_store_source
assert "function _detailGuesses" not in base_store_source
assert "slice(0, 24)" not in base_store_source
assert "NIAKVIO_PROVIDER_MODEL.officialHub,\n    ...(NIAKVIO_PROVIDER_MODEL.origins" not in base_store_source
embedded_source = base_store_source.split("function _embeddedText(value) {", 1)[1].split("function _slug(value) {", 1)[0]
assert embedded_source.count(".replace(") == 1, "embedded URL decoding must remain single-pass"
assert 'const raw = match[1] || match[0] || "";' in base_store_source
signed_runtime_block = base_store_source.split("const discoveredNested = _uniq(urls.filter(_playerLike));", 1)[1].split("} else {\n          const runtimeCandidates = _directPlayerUrls", 1)[0]
assert signed_runtime_block.index("_resolveRuntimeApi(") < signed_runtime_block.index("_crawlDirectMedia("), "signed runtime API must be consumed before third-party embed crawl"
assert "--clean-reconstruction" in discover
assert '"upstream_code_role": "knowledge-only"' in discover
assert '"upstream_code_executed": False' in discover
assert '"legacy_provider_js_executed_for_reconstruction": False' in discover
assert '"new-niakvio-clean-seed"' in discover
assert '"pending-niakvio-clean-reconstruction-v2"' in discover
assert '"legacy-providerbase-compatibility-only"' in discover
assert "CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS" in discover
assert "scripts/provider_patches/castle_strict_identity_v1.py" in base_store_source
assert "excluded_patch_scripts=CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS" in base_store_source

profiles_builder = (SCRIPTS / "build_provider_runtime_profiles.py").read_text(encoding="utf-8")
assert "CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS" in profiles_builder
assert "clean_seed_origin" in profiles_builder
assert "excluded_patch_scripts=(" in profiles_builder

published_reapply = (SCRIPTS / "reapply_published_overrides.py").read_text(encoding="utf-8")
assert "is_clean_reconstructed(provider_provenance)" in published_reapply
assert "is_clean_reconstruction_candidate(provider_provenance)" in published_reapply
assert "CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS" in published_reapply
assert "excluded_patch_scripts=(" in published_reapply
assert "compatibility/LKG JavaScript cannot seed or replace ProviderBase" in promoter
assert "legacy ProviderBase is compatibility-only" in promoter
assert "refusing legacy ProviderBase fallback" in promoter
assert "if previous_requires_clean:" in promoter
assert "CLEAN_RECONSTRUCTION_SOURCE" in promoter
assert "CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE" in promoter
assert "is_pending_clean_reconstruction_candidate" in promoter
assert "pending_clean_reconstruction_has_strict_deep_proof" in promoter
assert '"clean_reconstruction_strict_deep_proof_pending"' in promoter
assert '"pending-canonical-deep-proof"' in promoter
assert 'str(mode) == "deep"' in promoter
assert 'bool(decision.get("strict_activation_eligible", False))' in promoter

sync_workflow = (ROOT / ".github/workflows/sync.yml").read_text(encoding="utf-8")
assert "'PROVENANCE.json'" in sync_workflow
assert "'provider-bases/**'" in sync_workflow
assert "PROVENANCE\\.json|provider-bases/" in sync_workflow

materializer = (ROOT / "scripts" / "materialize_clean_provider_reconstruction.py").read_text(encoding="utf-8")
assert 'for provider_id in sorted(candidates):' in materializer, (
    "clean reconstruction proposals must persist every reconstruction-required candidate, "
    "not only providers reached by the Learning queue"
)
assert 'queue_results = {' in materializer
assert 'if not lab_is_strictly_playable(result):' not in materializer, (
    "Learning playability cannot discard a structurally valid clean ProviderBase candidate"
)
assert '"canonical-deep-proof-pending"' in materializer
assert '"strictLearningProofRequiredForProposal": False' in materializer
assert '"strictDeepProofRequiredForVerification": True' in materializer
assert 'build_base_from_seed(' in materializer, "candidate persistence must keep structural ProviderBase validation"

runtime_repair = (ROOT / "scripts" / "runtime_repair.py").read_text(encoding="utf-8")
repair_start = runtime_repair.index("def create_repair_candidate(")
repair_end = runtime_repair.index("\ndef ", repair_start + 10)
repair_fn = runtime_repair[repair_start:repair_end]
assert "parent_data = source_path.read_bytes()" in repair_fn
assert 'phase="runtime"' in repair_fn
assert "build_clean_provider_seed" not in repair_fn, (
    "routine Repair must patch the durable/current ProviderBase, never rebuild a clean seed from scratch"
)
assert 'repaired["runtime_repair"]' in repair_fn
assert '"parent_sha256": parent_digest' in repair_fn

print(
    "Provider clean reconstruction contract passed: "
    f"total={len(provider_ids)} required={len(required)} clean_v2={len(clean)}"
)

# Clean v2 runtime is a reader, not a discovery engine.
seed = base_store.build_clean_provider_seed(
    "reader-contract",
    {"id": "reader-contract", "name": "Reader Contract", "supportedTypes": ["tv"]},
    known_site="https://example.invalid/",
    provider_model={"strategy": "html_scraper", "routes": [], "observedUrls": []},
).decode("utf-8")
assert '"runtimeRole":"reader"' in seed
assert '"runtimeDiscovery":false' in seed
assert "function _detailGuesses" not in seed
assert '"/search?q="' not in seed
assert "if (!_runtimePlanAvailable()) return [];" in seed

overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
for provider_id, patch in (overrides.get("provider_patches") or {}).items():
    if not isinstance(patch, dict):
        continue
    scripts = [str(value) for value in patch.get("patch_scripts") or []]
    assert "scripts/provider_patches/adaptive_runtime_recovery_v4.py" not in scripts, (
        f"{provider_id}: runtime discovery v4 cannot be published; move route knowledge to Discovery/Learning"
    )
    assert "scripts/provider_patches/adaptive_runtime_recovery_v5.py" not in scripts, (
        f"{provider_id}: runtime discovery v5 cannot be published; move route knowledge to Discovery/Learning"
    )

for provider_id, patch in (overrides.get("provider_patches") or {}).items():
    if not isinstance(patch, dict):
        continue
    for path, options in (patch.get("patch_script_options") or {}).items():
        if path == "scripts/provider_patches/vf_catalogue_recovery.py" and isinstance(options, dict):
            assert options.get("strategy") != "api_discovery", (
                f"{provider_id}: provider runtime cannot discover API routes; persist them as learned routes"
            )
