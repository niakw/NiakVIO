#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import activation_preservation_core_rehash as adapter  # noqa: E402
import validate_activation_preservation as legacy  # noqa: E402

reason = "synthetic_wrong_content"
current_bundle = (
    f"/* NUVIO_PROVIDER_QUARANTINE_V1: {reason} */\n"
    '"use strict";\n'
    "async function getStreams(){return [];}\n"
    "if(typeof module!==\"undefined\"&&module&&module.exports)module.exports={getStreams:getStreams};\n"
)
current_sha = hashlib.sha256(current_bundle.encode("utf-8")).hexdigest()
current_filename = f"providers/test--quarantine--{current_sha[:16]}.js"
historical_sha = "a" * 64
historical_filename = f"providers/test--quarantine--{historical_sha[:16]}.js"
tested_sha = "b" * 64

manifest = {"id": "test", "enabled": False, "filename": current_filename}
patch = {
    "capability": "quarantined",
    "manifest_overrides": {"enabled": False},
    "patch_scripts": [legacy.QUARANTINE_PATCH],
    "patch_script_options": {legacy.QUARANTINE_PATCH: {"reason": reason}},
}
provenance = {
    "activation_mode": "configured_safety_quarantine",
    "activation_eligible": False,
    "activation_blockers": ["configured_safety_quarantine"],
    "published_filename": current_filename,
    "patched_sha256": current_sha,
}
finding = {
    "provider_id": "test",
    "evidence_source": "operator_live_client_report",
    "operator_confirmed": True,
    "quarantine_reason": reason,
    "tested_commit_sha": "c" * 40,
    "tested_bundle": f"providers/test--published-baseline--{tested_sha[:16]}.js",
    "tested_bundle_sha256": tested_sha,
    "fixture": {"tmdbId": "123", "mediaType": "movie", "title": "Synthetic"},
    "quarantined_bundle": historical_filename,
    "quarantined_bundle_sha256": historical_sha,
    "evidence_type": "manual_live_non_playable",
    "transport_playable": False,
    "observed_failure": "infinite_loading",
    "clients_with_failure": ["desktop_macos"],
}

with tempfile.TemporaryDirectory() as tmp:
    temp_root = Path(tmp)
    target = temp_root / current_filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(current_bundle, encoding="utf-8")

    original_root = legacy.ROOT
    legacy.ROOT = temp_root
    try:
        strict_ok, strict_reason = legacy.configured_safety_quarantine(
            "test", manifest, patch, provenance, finding
        )
        assert strict_ok is False
        assert strict_reason in {
            "safety_quarantine_bundle_finding_sha_mismatch",
            "safety_quarantine_bundle_finding_path_mismatch",
        }

        accepted, accepted_reason = adapter._configured_safety_quarantine_with_core_rehash(
            legacy.configured_safety_quarantine,
            "test",
            manifest,
            patch,
            provenance,
            finding,
        )
        assert accepted, accepted_reason
        assert accepted_reason.endswith(":deterministic_core_rehash")

        bad_provenance = copy.deepcopy(provenance)
        bad_provenance["patched_sha256"] = "d" * 64
        accepted, rejected_reason = adapter._configured_safety_quarantine_with_core_rehash(
            legacy.configured_safety_quarantine,
            "test",
            manifest,
            patch,
            bad_provenance,
            finding,
        )
        assert accepted is False
        assert rejected_reason == "safety_quarantine_provenance_sha_mismatch"

        bad_finding = copy.deepcopy(finding)
        bad_finding["operator_confirmed"] = False
        accepted, rejected_reason = adapter._configured_safety_quarantine_with_core_rehash(
            legacy.configured_safety_quarantine,
            "test",
            manifest,
            patch,
            provenance,
            bad_finding,
        )
        assert accepted is False
        assert rejected_reason == "manual_safety_finding_not_confirmed"
    finally:
        legacy.ROOT = original_root

assert adapter._record_requires_baseline_restore({
    "action": legacy.INCONCLUSIVE_DISABLE_ACTION,
    "enabled": False,
}) is True
assert adapter._record_requires_baseline_restore({
    "action": "published-disabled-failed-gates",
    "enabled": False,
    "failed_gates": ["02_healthy_functional_status", "00_current_playable_stream"],
    "observed_status": "unavailable",
    "evidence": {
        "streams_playable": 0,
        "payload_verified_streams": 0,
        "identity_contradiction_count": 0,
        "duration_identity_mismatch_count": 0,
        "disallowed_streams": 0,
        "failure_classes": ["provider_http_error"],
    },
}) is True
assert adapter._record_requires_baseline_restore({
    "action": "preserved-published-state-clean-candidate-pending",
    "enabled": True,
    "failed_gates": [],
}) is True
assert adapter._record_requires_baseline_restore({
    "action": "preserved-published-state-clean-candidate-pending",
    "enabled": False,
    "failed_gates": [],
}) is True
assert adapter._record_requires_baseline_restore({
    "action": "preserved-published-state-clean-candidate-pending",
    "enabled": True,
    "failed_gates": ["current_playable_stream"],
}) is False

original_context = os.environ.get("NUVIO_PROVIDER_V3_CONTEXT")
try:
    os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = "workspace"
    assert legacy.preexisting_published_disable_is_deferred(
        {"enabled": False},
        {"enabled": False},
        {"enabled": True, "action": "preserved-current-enabled-ci-uncertain"},
    ) is True
    os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = "production"
    assert legacy.preexisting_published_disable_is_deferred(
        {"enabled": False},
        {"enabled": False},
        {"enabled": True},
    ) is False
    assert legacy.preexisting_published_disable_is_deferred(
        {"enabled": False},
        {"enabled": False},
        {"enabled": False},
    ) is True
finally:
    if original_context is None:
        os.environ.pop("NUVIO_PROVIDER_V3_CONTEXT", None)
    else:
        os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = original_context

print("activation preservation deterministic Core rehash tests passed")

assert legacy.pending_clean_preservation_is_deferred(
    {
        "action": "preserved-published-state-clean-candidate-pending",
        "enabled": False,
        "failed_gates": [],
    },
    {},
) is True
assert legacy.pending_clean_preservation_is_deferred(
    {
        "action": "preserved-published-state-clean-candidate-pending",
        "enabled": False,
        "failed_gates": ["current_playable_stream"],
    },
    {"clean_reconstruction_verified": True},
) is True
assert legacy.pending_clean_preservation_is_deferred(
    {
        "action": "published-disabled-failed-gates",
        "enabled": False,
        "failed_gates": ["current_playable_stream"],
    },
    {},
) is False

# Pending clean-v2 migration state must not hard-block P2 activation preservation.
validator_source = (ROOT / "scripts" / "validate_activation_preservation.py").read_text(encoding="utf-8")
assert "deferred_to_learning" in validator_source
assert '"preserved-published-state-clean-candidate-pending"' in validator_source
assert '"pending-canonical-deep-proof"' in validator_source
assert "FIELD_ACTIVATION_DEFERRED_TO_LEARNING" in validator_source
assert "accounted_for = len(active) + len(justified) + len(deferred_to_learning)" in validator_source
