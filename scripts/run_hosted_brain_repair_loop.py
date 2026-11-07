#!/usr/bin/env python3
"""Bounded local propose -> external verification -> negative feedback loop."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))

from http_response_evidence import public_http_observation, public_reader_probe, public_network_error_code
from address_reference_evidence import public_address_fields
from observed_media_evidence import public_observed_media_probe

def should_replan(evaluation: dict, attempt: int, limit: int) -> bool:
    return (
        not int(evaluation.get('acceptedProviderCount') or 0)
        and attempt < limit
        and any(row.get('executionObserved') is True for row in evaluation.get('rows', []))
    )

def verification_feedback(evaluation: dict) -> dict:
    executed = [row for row in evaluation.get('rows', []) if row.get('executionObserved') is True]
    if not executed:
        return {}
    row = executed[-1]
    result = {'reason': row.get('reason'), 'executionObserved': True,
              'materializedMutationObserved': row.get('materializedMutationObserved') is True}
    for phase in ('baseline', 'candidate'):
        value = row.get(phase) or {}
        result[phase] = {key: value.get(key) for key in
                         ('streamsPlayable', 'streamsReturned', 'identityContradictions', 'fixtureCoverage')}
        # The Brain needs bounded reader/variant exploration deltas to avoid
        # treating an executed but deeper crawl as an unchanged failed edit.
        # Do not pass reachable hostnames, URLs, headers or raw network data.
        raw_coverage = value.get('variantCoverage') if isinstance(value.get('variantCoverage'), dict) else {}
        result[phase]['variantCoverage'] = {
            key: max(0, min(100000, raw_coverage[key])) if type(raw_coverage.get(key)) is int else 0
            for key in ('announcedPlayerCandidates', 'announcedVariantCandidates',
                        'exploredPlayerRequests', 'maxPlayableHeight')
        }
    result['candidate_network'] = [{
        **public_address_fields(event),
        'host': event.get('host'), 'stage': event.get('stage'), 'status': event.get('status'),
        'error_code': public_network_error_code(event.get('errorCode')),
        'fixture': event.get('fixture'),
        'functions': event.get('providerFunctions', []),
        'response_structure': event.get('responseStructure'),
        'media_observation': event.get('mediaObservation'),
        'http_observation': public_http_observation(event.get('httpObservation')),
        'reader_user_agent_probe': public_reader_probe(event.get('readerUserAgentProbe')) or None,
        'observed_media_probe': public_observed_media_probe(event.get('observedMediaProbe'))
            if public_address_fields(event) else None,
        'announced_players': event.get('announcedPlayerCandidates', 0),
    } for event in (row.get('candidate') or {}).get('networkTrace', [])[-12:]]
    omitted = {event.get('address_scope') for event in (row.get('candidate') or {}).get('networkTrace', [])[:-12]}
    for event in result['candidate_network']:
        if event.get('address_scope') in omitted:
            event['address_trace_truncated'] = True
    return result


def replay_mutations(path: Path, out: Path, provider: str, source_sha: str) -> int:
    """Reverify an archived model proposal without another inference request."""
    payload = json.loads(path.read_text())
    rows = payload.get('rows')
    if not isinstance(rows, list) or len(rows) != 1 or rows[0].get('providerId') != provider:
        raise ValueError('replay requires exactly one proposal for the selected provider')
    # Preserve the originating Brain revision, source and context fingerprints.
    # No Brain code is used for inference during replay. The receiver still
    # checks source drift, runtime bytes, ownership and the current provider entry.
    (out / 'mutations.json').write_text(json.dumps(payload, indent=2) + '\n')
    (out / 'diagnostics.json').write_text(json.dumps({'rows': [{'scopeTrace': [{
        'scope': 'provider_bloc', 'outcome': 'replay', 'reason': 'archived_model_proposal_no_inference',
    }]}]}))
    env = os.environ.copy()
    for key in ('NIAKVIO_OPENAI_API_KEY', 'OPENAI_API_KEY'):
        env.pop(key, None)
    subprocess.run([sys.executable, str(ROOT / 'scripts/evaluate_brain_llm_force_candidates.py'),
        '--input', str(out / 'mutations.json'), '--current-sha', source_sha,
        '--provider', provider, '--report', str(out / 'evaluation.json'),
        '--accepted-output', str(out / 'accepted.json')], cwd=ROOT, env=env, check=True, timeout=540)
    ledger = ROOT / 'automation/brain-llm-force-memory.json'
    memory = out / 'force-memory.json'
    memory.write_bytes(ledger.read_bytes() if ledger.exists() else b'{}')
    subprocess.run([sys.executable, str(ROOT / 'scripts/update_brain_llm_force_memory.py'),
        '--memory', str(memory), '--evaluation', str(out / 'evaluation.json')],
        cwd=ROOT, env=env, check=True, timeout=30)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--brain-root', type=Path, required=True)
    parser.add_argument('--provider', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-attempts', type=int, default=3)
    parser.add_argument('--budget-seconds', type=int, default=600)
    parser.add_argument('--replay-mutations', type=Path)
    parser.add_argument('--endpoint', default=os.environ.get('NIAKVIO_LLM_ENDPOINT', 'http://127.0.0.1:8080'))
    args = parser.parse_args()
    endpoint = urlsplit(args.endpoint)
    if (endpoint.scheme not in {'http', 'https'} or endpoint.hostname not in {'127.0.0.1', 'localhost', '::1'}
            or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment):
        raise ValueError('repair generation requires a local loopback model; paid API fallback is disabled')
    out = args.output.resolve()
    brain = args.brain_root.resolve()
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    brain_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=brain, text=True).strip()
    live = json.loads((out / 'live-context.json').read_text())
    if live.get('provider') != args.provider or live.get('sourceSha') != source_sha:
        raise ValueError('live provider evidence must match exact current source')
    preflight_status = str(live.get('preflight_status') or '').strip().casefold()
    network_blocked = (preflight_status in {'blocked', 'provider_unreachable'}
                       and live.get('preflight_playable') == 0)
    if live.get('http_script_shell_only') is True or network_blocked:
        # Never spend LLM repair tokens when the current exact-SHA preflight
        # cannot reach content at all. This is a transport/harness observation,
        # not a code failure or a finite retry-count rule. Preserve the debt.
        reason = ('http_script_shell_requires_content_evidence'
                  if live.get('http_script_shell_only') is True
                  else 'network_blocked_requires_transport_differential')
        (out / 'diagnostics.json').write_text(json.dumps({'rows': [{'scopeTrace': [{
            'scope': 'provider_bloc', 'outcome': 'abstain', 'reason': reason,
        }]}]}))
        (out / 'evaluation.json').write_text(json.dumps({
            'currentSha': source_sha, 'candidateCount': 0, 'acceptedProviderCount': 0,
            'rows': [], 'attempts': [], 'publicationAuthority': False,
        }))
        for name in ('mutations.json', 'accepted.json'):
            (out / name).write_text(json.dumps({'schemaVersion': 1, 'sourceNiakvioSha': source_sha,
                'rows': [], 'providerCount': 0, 'publicationAuthority': False, 'proofAuthority': False}))
        print('::notice title=Hosted evidence prerequisite::' + reason)
        return 0
    if args.replay_mutations:
        return replay_mutations(args.replay_mutations.resolve(), out, args.provider, source_sha)
    # Seed the first call from the latest *executed* diagnostic candidate.
    # This is a counterexample, never a positive training record or proof.
    for path in sorted((ROOT / 'automation/hosted-repair-evidence').glob('*-mutations.json'), reverse=True):
        evaluation_path = path.with_name(path.name.replace('-mutations.json', '-evaluation.json'))
        if not evaluation_path.is_file():
            continue
        result = json.loads(evaluation_path.read_text())
        if not any(row.get('provider') == args.provider and row.get('executionObserved') is True
                   and row.get('materializedMutationObserved') is True
                   and row.get('accepted') is False for row in result.get('rows', [])):
            continue
        payload = json.loads(path.read_text())
        executed = {row.get('mutationFingerprint') for row in result.get('rows', [])
                    if row.get('executionObserved') is True and row.get('materializedMutationObserved') is True
                    and row.get('accepted') is False}
        live['previous_verification'] = verification_feedback(result)
        live['previous_executed_edits'] = [edit for row in payload.get('rows', [])
                                          if row.get('providerId') == args.provider and row.get('mutationFingerprint') in executed
                                          for edit in row.get('mutations', [])][-2:]
        break
    limit = max(1, min(3, args.max_attempts))
    deadline = time.monotonic() + max(60, min(900, args.budget_seconds))
    ledger = ROOT / 'automation/brain-llm-force-memory.json'
    original = ledger.read_bytes() if ledger.exists() else None
    # Reclassify unverified historical v3 Bloc runs before the first model call.
    from update_brain_llm_force_memory import merge
    ledger.write_text(json.dumps(merge(json.loads(original) if original else {}, {}), indent=2) + '\n')
    rows = []
    attempts = []
    accepted = []
    mutation_rows = []

    def run(script: Path, *values: str, inference: bool = False):
        remaining = deadline - time.monotonic()
        if remaining < 10:
            raise TimeoutError('hosted repair loop budget exhausted')
        env = os.environ.copy()
        for key in ('NIAKVIO_OPENAI_API_KEY', 'OPENAI_API_KEY', 'NIAKVIO_ALLOW_PAID_API'):
            env.pop(key, None)
        subprocess.run([sys.executable, str(script), *map(str, values)], cwd=ROOT,
                       env=env, check=True, timeout=remaining)

    try:
        for attempt in range(1, limit + 1):
            directory = out / f'attempt-{attempt}'
            directory.mkdir(parents=True, exist_ok=True)
            context = directory / 'live-context.json'
            context.write_text(json.dumps(live))
            batch = directory / 'batch.jsonl'
            run(brain / 'scripts/plan_batch_from_checkout.py',
                '--niakvio-root', ROOT, '--experience', out / 'experience.jsonl',
                '--documents', out / 'documents.jsonl', '--mode', 'repair',
                '--provider', args.provider, '--backend', 'local', '--endpoint', args.endpoint, '--workers', '1',
                '--max-hypotheses', '1', '--max-tokens', '4096', '--timeout-seconds', '300',
                '--force-provider-budget-seconds', '360', '--live-evidence', context,
                '--output', batch, inference=True)
            for name, script in (('diagnostics', 'publish_niakvio_force_diagnostics.py'),
                                 ('mutations', 'publish_niakvio_force_mutations.py')):
                options = ['--input', batch, '--output', directory / (name + '.json'),
                           '--niakvio-sha', source_sha, '--brain-llm-sha', brain_sha]
                if name == 'mutations':
                    options += ['--niakvio-root', ROOT]
                run(brain / 'scripts' / script, *options)
            evaluation_path = directory / 'evaluation.json'
            run(ROOT / 'scripts/evaluate_brain_llm_force_candidates.py',
                '--input', directory / 'mutations.json', '--current-sha', source_sha,
                '--provider', args.provider, '--report', evaluation_path,
                '--accepted-output', directory / 'accepted.json')
            evaluation = json.loads(evaluation_path.read_text())
            run(ROOT / 'scripts/update_brain_llm_force_memory.py',
                '--memory', ledger, '--evaluation', evaluation_path)
            attempts.append({'attempt': attempt, 'candidateCount': evaluation['candidateCount'],
                             'acceptedProviderCount': evaluation['acceptedProviderCount']})
            rows.extend(evaluation.get('rows') or [])
            accepted.extend(evaluation.get('acceptedProviders') or [])
            mutations = json.loads((directory / 'mutations.json').read_text())
            mutation_rows.extend(mutations.get('rows') or [])
            for name in ('diagnostics.json', 'mutations.json', 'accepted.json'):
                shutil.copyfile(directory / name, out / name)
            print(f'::notice title=Hosted verification loop::attempt={attempt} candidates={evaluation["candidateCount"]} accepted={evaluation["acceptedProviderCount"]}')
            if not should_replan(evaluation, attempt, limit):
                break
            live['previous_verification'] = verification_feedback(evaluation)
            executed = {row.get('mutationFingerprint') for row in evaluation.get('rows', [])
                        if row.get('executionObserved') is True}
            live['previous_executed_edits'] = (live.get('previous_executed_edits', []) + [
                edit for row in mutations.get('rows', [])
                if row.get('mutationFingerprint') in executed
                for edit in row.get('mutations', [])
            ])[-2:]
    finally:
        mutations_path = out / 'mutations.json'
        if mutations_path.exists():
            mutations = json.loads(mutations_path.read_text())
            mutations['rows'] = mutation_rows
            mutations['providerCount'] = len({row.get('providerId') for row in mutation_rows})
            mutations_path.write_text(json.dumps(mutations, indent=2) + '\n')
        if ledger.exists():
            shutil.copyfile(ledger, out / 'force-memory.json')
        (out / 'evaluation.json').write_text(json.dumps({
            'currentSha': source_sha, 'sourceNiakvioSha': source_sha,
            'sourceBrainLlmSha': brain_sha, 'candidateCount': len(rows),
            'acceptedProviderCount': len(set(accepted)), 'acceptedProviders': sorted(set(accepted)),
            'rows': rows, 'attempts': attempts, 'publicationAuthority': False,
        }, indent=2) + '\n')
        if original is not None:
            ledger.write_bytes(original)
        else:
            ledger.unlink(missing_ok=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
