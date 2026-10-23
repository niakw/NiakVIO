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
                assert context['previous_executed_edits'][0]['replace'] == 'second()'
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
print('Hosted verification loop: measured rejection feedback, acceptance stop, credential isolation and source restoration passed')
