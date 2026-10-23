#!/usr/bin/env python3
"""Bounded hosted propose -> external verification -> negative feedback loop."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))

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
    result['candidate_network'] = [{
        'host': event.get('host'), 'stage': event.get('stage'), 'status': event.get('status'),
        'fixture': event.get('fixture'),
        'functions': event.get('providerFunctions', []),
        'response_structure': event.get('responseStructure'),
        'announced_players': event.get('announcedPlayerCandidates', 0),
    } for event in (row.get('candidate') or {}).get('networkTrace', [])[-12:]]
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--brain-root', type=Path, required=True)
    parser.add_argument('--provider', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-attempts', type=int, default=3)
    parser.add_argument('--budget-seconds', type=int, default=600)
    args = parser.parse_args()
    out = args.output.resolve()
    brain = args.brain_root.resolve()
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    brain_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=brain, text=True).strip()
    live = json.loads((out / 'live-context.json').read_text())
    if live.get('provider') != args.provider or live.get('sourceSha') != source_sha:
        raise ValueError('live provider evidence must match exact current source')
    if live.get('http_script_shell_only') is True:
        # Parser/cap rewrites cannot be justified from an empty script shell.
        # Keep this a missing-evidence prerequisite, never a failed code experiment.
        reason = 'http_script_shell_requires_content_evidence'
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
        if not inference:
            for key in ('NIAKVIO_OPENAI_API_KEY', 'OPENAI_API_KEY'):
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
                '--provider', args.provider, '--backend', 'hosted', '--workers', '1',
                '--max-hypotheses', '1', '--max-tokens', '4096', '--timeout-seconds', '120',
                '--force-provider-budget-seconds', '180', '--live-evidence', context,
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
