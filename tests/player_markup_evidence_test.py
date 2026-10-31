import copy
import contextlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from player_markup_evidence import public_player_markup
import capture_brain_live_context as capture

# Exercise the actual producer and public archive projection together.
code = '''
const {responseStructure}=require('./scripts/response_structure.cjs');
console.log(JSON.stringify(responseStructure('<html><iframe src="https://private.test/?token=PRIVATE"></iframe>'+
 '<button data-code="'+Buffer.from('<iframe src="https://private.test/PRIVATE"></iframe>').toString('base64')+'"></button></html>')));
'''
structure = json.loads(subprocess.check_output(['node', '-e', code], cwd=ROOT, text=True))
context = {'sourceSha': 'a' * 40, 'provider': 'demo', 'raw_body': 'PRIVATE',
           'network_evidence': [{'fixture': 'Missing S01E01', 'host': 'public.test', 'stage': 'player',
                                 'response_structure': structure, 'raw_url': 'https://private.test/PRIVATE'}]}
result = public_player_markup(context, 'a' * 40)
rows = result['observations'][0]['player_markup']['rows']
assert rows[0]['value_kinds'] == {'data-code': 'encoded_markup'}
assert rows[1]['value_kinds'] == {'src': 'absolute_url'}
assert result['publicationAuthority'] is False and result['proofAuthority'] is False
assert 'PRIVATE' not in json.dumps(result) and 'private.test' not in json.dumps(result)

# Preserve the producer's schema through the real preflight writer too.
with tempfile.TemporaryDirectory() as directory:
    output = Path(directory) / 'live.json'
    event = {'stage': 'player', 'host': 'public.test', 'status': 200, 'ok': True,
             'provider_function_names': ['resolve'], 'response_structure': structure}
    health = {'results': [{'provider': 'demo', 'tests': [{
        'fixture': {'label': 'Missing S01E01'}, 'streams_playable': 0,
        'network_observations': [event],
    }]}]}
    with patch.object(sys, 'argv', ['capture', '--provider', 'demo', '--output', str(output)]), \
         patch.object(capture.subprocess, 'check_output', return_value='a' * 40), \
         patch.object(capture.verifier, 'stage_provider'), \
         patch.object(capture, 'provider_owned_function_names', return_value={'resolve'}), \
         patch.object(capture.verifier, 'health_provider', return_value=health), \
         contextlib.redirect_stdout(io.StringIO()):
        capture.main()
    archived = public_player_markup(json.loads(output.read_text()), 'a' * 40)
    assert archived['observations'][0]['player_markup']['rows'] == rows

# A forged artifact may only contribute recognized enum values and bounded counts.
forged = copy.deepcopy(context)
markup = forged['network_evidence'][0]['response_structure']['player_markup']
markup.update(raw_body='PRIVATE', sampled_chars=999999)
markup['rows'] = [{'tag': 'iframe', 'value_kinds': {'src': 'absolute_url', 'data-token': 'PRIVATE',
                                                 'data-src': 'https://private.test/PRIVATE'},
                   'count': 999999, 'distinct_values': 999999, 'url': 'PRIVATE'}] * 30
forged['network_evidence'] *= 20
result = public_player_markup(forged, 'a' * 40)
assert len(result['observations']) == 12
assert len(result['observations'][0]['player_markup']['rows']) == 8
assert result['observations'][0]['player_markup']['sampled_chars'] == 131072
assert result['observations'][0]['player_markup']['rows'][0]['distinct_values'] == 128
assert 'PRIVATE' not in json.dumps(result) and 'private.test' not in json.dumps(result)
try:
    public_player_markup(context, 'b' * 40)
except ValueError:
    pass
else:
    raise AssertionError('source mismatch accepted')
print('Player markup evidence: actual producer, bounded projection, privacy and source matching passed')
