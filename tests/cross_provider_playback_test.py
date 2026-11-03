#!/usr/bin/env python3
"""Strict media controls must reject short, refused or incomplete endpoints."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('cross_provider', ROOT / 'scripts/check_cross_provider_playback.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def good(kind='mp4'):
    return {'host': 'media.example.com', 'http_status': 206, 'kind': kind, 'bytes_sampled': 32768,
            'playback_verified': True, 'payload_verified': True, 'direct_signature_verified': True,
            'variant_reachable': True, 'segment_reachable': True,
            'audio_manifest_reachable': None, 'audio_segment_reachable': None,
            'content_identity_status': 'match', 'content_identity_reason': 'season_episode_match',
            'media_duration_seconds': 1440, 'expected_duration_seconds': 1440,
            'duration_identity_authoritative': True, 'duration_identity_mismatch': False,
            'short_vod_preview': False,
            'media_decode': {'attempted': True, 'outcome': 'decoded', 'framesDecoded': 1}}


class CrossProviderTests(unittest.TestCase):
    def test_movie_tv_profile_uses_exact_expected_titles_and_durations(self):
        original = json.loads((ROOT / 'health-config.json').read_text())
        selected = mod.comparison_config(original, '4khdhub')
        self.assertEqual([str(row['tmdbId']) for row in selected['fixtures']['movie']], ['157336'])
        self.assertEqual([str(row['tmdbId']) for row in selected['fixtures']['tv']], ['1396'])
        self.assertEqual(selected['fixtures']['anime'], [])
        self.assertTrue(selected['modes']['deep']['verify_media_decode'])
        bad = copy.deepcopy(original)
        next(row for row in bad['fixtures']['movie'] if str(row['tmdbId']) == '157336')['expectedDurationMinutes'] = 24
        with self.assertRaises(ValueError):
            mod.comparison_config(bad, '4khdhub')
        self.assertEqual(original, json.loads((ROOT / 'health-config.json').read_text()))

    def test_movie_tv_controls_reject_refused_short_and_wrong_duration_media(self):
        tests = []
        for _category, tmdb, season, episode, minutes, _label in mod.control_fixtures('4khdhub'):
            probe = {**good(), 'expected_duration_seconds': minutes * 60,
                     'media_duration_seconds': minutes * 60}
            tests.append({'fixture': {'tmdbId': tmdb, 'season': season, 'episode': episode},
                          'streams_returned': 1, 'streams_playable': 1, 'streams_probed': 1,
                          'host_results': [probe]})
        report = mod.public_report('4khdhub', 'a' * 40, 'b' * 64, {'tests': tests})
        self.assertEqual([row['expectedDurationSeconds'] for row in report['fixtures']], [10140, 3480])
        self.assertTrue(all(row['passedMediaControl'] for row in report['fixtures']))
        for change in ({'http_status': 403}, {'media_duration_seconds': 5},
                       {'expected_duration_seconds': 1440}, {'media_decode': {}}):
            bad = copy.deepcopy(tests)
            for row in bad:
                row['host_results'][0].update(change)
            report = mod.public_report('4khdhub', 'a' * 40, 'b' * 64, {'tests': bad})
            self.assertFalse(report['passedMediaControl'], change)

    def test_real_media_contract_and_boundaries(self):
        for kind in ('mp4', 'matroska', 'hls'):
            self.assertTrue(mod.public_probe(good(kind))['passedMediaControl'])
        for duration in (792, 2592):
            self.assertTrue(mod.public_probe({**good(), 'media_duration_seconds': duration})['passedMediaControl'])
        failures = [{'media_duration_seconds': value} for value in (5, 0, None, True, float('nan'), 791, 2593)]
        failures += [{'http_status': 403}, {'kind': 'dash'}, {'kind': 'mpegts'},
                     {'content_identity_status': 'unknown'}, {'content_identity_status': 'contradiction'},
                     {'direct_signature_verified': False}, {'bytes_sampled': 0},
                     {'expected_duration_seconds': 5}, {'duration_identity_authoritative': False},
                     {'duration_identity_mismatch': True}, {'short_vod_preview': True},
                     {'playback_verified': 1}, {'payload_verified': False}]
        failures += [{'media_decode': value} for value in (None, {},
            {'attempted': True, 'outcome': 'failed', 'framesDecoded': 0},
            {'attempted': False, 'outcome': 'decoded', 'framesDecoded': 1},
            {'attempted': True, 'outcome': 'decoded', 'framesDecoded': True})]
        for changed in failures:
            with self.subTest(changed=changed):
                self.assertFalse(mod.public_probe({**good(), **changed})['passedMediaControl'])
        duration_only = mod.public_probe({**good(), 'content_identity_reason': 'fixture_duration_match'})
        self.assertTrue(duration_only['passedMediaControl'])
        self.assertEqual(duration_only['identityBasis'], 'duration_only')

    def test_hls_requires_variant_and_segment_and_no_failed_audio(self):
        for field in ('variant_reachable', 'segment_reachable'):
            for value in (False, None, 1):
                self.assertFalse(mod.public_probe({**good('hls'), field: value})['passedMediaControl'])
        for field in ('audio_manifest_reachable', 'audio_segment_reachable'):
            self.assertFalse(mod.public_probe({**good('hls'), field: False})['passedMediaControl'])

    def test_report_distinguishes_execution_from_media_and_hides_private_fields(self):
        tests = []
        for fixture in mod.FIXTURES:
            tests.append({'fixture': {'tmdbId': fixture, 'season': 1, 'episode': 1},
                          'streams_returned': 4, 'streams_playable': 4, 'streams_probed': 1,
                          'host_results': [{**good(), 'http_status': 403,
                              'url': 'PRIVATE_URL', 'headers': {'Cookie': 'PRIVATE_COOKIE'},
                              'body': 'PRIVATE_BODY', 'category': 'PRIVATE_CATEGORY',
                              'content_identity_reason': 'PRIVATE_REASON'}]})
        report = mod.public_report('anime-sama', 'a' * 40, 'b' * 64, {'tests': tests, 'private': 'PRIVATE'})
        self.assertTrue(report['executionSucceeded'])
        self.assertFalse(report['passedMediaControl'])
        self.assertFalse(any(row['passedMediaControl'] for row in report['fixtures']))
        self.assertNotIn('PRIVATE', json.dumps(report))
        tests[0]['host_results'] = [good()]
        report = mod.public_report('anime-sama', 'a' * 40, 'b' * 64, {'tests': tests})
        self.assertTrue(report['fixtures'][0]['passedMediaControl'])
        self.assertFalse(report['fixtures'][1]['passedMediaControl'])
        tests[0]['streams_returned'] = 0
        report = mod.public_report('anime-sama', 'a' * 40, 'b' * 64, {'tests': tests})
        self.assertFalse(report['fixtures'][0]['passedMediaControl'])
        self.assertRaises(ValueError, mod.public_report, 'anime-sama', 'a' * 40, 'b' * 64, {'tests': tests[:1]})

    def test_zero_stream_evidence_retains_short_media_and_refusal_without_inputs(self):
        events = [{'host': 'site.example.com', 'stage': 'search', 'status': 200}] * 30
        events += [{'host': 'media.example.com', 'stage': 'media', 'status': 206,
                    'url': 'PRIVATE_URL', 'headers': {'Cookie': 'PRIVATE_COOKIE'},
                    'media_observation': {'signature': 'mp4', 'durationSeconds': 5,
                        'bytesSampled': 32768, 'readState': 'data', 'cancelState': 'complete',
                        'body': 'PRIVATE_BODY'}},
                   {'host': 'reader.example.com', 'stage': 'player', 'status': 403, 'body': 'PRIVATE_BODY'}]
        projected = mod.network_evidence(events)
        self.assertEqual(len(projected), 24)
        self.assertEqual(projected[0]['mediaObservation']['durationSeconds'], 5)
        self.assertEqual(projected[1]['status'], 403)
        self.assertNotIn('PRIVATE', json.dumps(projected))

    def test_fixed_comparison_config_without_rotation_or_fallback(self):
        original = mod.verifier.load(ROOT / 'health-config.json')
        before = copy.deepcopy(original)
        config = mod.comparison_config(original)
        self.assertEqual(original, before)
        self.assertEqual([str(row['tmdbId']) for row in config['fixtures']['anime']], list(mod.FIXTURES))
        self.assertEqual(config['fixtures']['movie'], [])
        mode = config['modes']['deep']
        self.assertEqual(mode['primary_fixture_limit_per_category'], 2)
        self.assertEqual(mode['fallback_fixture_limit_per_category'], 0)
        self.assertFalse(mode['probe_streams_adaptively'])
        self.assertEqual(mode['max_streams_to_probe'], 3)
        self.assertEqual(mode['provider_timeout_ms'], 70000)
        self.assertEqual(mode['stream_probe_timeout_ms'], 18000)

    def test_staged_bytes_match_registry_and_current_published_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); stage = root / 'stage'; providers = root / 'providers'
            stage.mkdir(); providers.mkdir()
            data = b'published provider bytes'; digest = hashlib.sha256(data).hexdigest()
            filename = 'providers/anime-sama-' + digest[:16] + '.js'
            (root / filename).write_bytes(data); (stage / 'provider.js').write_bytes(data)
            (root / 'manifest.json').write_text(json.dumps({'scrapers': [
                {'id': 'ANIME-SAMA', 'enabled': True, 'filename': filename}]}))
            (stage / 'candidates.json').write_text(json.dumps({'candidates': [
                {'canonical_id': 'anime-sama', 'local_path': 'provider.js', 'sha256': digest}]}))
            self.assertEqual(mod.staged_hash('anime-sama', stage, root), digest)
            (stage / 'provider.js').write_bytes(b'mutated')
            self.assertRaises(ValueError, mod.staged_hash, 'anime-sama', stage, root)


if __name__ == '__main__':
    unittest.main()
