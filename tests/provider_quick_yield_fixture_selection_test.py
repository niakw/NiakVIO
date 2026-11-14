#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "audit_provider_quick_yield.py"
spec = importlib.util.spec_from_file_location("audit_provider_quick_yield", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


from current_provider_scope import pending_provider_ids, runtime_visible_provider_count
from generate_language_manifests import france_only_catalog_rows

tasks, provider_count = mod.build_tasks()
pending = pending_provider_ids()
france_only_runtime = {
    str(row.get("id") or "").strip().casefold().replace("_", "-")
    for row in france_only_catalog_rows(root=ROOT)
    if str(row.get("id") or "").strip()
} - pending
expected_current_union = runtime_visible_provider_count() + len(france_only_runtime)
assert provider_count == expected_current_union, (provider_count, expected_current_union)
task_ids = {row.get("provider_id") for row in tasks}
assert not (task_ids & pending)
assert france_only_runtime <= task_ids, sorted(france_only_runtime - task_ids)

# scope=all sharding must partition the same Global + France-only runtime union;
# otherwise France-only providers disappear before build_tasks sees them.
current_union = mod._current_census_provider_ids()
assert france_only_runtime <= current_union
sharded_union = set().union(*(mod._shard_filter(None, 8, index) or set() for index in range(8)))
assert sharded_union == current_union, (
    sorted(current_union - sharded_union),
    sorted(sharded_union - current_union),
)
for provider in current_union:
    memberships = sum(
        provider in (mod._shard_filter(None, 8, index) or set())
        for index in range(8)
    )
    assert memberships == 1, (provider, memberships)


def task(provider: str, semantic: str) -> dict:
    matches = [
        row for row in tasks
        if row.get("provider_id") == provider and row.get("semantic_type") == semantic
    ]
    assert len(matches) == 1, (provider, semantic, len(matches))
    return matches[0]


# Historical anime-movie targeting never manufactures a current movie lane.
for provider in ("anime-sama", "animesama-co", "animevostfr", "french-manga", "anikototv"):
    assert not [
        row for row in tasks
        if row.get("provider_id") == provider and row.get("semantic_type") == "movie"
    ], provider

# Generic/mixed movie providers keep the representative general movie fixture.
for provider in ("castle", "papadustream"):
    row = task(provider, "movie")
    fixture = row["fixture"]
    assert fixture.get("title") == "Interstellar", (provider, fixture)
    assert fixture.get("animeMovie") is not True, (provider, fixture)
    assert row["fixtures"][0] == fixture, (provider, row["fixtures"])
    assert 1 <= len(row["fixtures"]) <= mod.MAX_SAMPLES
    identities = [mod._fixture_identity(value) for value in row["fixtures"]]
    assert len(identities) == len(set(identities)), (provider, identities)

# The anime episodic semantic lane remains independent from the movie transport.
anime = task("anime-sama", "anime")["fixture"]
assert anime.get("title") == "Jujutsu Kaisen"
assert anime.get("mediaType") == "anime"

original = mod.run_single
try:
    calls = []
    def fake(current, *, timeout_seconds=None):
        slug = str(current["fixture"].get("slug") or "")
        calls.append(slug)
        positive = slug == "b"
        return {
            "provider_id": "example", "provider_name": "Example", "semantic_type": "movie",
            "fixture_title": slug,
            "status": "playable_verified" if positive else "no_streams",
            "debug_stage": "provider_returned_streams" if positive else "provider_network_zero_result",
            "raw": 1 if positive else 0, "playable": 1 if positive else 0,
            "verified": 1 if positive else 0, "contradictions": 0, "duration_ms": 1,
        }
    mod.run_single = fake
    result = mod.run({
        "provider_id": "example", "provider_name": "Example", "filename": "unused.js",
        "semantic_type": "movie", "fixture": {"slug": "a"},
        "fixtures": [{"slug": "a"}, {"slug": "b"}, {"slug": "c"}],
    })
    assert calls == ["a", "b"], calls
    assert result["verified"] == 1 and result["sample_count"] == 2, result

    calls.clear()
    def technical(current, *, timeout_seconds=None):
        slug = str(current["fixture"].get("slug") or "")
        calls.append(slug)
        return {
            "provider_id": "example", "provider_name": "Example", "semantic_type": "movie",
            "fixture_title": slug, "status": "no_streams",
            "debug_stage": "provider_network_http_error",
            "raw": 0, "playable": 0, "verified": 0, "contradictions": 0, "duration_ms": 1,
        }
    mod.run_single = technical
    result = mod.run({
        "provider_id": "example", "provider_name": "Example", "filename": "unused.js",
        "semantic_type": "movie", "fixture": {"slug": "a"},
        "fixtures": [{"slug": "a"}, {"slug": "b"}],
    })
    # One title-level HTTP/provider failure is not enough to classify an
    # entire semantic lane. Keep sampling the bounded fixture queue so catalogue
    # misses/transient title failures do not manufacture a provider-wide block.
    assert calls == ["a", "b"], calls
    assert result["sample_count"] == 2
    assert result["debug_stage"] == "provider_network_http_error", result
finally:
    mod.run_single = original

print("provider quick-yield fixture selection passed: current semantics + bounded clean-zero adaptive rotation")
