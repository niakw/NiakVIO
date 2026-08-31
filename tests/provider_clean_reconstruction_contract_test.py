#!/usr/bin/env python3
"""Fail closed until every current provider has a v2 clean reconstruction proof."""
from __future__ import annotations

import importlib.util
import json
import sys
import urllib.parse
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
        assert row.get("clean_reconstruction_authoring_version", 0) >= base_store.CLEAN_RECONSTRUCTION_AUTHORING_VERSION

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

# An unverified clean candidate must never strand an existing provider. Every
# preserved pre-reconstruction LKG reference must resolve locally and match the
# recorded SHA so production compilation can safely keep the known-good base
# until canonical Deep proves the replacement.
pending_lkg_checked = 0
for provider_id in required:
    row = rows[provider_id]
    if not base_store.is_clean_reconstruction_candidate(row):
        continue
    legacy_file = str(row.get("legacy_base_filename_before_clean_candidate") or "").strip()
    legacy_sha = str(row.get("legacy_base_sha256_before_clean_candidate") or "").strip().casefold()
    if not legacy_file or not legacy_sha:
        continue
    runtime_path, runtime_sha = base_store.resolve_runtime_base(provider_id, row, require=True)
    assert runtime_path is not None
    assert runtime_path.relative_to(ROOT).as_posix() == legacy_file, (
        f"{provider_id}: pending clean candidate did not resolve preserved LKG"
    )
    assert runtime_sha == legacy_sha, f"{provider_id}: preserved LKG SHA drift"
    pending_lkg_checked += 1

assert pending_lkg_checked > 0, "expected pending clean candidates with preserved production LKG"

# At the introduction of v2 every provider that existed at that time was
# untrusted for seeding. Future providers may be born directly as clean v2
# reconstructions, so current catalogue size must never be frozen here.
if not current_v2:
    assert len(required) == provider_count

pending_row = {
    "base_source": base_store.CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE,
    "clean_reconstruction_candidate": True,
    "clean_reconstruction_verified": False,
    "clean_reconstruction_authoring_version": base_store.CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
}
assert base_store.is_clean_reconstruction_candidate(pending_row) is True
assert base_store.requires_clean_reconstruction(pending_row) is True

discover = (SCRIPTS / "discover_candidates.py").read_text(encoding="utf-8")
promoter = (SCRIPTS / "promote_candidates.py").read_text(encoding="utf-8")
base_store_source = (SCRIPTS / "provider_base_store.py").read_text(encoding="utf-8")
assert 'row.setdefault("clean_reconstruction_marked_at", marked_at)' in base_store_source
assert "def provider_base_store_metadata(" in base_store_source
assert "INITIAL_RECONSTRUCTION_SCOPE = 95" in base_store_source
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
assert '"modelSchemaVersion": 3' in base_store_source
assert '"routePlanVersion": 2' in base_store_source
tmdb_block = base_store_source.split("async function _tmdb(tmdbId, mediaType) {", 1)[1].split("function _runtimeBases() {", 1)[0]
assert "TMDB_API_KEY" not in tmdb_block
assert "api.themoviedb.org" not in tmdb_block
assert "__nuvioMediaContext" in tmdb_block
assert "NUVIO_PROVIDER_TIMEOUT" in base_store_source
assert "function _recipeMediaType" in base_store_source
assert "function _collectionMediaType" in base_store_source
assert "__nuvioCollectionMediaType" in base_store_source
assert "actualMedia !== expectedMedia" in base_store_source
assert "recipe.strictIdentity" in base_store_source
assert "Math.abs(Number(year) - Number(expectedYear)) > 1" in base_store_source
assert "recipe.directSourcesOnly" in base_store_source
assert "urls.filter(_directMedia)" in base_store_source
assert "force_clean_reconstruction or (reconstruction_required and clean_reconstruction)" in discover

discover_spec = importlib.util.spec_from_file_location("discover_clean_contract", SCRIPTS / "discover_candidates.py")
assert discover_spec is not None and discover_spec.loader is not None
discover_module = importlib.util.module_from_spec(discover_spec)
discover_spec.loader.exec_module(discover_module)
contract_overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
polluted = {
    "hosts": ["purstream.id", "api.purstream.id", "api.purstream", "old.invalid", "raw.githubu"],
    "routes": ["/search-bar/search/{query}"],
    "observedUrls": ["https://api.purstream.id/api/v1", "https://api.purstream/foo", "https://old.invalid/x"],
    "routeFragments": [],
}
purstream_model = discover_module.clean_provider_model(
    "purstream",
    polluted,
    contract_overrides,
    "https://purstream.id",
)
assert purstream_model["apiRecipe"]["base"] == "https://api.purstream.id/api/v1"
purstream_origin_hosts = {
    (urllib.parse.urlparse(value).hostname or "").casefold()
    for value in purstream_model["origins"]
}
purstream_observed_hosts = {
    (urllib.parse.urlparse(value).hostname or "").casefold()
    for value in purstream_model["observedUrls"]
}
assert "api.purstream.id" in purstream_origin_hosts
assert purstream_origin_hosts.isdisjoint({"api.purstream", "old.invalid"})
assert purstream_observed_hosts.isdisjoint({"old.invalid", "raw.githubu"})

profiles_builder = (SCRIPTS / "build_provider_runtime_profiles.py").read_text(encoding="utf-8")
assert "CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS" in profiles_builder
assert "clean_seed_origin" in profiles_builder
assert "excluded_patch_scripts=(" in profiles_builder

published_reapply = (SCRIPTS / "reapply_published_overrides.py").read_text(encoding="utf-8")
assert "runtime_base_is_clean_v2(" in published_reapply
assert "resolve_runtime_base(" in published_reapply
assert "resolve_base(provider_id, provenance_row, require=True)" in published_reapply
assert "CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS" in published_reapply
assert "excluded_patch_scripts=(" in published_reapply

assert "CLEAN_V2_CORE_BOUNDARY_MARKER" in published_reapply
assert "_canonicalize_clean_v2_core_boundary" in published_reapply

assert "publication_configured_safety_quarantine" in published_reapply
assert '"source": "provider-overrides"' in published_reapply
assert '"scope": "configured-safety"' in published_reapply
assert "configured safety quarantine has no reason" in published_reapply
assert "clean v2 publication has no derived Core marker" in published_reapply
assert "compatibility/LKG JavaScript cannot seed or replace ProviderBase" in promoter
assert "legacy ProviderBase is compatibility-only" in promoter
assert "refusing legacy ProviderBase fallback" in promoter
copy_candidate_block = promoter.split("def copy_candidate(", 1)[1].split("\ndef build_entry(", 1)[0]
assert "apply_overrides(" not in copy_candidate_block, "promotion must not replay provider fixes"
assert 'authorization.get("reason") == "accepted_runtime_repair"' in copy_candidate_block
assert "require=True" in copy_candidate_block, "verified clean ProviderBase must fail closed if immutable base is missing"
assert "provider_base_store_metadata(" in promoter
assert 'or "clean reconstruction candidate could not be reduced" in message' in promoter
assert "if previous_requires_clean:" in promoter
assert "CLEAN_RECONSTRUCTION_SOURCE" in promoter
assert "CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE" in promoter
assert "is_pending_clean_reconstruction_candidate" in promoter
assert "is_clean_reconstruction_migration_candidate" in promoter
assert '"new-niakvio-clean-seed"' in promoter
assert '"pending-niakvio-clean-reconstruction-v2"' in promoter
assert "clean_reconstruction_has_strict_deep_proof" in promoter
assert '"pending-canonical-deep-proof"' in promoter
assert '"preserved-published-state-clean-candidate-pending"' in promoter
assert 'retained = dict(old_entry)' in promoter
migration_promoter_block = promoter.split(
    'is_clean_reconstruction_migration_candidate(selected, previous_base_row)',
    1,
)[1].split('\n            try:', 1)[0]
assert 'retained["enabled"]' not in migration_promoter_block
assert 'restore_pending_activation_lkg' not in migration_promoter_block
assert 'pending_configured_disabled' not in migration_promoter_block
assert 'old_safety_quarantine' not in migration_promoter_block
assert '"activation_mode": str(' in migration_promoter_block
assert 'str(mode) == "deep"' in promoter
assert 'str(health.get("status") or "") == "healthy"' in promoter
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
deep_repair_loop = (ROOT / "scripts" / "deep_repair_loop.py").read_text(encoding="utf-8")
assert '"provider_base_change_authorized"' in deep_repair_loop
assert '"reason": "accepted_runtime_repair"' in deep_repair_loop

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
