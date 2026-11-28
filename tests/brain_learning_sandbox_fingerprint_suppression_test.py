#!/usr/bin/env python3
"""Learning suppression must be scoped to the executable implementation."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_brain_learning_sandbox.py"
spec = importlib.util.spec_from_file_location("brain_learning_sandbox_fp", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

base = {
    "providerId": "representative",
    "providerVersion": "*",
    "signature": "media_extraction_gap",
    "profile": "document_request_contract_mining_v2",
    "successes": 0,
    "failures": 3,
    "consecutiveFailures": 3,
    "executionObserved": True,
    "lastOutcome": "rejected",
}
current = "b" * 64
legacy_candidate = {}

old_impl = {**base, "strategyImplementationFingerprint": "a" * 64}
assert mod._negative_failure_count(
    [old_impl],
    candidate=legacy_candidate,
    provider_id="representative",
    provider_version="*",
    signature="media_extraction_gap",
    profile=base["profile"],
    current_profile=base["profile"],
    current_fingerprint=current,
) == 0

same_impl = {**base, "strategyImplementationFingerprint": current}
assert mod._negative_failure_count(
    [same_impl],
    candidate=legacy_candidate,
    provider_id="representative",
    provider_version="*",
    signature="media_extraction_gap",
    profile=base["profile"],
    current_profile=base["profile"],
    current_fingerprint=current,
) == 3

legacy = {**base, "strategyImplementationFingerprint": ""}
assert mod._negative_failure_count(
    [legacy],
    candidate=legacy_candidate,
    provider_id="representative",
    provider_version="*",
    signature="media_extraction_gap",
    profile=base["profile"],
    current_profile=base["profile"],
    current_fingerprint=current,
) == 3

# Fingerprint freshness only relaxes the exact planner-selected Bloc. It must
# not erase negative memory for unrelated exploratory profiles.
other = {
    **base,
    "profile": "runtime_response_salvage_v1",
    "strategyImplementationFingerprint": "a" * 64,
}
assert mod._negative_failure_count(
    [other],
    candidate=legacy_candidate,
    provider_id="representative",
    provider_version="*",
    signature="media_extraction_gap",
    profile="runtime_response_salvage_v1",
    current_profile=base["profile"],
    current_fingerprint=current,
) == 3

exact_parent = {
    "learning_parent_authority": "published-exact-current-bytes",
    "learning_parent_published_sha256": "c" * 64,
    "sha256": "c" * 64,
}
# A legacy negative without parent-byte provenance cannot veto an exact current
# published parent. Same-parent evidence still suppresses normally.
assert mod._negative_failure_count(
    [same_impl],
    candidate=exact_parent,
    provider_id="representative",
    provider_version="*",
    signature="media_extraction_gap",
    profile=base["profile"],
    current_profile=base["profile"],
    current_fingerprint=current,
) == 0

wrong_parent = {
    **same_impl,
    "parentArtifactSha256": "d" * 64,
    "parentAuthority": "published-exact-current-bytes",
}
assert mod._negative_failure_count(
    [wrong_parent],
    candidate=exact_parent,
    provider_id="representative",
    provider_version="*",
    signature="media_extraction_gap",
    profile=base["profile"],
    current_profile=base["profile"],
    current_fingerprint=current,
) == 0

same_parent = {
    **same_impl,
    "parentArtifactSha256": "c" * 64,
    "parentAuthority": "published-exact-current-bytes",
}
assert mod._negative_failure_count(
    [same_parent],
    candidate=exact_parent,
    provider_id="representative",
    provider_version="*",
    signature="media_extraction_gap",
    profile=base["profile"],
    current_profile=base["profile"],
    current_fingerprint=current,
) == 3

print(
    "FIELD_BRAIN_LEARNING_IMPLEMENTATION_SUPPRESSION "
    "changed_impl_replay=true same_impl_blocked=true legacy_fail_closed=true"
)
