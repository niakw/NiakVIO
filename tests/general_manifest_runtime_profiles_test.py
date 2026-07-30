#!/usr/bin/env python3
import json,subprocess,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
subprocess.run(['python3',str(ROOT/'scripts/build_provider_runtime_profiles.py')],check=True,cwd=ROOT)
d=json.loads((ROOT/'provider-overrides.json').read_text())
m=json.loads((ROOT/'manifest.json').read_text())
ids={str(x.get('id')) for x in m.get('scrapers',[]) if x.get('id')}
caps=d.get('provider_capabilities',{})
missing=sorted(ids-set(caps))
assert not missing, f'missing capability profiles: {missing}'
valid={'iframe_player','mixed_embed_resolver','api_stream_resolver','direct_media','html_scraper','official_domain_hub'}
bad=sorted((i,caps[i].get('strategy')) for i in ids if caps[i].get('strategy') not in valid)
assert not bad,bad
assert d.get('provider_profile_generation',{}).get('provider_count')>=len(ids)
print(f'general manifest runtime profiles test passed ({len(ids)} providers covered)')
