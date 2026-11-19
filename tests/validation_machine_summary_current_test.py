#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from current_provider_scope import projection_active_provider_count, projection_active_provider_ids, projection_visible_provider_count
validation = json.loads((ROOT / "VALIDATION.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
corpus = json.loads((ROOT / ".github/triggers/rotating-popular-corpus.json").read_text(encoding="utf-8"))
candidate_workflow = (ROOT / ".github/workflows/release-candidate-validation.yml").read_text(encoding="utf-8")
finalizer_workflow = (ROOT / ".github/workflows/release-finalize.yml").read_text(encoding="utf-8")

assert validation["release"] == manifest["version"]
assert projection_visible_provider_count() >= len(manifest.get("scrapers") or [])
assert validation["catalogue"]["native_transport_manifests"] == ["manifest.json", "vf/manifest.json"]
assert validation["catalogue"]["consumer_manifests"] == [
    "manifest.json", "vf/manifest.json", "no-anime/manifest.json", "vf-no-anime/manifest.json"
]
assert validation["native_transport"]["manifests"] == ["manifest.json", "vf/manifest.json"]
assert validation["native_transport"]["synthetic_union_is_publication_authority"] is False
assert projection_active_provider_ids()
assert len(projection_active_provider_ids()) == projection_active_provider_count()
assert set(validation["native_sampling"]["global_lists"]) == {"movie", "tv", "anime"}
assert set(corpus.get("lists") or {}) == {"movie", "tv", "anime"}
for lane in ("movie", "tv", "anime"):
    assert len(corpus["lists"][lane]) == validation["native_sampling"]["reserve_size_per_lane"] == 32
assert validation["native_sampling"]["initial_fixtures_per_lane"] == 1
assert validation["native_sampling"]["fixed_batch"] is False
assert validation["native_sampling"]["rotate_only_on_clean_zero_streams"] is True
assert validation["core_contract"]["timeout_seconds"] == 25
certification = validation["final_certification"]
assert certification["status"] == "pending_current_projection_union_five_native_lab_verdicts"
assert certification["requires_five_native_platforms"] is True
assert certification["requires_projection_union_coverage"] is True
assert certification["requires_fixed_point_and_reverse_rebuild"] is True
assert certification["requires_sha_pinned_canonical_manifest_transport"] is True
assert certification["requires_exact_final_release_sha_native_labs"] is True
assert certification["requires_current_nuvio_client_refs"] is True
assert certification["native_proof_transitive_between_clients"] is False
assert certification["post_finalization_native_certification_workflow"] == ".github/workflows/release-candidate-validation.yml"
assert certification["requires_canonical_manifest_matrix"] is True
assert validation["nuvio_runtime_contract"]["subtitle_specific_headers_preserved"] is True

# Final certification is post-finalization and SHA-bound. The finalizer dispatches
# the permanent five-platform validation stack only after the SHA-bound canonical release is
# on main; the validation workflow refuses to certify a different main revision.
assert "expected_sha:" in candidate_workflow
assert "FIELD_RELEASE_CERTIFICATION_SHA_BOUND" in candidate_workflow
assert 'test "$ACTUAL_SHA" = "$EXPECTED_SHA"' in candidate_workflow
assert "Dispatch five-platform certification for exact finalized SHA" in finalizer_workflow
assert 'gh workflow run release-candidate-validation.yml' in finalizer_workflow
assert '-f expected_sha="$FINAL_SHA"' in finalizer_workflow
assert "FIELD_RELEASE_NATIVE_CERTIFICATION_DISPATCHED" in finalizer_workflow

print(
    "VALIDATION_MACHINE_SUMMARY_CURRENT_OK "
    f"release={validation['release']} visible={projection_visible_provider_count()} active={projection_active_provider_count()} corpus=3x32 certification=pending"
)
