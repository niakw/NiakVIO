#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "merge_waf_latest_evidence.py"
spec = importlib.util.spec_from_file_location("merge_waf_latest_evidence", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

previous = {
    "schemaVersion": 1,
    "rows": [
        {
            "provider": "demo",
            "lane": "movie",
            "publicUrl": "https://demo.invalid/",
            "outcome": "browser_challenge_persisted",
            "residentialExitNodeProfile": {
                "profile": "tailscale-residential-exit",
                "outcome": "browser_content_reached",
            },
        },
        {
            "provider": "untouched",
            "lane": "movie",
            "publicUrl": "https://untouched.invalid/",
            "outcome": "browser_content_reached",
        },
    ],
    "residentialExitNodeEvidence": {
        "available": True,
        "profile": "tailscale-residential-exit",
        "matchedProviderLanes": 1,
    },
    "residentialProviderReplay": {
        "available": True,
        "rows": [
            {
                "provider": "demo",
                "lane": "movie",
                "raw": 1,
                "playable": 1,
                "verified": 1,
                "contradictions": 0,
            }
        ],
    },
}

current_without_tailscale = {
    "schemaVersion": 1,
    "rows": [
        {
            "provider": "demo",
            "lane": "movie",
            "publicUrl": "https://demo.invalid/",
            "outcome": "browser_content_reached",
        }
    ],
    "residentialExitNodeEvidence": {
        "available": False,
        "reason": "tailscale-unavailable",
    },
}

merged = module.merge(previous, current_without_tailscale)
demo = next(row for row in merged["rows"] if row["provider"] == "demo")
assert demo["outcome"] == "browser_content_reached"
assert demo["residentialExitNodeProfile"]["outcome"] == "browser_content_reached"
assert any(row["provider"] == "untouched" for row in merged["rows"])
assert merged["residentialExitNodeEvidence"]["available"] is True
assert merged["residentialExitNodeLastAttempt"]["available"] is False
assert merged["residentialProviderReplay"]["verifiedProviders"] == ["demo"]
assert merged["residentialProviderReplay"]["lastAttempt"]["available"] is False

current_with_tailscale = {
    "schemaVersion": 1,
    "rows": [
        {
            "provider": "demo",
            "lane": "movie",
            "publicUrl": "https://demo.invalid/",
            "outcome": "browser_content_reached",
            "residentialExitNodeProfile": {
                "profile": "tailscale-residential-exit",
                "outcome": "browser_challenge_persisted",
            },
        }
    ],
    "residentialExitNodeEvidence": {
        "available": True,
        "profile": "tailscale-residential-exit",
        "matchedProviderLanes": 1,
    },
    "residentialProviderReplay": {
        "available": True,
        "rows": [
            {
                "provider": "demo",
                "lane": "movie",
                "raw": 0,
                "playable": 0,
                "verified": 0,
                "contradictions": 0,
            }
        ],
    },
}
merged2 = module.merge(merged, current_with_tailscale)
demo2 = next(row for row in merged2["rows"] if row["provider"] == "demo")
assert demo2["residentialExitNodeProfile"]["outcome"] == "browser_challenge_persisted"
assert merged2["residentialProviderReplay"]["verifiedProviders"] == []
assert merged2["residentialProviderReplay"]["lastAttempt"]["available"] is True

new_run = {
    "schemaVersion": 1,
    "freshRunReceipt": {"sourceNiakvioSha": "c" * 40, "runId": "44423214248"},
    "lastRefreshProviderFilter": ["target"],
    "rows": [
        {"provider": "target", "lane": "movie", "outcome": "browser_content_reached"},
        {"provider": "keep", "lane": "movie", "outcome": "browser_content_reached"},
    ],
    "residentialProviderReplay": {
        "available": True,
        "rows": [
            {"provider": "target", "lane": "movie", "verified": 0, "raw": 0, "playable": 0},
            {"provider": "keep", "lane": "movie", "verified": 1, "raw": 1, "playable": 1},
        ],
        "lastAttempt": {
            "available": True, "providerCount": 1,
            "refreshedProviders": ["target"], "replayedProviders": ["target"],
            "verifiedProviders": [],
            "sourceNiakvioSha": "c" * 40, "runId": "44423214248",
            "proofAuthority": False,
        },
    },
}
scoped = module.merge({}, new_run)
assert scoped["residentialProviderReplay"]["verifiedProviders"] == ["keep"]
assert scoped["residentialProviderReplay"]["lastAttempt"]["verifiedProviders"] == []
# A freshRunReceipt alone is not provider replay proof. Without a matching
# per-provider residentialReplayReceipt, the targeted row remains historical
# data only and must not be promoted into the fresh lastAttempt.
assert scoped["residentialProviderReplay"]["lastAttempt"]["replayedProviders"] == []
assert scoped["residentialProviderReplay"]["lastAttempt"]["providerCount"] == 0
assert scoped["residentialProviderReplay"]["lastAttempt"]["available"] is False
assert scoped["lastRefreshProviderFilter"] == ["target"], scoped
assert scoped["currentRefreshProviderCount"] == 1, scoped
assert scoped["currentRefreshRowCount"] == 1, scoped
assert scoped["currentRefreshCounts"] == {"browser_content_reached": 1}, scoped
assert scoped["historicalRetainedRowCount"] == 1, scoped
assert scoped["historicalRetainedCounts"] == {"browser_content_reached": 1}, scoped
mismatched = module.merge({}, {
    **new_run,
    "freshRunReceipt": {"sourceNiakvioSha": "d" * 40, "runId": "44423214249"},
})
assert mismatched["residentialProviderReplay"]["lastAttempt"]["replayedProviders"] == []
assert mismatched["residentialProviderReplay"]["lastAttempt"]["verifiedProviders"] == []
print("WAF latest scoped replay freshness contract passed")

# A source-pinned sharded census may finish after a newer targeted WAF run.
# Completion order is not evidence authority: unstamped/older current rows must
# not replace newer exact-byte transport or residential replay receipts.
stamped_previous = {
    "schemaVersion": 1,
    "freshRunReceipt": {
        "sourceNiakvioSha": "a" * 40,
        "runId": "200",
        "providerCount": 1,
        "proofAuthority": False,
        "publicationAuthority": False,
    },
    "rows": [{
        "provider": "race",
        "lane": "anime",
        "publicUrl": "https://race.invalid/",
        "outcome": "browser_challenge_persisted",
        "residentialExitNodeProfile": {
            "profile": "residential-exit",
            "outcome": "browser_content_reached",
        },
        "transportReceipt": {
            "sourceNiakvioSha": "a" * 40,
            "providerBundleSha256": "b" * 64,
            "runId": "200",
            "proofAuthority": False,
            "publicationAuthority": False,
        },
        "residentialReceipt": {
            "sourceNiakvioSha": "a" * 40,
            "providerBundleSha256": "b" * 64,
            "runId": "200",
            "proofAuthority": False,
            "publicationAuthority": False,
        },
    }],
    "residentialProviderReplay": {
        "available": True,
        "rows": [{
            "provider": "race",
            "lane": "anime",
            "status": "no_streams",
            "raw": 0,
            "playable": 0,
            "verified": 0,
            "contradictions": 0,
            "identitySafe": True,
            "residentialReplayReceipt": {
                "sourceNiakvioSha": "a" * 40,
                "providerBundleSha256": "b" * 64,
                "runId": "200",
                "proofAuthority": False,
                "publicationAuthority": False,
            },
        }],
    },
}
stale_shard = {
    "schemaVersion": 1,
    # This old receipt was merely carried by the source checkout.
    "freshRunReceipt": {
        "sourceNiakvioSha": "c" * 40,
        "runId": "100",
        "providerCount": 1,
        "proofAuthority": False,
        "publicationAuthority": False,
    },
    "lastRefreshProviderFilter": ["race"],
    "rows": [{
        "provider": "race",
        "lane": "anime",
        "publicUrl": "https://race.invalid/",
        "outcome": "browser_challenge_observed",
    }],
    "residentialProviderReplay": {
        "available": True,
        "rows": [{
            "provider": "race",
            "lane": "anime",
            "status": "no_streams",
            "raw": 0,
            "playable": 0,
            "verified": 0,
            "contradictions": 0,
            "identitySafe": True,
        }],
    },
}
race = module.merge(stamped_previous, stale_shard)
race_row = next(row for row in race["rows"] if row["provider"] == "race")
race_replay = next(
    row for row in race["residentialProviderReplay"]["rows"]
    if row["provider"] == "race"
)
assert race_row["outcome"] == "browser_challenge_persisted", race_row
assert race_row["transportReceipt"]["runId"] == "200", race_row
assert race_row["residentialExitNodeProfile"]["outcome"] == "browser_content_reached", race_row
assert race_replay["residentialReplayReceipt"]["runId"] == "200", race_replay
assert race["freshRunReceipt"]["runId"] == "200", race
assert race["residentialProviderReplay"]["lastAttempt"]["runId"] == "200", race
assert race["staleCurrentRowsSuppressedProviders"] == ["race"], race

newer_current = {
    **stale_shard,
    "freshRunReceipt": {
        "sourceNiakvioSha": "d" * 40,
        "runId": "201",
        "providerCount": 1,
        "proofAuthority": False,
        "publicationAuthority": False,
    },
    "rows": [{
        "provider": "race",
        "lane": "anime",
        "publicUrl": "https://race.invalid/",
        "outcome": "browser_content_reached",
        "transportReceipt": {
            "sourceNiakvioSha": "d" * 40,
            "providerBundleSha256": "b" * 64,
            "runId": "201",
            "proofAuthority": False,
            "publicationAuthority": False,
        },
    }],
    "residentialProviderReplay": {
        "available": True,
        "rows": [{
            "provider": "race",
            "lane": "anime",
            "status": "playable_unverified",
            "raw": 1,
            "playable": 1,
            "verified": 0,
            "contradictions": 0,
            "identitySafe": True,
            "residentialReplayReceipt": {
                "sourceNiakvioSha": "d" * 40,
                "providerBundleSha256": "b" * 64,
                "runId": "201",
                "proofAuthority": False,
                "publicationAuthority": False,
            },
        }],
    },
}
race2 = module.merge(stamped_previous, newer_current)
race2_row = next(row for row in race2["rows"] if row["provider"] == "race")
assert race2_row["outcome"] == "browser_content_reached", race2_row
assert race2_row["transportReceipt"]["runId"] == "201", race2_row
assert race2["freshRunReceipt"]["runId"] == "201", race2
assert race2["residentialProviderReplay"]["lastAttempt"]["runId"] == "201", race2
assert race2["staleCurrentRowsSuppressedProviders"] == [], race2
print("WAF latest provenance-monotone race contract passed")

