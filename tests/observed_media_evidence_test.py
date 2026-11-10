"""An alternate media diagnostic survives reports but cannot create streams."""
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
from observed_media_evidence import public_observed_media_probe
import capture_brain_live_context as capture
import evaluate_brain_llm_force_candidates as verifier
from run_hosted_brain_repair_loop import verification_feedback

code = r'''
const fs=require('node:fs');
const {createObservedMediaProbe,safeObservedMediaProbe}=require('./scripts/observed_media_probe.cjs');
const {safeAddressFields}=require('./scripts/address_reference.cjs');
const {safeHttpFacts}=require('./scripts/http_response_observation.cjs');
const {safeReaderProbe}=require('./scripts/reader_user_agent_probe.cjs');
const {safeMediaFacts}=require('./scripts/media_observation.cjs');
(async()=>{
 const bytes=Buffer.alloc(80);bytes.writeUInt32BE(16,0);bytes.write('ftyp',4);
 bytes.writeUInt32BE(48,16);bytes.write('mvhd',20);bytes.writeUInt32BE(1000,36);bytes.writeUInt32BE(1440000,40);
 const probe=createObservedMediaProbe({fetch:async()=>new Response(bytes,{status:206,headers:{'content-type':'video/mp4'}})});
 const scope='s0123456789abcdef';
 const parent={address_scope:scope,request_ref:'r1',response_ref:'r1',address_refs_truncated:false,
  address_trace_truncated:false,stage:'player',host:'reader.test',status:200,raw_body:'PRIVATE'};
 probe.recordRequest('https://media.test/old.mp4?token=PRIVATE',{headers:{Referer:'https://reader.test/embed?token=PRIVATE'}},
  {address_scope:scope,request_ref:'r2',referer_ref:'r1',method:'GET',media_observation:{signature:'mp4',
   durationSeconds:5,bytesSampled:80,readState:'complete',cancelState:'complete'}});
 probe.recordCandidate('https://media.test/fresh.mp4?token=PRIVATE','r3','r1',parent);
 await probe.flush({streamsReturned:0,expectedDurationSeconds:1440});
 const source=fs.readFileSync('./scripts/health_check.mjs','utf8');
 const begin=source.indexOf('network_observations: Array.isArray(worker.network_observations)');
 const end=source.indexOf('      settings_diagnostics:',begin);
 const expression=source.slice(begin+'network_observations: '.length,end).trim().replace(/,$/,'');
 const normalize=new Function('worker','safeMediaFacts','safeHttpFacts','safeReaderProbe','safeAddressFields','safeObservedMediaProbe','sanitizeError','return ('+expression+');');
 console.log(JSON.stringify(normalize({network_observations:[parent]},safeMediaFacts,safeHttpFacts,safeReaderProbe,safeAddressFields,safeObservedMediaProbe,()=>null)[0]));
})();
'''
event = json.loads(subprocess.check_output(['node', '-e', code], cwd=ROOT, text=True))
assert 'PRIVATE' not in json.dumps(event)
probe = event['observed_media_probe']
assert probe['attempted'] and probe['source_ref'] == 'r3' and probe['template_ref'] == 'r2'
assert probe['media_observation']['durationSeconds'] == 1440
assert public_observed_media_probe(probe) == probe
result = {'provider': 'demo', 'tests': [{'fixture': {'label': 'Missing'}, 'streams_playable': 0,
                                        'network_observations': [event]}]}
summary = verifier.result_summary(result)
assert summary['streamsPlayable'] == 0, 'a diagnostic response is never a playable stream'
assert summary['networkTrace'][0]['observedMediaProbe'] == probe
feedback = verification_feedback({'rows': [{'executionObserved': True, 'candidate': summary}]})
assert feedback['candidate_network'][0]['observed_media_probe'] == probe
with tempfile.TemporaryDirectory() as directory:
    output = Path(directory) / 'live.json'
    with patch.object(sys, 'argv', ['capture', '--provider', 'demo', '--output', str(output)]), \
         patch.object(capture.subprocess, 'check_output', return_value='a' * 40), \
         patch.object(capture.verifier, 'stage_provider'), \
         patch.object(capture, 'provider_owned_function_names', return_value=set()), \
         patch.object(capture.verifier, 'health_provider', return_value={'results': [result]}), \
         patch.object(capture.verifier, 'strict_repair_fixture_contract',
                      return_value={('anime', '95479'): {'tmdbId': '95479', 'season': 1, 'episode': 1}}), \
         contextlib.redirect_stdout(io.StringIO()):
        capture.main()
    assert json.loads(output.read_text())['network_evidence'][0]['observed_media_probe'] == probe
for forged in ({**probe, 'attempted': 'true'}, {**probe, 'source_ref': 'https://PRIVATE'},
               {**probe, 'template_ref': 'r513'}, {**probe, 'attempted': False, 'outcome': 'response'}):
    assert public_observed_media_probe(forged) is None
clean = public_observed_media_probe({**probe, 'status': True, 'url': 'PRIVATE',
    'media_observation': {**probe['media_observation'], 'bytesSampled': 999999, 'raw_body': 'PRIVATE'}})
assert clean['status'] is None and clean['media_observation']['bytesSampled'] == 32768
assert 'PRIVATE' not in json.dumps(clean)
subprocess.check_call([sys.executable, '-c',
    'from scripts.observed_media_evidence import public_observed_media_probe; '
    'assert public_observed_media_probe({}) is None'], cwd=ROOT)
print('Observed media evidence: real producer/health/report/feedback, prefix privacy and zero stream authority passed')
