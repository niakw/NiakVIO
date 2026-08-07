#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/validate_deep_health_integrity.py'

config=json.loads((ROOT/'health-config.json').read_text(encoding='utf-8'))
health_source=(ROOT/'scripts/health_check.mjs').read_text(encoding='utf-8')
assert int(config['modes']['deep']['worker_memory_mb']) >= 512
assert int(config['modes']['availability']['worker_memory_mb']) < int(config['modes']['deep']['worker_memory_mb'])
assert int(config['modes']['retry']['worker_memory_mb']) < int(config['modes']['deep']['worker_memory_mb'])
assert int(config['modes']['quick']['worker_memory_mb']) < int(config['modes']['deep']['worker_memory_mb'])
for mode_name, mode in config['modes'].items():
    assert int(mode.get('minimum_vod_duration_seconds', 0)) >= 60, mode_name
for token in ['modeConfig.worker_memory_mb', 'NUVIO_WORKER_MEMORY_MB', 'NUVIO_WORKER_MEMORY_EXHAUSTED', 'worker_memory_exhausted', 'appendTail', 'short_vod_preview', 'minimum_vod_duration_seconds', 'totalDurationSeconds']:
    assert token in health_source, token

def run(health, repairs):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); h=root/'health.json'; r=root/'repairs.json'
        h.write_text(json.dumps(health)); r.write_text(json.dumps(repairs))
        return subprocess.run([sys.executable,str(SCRIPT),'--health',str(h),'--repairs',str(r)],capture_output=True,text=True)

valid_health={'schema_version':66,'results':[{'key':'source:sample','tests':[{'status':'no_streams','failure_class':'content_lookup_completed_no_streams','worker_ok':True,'network_observations':[{'host':'provider.example','status':200,'infrastructure':False,'stage':'search'}]}]}]}
valid_repairs={'schema_version':2,'accepted_repairs':1,'rounds':[{'round':1,'attempts':[{'status':'generated','parent_sha256':'a','profile':'dle','repair_sha256':'b'}],'accepted':[{'parent_key':'source:sample','streams_playable_before':0,'streams_playable_after':1,'runtime_errors_before':0,'runtime_errors_after':0,'reason':'strict_playable_stream_improvement'}],'rejected':[]}]}
assert run(valid_health,valid_repairs).returncode==0

# The worker records locally rejected object serialization attempts so the
# invocation diagnostics remain explainable. status=None plus the dedicated
# error code proves guardedFetch was never reached and must therefore pass.
contained_health={'schema_version':66,'results':[{'key':'source:contained','tests':[{'status':'no_streams','failure_class':'content_lookup_completed_no_streams','worker_ok':True,'network_observations':[{'path_pattern':'/[object%20Object]/','status':None,'ok':False,'error_code':'NUVIO_INVALID_REQUEST_ARGUMENT'}]}]}]}
assert run(contained_health,{'schema_version':2,'rounds':[]}).returncode==0

# A malformed path with an HTTP status did escape local containment and remains
# a publication-blocking integrity failure.
bad_health={'schema_version':66,'results':[{'key':'source:bad','tests':[{'status':'runtime_error','worker_ok':False,'network_observations':[{'path_pattern':'/[object%20Object]/','status':400,'ok':False,'error_code':None}]}]}]}
bad_repairs={'schema_version':2,'rounds':[{'round':1,'attempts':[],'accepted':[{'parent_key':'source:bad','streams_playable_before':0,'streams_playable_after':0,'reason':'strict_runtime_improvement'}],'rejected':[{'parent_key':'source:bad','status':'runtime_error'}]}]}
result=run(bad_health,bad_repairs)
assert result.returncode==1
assert 'malformed invocation request' in result.stdout
assert 'accepted without playable-stream improvement' in result.stdout
assert 'runtime repair error not preserved' in result.stdout
print('deep health integrity tests passed')
