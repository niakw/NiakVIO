#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reconstruct_provider_v3_sequential_live import (  # noqa: E402
    credit_verified_playable_chains,
    is_qualified,
)

# Regression from Castle: a TV fixture can be genuinely playable while its
# successful provider URLs are opaque/generic and therefore unsafe to promote as
# semantic route templates. The playable chain must still prove the requested
# semantic type without inventing a reusable URL template.
evaluation = {
    "requiredTypes": ["movie", "tv"],
    "validatedTypes": ["movie"],
    "missingTypes": ["tv"],
    "declaredTypeCoverageRatio": 0.5,
    "effectiveCoverageRatio": 0.5,
    "typeComplete": False,
    "directOutputOnly": False,
    "providerSuccessHttp": True,
    "liveValidatedRouteCount": 1,
    "declaredTypeRouteEvidence": {
        "movie": [{"route": "/movie/{id}", "source": "declared-type-template-live-match"}],
        "tv": [],
    },
}
tv_task = {
    "semantic_type": "tv",
    "fixture_slug": "breaking-bad-s01e01",
    "fixture": {
        "tmdbId": "1396",
        "mediaType": "tv",
        "title": "Breaking Bad",
        "season": 1,
        "episode": 1,
    },
    "status": "playable_verified",
    "fetches": [{
        "url": "https://castle.test/player/opaque-525",
        "final_url": "https://castle.test/player/opaque-525",
        "method": "GET",
        "status": 200,
        "content_type": "application/json",
        "header_names": ["accept"],
        "body_kind": "none",
        "body_fields": [],
    }],
}
credited = credit_verified_playable_chains(evaluation, [tv_task])
assert credited["validatedTypes"] == ["movie", "tv"], credited
assert credited["missingTypes"] == [], credited
assert credited["declaredTypeCoverageRatio"] == 1.0, credited
assert credited["typeComplete"] is True, credited
assert credited["playableChainValidatedTypes"] == ["tv"], credited
assert credited["declaredTypeRouteEvidence"]["tv"][0]["route"] == "playable-chain", credited
assert credited["declaredTypeRouteEvidence"]["tv"][0]["reusableRoutePromoted"] is False, credited
assert is_qualified(credited) is True, credited

# Search/status success alone must still not invent type proof.
search_only = {
    **tv_task,
    "status": "no_streams",
    "fetches": [{
        **tv_task["fetches"][0],
        "url": "https://castle.test/search?q=Breaking%20Bad",
        "final_url": "https://castle.test/search?q=Breaking%20Bad",
    }],
}
not_credited = credit_verified_playable_chains({
    **evaluation,
    "validatedTypes": ["movie"],
    "missingTypes": ["tv"],
    "declaredTypeCoverageRatio": 0.5,
    "effectiveCoverageRatio": 0.5,
    "typeComplete": False,
    "declaredTypeRouteEvidence": {"movie": [], "tv": []},
}, [search_only])
assert not_credited["validatedTypes"] == ["movie"], not_credited
assert not_credited["missingTypes"] == ["tv"], not_credited
assert is_qualified(not_credited) is False, not_credited

# Regression from Cineby: wrong_content is retained as a quality diagnostic but
# the final gate no longer globally rejects an otherwise independently proven
# movie+tv bundle. A wrong-content-only semantic type is still a blocker.
source = (ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py").read_text(encoding="utf-8")
assert "wrong_only_types = (wrong_types & required_types) - playable_types" in source
assert "verified = is_qualified(evaluation) and not wrong_only_types and not runtime_error" in source
assert '"wrongContentOnlyTypes": sorted(wrong_only_types)' in source
assert "wrong = any(" not in source

print(
    "PROVIDER_V3_PLAYABLE_CHAIN_GATE_OK castle_tv=credited_without_route_invention "
    "search_only=not_credited cineby_wrong_content=per_type_not_global"
)
