#!/usr/bin/env python3
"""Evaluate external Brain-LLM Force mutations in isolated provider sandboxes.

Each provider candidate starts from the exact current Git SHA in its own detached
git worktree. The candidate is applied there, only that provider is
rematerialized, and the same Deep health lane is executed for baseline and
candidate bytes. A Force candidate can be exported for later application only
after strict runtime improvement AND the existing automatic identity gate pass.

This script never mutates the caller's working tree.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import deep_repair_loop as deep  # noqa: E402
import runtime_repair  # noqa: E402
from repair_identity_gate import automatic_repair_identity_gate  # noqa: E402
from http_response_evidence import public_http_observation, public_reader_probe  # noqa: E402
from address_reference_evidence import public_address_fields  # noqa: E402
from observed_media_evidence import public_observed_media_probe  # noqa: E402

SHA40 = __import__("re").compile(r"^[0-9a-f]{40}$")
DECODED_REPAIR_FIXTURES = {
    '95479': 'Jujutsu Kaisen S01E01',
    '280049': 'Hell Mode S01E01',
}


def require_decoded_repair() -> bool:
    return os.environ.get('NIAKVIO_REQUIRE_DECODE_PROOF') == '1'


def decoded_media_summary(test: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    # Imported after this module has initialized: the comparison CLI itself
    # imports the evaluator for staging, but its projection is pure.
    from check_cross_provider_playback import public_probe

    raw = test.get('host_results')
    fixture = test.get('fixture') if isinstance(test.get('fixture'), dict) else {}
    minutes = fixture.get('expectedDurationMinutes')
    # The standalone cross-provider anime analyzer defaults to 1440s. Brain
    # must instead pass the current *verified fixture* duration for films/TV.
    expected_seconds = (round(minutes * 60) if type(minutes) in (int, float)
                        and 0 < minutes <= 20160 else 1440)
    probes = [public_probe(row, expected_seconds=expected_seconds)
              for row in raw[:3] if isinstance(row, dict)] \
        if isinstance(raw, list) else []
    executed = all(type(test.get(key)) is int and test[key] > 0
                   for key in ('streams_returned', 'streams_playable', 'streams_probed'))
    return probes, sum(row['passedMediaControl'] is True for row in probes) if executed else 0


def strict_repair_fixture_contract(provider: str | None = None) -> dict[tuple[str, str], dict[str, Any]]:
    """Select immutable, category-matched fixture facts from health-config.json.

    The source of authority is never a provider, candidate output or model prompt.
    Anime-only legacy callers retain the same two fixed regression fixtures.
    A movie provider cannot be declared fixed by running two anime episodes.
    """
    source = load(ROOT / 'health-config.json').get('fixtures') or {}
    if provider is None:
        categories = {'anime'}
    else:
        manifest = load(ROOT / 'manifest.json')
        selected = [row for row in manifest.get('scrapers') or []
                    if isinstance(row, dict) and canon(row.get('id')) == canon(provider)
                    and row.get('enabled') is True]
        if len(selected) != 1:
            raise ValueError('decoded_repair_provider_manifest_contract')
        supported = {str(value).strip().casefold()
                     for value in (selected[0].get('supportedTypes') or [])}
        categories = supported.intersection({'movie', 'tv', 'anime', 'anime_movie'})
        if not categories or supported - categories:
            raise ValueError('decoded_repair_unsupported_media_category')
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for category in ('anime', 'movie', 'tv', 'anime_movie'):
        if category not in categories:
            continue
        candidates = [row for row in source.get(category) or []
                      if isinstance(row, dict)
                      and str(row.get('tmdbId') or '').isdigit()
                      and type(row.get('expectedDurationMinutes')) in (int, float)
                      and row['expectedDurationMinutes'] > 0
                      and (category in ('movie', 'anime_movie') or
                           (type(row.get('season')) is int and row['season'] >= 0
                            and type(row.get('episode')) is int and row['episode'] > 0))]
        if provider is None:
            candidates = [row for tmdb in DECODED_REPAIR_FIXTURES
                          for row in candidates if str(row.get('tmdbId')) == tmdb]
            if len(candidates) != len(DECODED_REPAIR_FIXTURES):
                raise ValueError('decoded_repair_fixture_contract')
        elif not candidates:
            raise ValueError('decoded_repair_missing_category_fixture:' + category)
        # Two independently identified anime fixtures; at least one authentic
        # fixture per other declared media category, never a synthetic stand-in.
        for fixture in candidates[:2]:
            key = category, str(fixture['tmdbId'])
            if key in result:
                raise ValueError('decoded_repair_duplicate_fixture')
            result[key] = copy.deepcopy(fixture)
    if not result:
        raise ValueError('decoded_repair_empty_fixture_contract')
    return result


def decoded_repair_gate(baseline: dict[str, Any], candidate: dict[str, Any],
                        provider: str | None = None) -> tuple[bool, str, dict[str, Any]]:
    """Require actual decoded improvement on the provider's own media types."""
    required = strict_repair_fixture_contract(provider)
    metadata = {'decodedProofRequired': True, 'improvedFixtures': [],
                'unresolvedFixtures': [str(row.get('label') or key[1])
                                       for key, row in required.items()]}

    def fixtures(result):
        tests = result.get('tests')
        if not isinstance(tests, list) or len(tests) != len(required):
            return None
        selected = {}
        for test in tests:
            if not isinstance(test, dict) or not isinstance(test.get('fixture'), dict):
                return None
            fixture = test['fixture']
            category = str(fixture.get('category') or '')
            key = (category, str(fixture.get('tmdbId') or ''))
            spec = required.get(key)
            if spec is None or key in selected:
                return None
            if (fixture.get('label') != spec.get('label')
                    or fixture.get('expectedDurationMinutes') != spec['expectedDurationMinutes']
                    or type(fixture.get('expectedDurationMinutes')) not in (int, float)):
                return None
            if category in ('anime', 'tv'):
                if (type(fixture.get('season')) is not int
                        or fixture['season'] != spec['season']
                        or type(fixture.get('episode')) is not int
                        or fixture['episode'] != spec['episode']):
                    return None
            elif fixture.get('season') is not None or fixture.get('episode') is not None:
                return None
            if any(type(test.get(field)) is not int or test[field] < 0
                   for field in ('streams_returned', 'streams_playable', 'streams_probed')):
                return None
            selected[key] = test
        return selected if set(selected) == set(required) else None

    before, after = fixtures(baseline), fixtures(candidate)
    if before is None or after is None:
        return False, 'decoded_repair_fixture_contract', metadata
    metadata['unresolvedFixtures'] = []
    regression = None
    for key, spec in required.items():
        old, new = before[key], after[key]
        _, old_controls = decoded_media_summary(old)
        _, new_controls = decoded_media_summary(new)
        label = str(spec.get('label') or key[1])
        if new_controls == 0:
            metadata['unresolvedFixtures'].append(label)
        if old['streams_playable'] == 0 and new_controls > 0:
            metadata['improvedFixtures'].append(label)
        if (new_controls < old_controls or any(new[field] < old[field]
                for field in ('streams_returned', 'streams_playable'))):
            regression = regression or f'decoded_repair_fixture_regression:{key[1]}'
    if regression:
        return False, regression, metadata
    if not metadata['improvedFixtures']:
        return False, 'decoded_repair_no_new_fixture_control', metadata
    return True, 'decoded_repair_fixture_improvement', metadata


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def run(*args: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        env=env,
        check=True,
    )


def provider_result(payload: dict[str, Any], provider: str) -> dict[str, Any]:
    rows = [
        row
        for row in payload.get("results") or []
        if isinstance(row, dict)
        and (
            canon(row.get("provider")) == provider
            or canon(row.get("provider_id")) == provider
            or str(row.get("key") or "").casefold().endswith(":" + provider)
        )
    ]
    if len(rows) != 1:
        if len(payload.get("results") or []) == 1 and isinstance((payload.get("results") or [None])[0], dict):
            return copy.deepcopy(payload["results"][0])
        raise ValueError(
            f"{provider}: expected exactly one provider health result, got {len(rows)}"
        )
    return copy.deepcopy(rows[0])


def invocation_summary(result: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for test in result.get("tests") or []:
        if not isinstance(test, dict):
            continue
        fixture = test.get("fixture") if isinstance(test.get("fixture"), dict) else {}
        for row in test.get("invocation_diagnostics") or []:
            if not isinstance(row, dict):
                continue
            output.append(
                {
                    "fixture": str(fixture.get("label") or fixture.get("tmdbId") or "")[:160],
                    "name": str(row.get("name") or "")[:80],
                    "inferredMode": str(row.get("inferred_mode") or "")[:40],
                    "result": str(row.get("result") or "")[:40],
                    "streamCount": int(row.get("stream_count") or 0),
                    "providerObservations": int(row.get("provider_observations") or 0),
                    "errorCode": str((row.get("error") or {}).get("code") or "")[:100]
                    if isinstance(row.get("error"), dict)
                    else "",
                }
            )
    return output[:48]


def network_summary(result: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[object, ...]] = set()
    for test in result.get("tests") or []:
        if not isinstance(test, dict):
            continue
        fixture = test.get("fixture") if isinstance(test.get("fixture"), dict) else {}
        label = str(fixture.get("label") or fixture.get("tmdbId") or "")[:120]
        for row in test.get("network_observations") or []:
            if not isinstance(row, dict):
                continue
            item = {
                **public_address_fields(row),
                "fixture": label,
                "stage": str(row.get("stage") or "")[:80],
                "host": str(row.get("host") or "")[:160],
                "method": str(row.get("method") or "GET")[:12],
                "path": str(row.get("path_pattern") or "")[:240],
                "status": row.get("status") if isinstance(row.get("status"), int) else None,
                "ok": bool(row.get("ok")),
                "errorCode": str(row.get("error_code") or "")[:100],
                "announcedPlayerCandidates": int(row.get("declared_player_candidate_count") or 0),
                "announcedPlayerHosts": [str(value)[:160] for value in (row.get("declared_player_hosts") or [])[:24]],
                "announcedQualityHeights": [
                    int(value) for value in (row.get("declared_quality_heights") or [])[:12]
                    if str(value or "").isdigit()
                ],
            }
            if isinstance(row.get("response_structure"), dict):
                item["responseStructure"] = row["response_structure"]
            if isinstance(row.get("media_observation"), dict):
                item["mediaObservation"] = row["media_observation"]
            if isinstance(row.get('http_observation'), dict):
                item['httpObservation'] = public_http_observation(row['http_observation'])
            if isinstance(row.get('reader_user_agent_probe'), dict):
                item['readerUserAgentProbe'] = public_reader_probe(row['reader_user_agent_probe'])
            if item.get('address_scope') and isinstance(row.get('observed_media_probe'), dict):
                item['observedMediaProbe'] = public_observed_media_probe(row['observed_media_probe'])
            if row.get("provider_function_names"):
                item["providerFunctions"] = row["provider_function_names"][:8]
            key = (
                item["fixture"],
                item["stage"],
                item["host"],
                item["path"],
                item["status"],
                item.get('address_scope'), item.get('request_ref'),
                item.get('response_ref'), item.get('referer_ref'),
            )
            if key in seen and not item.get('address_scope'):
                continue
            seen.add(key)
            if len(output) < 64:
                output.append(item)
            else:
                for kept in output:
                    if kept.get('address_scope'):
                        kept['address_trace_truncated'] = True
    return output


def variant_coverage_summary(result: dict[str, Any]) -> dict[str, Any]:
    quality_heights: set[int] = set()
    audio_languages: set[str] = set()
    reachable_hosts: set[str] = set()
    max_playable_height = 0
    announced_player_candidates = 0
    announced_variant_candidates = 0
    explored_player_requests = 0
    fanout_states: set[str] = set()
    announced_quality_heights: set[int] = set()
    for test in result.get("tests") or []:
        if not isinstance(test, dict):
            continue
        for raw in test.get("returned_quality_heights") or []:
            try:
                height = int(raw or 0)
            except (TypeError, ValueError):
                continue
            if height > 0:
                quality_heights.add(height)
        for key in ("effective_max_height", "verified_max_height"):
            try:
                height = int(test.get(key) or 0)
            except (TypeError, ValueError):
                height = 0
            max_playable_height = max(max_playable_height, height)
        for value in test.get("audio_languages") or []:
            value = str(value or "").strip().casefold()
            if value:
                audio_languages.add(value)
        for value in test.get("reachable_hosts") or []:
            value = str(value or "").strip().casefold()
            if value:
                reachable_hosts.add(value)
        announced_player_candidates = max(
            announced_player_candidates,
            int(test.get("announced_player_candidates") or 0),
        )
        announced_variant_candidates = max(
            announced_variant_candidates,
            int(test.get("announced_variant_candidates") or 0),
        )
        explored_player_requests = max(
            explored_player_requests,
            int(test.get("explored_player_requests") or 0),
        )
        state = str(test.get("variant_fanout_state") or "").strip().casefold()
        if state:
            fanout_states.add(state)
        for raw in test.get("announced_quality_heights") or []:
            try:
                height = int(raw or 0)
            except (TypeError, ValueError):
                continue
            if height > 0:
                announced_quality_heights.add(height)
    return {
        "qualityHeights": sorted(quality_heights),
        "maxPlayableHeight": max_playable_height,
        "audioLanguages": sorted(audio_languages),
        "reachableHosts": sorted(reachable_hosts),
        "announcedPlayerCandidates": announced_player_candidates,
        "announcedVariantCandidates": announced_variant_candidates,
        "exploredPlayerRequests": explored_player_requests,
        "fanoutStates": sorted(fanout_states),
        "announcedQualityHeights": sorted(announced_quality_heights),
    }


def evaluate_variant_coverage_pair(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[bool, str]:
    status = str(candidate.get("status") or "runtime_error")
    if status in runtime_repair.HARD_FAILURES:
        return False, f"variant_coverage_hard_failure:{status}"
    if runtime_repair.runtime_error_count(candidate) > runtime_repair.runtime_error_count(baseline):
        return False, "variant_coverage_introduced_runtime_error"
    if runtime_repair.malformed_request_count(candidate) > runtime_repair.malformed_request_count(baseline):
        return False, "variant_coverage_introduced_malformed_request"
    if runtime_repair.identity_contradiction_count(candidate) > runtime_repair.identity_contradiction_count(baseline):
        return False, "variant_coverage_introduced_identity_contradiction"
    if runtime_repair.playable_stream_count(candidate) < runtime_repair.playable_stream_count(baseline):
        return False, "variant_coverage_playable_regression"
    if runtime_repair.stream_count(candidate) < runtime_repair.stream_count(baseline):
        return False, "variant_coverage_stream_regression"

    before = variant_coverage_summary(baseline)
    after = variant_coverage_summary(candidate)
    before_streams = runtime_repair.stream_count(baseline)
    after_streams = runtime_repair.stream_count(candidate)
    before_playable = runtime_repair.playable_stream_count(baseline)
    after_playable = runtime_repair.playable_stream_count(candidate)
    gains: list[str] = []
    if after_streams > before_streams:
        gains.append("returned-stream-count")
    if int(after["maxPlayableHeight"]) > int(before["maxPlayableHeight"]):
        gains.append("playable-height")
    before_quality = set(before["qualityHeights"])
    after_quality = set(after["qualityHeights"])
    if after_quality - before_quality and max(after_quality or {0}) >= max(before_quality or {0}):
        gains.append("reported-quality-set")
    before_audio = set(before["audioLanguages"])
    after_audio = set(after["audioLanguages"])
    if after_audio - before_audio:
        gains.append("audio-language-set")
    before_hosts = set(before["reachableHosts"])
    after_hosts = set(after["reachableHosts"])
    if after_hosts - before_hosts:
        gains.append("reachable-host-set")

    verified_gain = (
        "playable-height" in gains
        or "audio-language-set" in gains
        or "reachable-host-set" in gains
        or (
            "returned-stream-count" in gains
            and after_playable > 0
            and after_playable >= before_playable
            and int(after.get("announcedVariantCandidates") or after.get("announcedPlayerCandidates") or 0) >= 2
        )
    )
    if not gains or not verified_gain:
        return False, "variant_coverage_no_verified_dimension_gain"

    identity_ok, identity_reason = automatic_repair_identity_gate(candidate)
    if not identity_ok:
        return False, identity_reason
    return True, "variant_coverage_improvement:" + ",".join(gains)


def fixture_summary(result: dict[str, Any]) -> list[dict[str, Any]]:
    output = [{
        'fixture': str((test.get('fixture') or {}).get('label') or '')[:120],
        'category': str((test.get('fixture') or {}).get('category') or '')[:24],
        'status': str(test.get('status') or '')[:64],
        'streamsPlayable': int(test.get('streams_playable') or 0),
        'streamsReturned': int(test.get('streams_returned') or 0),
    } for test in (result.get('tests') or [])[:12] if isinstance(test, dict)]
    for row, test in zip(output, [test for test in (result.get('tests') or [])[:12] if isinstance(test, dict)]):
        minutes = (test.get('fixture') or {}).get('expectedDurationMinutes')
        if type(minutes) in (int, float) and 0 < minutes <= 20160:
            row['expectedDurationSeconds'] = round(minutes * 60)
        raw_probes = test.get('host_results')
        if require_decoded_repair() or (isinstance(raw_probes, list) and any(
                isinstance(probe, dict) and isinstance(probe.get('media_decode'), dict)
                for probe in raw_probes)):
            probes, controls = decoded_media_summary(test)
            fixture = test.get('fixture') or {}
            tmdb = str(fixture.get('tmdbId') or '')
            row.update({'tmdbId': tmdb if tmdb in DECODED_REPAIR_FIXTURES else '',
                        'season': fixture.get('season') if type(fixture.get('season')) is int else None,
                        'episode': fixture.get('episode') if type(fixture.get('episode')) is int else None,
                        'decodedMediaControls': controls, 'decodedMediaProbes': probes})
    return output


def result_summary(result: dict[str, Any]) -> dict[str, Any]:
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    return {
        "status": str(result.get("status") or ""),
        "score": int(result.get("score") or 0),
        "streamsPlayable": runtime_repair.playable_stream_count(result),
        "streamsReturned": runtime_repair.stream_count(result),
        "fixtureCoverage": fixture_summary(result),
        "identityContradictions": runtime_repair.identity_contradiction_count(result),
        "providerRequests": int(evidence.get("provider_request_count"))
        if evidence.get("provider_request_count") is not None else sum(
            1 for test in result.get("tests", [])
            for row in test.get("network_observations", [])
            if isinstance(row, dict) and not row.get("infrastructure")
        ),
        "providerHosts": [str(value)[:160] for value in (evidence.get("provider_server_hosts") or [])[:24]],
        "providerHttpStatuses": [
            int(value) for value in (evidence.get("provider_server_http_statuses") or [])[:24]
            if isinstance(value, int)
        ],
        "failureClass": str(result.get("failure_class") or ""),
        "variantCoverage": variant_coverage_summary(result),
        "networkTrace": network_summary(result),
        "invocationDiagnostics": invocation_summary(result),
    }


def evaluate_pair(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    mechanism_family: str = "",
    provider: str | None = None,
) -> tuple[bool, str]:
    if require_decoded_repair():
        decoded_ok, decoded_reason, _ = decoded_repair_gate(baseline, candidate, provider)
        if not decoded_ok:
            return False, decoded_reason
    family = str(mechanism_family or "").strip().casefold().replace("_", "-")
    if family in {
        "bounded-variant-enumeration-before-cap",
        "quality-stratified-variant-enumeration",
        "quality-aware-global-stop",
        "cross-source-round-robin-before-global-cap",
        "bidirectional-source-frontier-before-global-cap",
    }:
        return evaluate_variant_coverage_pair(baseline, candidate)
    accepted, reason = runtime_repair.compare_results(baseline, candidate)
    if not accepted:
        return False, reason
    identity_ok, identity_reason = automatic_repair_identity_gate(candidate)
    if not identity_ok:
        return False, identity_reason
    return True, reason


def write_targets(path: Path, provider: str) -> None:
    path.write_text(
        json.dumps({"targets": [{"id": provider}]}, indent=2) + "\n",
        encoding="utf-8",
    )


def stage_provider(repo_root: Path, provider: str, stage: Path, targets: Path) -> None:
    run(
        sys.executable,
        "scripts/stage_published.py",
        "--stage",
        str(stage),
        "--include-file",
        str(targets),
        cwd=repo_root,
    )


def health_provider(stage: Path, output: Path, provider: str | None = None) -> dict[str, Any]:
    # Activation stops after its first healthy HD example. A repair comparison
    # must observe more than that first success and probe the bounded stream set.
    output.mkdir(parents=True, exist_ok=True)
    config = load(ROOT / 'health-config.json')
    config['modes']['deep'].update({
        'primary_fixture_limit_per_category': 2,
        'probe_streams_adaptively': False,
    })
    if require_decoded_repair():
        from check_cross_provider_playback import comparison_config
        config = comparison_config(config)
        if provider is not None:
            # The baseline and candidate must run precisely the same immutable,
            # media-type-correct fixtures; the model cannot choose them.
            required = strict_repair_fixture_contract(provider)
            config['fixtures'] = {key: [] for key in ('anime', 'movie', 'tv', 'anime_movie')}
            for (category, _tmdb), fixture in required.items():
                config['fixtures'][category].append(copy.deepcopy(fixture))
            count = len(required)
            config['modes']['deep']['fixture_limit'] = count
            print('FIELD_BRAIN_STRICT_FIXTURES provider=' + canon(provider)
                  + ' categories=' + ','.join(sorted({key[0] for key in required}))
                  + ' fixtures=' + str(count), flush=True)
    if os.environ.get('NIAKVIO_READER_UA_PROBE') == '1':
        config['modes']['deep']['reader_user_agent_probe'] = True
    if os.environ.get('NIAKVIO_OBSERVED_MEDIA_PROBE') == '1':
        config['modes']['deep']['observed_media_probe'] = True
    config_path = output / 'comparison-health-config.json'
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    return deep.run_health(
        stage=stage,
        registry_path=stage / "candidates.json",
        output_dir=output,
        mode="deep",
        health_check=ROOT / "scripts" / "health_check.mjs",
        health_config=config_path,
    )


def candidate_execution_error(exc: BaseException) -> str:
    if isinstance(exc, subprocess.CalledProcessError):
        command = exc.cmd if isinstance(exc.cmd, (list, tuple)) else [exc.cmd]
        executable = Path(str(command[1] if len(command) > 1 else command[0])).name
        return f"command_failed:{executable}:rc={exc.returncode}"
    return f"{type(exc).__name__}:{str(exc)[:500]}"


def mutation_summary(row: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for mutation in row.get("mutations") or []:
        if not isinstance(mutation, dict):
            continue
        item = {
            "scope": str(mutation.get("scope") or "")[:40],
            "operation": str(mutation.get("operation") or "")[:40],
        }
        family = str(mutation.get("family") or "")[:80]
        if family:
            item["family"] = family
        path = str(mutation.get("path") or "")[:160]
        if path:
            item["path"] = path
        out.append(item)
    return out[:8]


def single_row_payload(payload: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: copy.deepcopy(value)
        for key, value in payload.items()
        if key != "rows"
    }
    result["rows"] = [copy.deepcopy(row)]
    result["providerCount"] = 1
    return result


def materialization_proof(baseline_stage: Path, candidate_stage: Path, provider: str,
                          row: dict[str, Any]) -> dict[str, Any]:
    from provider_patch_blocks import decode_managed_data

    def bundle(stage):
        registry = load(stage / 'candidates.json')
        matches = [item for item in registry.get('candidates', [])
                   if canon(item.get('canonical_id')) == provider]
        if len(matches) != 1:
            raise ValueError('materialized provider is missing or ambiguous')
        path = (stage / matches[0]['local_path']).resolve()
        if not path.is_relative_to(stage.resolve()):
            raise ValueError('materialized provider path leaves stage')
        value = path.read_bytes()
        digest = hashlib.sha256(value).hexdigest()
        if digest != matches[0].get('sha256'):
            raise ValueError('materialized provider digest does not match staged registry')
        return value.decode('utf-8'), digest

    baseline, baseline_hash = bundle(baseline_stage)
    candidate, candidate_hash = bundle(candidate_stage)
    observed = baseline_hash != candidate_hash
    for mutation in row.get('mutations', []):
        if mutation.get('scope') != 'provider_bloc':
            continue
        spec = {'schemaVersion': 1, 'family': mutation.get('family'),
                'find': mutation.get('find'), 'replace': mutation.get('replace')}
        fingerprint = hashlib.sha256(json.dumps(spec, ensure_ascii=True, sort_keys=True,
                                               separators=(',', ':')).encode('ascii')).hexdigest()
        data = [decode_managed_data(candidate, fix_id) or {} for fix_id in
                __import__('re').findall(r'/\* STARTFIX:([A-Z0-9_.-]+) \*/', candidate)
                if fix_id.startswith(f'PROVIDER.{provider.upper()}.')]
        observed = observed and any(fingerprint in item.get('brain_applied_specs', []) for item in data)
    return {'materializedMutationObserved': bool(observed),
            'baselineBundleSha256': baseline_hash, 'candidateBundleSha256': candidate_hash}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--accepted-output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    args = parser.parse_args()

    current_sha = str(args.current_sha or "").strip().casefold()
    if not SHA40.fullmatch(current_sha):
        raise SystemExit("exact 40-hex current SHA required")
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip().casefold()
    if actual != current_sha:
        raise SystemExit(f"Force sandbox SHA mismatch current={current_sha} actual={actual}")

    payload = load(args.input)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("Force mutation rows missing")
    selected = {canon(value) for value in args.provider if canon(value)}

    eligible: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        provider = canon(raw.get("providerId"))
        if not provider or (selected and provider not in selected):
            continue
        eligible.append(copy.deepcopy(raw))

    # Page-merge order is not proof order. Honor Brain's explicit candidate
    # ordinal so each provider's causal portfolio is sandboxed deterministically.
    eligible.sort(
        key=lambda row: (
            canon(row.get("providerId")),
            max(1, int(row.get("candidateOrdinal") or 999999)),
        )
    )

    report_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    accepted_providers: set[str] = set()

    if args.work_root:
        parent = args.work_root.resolve()
        owned_parent = False
    else:
        local_output_root = ROOT / "local-output"
        local_output_root.mkdir(parents=True, exist_ok=True)
        parent = Path(tempfile.mkdtemp(prefix="force-candidates-", dir=local_output_root))
        owned_parent = True
    parent.mkdir(parents=True, exist_ok=True)

    try:
        for index, row in enumerate(eligible, start=1):
            provider = canon(row.get("providerId"))
            fingerprint = str(row.get("mutationFingerprint") or "").strip().casefold()
            ordinal = max(1, int(row.get("candidateOrdinal") or index))
            if provider in accepted_providers:
                report_rows.append({
                    "provider": provider,
                    "candidateOrdinal": ordinal,
                    "mutationFingerprint": fingerprint,
                    "mutationContextFingerprint": str(row.get("mutationContextFingerprint") or "").strip().casefold(),
                    "mutationSummary": mutation_summary(row),
                    "repairFamily": row.get("repairFamily") if isinstance(row.get("repairFamily"), dict) else {},
                    "mechanismFamily": str(row.get("mechanismFamily") or "")[:160],
                    "accepted": False,
                    "executionObserved": False,
                    "reason": "skipped_after_provider_winner",
                })
                continue
            root = parent / f"{index:03d}-{provider}-h{ordinal}"
            baseline_stage = root / "baseline-stage"
            candidate_stage = root / "candidate-stage"
            baseline_out = root / "baseline-health"
            candidate_out = root / "candidate-health"
            worktree = root / "worktree"
            targets = root / "targets.json"
            row_payload = root / "force-row.json"
            apply_report = root / "apply-report.json"
            root.mkdir(parents=True, exist_ok=True)
            write_targets(targets, provider)

            stage_provider(ROOT, provider, baseline_stage, targets)
            baseline_health = health_provider(baseline_stage, baseline_out, provider)
            baseline = provider_result(baseline_health, provider)

            run("git", "worktree", "add", "--detach", str(worktree), current_sha)
            try:
                isolated = single_row_payload(payload, row)
                row_payload.write_text(
                    json.dumps(isolated, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                apply_args = [
                    sys.executable,
                    "scripts/apply_brain_llm_force_mutations.py",
                    "--input",
                    str(row_payload),
                    "--current-sha",
                    current_sha,
                    "--provider",
                    provider,
                    "--census",
                    "automation/provider-census-status.json",
                    "--report",
                    str(apply_report),
                ]
                try:
                    run(*apply_args, cwd=worktree)
                    applied = load(apply_report)
                    if int(applied.get("appliedProviderCount") or 0) != 1:
                        report_rows.append(
                            {
                                "provider": provider,
                                "candidateOrdinal": ordinal,
                                "mutationFingerprint": fingerprint,
                                "mutationContextFingerprint": str(row.get("mutationContextFingerprint") or "").strip().casefold(),
                                "mutationSummary": mutation_summary(row),
                                "repairFamily": row.get("repairFamily") if isinstance(row.get("repairFamily"), dict) else {},
                                "mechanismFamily": str(row.get("mechanismFamily") or "")[:160],
                                "accepted": False,
                                "executionObserved": False,
                                "reason": "force_candidate_not_applied",
                                "baseline": result_summary(baseline),
                                "application": applied,
                            }
                        )
                        continue

                    run(
                        sys.executable,
                        "scripts/materialize_provider_v3_one.py",
                        provider,
                        "--preserve-structured-data",
                        cwd=worktree,
                    )
                    stage_provider(worktree, provider, candidate_stage, targets)
                    proof = materialization_proof(baseline_stage, candidate_stage, provider, row)
                    if not proof['materializedMutationObserved']:
                        report_rows.append({
                            'provider': provider, 'candidateOrdinal': ordinal,
                            'mutationFingerprint': fingerprint,
                            'mutationContextFingerprint': row.get('mutationContextFingerprint'),
                            'mutationSummary': mutation_summary(row), 'accepted': False,
                            'executionObserved': False, 'reason': 'force_candidate_not_materialized',
                            **proof,
                        })
                        continue
                    candidate_health = health_provider(candidate_stage, candidate_out, provider)
                    candidate = provider_result(candidate_health, provider)
                    mechanism_family = str(row.get("mechanismFamily") or "")
                    if not mechanism_family:
                        mechanism_family = next(
                            (
                                str(mutation.get("family") or "")
                                for mutation in row.get("mutations") or []
                                if isinstance(mutation, dict) and str(mutation.get("family") or "")
                            ),
                            "",
                        )
                    accepted, reason = evaluate_pair(
                        baseline,
                        candidate,
                        mechanism_family,
                        provider,
                    )

                    result = {
                        "provider": provider,
                        "candidateOrdinal": ordinal,
                        "mutationFingerprint": fingerprint,
                        "mutationContextFingerprint": str(row.get("mutationContextFingerprint") or "").strip().casefold(),
                                "mutationSummary": mutation_summary(row),
                                "repairFamily": row.get("repairFamily") if isinstance(row.get("repairFamily"), dict) else {},
                                "mechanismFamily": str(row.get("mechanismFamily") or "")[:160],
                        "accepted": bool(accepted),
                        "executionObserved": True,
                        **proof,
                        "reason": reason,
                        "baseline": result_summary(baseline),
                        "candidate": result_summary(candidate),
                        "application": {
                            "changedFiles": applied.get("changedFiles") or [],
                            "sourceBrainLlmSha": applied.get("sourceBrainLlmSha"),
                            "sourceNiakvioSha": applied.get("sourceNiakvioSha"),
                        },
                    }
                    if require_decoded_repair():
                        # This point is reached only after materialization and
                        # both actual health executions. These fixture facts
                        # do not replace the existing runtime/identity verdict.
                        result.update(decoded_repair_gate(baseline, candidate, provider)[2])
                    report_rows.append(result)
                    if accepted:
                        accepted_rows.append(copy.deepcopy(row))
                        accepted_providers.add(provider)
                        print(
                            "FIELD_BRAIN_LLM_FORCE_PORTFOLIO_WINNER "
                            f"provider={provider} ordinal={ordinal} fingerprint={fingerprint}",
                            flush=True,
                        )
                except (subprocess.SubprocessError, ValueError, OSError) as exc:
                    # One malformed/stale Force hypothesis must never cancel
                    # the other provider sandboxes or suppress canonical FORCE.
                    report_rows.append(
                        {
                            "provider": provider,
                            "candidateOrdinal": ordinal,
                            "mutationFingerprint": fingerprint,
                            "mutationContextFingerprint": str(row.get("mutationContextFingerprint") or "").strip().casefold(),
                                "mutationSummary": mutation_summary(row),
                                "repairFamily": row.get("repairFamily") if isinstance(row.get("repairFamily"), dict) else {},
                                "mechanismFamily": str(row.get("mechanismFamily") or "")[:160],
                            "accepted": False,
                            "executionObserved": False,
                            "reason": "force_candidate_execution_error",
                            "baseline": result_summary(baseline),
                            "error": candidate_execution_error(exc),
                        }
                    )
                    continue
            finally:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=ROOT,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

        accepted_payload = {
            key: copy.deepcopy(value)
            for key, value in payload.items()
            if key != "rows"
        }
        accepted_payload["rows"] = accepted_rows
        accepted_payload["providerCount"] = len(
            {canon(row.get("providerId")) for row in accepted_rows}
        )

        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.accepted_output.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "currentSha": current_sha,
                    "sourceNiakvioSha": str(payload.get("sourceNiakvioSha") or "").strip().casefold(),
                    "sourceBrainLlmSha": str(payload.get("brainLlmSha") or "").strip().casefold(),
                    "candidateCount": len(eligible),
                    "acceptedProviderCount": len(accepted_rows),
                    "acceptedProviders": [
                        canon(row.get("providerId")) for row in accepted_rows
                    ],
                    "rows": report_rows,
                    "publicationAuthority": False,
                    "proofAuthority": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        args.accepted_output.write_text(
            json.dumps(accepted_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            "FIELD_BRAIN_LLM_FORCE_SANDBOX "
            f"candidates={len(eligible)} accepted={len(accepted_rows)} "
            f"providers={','.join(canon(row.get('providerId')) for row in accepted_rows) or '-'}"
        )
        return 0
    finally:
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if owned_parent:
            shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
