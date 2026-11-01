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
from player_markup_evidence import project_player_markup, public_player_markup
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
typed = copy.deepcopy(context)
typed_markup = typed['network_evidence'][0]['response_structure']['player_markup']
typed_markup['rows'] = [{'tag': 'div', 'value_kinds': {'data-src': 'absolute_url'},
    'value_shapes': {'data-src': {'kind': 'image_extension', 'origin': 'cross_origin', 'url': 'PRIVATE'},
                     'src': {'kind': 'https://private.test/PRIVATE', 'origin': 'PRIVATE'}},
    'count': 3, 'distinct_values': 3}]
typed_row = public_player_markup(typed, 'a' * 40)['observations'][0]['player_markup']['rows'][0]
assert typed_row['value_shapes'] == {'data-src': {'kind': 'image_extension', 'origin': 'cross_origin'}}
assert 'PRIVATE' not in json.dumps(typed_row)
assert project_player_markup(structure['player_markup']) == result['observations'][0]['player_markup']
assert project_player_markup(None) == {'rows': [], 'sampled_chars': 0, 'truncated': False}

# Scoped opaque references survive only for attributes retained by the schema.
scoped = copy.deepcopy(typed)
scoped_event = scoped['network_evidence'][0]
scoped_event.update(address_scope='s0123456789abcdef', request_ref='r1', response_ref='r2', referer_ref='r512',
                    address_refs_truncated=True, address_trace_truncated=False)
scoped_markup = scoped_event['response_structure']['player_markup']
scoped_markup['rows'][0].update(address_refs={'data-src': ['r3', 'r4'], 'src': ['r5'], 'data-token': ['PRIVATE']},
                                address_refs_truncated=True)
scoped_result = public_player_markup(scoped, 'a' * 40)
scoped_observation = scoped_result['observations'][0]
assert scoped_observation['address_scope'] == 's0123456789abcdef'
assert scoped_observation['request_ref'] == 'r1'
assert scoped_observation['response_ref'] == 'r2'
assert scoped_observation['referer_ref'] == 'r512'
assert scoped_observation['address_refs_truncated'] is True
assert scoped_observation['address_trace_truncated'] is False
assert scoped_observation['player_markup']['rows'][0]['address_refs'] == {'data-src': ['r3', 'r4']}
assert scoped_observation['player_markup']['rows'][0]['address_refs_truncated'] is True
assert scoped_observation['player_markup']['truncated'] is True
assert 'PRIVATE' not in json.dumps(scoped_result) and 'private.test' not in json.dumps(scoped_result)
assert project_player_markup(scoped_markup, allow_address_refs=True) == scoped_observation['player_markup']

for scope in (None, '', 'PRIVATE', 's0123456789abcdeF'):
    unscoped = copy.deepcopy(scoped)
    unscoped['network_evidence'][0]['address_scope'] = scope
    unscoped_observation = public_player_markup(unscoped, 'a' * 40)['observations'][0]
    assert not any(key in unscoped_observation for key in
                   ('address_scope', 'request_ref', 'response_ref', 'referer_ref',
                    'address_refs_truncated', 'address_trace_truncated'))
    assert unscoped_observation['player_markup'] == project_player_markup(scoped_markup)
    assert 'address_refs' not in unscoped_observation['player_markup']['rows'][0]
    assert 'address_refs_truncated' not in unscoped_observation['player_markup']['rows'][0]
    assert unscoped_observation['player_markup']['truncated'] is False

# A complete producer row explicitly reports completeness to the public boundary.
scoped_code = '''
const {responseStructure}=require('./scripts/response_structure.cjs');
console.log(JSON.stringify(responseStructure('<html><iframe src="/embed/PRIVATE"></iframe></html>',
 {baseUrl:'https://private.test/',addressRef:()=>'r1'})));
'''
complete = copy.deepcopy(context)
complete['network_evidence'][0].update(
    address_scope='s0123456789abcdef', address_refs_truncated=False, address_trace_truncated=False,
    response_structure=json.loads(subprocess.check_output(['node', '-e', scoped_code], cwd=ROOT, text=True)))
complete_markup = public_player_markup(complete, 'a' * 40)['observations'][0]['player_markup']
assert complete_markup['rows'][0]['address_refs'] == {'src': ['r1']}
assert complete_markup['rows'][0]['address_refs_truncated'] is False
assert complete_markup['truncated'] is False
assert 'PRIVATE' not in json.dumps(complete_markup) and 'private.test' not in json.dumps(complete_markup)

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
