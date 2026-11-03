#!/usr/bin/env python3
"""Compare fixed titles using exact published bytes and strict media facts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import evaluate_brain_llm_force_candidates as verifier

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = ('animevostfr', 'anime-sama', 'french-manga', 'neko-sama', 'voiranime',
             'voiranime-homes', 'allanime', 'animekai', '4khdhub')
FIXTURES = ('95479', '280049')
LABELS = {'95479': 'Jujutsu Kaisen S01E01', '280049': 'Hell Mode S01E01'}
BOOL_FIELDS = ('playback_verified', 'payload_verified', 'direct_signature_verified',
               'variant_reachable', 'segment_reachable', 'audio_manifest_reachable',
               'audio_segment_reachable', 'duration_identity_authoritative',
               'duration_identity_mismatch', 'short_vod_preview')
IDENTITY_REASONS = {'forbidden_title_alias', 'media_filename_title_mismatch', 'strong_title_mismatch',
                    'movie_row_is_episode', 'wrong_season_episode', 'season_episode_match',
                    'wrong_episode', 'episode_match', 'expected_title_alias',
                    'insufficient_identity_metadata', 'fixture_duration_match',
                    'fixture_duration_mismatch'}
CATEGORIES = {'playable', 'content_identity_mismatch', 'duration_identity_mismatch', 'short_vod_preview',
              'blocked', 'not_found', 'host_down', 'http_error', 'invalid_payload',
              'endpoint_reachable', 'timeout', 'network_error', 'dns_error', 'tls_error',
              'disallowed_or_invalid_url'}


def number(value, maximum):
    return value if type(value) in (int, float) and 0 <= value <= maximum and math.isfinite(value) else None


def count(value):
    return min(value, 10000) if type(value) is int and value >= 0 else 0


def safe_host(value):
    return value.lower() if isinstance(value, str) and re.fullmatch(
        r'(?=.{1,160}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', value) else None


def network_evidence(value):
    events = value if isinstance(value, list) else []
    events = [row for row in events if isinstance(row, dict) and not row.get('infrastructure')]
    # Media facts and rejected responses explain zero-stream results even when
    # the runtime removes their streams before the external health probe.
    events.sort(key=lambda row: (row.get('stage') == 'media',
                type(row.get('status')) is int and row['status'] >= 400), reverse=True)
    output = []
    for row in events[:24]:
        item = {'host': safe_host(row.get('host')),
                'stage': row.get('stage') if row.get('stage') in
                    ('search', 'content_lookup', 'episode', 'player', 'media', 'source', 'catalog') else 'unknown',
                'status': row.get('status') if type(row.get('status')) is int
                    and 100 <= row['status'] <= 599 else None}
        media = row.get('media_observation')
        if isinstance(media, dict):
            item['mediaObservation'] = {
                'signature': media.get('signature') if media.get('signature') in
                    ('unknown', 'mp4', 'ebml', 'mpegts', 'hls', 'html') else 'unknown',
                'durationSeconds': number(media.get('durationSeconds'), 1209600),
                'bytesSampled': min(media['bytesSampled'], 65536)
                    if type(media.get('bytesSampled')) is int and media['bytesSampled'] >= 0 else 0,
                'readState': media.get('readState') if media.get('readState') in
                    ('not_read', 'data', 'empty', 'complete', 'error') else 'not_read',
                'cancelState': media.get('cancelState') if media.get('cancelState') in
                    ('not_requested', 'requested', 'complete', 'error') else 'not_requested'}
        output.append(item)
    return output


def public_probe(value, expected_seconds=1440):
    """Revalidate a narrow contract; a successful endpoint alone has no authority."""
    value = value if isinstance(value, dict) else {}
    result = {key: value.get(key) if type(value.get(key)) is bool else None for key in BOOL_FIELDS}
    result.update({
        'kind': value.get('kind') if value.get('kind') in ('mp4', 'matroska', 'mpegts', 'hls', 'dash', 'html', 'json', 'empty', 'unknown') else 'unknown',
        'http_status': value.get('http_status') if type(value.get('http_status')) is int
            and 100 <= value['http_status'] <= 599 else None,
        'bytes_sampled': count(value.get('bytes_sampled')),
        'media_duration_seconds': number(value.get('media_duration_seconds'), 1209600),
        'expected_duration_seconds': number(value.get('expected_duration_seconds'), 1209600),
        'content_identity_status': value.get('content_identity_status')
            if value.get('content_identity_status') in ('match', 'unknown', 'contradiction') else 'unknown',
        'content_identity_reason': value.get('content_identity_reason')
            if isinstance(value.get('content_identity_reason'), str) and value['content_identity_reason'] in IDENTITY_REASONS else 'unknown',
        'category': value.get('category') if isinstance(value.get('category'), str)
            and value['category'] in CATEGORIES else 'unknown',
    })
    # Sample bytes are bounded counters, not content. Preserve the configured
    # 512 KiB prefix size rather than the smaller stream-count counter bound.
    result['bytes_sampled'] = min(value['bytes_sampled'], 1048576) \
        if type(value.get('bytes_sampled')) is int and value['bytes_sampled'] >= 0 else 0
    result['host'] = safe_host(value.get('host'))
    decode = value.get('media_decode') if isinstance(value.get('media_decode'), dict) else {}
    frames = decode.get('framesDecoded')
    outcome = decode.get('outcome')
    result['mediaDecode'] = {
        'attempted': decode.get('attempted') is True,
        'outcome': outcome if isinstance(outcome, str) and outcome in
            ('decoded', 'failed', 'timeout', 'unavailable', 'unsupported') else 'unsupported',
        'framesDecoded': 1 if type(frames) is int and frames >= 1 else 0,
    }
    result['identityBasis'] = ('duration_only' if result['content_identity_reason'] == 'fixture_duration_match'
        else 'metadata' if result['content_identity_status'] == 'match' else 'unknown')
    duration = result['media_duration_seconds']
    transport = (result['kind'] in ('mp4', 'matroska') and result['direct_signature_verified'] is True) or (
        result['kind'] == 'hls' and result['variant_reachable'] is True
        and result['segment_reachable'] is True and result['audio_manifest_reachable'] is not False
        and result['audio_segment_reachable'] is not False)
    result['passedMediaControl'] = bool(
        result['playback_verified'] is True and result['payload_verified'] is True
        and result['content_identity_status'] == 'match'
        and result['duration_identity_authoritative'] is True
        and result['duration_identity_mismatch'] is False and result['short_vod_preview'] is False
        and result['expected_duration_seconds'] == expected_seconds
        and duration is not None and duration >= 60
        and 0.55 <= duration / expected_seconds <= 1.8
        and result['http_status'] is not None and 200 <= result['http_status'] < 300
        and result['bytes_sampled'] > 0 and transport
        and result['mediaDecode'] == {'attempted': True, 'outcome': 'decoded', 'framesDecoded': 1})
    return result


def control_fixtures(provider):
    if provider == '4khdhub':
        return [('movie', '157336', None, None, 169, 'Interstellar'),
                ('tv', '1396', 1, 1, 58, 'Breaking Bad S01E01')]
    return [('anime', tmdb_id, 1, 1, 24, LABELS[tmdb_id]) for tmdb_id in FIXTURES]


def comparison_config(original, provider='anime-sama'):
    config = copy.deepcopy(original)
    chosen = {'anime': [], 'movie': [], 'tv': [], 'anime_movie': []}
    for category, tmdb_id, season, episode, minutes, _label in control_fixtures(provider):
        matching = [row for row in original.get('fixtures', {}).get(category, [])
                    if str(row.get('tmdbId')) == tmdb_id
                    and row.get('season') == season and row.get('episode') == episode]
        if len(matching) != 1 or matching[0].get('expectedDurationMinutes') != minutes:
            raise ValueError('fixture_contract')
        chosen[category].append(copy.deepcopy(matching[0]))
    config['fixtures'] = chosen
    config['concurrency'] = 1
    config.setdefault('modes', {}).setdefault('deep', {}).update({
        'fixture_limit': 2, 'fixture_limit_per_category': True,
        'primary_fixture_limit_per_category': 2, 'fallback_fixture_limit': 0,
        'fallback_fixture_limit_per_category': 0, 'probe_streams_adaptively': False,
        'provider_timeout_ms': 70000, 'stream_probe_timeout_ms': 18000,
        'max_streams_to_probe': 3, 'sample_bytes': 524288,
        'probe_best_variant': True, 'probe_first_segment': True,
        'inspect_direct_dimensions': True, 'verify_fixture_duration_identity': True,
        'minimum_fixture_duration_ratio': 0.55, 'maximum_fixture_duration_ratio': 1.8,
        'minimum_vod_duration_seconds': 60, 'reader_user_agent_probe': False,
        'observed_media_probe': False,
        'verify_media_decode': True,
    })
    return config


def staged_hash(provider, stage, repo_root=ROOT):
    registry = verifier.load(stage / 'candidates.json')
    candidates = [row for row in registry.get('candidates', [])
                  if verifier.canon(row.get('canonical_id')) == provider]
    manifest = verifier.load(repo_root / 'manifest.json')
    entries = [row for row in manifest.get('scrapers', [])
               if verifier.canon(row.get('id')) == provider and row.get('enabled') is True]
    if len(candidates) != 1 or len(entries) != 1:
        raise ValueError('published_provider_contract')
    staged = (stage / candidates[0]['local_path']).resolve()
    published = (repo_root / entries[0]['filename']).resolve()
    if not staged.is_relative_to(stage.resolve()) or not published.is_relative_to((repo_root / 'providers').resolve()):
        raise ValueError('published_provider_path')
    data = staged.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    suffix = re.search(r'-([0-9a-f]{16})\.js$', published.name)
    if (digest != candidates[0].get('sha256') or data != published.read_bytes()
            or not suffix or digest[:16] != suffix[1]):
        raise ValueError('published_provider_hash')
    return digest


def public_report(provider, source_sha, bundle_sha, result):
    tests = result.get('tests') if isinstance(result, dict) else None
    if not isinstance(tests, list):
        raise ValueError('health_fixture_contract')
    fixtures = []
    for _category, tmdb_id, season, episode, minutes, label in control_fixtures(provider):
        matches = [test for test in tests if isinstance(test, dict)
                   and str((test.get('fixture') or {}).get('tmdbId')) == tmdb_id
                   and (test.get('fixture') or {}).get('season') == season
                   and (test.get('fixture') or {}).get('episode') == episode]
        if len(matches) != 1:
            raise ValueError('health_fixture_contract')
        test = matches[0]
        raw = test.get('host_results') if isinstance(test.get('host_results'), list) else []
        probes = [public_probe(row, minutes * 60) for row in raw[:3] if isinstance(row, dict)]
        fixtures.append({'fixture': label, 'tmdbId': tmdb_id, 'season': season, 'episode': episode,
            'expectedDurationSeconds': minutes * 60, 'streamsReturned': count(test.get('streams_returned')),
            'streamsPlayable': count(test.get('streams_playable')), 'streamsProbed': count(test.get('streams_probed')),
            'passedMediaControl': count(test.get('streams_returned')) > 0
                and count(test.get('streams_playable')) > 0 and count(test.get('streams_probed')) > 0
                and any(row['passedMediaControl'] for row in probes), 'probes': probes,
            'status': test.get('status') if test.get('status') in
                ('healthy', 'reachable', 'blocked', 'degraded', 'no_streams', 'provider_unreachable',
                 'runtime_error', 'unavailable', 'excluded') else 'unknown',
            'failureClass': test.get('failure_class') if test.get('failure_class') in
                ('content_lookup_completed_no_streams', 'provider_returned_no_streams',
                 'provider_network_zero_result', 'stream_not_playback_verified',
                 'content_identity_mismatch', 'duration_identity_mismatch', 'short_vod_preview',
                 'provider_timeout', 'provider_runtime_error', 'provider_network_http_error',
                 'provider_network_exception', 'provider_waf_challenge') else 'unknown',
            'networkEvidence': network_evidence(test.get('network_observations'))})
    return {'schemaVersion': 1, 'providerId': provider, 'sourceNiakvioSha': source_sha,
            'bundleSha256': bundle_sha, 'executionSucceeded': True,
            'passedMediaControl': any(row['passedMediaControl'] for row in fixtures),
            'fixtures': fixtures, 'publicationAuthority': False}


def run_check(provider, output, repo_root=None):
    repo_root = (repo_root or ROOT).resolve()
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_root, text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', source_sha):
        raise ValueError('source_sha_contract')
    bundle_sha = None
    try:
        work = output.resolve().parent / ('cross-provider-' + provider)
        work.mkdir(parents=True, exist_ok=True)
        targets, stage, health = work / 'targets.json', work / 'stage', work / 'health'
        verifier.write_targets(targets, provider)
        verifier.stage_provider(repo_root, provider, stage, targets)
        bundle_sha = staged_hash(provider, stage, repo_root)
        config = comparison_config(verifier.load(repo_root / 'health-config.json'), provider)
        config_path = work / 'comparison-health-config.json'
        config_path.write_text(json.dumps(config, indent=2) + '\n')
        report = verifier.deep.run_health(stage=stage, registry_path=stage / 'candidates.json',
            output_dir=health, mode='deep', health_check=ROOT / 'scripts' / 'health_check.mjs',
            health_config=config_path)
        result = verifier.provider_result(report, provider)
        # Runtime execution must not modify the bytes that were selected.
        if staged_hash(provider, stage, repo_root) != bundle_sha:
            raise ValueError('published_provider_hash')
        return public_report(provider, source_sha, bundle_sha, result)
    except Exception as exc:
        # Error messages may contain response data or transport credentials.
        code = 'command_failed' if isinstance(exc, subprocess.CalledProcessError) else {
            ValueError: 'contract_error', OSError: 'filesystem_error',
            json.JSONDecodeError: 'invalid_json', KeyError: 'contract_error',
        }.get(type(exc), 'execution_error')
        return {'schemaVersion': 1, 'providerId': provider, 'sourceNiakvioSha': source_sha,
                'bundleSha256': bundle_sha, 'executionSucceeded': False,
                'passedMediaControl': False, 'fixtures': [], 'errorCode': code,
                'publicationAuthority': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', choices=PROVIDERS, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    args = parser.parse_args()
    report = run_check(args.provider, args.output, args.repo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('CROSS_PROVIDER_REPORT=' + json.dumps(report, separators=(',', ':')))
    return 0 if report['executionSucceeded'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
