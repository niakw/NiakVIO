#!/usr/bin/env python3
import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_provider_quick_yield.py"
spec = importlib.util.spec_from_file_location("quick_yield", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

hierarchical = {
    "fetches": [
        {
            "url": "https://coflix.example/ajax/episode/player",
            "response_url": "https://coflix.example/ajax/episode/player",
            "declared_player_candidate_count": 2,
            "declared_url_player_candidate_count": 2,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": ["one.test", "two.test"],
            "declared_quality_heights": [480],
        },
        {
            "url": "https://one.test/player/1",
            "response_url": "https://one.test/player/1",
            "declared_player_candidate_count": 10,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 10,
            "declared_player_hosts": [],
            "declared_quality_heights": [720, 1080],
        },
        {
            "url": "https://two.test/player/2",
            "response_url": "https://two.test/player/2",
            "declared_player_candidate_count": 9,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 9,
            "declared_player_hosts": [],
            "declared_quality_heights": [1080],
        },
    ]
}
summary = mod._variant_fanout_summary(hierarchical, 8)
assert summary["announced_player_candidates"] == 2, summary
assert summary["announced_variant_candidates"] == 19, summary
assert summary["explored_player_requests"] == 2, summary
assert summary["explored_player_hosts"] == ["one.test", "two.test"], summary
assert summary["announced_quality_heights"] == [480, 720, 1080], summary
assert summary["variant_fanout_state"] == "returned-subset", summary

index_only = {
    "fetches": [{
        "url": "https://coflix.example/title",
        "response_url": "https://coflix.example/title",
        "declared_player_candidate_count": 19,
        "declared_url_player_candidate_count": 0,
        "declared_indexed_player_candidate_count": 19,
        "declared_player_hosts": [],
        "declared_quality_heights": [480, 720, 1080],
    }]
}
summary = mod._variant_fanout_summary(index_only, 8)
assert summary["announced_variant_candidates"] == 19, summary
assert summary["explored_player_requests"] == 0, summary
assert summary["variant_fanout_state"] == "returned-subset", summary

domain_drift = {
    "model": {
        "official_site": "https://coflix.ac",
        "official_hub": "https://coflix.domains/",
    },
    "fetches": [
        {
            "url": "https://coflix.wiki/ajax/search/suggest?keyword=fixture",
            "response_url": "https://coflix.wiki/ajax/search/suggest?keyword=fixture",
            "declared_player_candidate_count": 0,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": [],
            "declared_quality_heights": [],
        },
        {
            "url": "https://coflix.wiki/film/fixture/",
            "response_url": "https://coflix.wiki/film/fixture/",
            "declared_player_candidate_count": 19,
            "declared_url_player_candidate_count": 19,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": ["coflix.wiki"],
            "declared_quality_heights": [1080],
        },
        {
            "url": "https://coflix.wiki/ajax/episode/player?episode_id=1",
            "response_url": "https://coflix.wiki/ajax/episode/player?episode_id=1",
            "declared_player_candidate_count": 2,
            "declared_url_player_candidate_count": 2,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": ["coflix.wiki", "one.test", "two.test"],
            "declared_quality_heights": [],
        },
        {
            "url": "https://one.test/player/1",
            "response_url": "https://one.test/player/1",
            "declared_player_candidate_count": 10,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 10,
            "declared_player_hosts": [],
            "declared_quality_heights": [720, 1080],
        },
        {
            "url": "https://two.test/player/2",
            "response_url": "https://two.test/player/2",
            "declared_player_candidate_count": 9,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 9,
            "declared_player_hosts": [],
            "declared_quality_heights": [1080],
        },
    ],
}
summary = mod._variant_fanout_summary(domain_drift, 2)
assert summary["announced_player_candidates"] == 2, summary
assert summary["announced_variant_candidates"] == 19, summary
assert summary["announced_player_hosts"] == ["one.test", "two.test"], summary
assert summary["explored_player_requests"] == 2, summary
assert summary["variant_fanout_state"] == "returned-subset", summary

# HTML pages can contain many unrelated absolute URLs near player markup.
# Only explicit controls/iframes and actually traversed off-origin hosts are
# reader/server evidence; generic page URLs must not inflate completeness debt.
html_noise = {
    "model": {"official_site": "https://papa.test"},
    "fetches": [
        {
            "url": "https://papa.test/movie/fixture",
            "response_url": "https://papa.test/movie/fixture",
            "declared_player_candidate_count": 23,
            "declared_url_player_candidate_count": 23,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": [
                "image.tmdb.org", "www.w3.org", "papa.info",
                "one.test", "two.test",
            ],
            "declared_quality_heights": [720, 1080],
            "response_shape": {"kind": "html", "iframes": 2, "videos": 2, "sources": 2},
        },
        {
            "url": "https://one.test/embed/1",
            "response_url": "https://one.test/embed/1",
            "declared_player_candidate_count": 7,
            "declared_url_player_candidate_count": 7,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": ["cdn-one.test"],
            "declared_quality_heights": [720, 1080],
            "response_shape": {"kind": "html", "iframes": 0},
        },
        {
            "url": "https://two.test/embed/2",
            "response_url": "https://two.test/embed/2",
            "declared_player_candidate_count": 5,
            "declared_url_player_candidate_count": 5,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": ["cdn-two.test"],
            "declared_quality_heights": [1080],
            "response_shape": {"kind": "html", "iframes": 0},
        },
    ],
}
summary = mod._variant_fanout_summary(html_noise, 2)
assert summary["announced_player_candidates"] == 2, summary
assert summary["announced_variant_candidates"] == 2, summary
assert summary["announced_player_hosts"] == ["one.test", "two.test"], summary
assert summary["explored_player_requests"] == 2, summary
assert summary["variant_fanout_state"] == "fanout-observed", summary

# Structured JSON streams remain authoritative even when many variants share
# only a small number of CDN hosts.
json_variants = {
    "model": {"official_site": "https://api.example.test"},
    "fetches": [
        {
            "url": "https://api.example.test/stream/series/id.json",
            "response_url": "https://api.example.test/stream/series/id.json",
            "declared_player_candidate_count": 17,
            "declared_url_player_candidate_count": 17,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": ["cdn-a.test", "cdn-b.test"],
            "declared_quality_heights": [480, 720, 1080],
            "response_shape": {"kind": "json", "top": "object", "keys": ["streams"]},
        },
        {
            "url": "https://cdn-a.test/file/1.mkv",
            "response_url": "https://cdn-a.test/file/1.mkv",
            "declared_player_candidate_count": 0,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": [],
            "declared_quality_heights": [],
        },
        {
            "url": "https://cdn-b.test/file/2.mkv",
            "response_url": "https://cdn-b.test/file/2.mkv",
            "declared_player_candidate_count": 0,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": [],
            "declared_quality_heights": [],
        },
    ],
}
summary = mod._variant_fanout_summary(json_variants, 1)
assert summary["announced_player_candidates"] == 17, summary
assert summary["announced_variant_candidates"] == 17, summary
assert summary["announced_player_hosts"] == ["cdn-a.test", "cdn-b.test"], summary
assert summary["explored_player_requests"] == 2, summary
assert summary["variant_fanout_state"] == "explored-not-resolved", summary

# Execute the real run_single integration path with a synthetic probe result.
# This catches stale/undefined fan-out locals that helper-only tests cannot see.
original_run = mod.subprocess.run
try:
    mod.subprocess.run = lambda *args, **kwargs: SimpleNamespace(
        stdout='{"playable_stream_count":1,"raw_stream_count":1,"content_verified_count":1,"identity_verified_count":1,"identity_contradiction_count":0,"runtime_error":null,"duration_ms":1,"streams":[],"debug":{"fetches":[]}}\n',
        stderr="",
        returncode=0,
    )
    run_single_result = mod.run_single({
        "provider_id": "demo",
        "provider_name": "Demo",
        "semantic_type": "movie",
        "filename": "providers/demo.js",
        "fixture": {"title": "Fixture", "mediaType": "movie", "tmdbId": "1"},
    })
finally:
    mod.subprocess.run = original_run
assert run_single_result["streams_returned"] == 1, run_single_result
assert run_single_result["variant_fanout_state"] == "not-observed", run_single_result

probe_path = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"
syntax = subprocess.run(["node", "--check", str(probe_path)], cwd=ROOT, text=True, capture_output=True, check=False)
assert syntax.returncode == 0, syntax.stdout + syntax.stderr
probe = probe_path.read_text(encoding="utf-8")
assert "extractResponseVariantHints" in probe
assert "declared_player_candidate_count" in probe
assert "declared_player_hosts" in probe
assert "declared_quality_heights" in probe

print("provider quick-yield variant fan-out contract passed")
