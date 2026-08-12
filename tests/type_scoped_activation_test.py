#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'health-config.json').read_text(encoding='utf-8'))
source = (ROOT / 'scripts' / 'promote_candidates.py').read_text(encoding='utf-8')

assert config['activation'].get('allow_type_scoped_activation') is True
assert 'def independently_proven_categories(' in source
assert 'minimum_height > 0 and height > 0 and height < minimum_height' in source
assert 'minimum_bandwidth > 0 and bandwidth is not None and bandwidth < minimum_bandwidth' in source
assert 'if require_language and not (audio or subtitle_ok):' in source
assert 'scoped_categories = required_categories & independently_proven' in source
assert '"activation_supported_types": sorted(scoped_categories)' in source
assert 'authoritative_published_types = [' in source
assert 'and not authoritative_published_types' in source
assert 'promoted_entry["supportedTypes"] = activation_supported_types' in source
assert 'tracked_fields = ("filename", "supportedTypes", "supportsExternalPlayer")' in source

# A type cannot be published from metadata alone: the independently-proven set
# explicitly requires a healthy current fixture plus verified media; optional quality/language thresholds apply only when configured.
healthy_idx = source.index('if not isinstance(test, dict) or test.get("status") != "healthy":')
payload_idx = source.index('if int(test.get("payload_verified_streams", 0)) < minimum_payload:')
quality_idx = source.index('if minimum_height > 0 and height > 0 and height < minimum_height')
publish_idx = source.index('promoted_entry["supportedTypes"] = activation_supported_types')
assert healthy_idx < payload_idx < quality_idx < publish_idx

# A catalogue may miss several representative titles before one current payload
# proves the type. Raw title misses must not reduce type-scoped coverage.
import importlib.util
import json
import sys
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("promote_type_scope", ROOT / "scripts" / "promote_candidates.py")
assert spec and spec.loader
promoter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promoter)
activation = json.loads((ROOT / "health-config.json").read_text(encoding="utf-8"))["activation"]
healthy_movie = {
    "fixture": {"category": "movie"},
    "status": "healthy",
    "streams_playable": 1,
    "payload_verified_streams": 1,
    "effective_max_height": 360,
    "max_bandwidth": 300000,
    "accepted_audio_languages": [],
    "accepted_subtitle_languages": [],
    "accepted_subtitles_advertised": 0,
    "accepted_subtitles_reachable": 0,
}
miss = lambda: {"fixture": {"category": "movie"}, "status": "no_streams", "streams_playable": 0, "payload_verified_streams": 0}
item = {
    "health": {
        "status": "healthy",
        "score": 60,
        "tests": [miss(), miss(), miss(), healthy_movie],
        "evidence": {
            "required_fixture_categories": ["movie", "tv", "anime"],
            "healthy_fixture_categories": ["movie"],
            "healthy_fixtures": 1,
            "healthy_fixture_ratio": 0.25,
            "fixtures_tested": 4,
            "streams_playable": 1,
            "playable_fixtures": 1,
            "payload_verified_streams": 1,
            "distinct_reachable_hosts": 1,
            "reachable_hosts": ["media.example"],
            "effective_max_height": 360,
            "max_bandwidth": 300000,
            "accepted_audio_languages": [],
            "accepted_subtitle_languages": [],
            "audio_languages": ["hi"],
            "subtitle_languages": [],
            "accepted_subtitles_advertised": 0,
            "accepted_subtitles_reachable": 0,
            "disallowed_streams": 0,
            "provider_server_accessible": True,
            "provider_server_successful_response": True,
            "provider_median_latency_ms": 500,
            "stream_median_latency_ms": 500,
            "manifest_description_present": True,
            "manifest_supported_types": ["movie", "tv", "anime"],
            "manifest_formats": ["mp4"],
            "manifest_curation_score": 5,
        },
    }
}
gates, proof = promoter.evaluate_pre_stability_gates(item, activation)
assert proof["activation_supported_types"] == ["movie"], proof
assert gates["04_fixture_and_type_coverage"]["passed"] is True, gates["04_fixture_and_type_coverage"]
assert gates["04_fixture_and_type_coverage"]["evidence"]["healthy_fixture_ratio"] == 1.0
assert gates["04_fixture_and_type_coverage"]["evidence"]["fixtures_tested"] == 1

print('type-scoped activation tests passed')
