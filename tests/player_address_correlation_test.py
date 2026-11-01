"""Opaque reader identities must survive the real health/report projections."""
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
from address_reference_evidence import public_address_fields
from player_markup_evidence import public_player_markup, project_player_markup
import capture_brain_live_context as capture
import evaluate_brain_llm_force_candidates as verifier
from run_hosted_brain_repair_loop import verification_feedback

code = r'''
const fs=require('node:fs');
const {createAddressReferences,safeAddressFields}=require('./scripts/address_reference.cjs');
const {responseStructure}=require('./scripts/response_structure.cjs');
const {safeHttpFacts}=require('./scripts/http_response_observation.cjs');
const {safeReaderProbe}=require('./scripts/reader_user_agent_probe.cjs');
const {safeMediaFacts}=require('./scripts/media_observation.cjs');
const refs=createAddressReferences(), base='https://provider.test/episode?token=PRIVATE';
const wrappers=[0,1,2].map(n=>'https://provider.test/?trembed='+n+'&trid=PRIVATE');
const players=['https://reader.test/embed?video=PRIVATE','https://other.test/shell.php?videoid=PRIVATE'];
const events=[];
function record(url,stage,body,status=200,referer=''){
 const row={...safeAddressFields({address_scope:refs.scope,request_ref:refs.ref(url),response_ref:refs.ref(url),
  referer_ref:refs.ref(referer),address_refs_truncated:false,address_trace_truncated:false}),
  stage,host:new URL(url).hostname,path_pattern:stage==='player'?'/?trembed={value}&trid={value}':'/episode',
  status,ok:status===200,provider_function_names:['resolve']};
 if(body)row.response_structure=responseStructure(body,{baseUrl:url,addressRef:v=>refs.ref(v)});
 events.push(row);
}
record(base,'episode',wrappers.map(url=>'<div data-src="'+url.replace(/&/g,'&amp;')+'"></div>').join(''));
for(let i=0;i<3;i++)record(wrappers[i],'player','<iframe src="'+players[i===1?1:0]+'"></iframe>',200,base);
record(players[0],'player','<video></video>',200,wrappers[0]);
record(players[1],'player','',403,wrappers[1]);
const source=fs.readFileSync('./scripts/health_check.mjs','utf8');
const begin=source.indexOf('network_observations: Array.isArray(worker.network_observations)');
const end=source.indexOf('      settings_diagnostics:',begin);
if(begin<0||end<0)throw new Error('production projection unavailable');
const expression=source.slice(begin+'network_observations: '.length,end).trim().replace(/,$/,'');
const normalize=new Function('worker','safeMediaFacts','safeHttpFacts','safeReaderProbe','safeAddressFields','sanitizeError','return ('+expression+');');
console.log(JSON.stringify({scope:refs.scope,events:normalize({network_observations:events},safeMediaFacts,safeHttpFacts,safeReaderProbe,safeAddressFields,()=>null)}));
'''
produced = json.loads(subprocess.check_output(['node', '-e', code], cwd=ROOT, text=True))
assert 'PRIVATE' not in json.dumps(produced)
events = produced['events']
declared = events[0]['response_structure']['player_markup']['rows'][0]['address_refs']['data-src']
assert len(set(declared)) == 3
assert set(declared) == {event['request_ref'] for event in events[1:4]}
assert all(event['referer_ref'] == events[0]['request_ref'] for event in events[1:4])
assert events[1]['response_structure']['player_markup']['rows'][0]['address_refs'] == events[3]['response_structure']['player_markup']['rows'][0]['address_refs']
result = {'provider': 'demo', 'tests': [{'fixture': {'label': 'Missing'}, 'streams_playable': 0,
                                        'network_observations': events}]}
trace = verifier.network_summary(result)
assert len(trace) == 6, 'query-distinct wrappers must survive normalized-path deduplication'
assert len({row['request_ref'] for row in trace}) == 6
assert all(row['address_scope'] == produced['scope'] and row['address_trace_truncated'] is False for row in trace)
feedback = verification_feedback({'rows': [{'executionObserved': True,
    'materializedMutationObserved': True, 'candidate': {'networkTrace': trace}}]})
assert {row['request_ref'] for row in feedback['candidate_network']} == {row['request_ref'] for row in trace}

with tempfile.TemporaryDirectory() as directory:
    output = Path(directory) / 'live.json'
    with patch.object(sys, 'argv', ['capture', '--provider', 'demo', '--output', str(output)]), \
         patch.object(capture.subprocess, 'check_output', return_value='a' * 40), \
         patch.object(capture.verifier, 'stage_provider'), \
         patch.object(capture, 'provider_owned_function_names', return_value={'resolve'}), \
         patch.object(capture.verifier, 'health_provider', return_value={'results': [result]}), \
         contextlib.redirect_stdout(io.StringIO()):
        capture.main()
    receipt = public_player_markup(json.loads(output.read_text()), 'a' * 40)
    episode = next(row for row in receipt['observations'] if row['stage'] == 'episode')
    assert episode['address_scope'] == produced['scope']
    assert episode['player_markup']['rows'][0]['address_refs']['data-src'] == declared
    assert episode['address_trace_truncated'] is False and 'PRIVATE' not in json.dumps(receipt)

many = [{**events[0], 'request_ref': f'r{i}'} for i in range(1, 70)]
bounded = verifier.network_summary({'tests': [{'fixture': {'label': 'Missing'}, 'network_observations': many}]})
assert len(bounded) == 64 and all(row['address_trace_truncated'] for row in bounded)
feedback = verification_feedback({'rows': [{'executionObserved': True, 'candidate': {'networkTrace': trace * 3}}]})
assert all(row['address_trace_truncated'] for row in feedback['candidate_network'])
for forged in ({'address_scope': 'https://PRIVATE', 'request_ref': 'r1'},
               {'address_scope': produced['scope'], 'request_ref': 'r1\n'},
               {'address_scope': produced['scope'], 'request_ref': 'r513', 'address_refs_truncated': False}):
    clean = public_address_fields(forged)
    assert 'PRIVATE' not in json.dumps(clean) and '\n' not in str(clean)
    assert public_address_fields(clean) == clean
    if clean:
        assert clean['address_refs_truncated']
row = {'tag': 'iframe', 'value_kinds': {'src': 'absolute_url'}, 'count': 1, 'distinct_values': 1,
       'address_refs': {'src': ['r1', 'https://PRIVATE', 'r513'], 'cookie': ['r2']}, 'address_refs_truncated': False}
projected = project_player_markup({'rows': [row], 'truncated': False}, allow_address_refs=True)
assert projected['rows'][0]['address_refs'] == {'src': ['r1']}
assert projected['truncated'] and 'PRIVATE' not in json.dumps(projected)
assert 'address_refs' not in project_player_markup({'rows': [row]})['rows'][0]
assert project_player_markup({'rows': [{**row, 'address_refs': {'src': ['r1']}}] * 9,
                             'truncated': False}, allow_address_refs=True)['truncated']
print('Player address correlation: production health projection, distinct queries, archive/feedback and honest truncation passed')
