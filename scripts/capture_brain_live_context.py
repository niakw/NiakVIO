#!/usr/bin/env python3
"""Observe current provider bytes before model synthesis, without editing them."""
import argparse
import json
import re
import subprocess
from pathlib import Path
import evaluate_brain_llm_force_candidates as verifier

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
    events = [event for test in result.get('tests', []) for event in test.get('network_observations', [])
              if isinstance(event, dict) and not event.get('infrastructure')]
    events.sort(key=lambda row: (int(row.get('declared_player_candidate_count') or 0) > 0,
                                 str(row.get('stage')) in {'episode', 'player', 'source', 'media'}), reverse=True)
    names = []
    for event in events:
        for name in event.get('provider_function_names', []):
            if re.fullmatch(r'[A-Za-z_$][\w$]{0,63}', str(name)) and not re.search(r'fetch|request', name, re.I) and name not in names:
                names.append(name)
    payload = {
        'provider': args.provider,
        'sourceSha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, cwd=verifier.ROOT).strip(),
        'active_functions': names[:6],
        'streams_playable': verifier.runtime_repair.playable_stream_count(result),
        'publicationAuthority': False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + '\n')
    print('::notice title=Live provider execution::provider=' + args.provider + ' functions=' + ','.join(payload['active_functions']))

if __name__ == '__main__':
    main()
