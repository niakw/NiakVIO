#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/learn_provider_positive_fixtures.py"
spec = importlib.util.spec_from_file_location("positive_memory", MODULE)
assert spec and spec.loader
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)

registry = {
    "providers": {
        "demo": {
            "lanes": {
                "movie": {
                    "fixtureSlug": "old-film",
                    "knownPositiveFixtures": ["old-film", "older-film"],
                    "state": "certified",
                },
                "tv": {
                    "fixtureSlug": "old-show",
                    "knownPositiveFixtures": ["old-show"],
                    "state": "certified",
                },
            }
        }
    }
}
certification = {
    "authority": "exact-bundle-playable-lane-certification-v1",
    "generatedAt": "2026-09-18T00:00:00+00:00",
    "manifestVersion": "5.21.51",
    "providers": [
        {
            "providerId": "demo",
            "filename": "providers/demo.js",
            "bundleSha256": "abc",
            "requiredTypes": ["movie", "tv"],
            "certifiedTypes": ["movie"],
            "missingTypes": ["tv"],
            "certified": False,
            "lanes": {
                "movie": {
                    "state": "certified",
                    "fixtureSlug": "new-film",
                    "fixture": {"slug": "new-film", "tmdbId": "1", "mediaType": "movie"},
                },
                "tv": {"state": "uncertified", "fixtureSlug": None},
            },
        }
    ],
}
merged = memory.merge(certification, registry)
demo = merged["providers"]["demo"]
assert demo["certified"] is False
assert demo["lanes"]["movie"]["fixtureSlug"] == "new-film"
assert demo["lanes"]["movie"]["knownPositiveFixtures"][:3] == ["new-film", "old-film", "older-film"]
assert demo["lanes"]["movie"]["bundleSha256"] == "abc"
# Failure never erases the old witness; it marks it stale so Learning can replace it.
assert demo["lanes"]["tv"]["fixtureSlug"] == "old-show"
assert demo["lanes"]["tv"]["state"] == "stale-or-unverified"
assert demo["lanes"]["tv"]["lastFailedBundleSha256"] == "abc"


targeted_registry = {
    "providers": {
        "demo": registry["providers"]["demo"],
        "unseen": {
            "certified": True,
            "registryState": "certified",
            "lanes": {
                "movie": {
                    "state": "certified",
                    "fixtureSlug": "stable-film",
                    "knownPositiveFixtures": ["stable-film"],
                }
            },
        },
    }
}
targeted = dict(certification)
targeted["fullManifestCensus"] = False
targeted_merged = memory.merge(targeted, targeted_registry)
assert targeted_merged["providers"]["unseen"]["certified"] is True
assert targeted_merged["providers"]["unseen"]["registryState"] == "certified"
assert targeted_merged["providers"]["unseen"]["lanes"]["movie"]["state"] == "certified"

full = dict(certification)
full["fullManifestCensus"] = True
full_merged = memory.merge(full, targeted_registry)
assert full_merged["providers"]["unseen"]["certified"] is False
assert full_merged["providers"]["unseen"]["registryState"] == "not-observed-in-latest-full-manifest-certification"

print("provider positive fixture memory tests passed")
