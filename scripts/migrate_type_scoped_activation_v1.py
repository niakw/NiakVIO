#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTE = ROOT / 'scripts' / 'promote_candidates.py'
CONFIG = ROOT / 'health-config.json'
PACKAGE = ROOT / 'package.json'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    source = PROMOTE.read_text(encoding='utf-8')

    helper_anchor = '''def gate(
    passed: bool,
    evidence: Any,
    threshold: Any,
) -> dict[str, Any]:
'''
    helper = '''def independently_proven_categories(
    result: dict[str, Any], activation: dict[str, Any]
) -> set[str]:
    """Return catalogue types that independently pass current media proof.

    This is deliberately stricter than merely observing a healthy provider. A
    type is eligible only when at least one current fixture for that type has a
    verified playable payload, meets the unchanged quality/bitrate floor, and
    carries accepted FR/EN audio or subtitle evidence. The result can safely
    narrow supportedTypes without allowing a good movie to mask a broken TV
    path (or vice versa).
    """
    tests = result.get("tests") if isinstance(result.get("tests"), list) else []
    minimum_streams = int(activation.get("minimum_playable_streams", 1))
    minimum_payload = int(activation.get("minimum_payload_verified_streams", 1))
    minimum_height = int(activation.get("minimum_effective_height", 720))
    minimum_bandwidth = int(activation.get("minimum_bandwidth_bps_when_reported", 1_000_000))
    accepted_audio = {
        str(value).casefold() for value in activation.get("accepted_audio_languages", ["fr", "en"])
    }
    accepted_subtitles = {
        str(value).casefold() for value in activation.get("accepted_subtitle_languages", ["fr", "en"])
    }
    require_language = bool(activation.get("require_accepted_language_evidence", True))
    require_reachable_subtitles = bool(
        activation.get("require_reachable_accepted_subtitle_when_advertised", True)
    )
    proven: set[str] = set()
    for test in tests:
        if not isinstance(test, dict) or test.get("status") != "healthy":
            continue
        category = str((test.get("fixture") or {}).get("category") or "")
        if category not in {"movie", "tv", "anime"}:
            continue
        if int(test.get("streams_playable", 0)) < minimum_streams:
            continue
        if int(test.get("payload_verified_streams", 0)) < minimum_payload:
            continue
        height = int(test.get("effective_max_height", 0) or 0)
        bandwidth_raw = test.get("max_bandwidth")
        bandwidth = int(bandwidth_raw) if bandwidth_raw else None
        if height < minimum_height or (bandwidth is not None and bandwidth < minimum_bandwidth):
            continue
        audio = {
            str(value).casefold() for value in test.get("accepted_audio_languages", []) if value
        } & accepted_audio
        subtitles = {
            str(value).casefold() for value in test.get("accepted_subtitle_languages", []) if value
        } & accepted_subtitles
        advertised = int(test.get("accepted_subtitles_advertised", 0) or 0)
        reachable = int(test.get("accepted_subtitles_reachable", 0) or 0)
        subtitle_ok = bool(subtitles) and (
            not require_reachable_subtitles or advertised == 0 or reachable > 0
        )
        if require_language and not (audio or subtitle_ok):
            continue
        proven.add(category)
    return proven


'''
    if 'def independently_proven_categories(' not in source:
        if helper_anchor not in source:
            raise SystemExit('promote_candidates.py gate helper anchor not found')
        source = source.replace(helper_anchor, helper + helper_anchor, 1)

    old_categories = '''    required_categories = {
        str(value)
        for value in proof.get("required_fixture_categories", [])
        if value
    }
    healthy_categories = {
        str(value)
        for value in proof.get("healthy_fixture_categories", [])
        if value
    }
    representative_fixture_mode = bool(
        activation.get("representative_fixture_mode", True)
    )
    category_coverage = (
        not require_type_coverage
        or not required_categories
        or (
            bool(required_categories & healthy_categories)
            if representative_fixture_mode
            else required_categories.issubset(healthy_categories)
        )
    )

    healthy_fixtures = int(proof.get("healthy_fixtures", 0))
    healthy_ratio = float(proof.get("healthy_fixture_ratio", 0.0) or 0.0)
'''
    new_categories = '''    required_categories = {
        str(value)
        for value in proof.get("required_fixture_categories", [])
        if value
    }
    healthy_categories = {
        str(value)
        for value in proof.get("healthy_fixture_categories", [])
        if value
    }
    type_scoped_activation = bool(activation.get("allow_type_scoped_activation", False))
    independently_proven = independently_proven_categories(result, activation) if type_scoped_activation else set()
    scoped_categories = required_categories & independently_proven
    effective_required_categories = scoped_categories if scoped_categories else required_categories
    representative_fixture_mode = bool(
        activation.get("representative_fixture_mode", True)
    )
    category_coverage = (
        not require_type_coverage
        or not effective_required_categories
        or (
            bool(effective_required_categories & healthy_categories)
            if representative_fixture_mode
            else effective_required_categories.issubset(healthy_categories)
        )
    )

    healthy_fixtures = int(proof.get("healthy_fixtures", 0))
    healthy_ratio = float(proof.get("healthy_fixture_ratio", 0.0) or 0.0)
    scoped_tests = [
        item for item in (result.get("tests") or [])
        if isinstance(item, dict)
        and str((item.get("fixture") or {}).get("category") or "") in scoped_categories
    ]
    scoped_healthy = [item for item in scoped_tests if item.get("status") == "healthy"]
    coverage_healthy_fixtures = len(scoped_healthy) if scoped_categories else healthy_fixtures
    coverage_ratio = (
        len(scoped_healthy) / len(scoped_tests)
        if scoped_categories and scoped_tests
        else healthy_ratio
    )
'''
    if new_categories not in source:
        if old_categories not in source:
            raise SystemExit('promote_candidates.py category coverage anchor not found')
        source = source.replace(old_categories, new_categories, 1)

    old_gate = '''        "04_fixture_and_type_coverage": gate(
            (healthy_fixtures >= minimum_fixtures
            and healthy_ratio >= minimum_ratio
            and category_coverage) or (runtime_light and manifest_description_present),
            {
                "healthy_fixtures": healthy_fixtures,
                "fixtures_tested": int(proof.get("fixtures_tested", 0)),
                "healthy_fixture_ratio": healthy_ratio,
                "required_categories": sorted(required_categories),
                "healthy_categories": sorted(healthy_categories),
            },
'''
    new_gate = '''        "04_fixture_and_type_coverage": gate(
            (coverage_healthy_fixtures >= minimum_fixtures
            and coverage_ratio >= minimum_ratio
            and category_coverage) or (runtime_light and manifest_description_present),
            {
                "healthy_fixtures": coverage_healthy_fixtures,
                "fixtures_tested": len(scoped_tests) if scoped_categories else int(proof.get("fixtures_tested", 0)),
                "healthy_fixture_ratio": coverage_ratio,
                "required_categories": sorted(effective_required_categories),
                "original_required_categories": sorted(required_categories),
                "healthy_categories": sorted(healthy_categories),
                "activation_supported_types": sorted(scoped_categories),
                "type_scope_applied": bool(scoped_categories and scoped_categories != required_categories),
            },
'''
    if new_gate not in source:
        if old_gate not in source:
            raise SystemExit('promote_candidates.py gate 04 anchor not found')
        source = source.replace(old_gate, new_gate, 1)

    old_return = '    return gates, {**proof, "performance": performance}\n'
    new_return = '''    return gates, {
        **proof,
        "performance": performance,
        "activation_supported_types": sorted(scoped_categories),
        "activation_type_scope_applied": bool(scoped_categories and scoped_categories != required_categories),
        "activation_original_supported_types": sorted(required_categories),
    }
'''
    if new_return not in source:
        if old_return not in source:
            raise SystemExit('promote_candidates.py evaluated proof return anchor not found')
        source = source.replace(old_return, new_return, 1)

    old_entry = '            promoted_entry = build_entry(selected, destination, enabled, aggregated_claims)\n'
    new_entry = '''            promoted_entry = build_entry(selected, destination, enabled, aggregated_claims)
            activation_supported_types = [
                str(value) for value in (proof.get("activation_supported_types") or [])
                if str(value) in {"movie", "tv", "anime"}
            ]
            if enabled and activation_mode == "strict_current" and activation_supported_types:
                promoted_entry["supportedTypes"] = activation_supported_types
'''
    if new_entry not in source:
        if old_entry not in source:
            raise SystemExit('promote_candidates.py promoted entry anchor not found')
        source = source.replace(old_entry, new_entry, 1)

    old_version = '''    previous = str(old_entry.get("version") or declared or "1.0.0")
    if str(old_entry.get("filename") or "") != str(new_entry.get("filename") or ""):
        return bump_provider_version(previous)
    return previous
'''
    new_version = '''    previous = str(old_entry.get("version") or declared or "1.0.0")
    tracked_fields = ("filename", "supportedTypes", "supportsExternalPlayer")
    if any(old_entry.get(field) != new_entry.get(field) for field in tracked_fields):
        return bump_provider_version(previous)
    return previous
'''
    if new_version not in source:
        if old_version not in source:
            raise SystemExit('promote_candidates.py provider version anchor not found')
        source = source.replace(old_version, new_version, 1)

    PROMOTE.write_text(source, encoding='utf-8')

    cfg = load(CONFIG)
    activation = cfg.setdefault('activation', {})
    activation['allow_type_scoped_activation'] = True
    dump(CONFIG, cfg)

    package = load(PACKAGE)
    command = package['scripts']['test']
    test = 'python3 tests/type_scoped_activation_test.py'
    if test not in command:
        command += ' && ' + test
    package['scripts']['test'] = command
    dump(PACKAGE, package)

    print('type-scoped activation enabled: current per-type media/quality/language proof can safely narrow supportedTypes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
