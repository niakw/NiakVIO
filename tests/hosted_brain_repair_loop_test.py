import importlib.util
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hosted_loop', ROOT / 'scripts/run_hosted_brain_repair_loop.py')
loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loop)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    out = root / 'output'
    out.mkdir()
    ledger = root / 'automation/brain-llm-force-memory.json'
    ledger.parent.mkdir()
    original = b'{"entries":[]}\n'
    ledger.write_bytes(original)
    evidence = ledger.parent / 'hosted-repair-evidence'
    evidence.mkdir()
    (evidence / '999-evaluation.json').write_text(json.dumps({'rows': [{
        'provider': 'demo', 'mutationFingerprint': 'b' * 64, 'accepted': False,
        'executionObserved': True, 'materializedMutationObserved': True,
    }, {'provider': 'demo', 'mutationFingerprint': 'c' * 64, 'accepted': False,
        'executionObserved': False}]}))
    (evidence / '999-mutations.json').write_text(json.dumps({'rows': [
        {'providerId': 'demo', 'mutationFingerprint': 'b' * 64,
         'mutations': [{'find': 'older()', 'replace': 'prior()'}]},
        {'providerId': 'demo', 'mutationFingerprint': 'c' * 64,
         'mutations': [{'find': 'unexecuted_poison()', 'replace': 'ignored()'}]},
    ]}))
    (out / 'live-context.json').write_text(json.dumps({'provider': 'demo', 'sourceSha': 'a' * 40, 'active_functions': ['resolve']}))
    count = 0
    def run(command, **options):
        global count
        script = Path(command[1]).name
        value = lambda key: Path(command[command.index(key) + 1])
        if script == 'plan_batch_from_checkout.py':
            count += 1
            assert options['env']['NIAKVIO_OPENAI_API_KEY'] == 'test-only'
            if count == 2:
                context = json.loads(value('--live-evidence').read_text())
                assert len(context['previous_executed_edits']) == 2
                assert context['previous_executed_edits'][-1]['replace'] == 'second()'
                assert context['previous_executed_edits'][0]['find'] == 'older()'
                assert 'unexecuted_poison' not in str(context)
                assert context['previous_verification']['reason'] == 'no_playable'
                assert context['previous_verification']['candidate']['streamsPlayable'] == 0
                assert json.loads(ledger.read_text())['executed'] == 1
            value('--output').write_text('{}\n')
        else:
            assert 'NIAKVIO_OPENAI_API_KEY' not in options['env']
        if script == 'publish_niakvio_force_diagnostics.py':
            value('--output').write_text('{"rows":[]}')
        if script == 'publish_niakvio_force_mutations.py':
            value('--output').write_text(json.dumps({'rows': [{
                'mutationFingerprint': str(count) * 64,
                'mutations': [{'scope': 'provider_bloc', 'find': 'first()', 'replace': 'second()'}],
            }]}))
        if script == 'evaluate_brain_llm_force_candidates.py':
            value('--report').write_text(json.dumps({
                'candidateCount': 1, 'acceptedProviderCount': int(count == 2),
                'acceptedProviders': ['demo'] if count == 2 else [],
                'rows': [{'executionObserved': True, 'mutationFingerprint': str(count) * 64,
                          'reason': 'no_playable', 'candidate': {'streamsPlayable': 0}}],
            }))
            value('--accepted-output').write_text('{}')
        if script == 'update_brain_llm_force_memory.py':
            value('--memory').write_text(json.dumps({'executed': count}))
    argv = ['loop', '--brain-root', str(root / 'brain'), '--provider', 'demo', '--output', str(out)]
    with patch.object(loop, 'ROOT', root), patch.object(sys, 'argv', argv), \
         patch.dict(os.environ, {'NIAKVIO_OPENAI_API_KEY': 'test-only'}), \
         patch.object(loop.subprocess, 'check_output', return_value='a' * 40), \
         patch.object(loop.subprocess, 'run', side_effect=run), \
         contextlib.redirect_stdout(io.StringIO()):
        assert loop.main() == 0
    result = json.loads((out / 'evaluation.json').read_text())
    assert len(result['attempts']) == 2 and result['acceptedProviderCount'] == 1
    assert count == 2 and result['publicationAuthority'] is False
    assert ledger.read_bytes() == original
    assert json.loads((out / 'force-memory.json').read_text())['executed'] == 2
    assert len(json.loads((out / 'mutations.json').read_text())['rows']) == 2

assert not loop.should_replan({'rows': []}, 1, 3)
assert not loop.should_replan({'rows': [{'executionObserved': False}]}, 1, 3)
assert not loop.should_replan({'rows': [{'executionObserved': True}]}, 3, 3)
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    out = root / 'output'
    out.mkdir()
    source = root / 'archived.json'
    payload = {'brainLlmSha': 'b' * 40, 'sourceNiakvioSha': 'c' * 40,
               'rows': [{'providerId': 'demo', 'mutationFingerprint': 'd' * 64}]}
    source.write_text(json.dumps(payload))
    ledger = root / 'automation/brain-llm-force-memory.json'
    ledger.parent.mkdir()
    ledger.write_text('{"original":true}')
    calls = []
    def replay_run(command, **options):
        assert 'NIAKVIO_OPENAI_API_KEY' not in options['env']
        assert 'OPENAI_API_KEY' not in options['env']
        calls.append(Path(command[1]).name)
        if calls[-1] == 'evaluate_brain_llm_force_candidates.py':
            assert command[command.index('--current-sha') + 1] == 'a' * 40
            assert json.loads((out / 'mutations.json').read_text()) == payload
        elif calls[-1] == 'update_brain_llm_force_memory.py':
            assert Path(command[command.index('--memory') + 1]) == out / 'force-memory.json'
    with patch.object(loop, 'ROOT', root), \
         patch.dict(os.environ, {'NIAKVIO_OPENAI_API_KEY': 'test-only', 'OPENAI_API_KEY': 'test-only'}), \
         patch.object(loop.subprocess, 'run', side_effect=replay_run):
        assert loop.replay_mutations(source, out, 'demo', 'a' * 40) == 0
        for provider in ['other']:
            try:
                loop.replay_mutations(source, out, provider, 'a' * 40)
            except ValueError:
                pass
            else:
                raise AssertionError('replay accepted a mismatched provider')
    assert calls == ['evaluate_brain_llm_force_candidates.py', 'update_brain_llm_force_memory.py']
    assert ledger.read_text() == '{"original":true}'

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / 'live-context.json').write_text(json.dumps({
        'provider': 'demo', 'sourceSha': 'a' * 40, 'http_script_shell_only': True,
    }))
    argv = ['loop', '--brain-root', str(root / 'brain'), '--provider', 'demo', '--output', str(root)]
    with patch.object(sys, 'argv', argv), \
         patch.object(loop.subprocess, 'check_output', return_value='a' * 40), \
         patch.object(loop.subprocess, 'run', side_effect=AssertionError('missing evidence must not spend inference')), \
         contextlib.redirect_stdout(io.StringIO()):
        assert loop.main() == 0
    result = json.loads((root / 'evaluation.json').read_text())
    assert result['rows'] == [] and result['candidateCount'] == 0
    assert json.loads((root / 'diagnostics.json').read_text())['rows'][0]['scopeTrace'][0]['reason'] == 'http_script_shell_requires_content_evidence'
print('Hosted verification loop: measured rejection feedback, acceptance stop, credential isolation and source restoration passed')
