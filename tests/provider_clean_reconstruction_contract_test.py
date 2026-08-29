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
assert len(provider_ids) == 95, f"expected the canonical 95-provider catalogue, got {len(provider_ids)}"

store = provenance.get("provider_base_store")
assert isinstance(store, dict)
assert store.get("provider_count") == 95
assert store.get("initial_reconstruction_scope") == 95
assert store.get("migration_scope") == "all-current-providers"
assert store.get("published_legacy_code_may_seed_new_base") is False
assert store.get("upstream_code_may_seed_new_base") is False
assert store.get("git_history_code_may_seed_new_base") is False

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
assert len(required) + len(clean) == 95
assert store.get("reconstruction_required") == len(required)
assert store.get("clean_reconstructed") == len(clean)

# At the introduction of v2, all 95 historical bases are untrusted for seeding.
# Once genuine v2 reconstructions land, this exact initial-state assertion may
# be removed; the invariant above remains permanent.
if not current_v2:
    assert len(required) == 95

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
assert "--clean-reconstruction" in discover
assert '"upstream_code_role": "knowledge-only"' in discover
assert '"upstream_code_executed": False' in discover
assert '"legacy_provider_js_executed_for_reconstruction": False' in discover
assert '"new-niakvio-clean-seed"' in discover
assert '"pending-niakvio-clean-reconstruction-v2"' in discover
assert '"legacy-providerbase-compatibility-only"' in discover
assert "compatibility/LKG JavaScript cannot seed or replace ProviderBase" in promoter
assert "legacy ProviderBase is compatibility-only" in promoter
assert "refusing legacy ProviderBase fallback" in promoter
assert "if previous_requires_clean:" in promoter
assert "CLEAN_RECONSTRUCTION_SOURCE" in promoter

print(
    "Provider clean reconstruction contract passed: "
    f"total={len(provider_ids)} required={len(required)} clean_v2={len(clean)}"
)
