#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

audit_path = ROOT / "scripts" / "audit_provider_quick_yield.py"
spec = importlib.util.spec_from_file_location("audit_provider_quick_yield", audit_path)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

from rotating_corpus import health_fixtures, provider_census_candidates, regression_fixtures, global_fixtures

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    status_path = root / "status.json"
    manifest_path = root / "manifest.json"
    rows = [
        {"provider": "green", "status": "FULL OK"},
        {"provider": "partial", "status": "PARTIAL OK"},
        {"provider": "miss", "status": "NO PROOF"},
        {"provider": "broken", "status": "PROVIDER JS BROKEN"},
        {"provider": "reg", "status": "REGRESSION PROVIDER"},
    ]
    status_path.write_text(json.dumps({"providers": rows}), encoding="utf-8")
    manifest_path.write_text(json.dumps({
        "scrapers": [{"id": row["provider"]} for row in rows]
    }), encoding="utf-8")

    # Isolate the fixture from the live repository manifest. The production
    # helper intentionally adds newly-onboarded manifest rows that are missing
    # from a stale status snapshot; this test is about status semantics, not the
    # current repository onboarding delta.
    previous_manifest = audit.MANIFEST
    audit.MANIFEST = manifest_path
    try:
        selected, scope = audit._scope_provider_filter("unresolved", status_path, [])
        assert scope == "unresolved"
        assert selected == {"miss", "broken", "reg"}, selected

        selected, scope = audit._scope_provider_filter("all", status_path, [])
        assert selected is None and scope == "all"

        selected, scope = audit._scope_provider_filter("unresolved", status_path, ["green,miss"])
        assert selected == {"green", "miss"} and scope == "explicit"
    finally:
        audit.MANIFEST = previous_manifest

# The proof search really spans the three durable sources, rather than only the
# 32-row rotating lane used by the old quick census.
assert global_fixtures()
assert regression_fixtures()
assert health_fixtures()
movie_candidates = provider_census_candidates("movie", seed="test", provider="demo")
movie_keys = {str(row.get("slug") or "") for row in movie_candidates}
assert any(key.startswith("health-movie-") for key in movie_keys), list(movie_keys)[:10]
assert len(movie_candidates) >= len([row for row in global_fixtures() if row.get("lane") == "movie"])

# Retained proof is first; retained chain hits are replayed immediately after it;
# remembered clean misses are not selected again while other corpus works remain.
history = {
    "providers": {
        "movieshunt": {
            "lanes": {
                "movie": {
                    "proofs": [{"fixture": {
                        "slug": "known-proof",
                        "tmdbId": "1",
                        "mediaType": "movie",
                        "title": "Known Proof",
                    }}],
                    "chainHits": [{"fixture": {
                        "slug": "known-chain",
                        "tmdbId": "9",
                        "mediaType": "movie",
                        "title": "Known Chain",
                    }}],
                    "misses": [{"fixture": {
                        "slug": "known-miss",
                        "tmdbId": "2",
                        "mediaType": "movie",
                        "title": "Known Miss",
                    }}],
                }
            }
        }
    }
}
fixtures = audit._adaptive_fixtures(
    "movieshunt",
    "movie",
    {"slug": "representative", "tmdbId": "3", "mediaType": "movie", "title": "Representative"},
    history=history,
)
assert fixtures[0]["slug"] == "known-proof", fixtures
assert fixtures[1]["slug"] == "known-chain", fixtures
assert "known-miss" not in [row.get("slug") for row in fixtures], fixtures

# The targeted recovery workflow must preserve the same retained-proof / miss
# memory as the full census. Otherwise a repair run silently falls back to
# generic fixtures and re-discovers catalogue matches that are already known.
targeted = (ROOT / ".github/workflows/temp-targeted-regression-recovery.yml").read_text(encoding="utf-8")
assert 'tests/allanime_site_runtime_contract_test.py' in targeted
assert 'tests/provider_census_scope_history_test.py' in targeted
assert '--history automation/provider-census-proof-history.json' in targeted
targeted_runner = (ROOT / "scripts/run_provider_targeted_recovery.py").read_text(encoding="utf-8")
assert 'history=load(args.history,{})' in targeted_runner
assert 'audit.build_tasks(selected_targets,history=history)' in targeted_runner

print("provider census scope/history contract passed")
