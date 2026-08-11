#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTE = ROOT / 'scripts' / 'promote_candidates.py'
TEST = ROOT / 'tests' / 'type_scoped_activation_test.py'

source = PROMOTE.read_text(encoding='utf-8')
old = '''    scoped_tests = [\n        item for item in (result.get("tests") or [])\n        if isinstance(item, dict)\n        and str((item.get("fixture") or {}).get("category") or "") in scoped_categories\n    ]\n    scoped_healthy = [item for item in scoped_tests if item.get("status") == "healthy"]\n    coverage_healthy_fixtures = len(scoped_healthy) if scoped_categories else healthy_fixtures\n    coverage_ratio = (\n        len(scoped_healthy) / len(scoped_tests)\n        if scoped_categories and scoped_tests\n        else healthy_ratio\n    )\n'''
new = '''    scoped_tests = [\n        item for item in (result.get("tests") or [])\n        if isinstance(item, dict)\n        and str((item.get("fixture") or {}).get("category") or "") in scoped_categories\n    ]\n    # Type-scoped activation measures proven catalogue capabilities, not how many\n    # arbitrary titles happened to be absent. Once a category has a current\n    # verified payload, earlier primary/fallback catalogue misses remain\n    # diagnostics and cannot dilute that category's activation ratio.\n    scoped_healthy_categories = scoped_categories & healthy_categories\n    coverage_healthy_fixtures = (\n        len(scoped_healthy_categories) if scoped_categories else healthy_fixtures\n    )\n    coverage_ratio = (\n        len(scoped_healthy_categories) / len(scoped_categories)\n        if scoped_categories\n        else healthy_ratio\n    )\n'''
if new not in source:
    if old not in source:
        raise SystemExit('type-scoped coverage anchor missing')
    source = source.replace(old, new, 1)
source = source.replace(
    '"fixtures_tested": len(scoped_tests) if scoped_categories else int(proof.get("fixtures_tested", 0)),',
    '"fixtures_tested": len(scoped_categories) if scoped_categories else int(proof.get("fixtures_tested", 0)),',
    1,
)
PROMOTE.write_text(source, encoding='utf-8')

test = TEST.read_text(encoding='utf-8')
block = '''\n# A catalogue may miss several representative titles before one current payload\n# proves the type. Raw title misses must not reduce type-scoped coverage.\nimport importlib.util\nimport json\nspec = importlib.util.spec_from_file_location("promote_type_scope", ROOT / "scripts" / "promote_candidates.py")\nassert spec and spec.loader\npromoter = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(promoter)\nactivation = json.loads((ROOT / "health-config.json").read_text(encoding="utf-8"))["activation"]\nhealthy_movie = {\n    "fixture": {"category": "movie"},\n    "status": "healthy",\n    "streams_playable": 1,\n    "payload_verified_streams": 1,\n    "effective_max_height": 360,\n    "max_bandwidth": 300000,\n    "accepted_audio_languages": [],\n    "accepted_subtitle_languages": [],\n    "accepted_subtitles_advertised": 0,\n    "accepted_subtitles_reachable": 0,\n}\nmiss = lambda: {"fixture": {"category": "movie"}, "status": "no_streams", "streams_playable": 0, "payload_verified_streams": 0}\nitem = {\n    "health": {\n        "status": "healthy",\n        "score": 60,\n        "tests": [miss(), miss(), miss(), healthy_movie],\n        "evidence": {\n            "required_fixture_categories": ["movie", "tv", "anime"],\n            "healthy_fixture_categories": ["movie"],\n            "healthy_fixtures": 1,\n            "healthy_fixture_ratio": 0.25,\n            "fixtures_tested": 4,\n            "streams_playable": 1,\n            "playable_fixtures": 1,\n            "payload_verified_streams": 1,\n            "distinct_reachable_hosts": 1,\n            "reachable_hosts": ["media.example"],\n            "effective_max_height": 360,\n            "max_bandwidth": 300000,\n            "accepted_audio_languages": [],\n            "accepted_subtitle_languages": [],\n            "audio_languages": ["hi"],\n            "subtitle_languages": [],\n            "accepted_subtitles_advertised": 0,\n            "accepted_subtitles_reachable": 0,\n            "disallowed_streams": 0,\n            "provider_server_accessible": True,\n            "provider_server_successful_response": True,\n            "provider_median_latency_ms": 500,\n            "stream_median_latency_ms": 500,\n            "manifest_description_present": True,\n            "manifest_supported_types": ["movie", "tv", "anime"],\n            "manifest_formats": ["mp4"],\n            "manifest_curation_score": 5,\n        },\n    }\n}\ngates, proof = promoter.evaluate_pre_stability_gates(item, activation)\nassert proof["activation_supported_types"] == ["movie"], proof\nassert gates["04_fixture_and_type_coverage"]["passed"] is True, gates["04_fixture_and_type_coverage"]\nassert gates["04_fixture_and_type_coverage"]["evidence"]["healthy_fixture_ratio"] == 1.0\nassert gates["04_fixture_and_type_coverage"]["evidence"]["fixtures_tested"] == 1\n'''
marker = '\nprint(' if '\nprint(' in test else None
if 'Raw title misses must not reduce type-scoped coverage' not in test:
    if not marker:
        raise SystemExit('type scope test print anchor missing')
    pos = test.rfind('\nprint(')
    test = test[:pos] + block + test[pos:]
TEST.write_text(test, encoding='utf-8')

print('type-scoped catalogue coverage semantics aligned')
