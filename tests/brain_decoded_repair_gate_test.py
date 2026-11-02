#!/usr/bin/env python3
"""A repair needs a new decoded fixture control, without losing working cases."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import evaluate_brain_llm_force_candidates as verifier


def good_probe(**changes):
    value = {
        'host': 'media.example.com', 'http_status': 200, 'kind': 'hls',
        'bytes_sampled': 1024, 'playback_verified': True, 'payload_verified': True,
        'direct_signature_verified': False, 'variant_reachable': True,
        'segment_reachable': True, 'audio_manifest_reachable': True,
        'audio_segment_reachable': True, 'duration_identity_authoritative': True,
        'duration_identity_mismatch': False, 'short_vod_preview': False,
        'media_duration_seconds': 1435, 'expected_duration_seconds': 1440,
        'content_identity_status': 'match', 'content_identity_reason': 'fixture_duration_match',
        'media_decode': {'attempted': True, 'outcome': 'decoded', 'framesDecoded': 1},
    }
    value.update(changes)
    return value


def fixture(tmdb, probes=None, count=None):
    probes = probes or []
    count = len(probes) if count is None else count
    return {
        'fixture': {'label': verifier.DECODED_REPAIR_FIXTURES[tmdb], 'category': 'anime',
                    'tmdbId': tmdb, 'season': 1, 'episode': 1, 'expectedDurationMinutes': 24},
        'status': 'healthy' if count else 'no_streams',
        'streams_returned': count, 'streams_playable': count, 'streams_probed': len(probes),
        'identity_verified_streams': count, 'identity_unverified_streams': 0,
        'identity_contradiction_count': 0, 'duration_identity_mismatch_count': 0,
        'host_results': probes,
    }


def result(jjk=None, hell=None):
    tests = [fixture('95479', jjk), fixture('280049', hell)]
    total = sum(test['streams_playable'] for test in tests)
    return {'status': 'healthy' if total else 'no_streams', 'score': 90 if total else 0,
            'evidence': {'streams_playable': total, 'streams_returned': total,
                'identity_verified_streams': total, 'identity_unverified_streams': 0,
                'identity_contradiction_count': 0, 'duration_identity_mismatch_count': 0,
                'required_fixture_categories': ['anime'],
                'healthy_fixture_categories': ['anime'] if total else []}, 'tests': tests}


class DecodedRepairGateTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'NIAKVIO_REQUIRE_DECODE_PROOF': '1'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_partial_improvement_is_useful_but_reports_unresolved_fixture(self):
        baseline, candidate = result(), result([good_probe()])
        self.assertEqual(verifier.evaluate_pair(baseline, candidate),
                         (True, 'strict_playable_stream_improvement'))
        ok, reason, facts = verifier.decoded_repair_gate(baseline, candidate)
        self.assertTrue(ok, reason)
        self.assertEqual(facts['improvedFixtures'], ['Jujutsu Kaisen S01E01'])
        self.assertEqual(facts['unresolvedFixtures'], ['Hell Mode S01E01'])
        self.assertTrue(facts['decodedProofRequired'])
        both = result([good_probe()], [good_probe()])
        self.assertTrue(verifier.evaluate_pair(baseline, both)[0])
        self.assertEqual(verifier.decoded_repair_gate(baseline, both)[2]['unresolvedFixtures'], [])

    def test_five_seconds_403_unknown_duration_and_missing_decode_never_gain(self):
        changes = [
            {'media_duration_seconds': 5}, {'http_status': 403},
            {'media_duration_seconds': None}, {'media_decode': None},
            {'media_decode': {'attempted': True, 'outcome': 'failed', 'framesDecoded': 0}},
            {'media_decode': {'attempted': True, 'outcome': 'decoded', 'framesDecoded': True}},
            {'segment_reachable': False}, {'content_identity_status': 'contradiction'},
        ]
        for changed in changes:
            with self.subTest(changed=changed):
                candidate = result([good_probe(**changed)])
                for family in ('', 'bounded-variant-enumeration-before-cap'):
                    accepted, reason = verifier.evaluate_pair(result(), candidate, family)
                    self.assertFalse(accepted)
                    self.assertEqual(reason, 'decoded_repair_no_new_fixture_control')
        for counter in ('streams_returned', 'streams_playable', 'streams_probed'):
            candidate = result([good_probe()])
            candidate['tests'][0][counter] = 0
            self.assertFalse(verifier.evaluate_pair(result(), candidate)[0])

    def test_aggregate_gain_cannot_hide_loss_of_working_fixture_or_control(self):
        baseline = result(hell=[good_probe()])
        candidate = result([good_probe(), good_probe(), good_probe()])
        self.assertGreater(candidate['evidence']['streams_playable'], baseline['evidence']['streams_playable'])
        self.assertEqual(verifier.evaluate_pair(baseline, candidate),
                         (False, 'decoded_repair_fixture_regression:280049'))
        self.assertTrue(verifier.evaluate_pair(baseline,
            result([good_probe()], [good_probe()]))[0])
        # Preserved broad health counters cannot hide a lost decoded control.
        old = result(hell=[good_probe(), good_probe()])
        new = result([good_probe()], [good_probe(), good_probe(media_decode=None)])
        self.assertEqual(verifier.evaluate_pair(old, new),
                         (False, 'decoded_repair_fixture_regression:280049'))
        same = result([good_probe()])
        self.assertEqual(verifier.evaluate_pair(same, copy.deepcopy(same)),
                         (False, 'decoded_repair_no_new_fixture_control'))

    def test_exact_fixture_identity_is_required_in_both_executions(self):
        baseline, candidate = result(), result([good_probe()])
        invalid = [({'episode': 2}), ({'season': True}), ({'tmdbId': '40748'}),
                   ({'expectedDurationMinutes': 5}), ({'category': 'tv'})]
        for changed in invalid:
            for side in ('baseline', 'candidate'):
                before, after = copy.deepcopy(baseline), copy.deepcopy(candidate)
                target = before if side == 'baseline' else after
                target['tests'][0]['fixture'].update(changed)
                with self.subTest(side=side, changed=changed):
                    self.assertEqual(verifier.evaluate_pair(before, after),
                                     (False, 'decoded_repair_fixture_contract'))
        for missing in ([], [candidate['tests'][0]], [candidate['tests'][0]] * 2):
            self.assertEqual(verifier.evaluate_pair(baseline, {**candidate, 'tests': missing}),
                             (False, 'decoded_repair_fixture_contract'))
            facts = verifier.decoded_repair_gate(baseline, {**candidate, 'tests': missing})[2]
            self.assertEqual(facts['improvedFixtures'], [])
            self.assertEqual(facts['unresolvedFixtures'], list(verifier.DECODED_REPAIR_FIXTURES.values()))

    def test_decoding_does_not_create_identity_authority_and_reports_are_safe(self):
        candidate = result([good_probe(url='PRIVATE_URL', headers={'Cookie': 'PRIVATE_HEADER'},
            body='PRIVATE_BODY', media_decode={'attempted': True, 'outcome': 'decoded',
                                             'framesDecoded': 1, 'raw': 'PRIVATE_PROGRESS'})])
        summary = verifier.result_summary(candidate)
        coverage = summary['fixtureCoverage'][0]
        self.assertEqual(coverage['decodedMediaControls'], 1)
        self.assertEqual(coverage['decodedMediaProbes'][0]['identityBasis'], 'duration_only')
        self.assertEqual(coverage['decodedMediaProbes'][0]['mediaDecode'],
                         {'attempted': True, 'outcome': 'decoded', 'framesDecoded': 1})
        self.assertNotIn('PRIVATE', json.dumps(summary))
        self.assertEqual(summary['fixtureCoverage'][1]['decodedMediaControls'], 0)
        self.assertEqual(coverage['tmdbId'], '95479')
        self.assertEqual(coverage['expectedDurationSeconds'], 1440)
        # A decoded frame must still pass the existing positive-identity gate;
        # this new evidence cannot fill missing identity counters itself.
        candidate['evidence']['identity_verified_streams'] = 0
        candidate['evidence']['identity_unverified_streams'] = 1
        candidate['tests'][0]['identity_verified_streams'] = 0
        candidate['tests'][0]['identity_unverified_streams'] = 1
        accepted, reason = verifier.evaluate_pair(result(), candidate)
        self.assertFalse(accepted)
        self.assertEqual(reason, 'identity_gate:no_positive_content_identity_proof')

    def test_explicit_mode_uses_symmetric_fixed_decode_config_without_mutating_defaults(self):
        original = verifier.load(ROOT / 'health-config.json')
        seen = []
        def health(**options):
            config = verifier.load(options['health_config'])
            seen.append(config)
            mode = config['modes']['deep']
            self.assertTrue(mode['verify_media_decode'])
            self.assertEqual(mode['primary_fixture_limit_per_category'], 2)
            self.assertFalse(mode['probe_streams_adaptively'])
            self.assertEqual(mode['fallback_fixture_limit_per_category'], 0)
            self.assertEqual([str(row['tmdbId']) for row in config['fixtures']['anime']],
                             ['95479', '280049'])
            self.assertEqual(config['fixtures']['movie'], [])
            self.assertEqual(config['fixtures']['tv'], [])
            return {'results': []}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(verifier.deep, 'run_health', side_effect=health):
            root = Path(directory)
            verifier.health_provider(root / 'base', root / 'before')
            verifier.health_provider(root / 'candidate', root / 'after')
        self.assertEqual(seen[0], seen[1])
        self.assertEqual(original, verifier.load(ROOT / 'health-config.json'))
        with patch.dict(os.environ, {'NIAKVIO_REQUIRE_DECODE_PROOF': '0'}):
            # A default legacy comparison is not silently put behind the new
            # fixed-fixture gate; its existing runtime/identity gates still run.
            accepted, reason = verifier.evaluate_pair(result(), result([good_probe(media_decode=None)]))
            self.assertTrue(accepted, reason)


if __name__ == '__main__':
    unittest.main()
