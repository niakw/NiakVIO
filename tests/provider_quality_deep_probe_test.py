#!/usr/bin/env python3
"""No synthetic positive may be mistaken for a repaired real provider."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path("scripts").resolve()))
from summarize_provider_quality_probe import summarize

sha = "a"*40
provider = "castle"
def report(fixtures):
    return {"mode": "deep", "results": [{
        "canonical_id": provider, "sha256": "b"*64, "status": "healthy", "tests": fixtures
    }]}
original = {
    "fixture": {"category": "movie", "title": "PRIVATE TITLE", "tmdbId": "PRIVATE-ID"},
    "status": "healthy", "announced_quality_heights": [720,1080,2160],
    "returned_quality_heights": [720,2160], "verified_max_height": 720,
    "announced_variant_candidates": 6, "explored_player_requests": 4,
    "streams_returned": 2, "streams_probed": 2,
    "streams_playable": 1, "identity_verified_streams": 0,
    "network_observations": [{"url": "https://secret.invalid/PRIVATE?token=secret"}],
}
value = summarize(report([original]), provider=provider, sha=sha)
assert value["observedQualityGap"] is False
assert value["fixtures"][0]["declared4kButUnverified"] is True
assert value["identityVerified4k"] is False
assert value["fixtures"][0]["fanoutCandidateLoss"] is True
assert "PRIVATE" not in json.dumps(value)
assert "https://" not in json.dumps(value)
good = {**original, "verified_max_height": 2160, "streams_playable": 2,
        "identity_verified_streams": 1}
out = summarize(report([good]), provider=provider, sha=sha)
assert out["identityVerified4k"] is True
assert out["publicationAuthority"] is False and out["mutationsAllowed"] is False
no_return = {**original, "streams_returned": 0, "returned_quality_heights": [],
             "verified_max_height": 0, "streams_playable": 0}
gap = summarize(report([no_return]), provider=provider, sha=sha)
assert gap["observedQualityGap"] is True
assert gap["identityVerified4k"] is False
for bad in (
    ({**report([original]), "mode": "availability"}, "Deep"),
    (report([]), "Deep fixture"),
    (report([{**original, "fixture": {"category": "series"}}]), "category"),
):
    try: summarize(bad[0], provider=provider, sha=sha)
    except ValueError as e: assert bad[1] in str(e), e
    else: raise AssertionError("bad proof accepted")
try: summarize(report([original]), provider="other", sha=sha)
except ValueError as e: assert "provider identity" in str(e)
else: raise AssertionError("cross-provider evidence accepted")

wf = Path(".github/workflows/provider-quality-deep-diagnostic.yml").read_text(encoding="utf-8")
for token in (
    "TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}",
    "TMDB_ACCESS_TOKEN: ${{ secrets.TMDB_ACCESS_TOKEN }}",
    "max_streams_to_probe",
    "probe_streams_adaptively",
    "probe_all_selected_quality_variants",
    "inspect_quality",
    "NUVIO_HEALTH_PROVIDER_FILTER",
    "node scripts/health_check.mjs --deep",
    "summarize_provider_quality_probe.py",
    "tests/provider_quality_deep_probe_test.py",
    "provider: castle",
    "provider: uhdmovies",
    "provider: allanime",
    "provider: hindmoviez",
    "provider: streamzo",
    "contents: read",
):
    assert token in wf, token
assert "contents: write" not in wf
assert "git push" not in wf
assert "NIAKVIO_ALLOW_PAID_API" not in wf
upload = wf.split("      - name: Upload sanitized quality-only proof",1)[1]
assert "quality-summary.json" in upload
assert "health-results.json" not in upload
print("PROVIDER_QUALITY_DEEP_TEST_OK evidence-only multi-family")
