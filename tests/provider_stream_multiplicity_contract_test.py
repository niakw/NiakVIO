#!/usr/bin/env python3
"""Generic stream multiplicity contract for NiakVIO runtime/Core/Labs."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

base = (ROOT / "scripts/provider_base_store.py").read_text(encoding="utf-8")
apply_source = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
sanitizer = (ROOT / "scripts/provider_patches/stream_output_sanitizer.py").read_text(encoding="utf-8")
ios = (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")
tv = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text(encoding="utf-8")
mobile = (ROOT / "scripts/run_native_corpus_mobile_suite.sh").read_text(encoding="utf-8")
desktop = (ROOT / "scripts/run_native_corpus_desktop_suite.sh").read_text(encoding="utf-8")
config = json.loads((ROOT / ".github/triggers/nuvio-client-lab.json").read_text(encoding="utf-8"))

# Runtime: discover/aggregate reader, source and explicit quality variants before
# the final bounded stream cap. Historical 8/12/16 windows are forbidden here.
assert "NIAKVIO_PROVIDER_MULTI_VARIANT_FANOUT_V26" in base
assert "NIAKVIO_PROVIDER_EXPLICIT_MEDIA_VARIANTS_V26" in base
assert "const seedCap = Math.min(32" in base
assert "const requestBudget = Math.min(32" in base
assert "streams.length < 40" in base
assert "return _dedupeStreamRows(streams).slice(0, 40);" in base
assert ".slice(0, 24)" in base, "explicit player fanout must cover dense pages"
assert ".slice(0, 16)" in base, "nested/player episode fanout must exceed legacy window"
assert "streams.push(..._spv26ExplicitMediaRows" in base
assert "_spv26JsonMediaRows" in base
assert "if (!direct.length && /iframe|mixed_embed|html_scraper|direct_media/i.test" not in base
assert "const planStreams = [];" in base
assert "if (direct.length) planStreams.push(..._streams(direct, payload.base || stepUrl));" in base
assert "if (episodeHop.length) planStreams.push(...episodeHop);" in base
assert "if (crawledStreams.length) planStreams.push(...crawledStreams);" in base
assert "if (fallbackStreams.length) planStreams.push(...fallbackStreams);" in base
assert "return _streams(direct, payload.base || stepUrl)" not in base
assert "if (episodeHop.length) return episodeHop" not in base
assert "if (streams.length) return streams.slice(0, 40);" not in base
assert "if (explicitCrawled.length) return explicitCrawled" not in base
assert "return resolvedPlanStreams.slice(0, 40);" in base
assert "NIAKVIO_PROVIDER_API_RECIPE_SOURCE_COVERAGE_V27" in base
assert "minStreamsBeforeStop" not in base
assert "if (_dedupeStreamRows(streams).length >= 40) break;" in base
assert "return _dedupeStreamRows(streams).slice(0, 40);" in base
assert "NIAKVIO_PROVIDER_RUNTIME_PLAYER_COVERAGE_V27" in base
runtime_api = base.split("async function _resolveRuntimeApi", 1)[1].split("async function _resolveKnownPlayer", 1)[0]
assert "if (streams.length) break;" not in runtime_api
assert "if (_dedupeStreamRows(streams).length >= 40) break;" in runtime_api
known_player = base.split("async function _resolveKnownPlayer", 1)[1].split("function _htmlVisibleText", 1)[0]
assert "if (runtime.length) return runtime;" not in known_player
assert "if (direct.length) return _streams" not in known_player
assert "streams.push(...runtime)" in known_player
assert "streams.push(..._streams(direct, responseUrl))" in known_player

assert "NIAKVIO_PROVIDER_PLAN_STREAM_COVERAGE_V28" in base
search_plan = base.split("async function _resolveSearchRequestPlan", 1)[1].split("async function _resolveExternalIdentityPlan", 1)[0]
assert "if (Array.isArray(detailStreams) && detailStreams.length) return detailStreams" not in search_plan
assert "if (crawled.length) return crawled" not in search_plan
assert "planStreams.push(...detailStreams)" in search_plan
assert "planStreams.push(...crawled)" in search_plan
assert "return _dedupeStreamRows(planStreams).slice(0, 40);" in search_plan

assert "NIAKVIO_PROVIDER_EXTERNAL_IDENTITY_COVERAGE_V28" in base
external_plan = base.split("async function _resolveExternalIdentityPlan", 1)[1].split("async function getStreams", 1)[0]
assert "return _streams(selected" not in external_plan
assert "if (crawled.length) return crawled" not in external_plan
assert "planStreams.push(..._streams(selected" in external_plan
assert "planStreams.push(...crawled)" in external_plan
assert "return _dedupeStreamRows(planStreams).slice(0, 40);" in external_plan

family_path = base.split('if (family && family !== "unknown") {', 1)[1].split("const primary = await getStreams", 1)[0]
assert "if (streams.length) return streams;" not in family_path
assert "familyStreams.push(...streams)" in family_path
assert "return _dedupeStreamRows(familyStreams).slice(0, 40);" in family_path

assert "NIAKVIO_PROVIDER_DLE_PLAYER_COVERAGE_V29" in base
play_episode = base.split("async function _spv4PlayEpisode", 1)[1].split("function _spv4SagaTargets", 1)[0]
assert "if (direct.length) return direct;" not in play_episode
assert "if (nested.length) return nested;" not in play_episode
assert "streams.push(...direct)" in play_episode
assert "streams.push(...nested)" in play_episode

assert "NIAKVIO_PROVIDER_STREMIO_COVERAGE_V29" in base
stremio = base.split("async function _spv5Stremio", 1)[1].split("async function _spv5DleFilmApi", 1)[0]
assert "if (urls.length) return _streams" not in stremio
assert "streams.push(..._streams(urls" in stremio
assert "return _dedupeStreamRows(streams).slice(0, 40);" in stremio

assert "NIAKVIO_PROVIDER_DLE_FILM_API_COVERAGE_V29" in base
film_api = base.split("async function _spv5DleFilmApi", 1)[1].split("async function _spv4ResolveDetail", 1)[0]
assert "if (direct.length) return direct;" not in film_api
assert "if (nested.length) return nested;" not in film_api
assert "streams.push(...direct)" in film_api
assert "streams.push(...nested)" in film_api

assert "NIAKVIO_PROVIDER_DETAIL_STREAM_COVERAGE_V29" in base
detail = base.split("async function _spv4ResolveDetail", 1)[1].split("function _spv7ProviderSiteBases", 1)[0]
assert "const direct = _spv4DirectStreams(urls, base);" in detail
assert "if (direct.length) return direct;" not in detail
assert "streams.push(...direct)" in detail
assert "streams.push(...nested)" in detail
assert "return _dedupeStreamRows(streams).slice(0, 40);" in detail

# Core: validation capacity must match the runtime output contract. Dedupe is by
# exact playback identity (URL + request headers), not bare URL.
assert 'min(int(options.get("max_probes", 6)), 40)' in sanitizer
assert "NUVIO_STREAM_PLAYBACK_IDENTITY_V11" in sanitizer
assert "function playbackKey(stream,url)" in sanitizer
assert "var batchSize=4" in sanitizer
assert 'min(int(sanitizer_options.get("max_probes") or 40), 40)' in apply_source
assert 'min(int(sanitizer_options.get("max_probes") or 8), 8)' not in apply_source
assert "PROVIDER_STREAM_OUTPUT_CAP = 40" in apply_source
assert "_normalize_provider_stream_output_options" in apply_source
assert "_normalize_provider_owned_stream_output_cap" in apply_source
assert '"type": "provider_stream_output_cap"' in apply_source

# Labs: full acceptance actually observes the multiplicity instead of only the
# first 2/3 results, and S00 is a mandatory additive regression.
assert config["probe_all_streams"] is True
assert config["all_streams_safety_cap"] == 40
assert config["max_streams_per_runtime"] == 40
assert config["stream_sampling"] == "spread"
acceptance = config["native_reader_acceptance"]
assert acceptance["mandatory_regression_fixtures"] == ["spartacus-s00e01"]
special = next(row for row in config["fixtures"] if row.get("slug") == "spartacus-s00e01")
assert special["fixture"]["season"] == 0 and special["fixture"]["episode"] == 1
assert special["fixture"]["tmdbId"] == "46296"

for label, source in (("tv", tv), ("mobile", mobile), ("desktop", desktop)):
    assert "native_regression_fixtures.py" in source, label
    assert 'NIAKVIO_REGRESSION_STREAM_SCOPE:-all' in source, label

assert "mandatory_fixture_rows" in ios
assert "mandatoryRegression: Boolean = false" in ios
assert "fixture.mandatoryRegression || key !in terminalProviders" in ios
assert "rows.take(40)" in ios
assert "rows.firstOrNull()?.let" not in ios

print("provider stream multiplicity contract passed")
