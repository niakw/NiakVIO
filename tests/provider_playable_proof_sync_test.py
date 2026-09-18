#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/sync_provider_playable_proof.py"
spec = importlib.util.spec_from_file_location("proof_sync", MODULE)
assert spec and spec.loader
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)

manifest = {
    "version": "x",
    "scrapers": [
        {"id": "complete", "filename": "providers/complete.js", "enabled": True, "canonicalSupportedTypes": ["movie", "tv"]},
        {"id": "partial", "filename": "providers/partial.js", "enabled": True, "canonicalSupportedTypes": ["movie", "tv"]},
        {"id": "negative", "filename": "providers/negative.js", "enabled": True, "canonicalSupportedTypes": ["anime"]},
        {"id": "wrong-sha", "filename": "providers/wrong.js", "enabled": True, "canonicalSupportedTypes": ["movie"]},
    ],
}
overrides = {
    "provider_patches": {
        "complete": {
            "route_data_state": "repair",
            "repair_disposition": {
                "requiredLanes": ["movie", "tv"],
                "currentVerifiedLanes": [],
                "provenLanes": [],
                "missingLanes": ["movie", "tv"],
                "completeCapabilityProof": False,
                "reasonCodes": ["declared_lane_unproven", "repair_survival_restored_requires_exact_bundle_reproof"],
                "laneStatuses": {},
            },
        },
        "partial": {
            "route_data_state": "repair",
            "repair_disposition": {
                "requiredLanes": ["movie", "tv"],
                "currentVerifiedLanes": [],
                "provenLanes": [],
                "missingLanes": ["movie", "tv"],
                "completeCapabilityProof": False,
                "reasonCodes": ["declared_lane_unproven"],
                "laneStatuses": {},
            },
        },
        "negative": {
            "route_data_state": "on",
            "repair_disposition": {
                "requiredLanes": ["anime"],
                "currentVerifiedLanes": ["anime"],
                "provenLanes": ["anime"],
                "missingLanes": [],
                "completeCapabilityProof": True,
                "recoveryStatus": "proven",
                "reasonCodes": ["native_playback_proven"],
                "laneStatuses": {"anime": ["playable_verified"]},
            },
        },
        "wrong-sha": {
            "route_data_state": "repair",
            "repair_disposition": {
                "requiredLanes": ["movie"],
                "currentVerifiedLanes": [],
                "provenLanes": [],
                "missingLanes": ["movie"],
                "completeCapabilityProof": False,
            },
        },
    }
}
certification = {
    "authority": "exact-bundle-playable-lane-certification-v1",
    "manifestVersion": "x",
    "generatedAt": "2026-09-18T01:00:00+00:00",
    "fullManifestCensus": True,
    "providers": [
        {
            "providerId": "complete",
            "filename": "providers/complete.js",
            "bundleSha256": "sha-complete",
            "requiredTypes": ["movie", "tv"],
            "certifiedTypes": ["movie", "tv"],
            "certified": True,
            "lanes": {
                "movie": {"state": "certified", "fixtureSlug": "film"},
                "tv": {"state": "certified", "fixtureSlug": "show"},
            },
        },
        {
            "providerId": "partial",
            "filename": "providers/partial.js",
            "bundleSha256": "sha-partial",
            "requiredTypes": ["movie", "tv"],
            "certifiedTypes": ["movie"],
            "certified": False,
            "lanes": {
                "movie": {"state": "certified", "fixtureSlug": "film"},
                "tv": {"state": "uncertified", "fixtureSlug": None},
            },
        },
        {
            "providerId": "negative",
            "filename": "providers/negative.js",
            "bundleSha256": "sha-negative",
            "requiredTypes": ["anime"],
            "certifiedTypes": [],
            "certified": False,
            "lanes": {"anime": {"state": "uncertified", "fixtureSlug": None}},
        },
        {
            "providerId": "wrong-sha",
            "filename": "providers/wrong.js",
            "bundleSha256": "old-sha",
            "requiredTypes": ["movie"],
            "certifiedTypes": ["movie"],
            "certified": True,
            "lanes": {"movie": {"state": "certified", "fixtureSlug": "film"}},
        },
    ],
}

sha = {
    "complete": "sha-complete",
    "partial": "sha-partial",
    "negative": "sha-negative",
    "wrong-sha": "new-sha",
}
output, report = proof.sync(
    manifest,
    overrides,
    certification,
    sha_lookup=lambda row: sha[proof.cid(row["id"])],
)

complete = output["provider_patches"]["complete"]
disp = complete["repair_disposition"]
assert complete["route_data_state"] == "on"
assert disp["currentVerifiedLanes"] == ["movie", "tv"]
assert disp["provenLanes"] == ["movie", "tv"]
assert disp["missingLanes"] == []
assert disp["completeCapabilityProof"] is True
assert disp["exactBundleProof"]["bundleSha256"] == "sha-complete"
assert disp["exactBundleProof"]["complete"] is True
assert complete["current_stream_proof"]["streamPositive"] is True
assert complete["current_stream_proof"]["verifiedLanes"] == ["movie", "tv"]
assert complete.get("manifest_overrides") is None

partial = output["provider_patches"]["partial"]["repair_disposition"]
assert partial["currentVerifiedLanes"] == ["movie"]
assert partial["provenLanes"] == ["movie"]
assert partial["missingLanes"] == ["tv"]
assert partial["completeCapabilityProof"] is False
assert partial["exactBundleProof"]["verifiedLanes"] == ["movie"]
assert output["provider_patches"]["partial"]["route_data_state"] == "repair"

# Node-negative evidence is non-destructive: the existing Native/proven state is
# byte-for-byte unchanged because there is no positive lane to synchronize.
assert output["provider_patches"]["negative"] == overrides["provider_patches"]["negative"]

# A certificate for another bundle is historical evidence only.
assert output["provider_patches"]["wrong-sha"] == overrides["provider_patches"]["wrong-sha"]
assert report["completeExactBundleProviders"] == ["complete"]
assert report["partialPositiveProviders"] == ["partial"]
assert report["negativeEvidenceDestructive"] is False
assert report["ignoredProviders"]["negative"] == "no_positive_lane"
assert report["ignoredProviders"]["wrong-sha"] == "bundle_sha_mismatch"

print("provider playable proof sync positive-only tests passed")
