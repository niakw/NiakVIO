#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OVR=ROOT/'provider-overrides.json'

def main():
    original=OVR.read_bytes()
    tmp=Path(tempfile.mkdtemp(prefix='nuvio-new-provider-'))
    try:
        providers=tmp/'providers'/'synthetic'
        providers.mkdir(parents=True)
        js=providers/'brandnew.js'
        payload=b'''module.exports={getStreams:function(){return fetch("https://api.brandnew.example/api/movie/1").then(function(){return fetch("https://brandnew.example/embed/1")}).then(function(){return [];});}};'''
        js.write_bytes(payload)
        registry={
          'schema_version':63,
          'candidates':[{
            'key':'synthetic:brandnew','source':'synthetic','upstream_id':'brandnew','canonical_id':'brandnew',
            'local_path':str(js.relative_to(tmp)),'sha256':hashlib.sha256(payload).hexdigest(),
            'local_patches':[],'metadata':{'id':'brandnew','name':'BrandNew'}
          }]
        }
        (tmp/'candidates.json').write_text(json.dumps(registry,indent=2)+'\n')
        subprocess.run([
          sys.executable,str(ROOT/'scripts/build_provider_runtime_profiles.py'),
          '--stage',str(tmp),'--apply-stage'
        ],cwd=ROOT,check=True,capture_output=True,text=True)
        data=json.loads(OVR.read_text())
        assert data['provider_profile_generation']['same_deep_new_provider_support'] is True
        assert data['provider_profile_generation']['staged_provider_count'] >= 1
        assert 'brandnew' in data['provider_capabilities']
        assert not any(name.startswith('adaptive_domain_') for name in data['patch_profiles'])
        patched=js.read_text()
        assert 'NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1' not in patched
        assert data['provider_profile_generation']['automatic_bundle_rewrite'] is False
        updated=json.loads((tmp/'candidates.json').read_text())['candidates'][0]
        assert updated['sha256']==hashlib.sha256(js.read_bytes()).hexdigest()
        assert not any('adaptive_domain_brandnew' in str(x) for x in updated.get('local_patches',[]))
        print('same-deep new provider profile test passed')
    finally:
        OVR.write_bytes(original)
        shutil.rmtree(tmp,ignore_errors=True)

if __name__=='__main__': main()
