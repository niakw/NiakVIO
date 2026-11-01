"""A failed reader's diagnostic survives preflight, archive and feedback safely."""
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
from http_response_evidence import public_http_observation, public_http_evidence
import capture_brain_live_context as capture
import evaluate_brain_llm_force_candidates as verifier
from run_hosted_brain_repair_loop import verification_feedback

code = '''
const {observeHttpResponse,safeHttpFacts}=require('./scripts/http_response_observation.cjs');
const {safeMediaFacts}=require('./scripts/media_observation.cjs');
const fs=require('node:fs');
(async()=>{
 const response=new Response('<html><div id="cf-chl-widget">PRIVATE</div></html>',
  {status:403,headers:{'content-type':'text/html','set-cookie':'PRIVATE'}});
 Object.defineProperty(response,'url',{value:'https://private.test/error?token=PRIVATE'});
 const facts=await observeHttpResponse(response,'https://private.test/embed?token=PRIVATE');
 // Execute the actual health-report projection, which previously dropped this field.
 const source=fs.readFileSync('./scripts/health_check.mjs','utf8');
 const begin=source.indexOf('network_observations: Array.isArray(worker.network_observations)');
 const end=source.indexOf('      settings_diagnostics:',begin);
 if(begin<0||end<0) throw new Error('health projection unavailable');
 const expression=source.slice(begin+'network_observations: '.length,end).trim().replace(/,$/,'');
 const normalize=new Function('worker','safeMediaFacts','safeHttpFacts','sanitizeError','return ('+expression+');');
 const worker={network_observations:[{status:403,host:'reader.test',http_observation:{...facts,raw_body:'PRIVATE'}}]};
 const row=normalize(worker,safeMediaFacts,safeHttpFacts,()=>null)[0];
 if(!row.http_observation) throw new Error('health projection dropped HTTP diagnostics');
 if(JSON.stringify(row.http_observation).includes('PRIVATE')) throw new Error('health projection leaked raw values');
 console.log(JSON.stringify(row.http_observation));
})();
'''
observed = json.loads(subprocess.check_output(['node', '-e', code], cwd=ROOT, text=True))
assert observed['page_signal'] == 'challenge_markup' and observed['body_state'] == 'complete'
forged = {**observed, 'raw_body': 'PRIVATE', 'url': 'https://private.test/PRIVATE', 'cookie': 'PRIVATE'}
event = {'stage': 'player', 'host': 'reader.test', 'status': 403, 'ok': False,
         'http_observation': forged, 'provider_function_names': ['resolve']}
result = {'tests': [{'fixture': {'label': 'Missing'}, 'streams_playable': 0,
                     'network_observations': [event]}]}
summary = verifier.result_summary(result)
archived = public_http_observation(summary['networkTrace'][0]['httpObservation'])
assert archived == observed
feedback = verification_feedback({'rows': [{'executionObserved': True,
    'materializedMutationObserved': True, 'candidate': summary}]})
assert feedback['candidate_network'][0]['http_observation'] == observed
assert 'PRIVATE' not in json.dumps(feedback) and 'private.test' not in json.dumps(feedback)

with tempfile.TemporaryDirectory() as directory:
    output = Path(directory) / 'live.json'
    with patch.object(sys, 'argv', ['capture', '--provider', 'demo', '--output', str(output)]), \
         patch.object(capture.subprocess, 'check_output', return_value='a' * 40), \
         patch.object(capture.verifier, 'stage_provider'), \
         patch.object(capture, 'provider_owned_function_names', return_value={'resolve'}), \
         patch.object(capture.verifier, 'health_provider', return_value={'results': [{'provider': 'demo', **result}]}), \
         contextlib.redirect_stdout(io.StringIO()):
        capture.main()
    live = json.loads(output.read_text())
    assert live['network_evidence'][0]['http_observation'] == observed
    # The independent preflight receipt also works when no candidate was produced.
    receipt = public_http_evidence(live, 'a' * 40)
    assert receipt['observations'][0]['http_observation'] == observed
    assert receipt['publicationAuthority'] is False and receipt['proofAuthority'] is False
    assert 'PRIVATE' not in json.dumps(receipt) and 'private.test' not in json.dumps(receipt)
    try:
        public_http_evidence(live, 'b' * 40)
    except ValueError:
        pass
    else:
        raise AssertionError('source mismatch accepted')

for value in ({**forged, 'sampled_bytes': 999999}, {key: ['PRIVATE'] for key in observed},
              {key: 'https://private.test/PRIVATE' for key in observed}):
    clean = public_http_observation(value)
    assert 0 <= clean['sampled_bytes'] <= 8192
    assert public_http_observation(clean) == clean
    assert 'PRIVATE' not in json.dumps(clean) and 'private.test' not in json.dumps(clean)
print('HTTP evidence: real producer -> preflight/evaluation -> public receipt -> feedback, privacy and source matching passed')
