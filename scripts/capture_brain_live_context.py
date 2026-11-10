#!/usr/bin/env python3
"""Observe current provider bytes before model synthesis, without editing them."""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path
import evaluate_brain_llm_force_candidates as verifier
from http_response_evidence import public_http_observation, public_reader_probe, public_network_error_code
from address_reference_evidence import public_address_fields, address_scope
from observed_media_evidence import public_observed_media_probe


def script_shell_only(events):
    replies = [event for event in events if event.get('ok') and event.get('response_structure')]
    return bool(replies) and all(
        shape.get('kind') == 'html' and shape.get('variables')
        and {tag.get('tag') for tag in shape.get('tags', [])} == {'script'}
        for shape in (event['response_structure'] for event in replies)
    )

def provider_owned_function_names(stage, provider):
    registry = verifier.load(stage / 'candidates.json')
    matches = [row for row in registry.get('candidates', [])
               if verifier.canon(row.get('canonical_id')) == provider]
    if len(matches) != 1:
        raise ValueError('provider execution source missing or ambiguous')
    path = (stage / matches[0]['local_path']).resolve()
    if not path.is_relative_to(stage.resolve()):
        raise ValueError('provider execution source leaves its stage')
    source = path.read_text()
    for marker in ('/* STARTFIX:CORE.', '/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */'):
        source = source.split(marker, 1)[0]
    return set(re.findall(r'\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(', source))


def diverse_execution_events(events):
    """Keep distinct response shapes ahead of repeated fallback requests.

    Return every event so truncation accounting still covers omitted addresses.
    The existing failure/media order decides which event represents each shape.
    """
    distinct, repeated, seen = [[], []], [[], []], set()
    for event in events:
        shape = event.get('response_structure') or {}
        fields = tuple(sorted((str(field.get('path')), str(field.get('type')))
                              for field in shape.get('fields', [])[:48]
                              if isinstance(field, dict)))
        html = json.dumps({key: shape[key] for key in
                           ('tags', 'variables', 'inline_fields', 'script_resources')
                           if key in shape}, sort_keys=True)
        group = 0 if event.get('fixture_failed') else 1
        signature = (str(event.get('fixture_label')), str(event.get('host')),
                     str(event.get('stage')), str(event.get('status')),
                     str(event.get('error_code')), str(shape.get('kind')), fields, html, group)
        if signature in seen:
            repeated[group].append(event)
        else:
            seen.add(signature)
            distinct[group].append(event)
    return distinct[0] + repeated[0] + distinct[1] + repeated[1]


def prioritized_execution(result, owned_names=None):
    events = [{**event, 'fixture_label': (test.get('fixture') or {}).get('label'), 'observation_index': index,
               'fixture_failed': int(test.get('streams_playable') or 0) == 0}
              for test in result.get('tests', []) for index, event in enumerate(test.get('network_observations', []))
              if isinstance(event, dict) and not event.get('infrastructure')]
    events.sort(key=lambda row: (
        bool(row['fixture_failed']), {'media': 4, 'source': 3, 'player': 2, 'episode': 1}.get(str(row.get('stage')), 0),
        row['observation_index'],
    ), reverse=True)
    events = diverse_execution_events(events)
    buckets = [[], [], [], []]
    for event in events:
        for name in event.get('provider_function_names', []):
            if not re.fullmatch(r'[A-Za-z_$][\w$]{0,63}', str(name)) or re.search(r'fetch|request', name, re.I):
                continue
            utility = (name in {'wrapped', 'wrap', 'text', 'json', 'apiJson', 'jsonPostAt'}
                       or (owned_names is not None and name not in owned_names))
            index = (0 if event['fixture_failed'] else 2) + int(utility)
            if name not in buckets[index]:
                buckets[index].append(name)
    names = list(dict.fromkeys(name for bucket in buckets for name in bucket))
    return events, names[:6]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recheck-script-shell', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', args.provider):
        raise SystemExit('invalid provider')
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, cwd=verifier.ROOT).strip()
    previous = {}
    if args.recheck_script_shell:
        previous = json.loads(args.output.read_text())
        if (previous.get('provider') != args.provider or previous.get('sourceSha') != source_sha
                or previous.get('http_script_shell_only') is not True
                or previous.get('script_shell_recheck_performed') is True):
            raise ValueError('one script-shell recheck requires exact-current missing-content evidence')
    root = args.output.resolve().parent / 'live-preflight'
    root.mkdir(parents=True, exist_ok=True)
    targets = root / 'targets.json'
    verifier.write_targets(targets, args.provider)
    verifier.stage_provider(verifier.ROOT, args.provider, root / 'stage', targets)
    # The decoded comparison must use this provider's declared film/TV/anime
    # fixtures, not the evaluator's anime-only legacy defaults. Otherwise a
    # movie provider can report runtime_error with zero executed fixtures.
    health = verifier.health_provider(root / 'stage', root / 'health', args.provider)
    result = verifier.provider_result(health, args.provider)
    events, names = prioritized_execution(result, provider_owned_function_names(root / 'stage', args.provider))
    payload = {
        'provider': args.provider,
        'sourceSha': source_sha,
        # The current preflight can be externally blocked even when an old
        # census row says ROUTE PROVEN. Do not turn WAF/network evidence into a
        # code-causal mutation prompt just because a model is available.
        'preflight_status': str(result.get('status') or '').strip().casefold()[:48],
        'preflight_playable': verifier.runtime_repair.playable_stream_count(result),
        'active_functions': names[:6],
        'http_script_shell_only': script_shell_only(events),
        'fixture_evidence': verifier.fixture_summary(result),
        'network_evidence': [{
            **public_address_fields(event),
            'fixture': event.get('fixture_label'),
            'stage': event.get('stage'), 'host': event.get('host'),
            'status': event.get('status'), 'functions': event.get('provider_function_names', [])[:8],
            'error_code': public_network_error_code(event.get('error_code')),
            'response_structure': event.get('response_structure'),
            'media_observation': event.get('media_observation'),
            'http_observation': public_http_observation(event.get('http_observation')),
            'reader_user_agent_probe': public_reader_probe(event.get('reader_user_agent_probe')) or None,
            'observed_media_probe': public_observed_media_probe(event.get('observed_media_probe'))
                if public_address_fields(event) else None,
            'announced_players': int(event.get('declared_player_candidate_count') or 0),
        } for event in events[:12]],
        'streams_playable': verifier.runtime_repair.playable_stream_count(result),
        'publicationAuthority': False,
    }
    omitted_scopes = {address_scope(event.get('address_scope')) for event in events[12:]}
    for event in payload['network_evidence']:
        if event.get('address_scope') in omitted_scopes:
            event['address_trace_truncated'] = True
    if previous:
        payload['script_shell_recheck_performed'] = True
        browser = previous.get('browser_observation') or {}
        allowed = {'browser_unavailable', 'browser_content_reached', 'browser_challenge_persisted',
                   'browser_timeout', 'browser_inconclusive', 'browser_error'}
        if browser.get('outcome') in allowed:
            payload['browser_observation'] = {
                'outcome': browser['outcome'], 'browser_available': browser.get('browser_available') is True,
                'publicationAuthority': False,
            }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + '\n')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as handle:
            handle.write('script_shell_only=' + str(payload['http_script_shell_only']).lower() + '\n')
    print('::notice title=Live provider execution::provider=' + args.provider + ' functions=' + ','.join(payload['active_functions']))

if __name__ == '__main__':
    main()
