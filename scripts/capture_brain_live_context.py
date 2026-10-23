#!/usr/bin/env python3
"""Observe current provider bytes before model synthesis, without editing them."""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path
import evaluate_brain_llm_force_candidates as verifier

def script_shell_only(events):
    replies = [event for event in events if event.get('ok') and event.get('response_structure')]
    return bool(replies) and all(
        shape.get('kind') == 'html' and shape.get('variables')
        and {tag.get('tag') for tag in shape.get('tags', [])} == {'script'}
        for shape in (event['response_structure'] for event in replies)
    )

def prioritized_execution(result):
    events = [{**event, 'fixture_label': (test.get('fixture') or {}).get('label'), 'observation_index': index,
               'fixture_failed': int(test.get('streams_playable') or 0) == 0}
              for test in result.get('tests', []) for index, event in enumerate(test.get('network_observations', []))
              if isinstance(event, dict) and not event.get('infrastructure')]
    events.sort(key=lambda row: (
        bool(row['fixture_failed']), {'media': 4, 'source': 3, 'player': 2, 'episode': 1}.get(str(row.get('stage')), 0),
        row['observation_index'],
    ), reverse=True)
    buckets = [[], [], [], []]
    for event in events:
        for name in event.get('provider_function_names', []):
            if not re.fullmatch(r'[A-Za-z_$][\w$]{0,63}', str(name)) or re.search(r'fetch|request', name, re.I):
                continue
            utility = name in {'wrapped', 'wrap', 'text', 'json', 'apiJson', 'jsonPostAt'}
            index = (0 if event['fixture_failed'] else 2) + int(utility)
            if name not in buckets[index]:
                buckets[index].append(name)
    names = list(dict.fromkeys(name for bucket in buckets for name in bucket))
    return events, names[:6]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', args.provider):
        raise SystemExit('invalid provider')
    root = args.output.resolve().parent / 'live-preflight'
    root.mkdir(parents=True, exist_ok=True)
    targets = root / 'targets.json'
    verifier.write_targets(targets, args.provider)
    verifier.stage_provider(verifier.ROOT, args.provider, root / 'stage', targets)
    health = verifier.health_provider(root / 'stage', root / 'health')
    result = verifier.provider_result(health, args.provider)
    events, names = prioritized_execution(result)
    payload = {
        'provider': args.provider,
        'sourceSha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, cwd=verifier.ROOT).strip(),
        'active_functions': names[:6],
        'http_script_shell_only': script_shell_only(events),
        'fixture_evidence': verifier.fixture_summary(result),
        'network_evidence': [{
            'fixture': event.get('fixture_label'),
            'stage': event.get('stage'), 'host': event.get('host'),
            'status': event.get('status'), 'functions': event.get('provider_function_names', [])[:8],
            'response_structure': event.get('response_structure'),
            'announced_players': int(event.get('declared_player_candidate_count') or 0),
        } for event in events[:12]],
        'streams_playable': verifier.runtime_repair.playable_stream_count(result),
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
