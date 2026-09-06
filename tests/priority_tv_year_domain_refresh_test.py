#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import refresh_authoritative_hub_domains as refresh
identity=(ROOT/'scripts/provider_patches/global_stream_identity_v1.py').read_text(encoding='utf-8')
assert 'cross-client-shared-tv-year-soft-v8' in identity
assert 'q.seriesYear=Number(q.seriesYear||q.series_year||q.year||0)||0' in identity
assert 'q.seasonYear=Number(q.seasonYear||q.season_year||0)||0' in identity
assert 'if(!episodic(q)&&m.year&&years.length' in identity
assert 'if(m.year&&years.length&&!years.some' not in identity
patch={
 'official_site':'https://flemmix.kim',
 'domain_substitutions':{'flemmix.casa':'flemmix.men'},
 'replacements':{'flemmix.men':'flemmix.kim'},
 'runtime_domain_replacements':{'flemmix.men':'flemmix.kim'},
 'manifest_overrides':{'logo':'https://flemmix.men/favicon.ico'},
}
changes=refresh._reconcile_domain_derivatives(patch,'https://flemmix.kim','https://flemmix.kim')
assert patch['domain_substitutions']['flemmix.casa']=='flemmix.kim', patch
assert patch['manifest_overrides']['logo']=='https://flemmix.kim/favicon.ico', patch
assert changes
data=json.loads((ROOT/'provider-overrides.json').read_text(encoding='utf-8'))
f=data['provider_patches']['flemmix']
assert f['official_site']=='https://flemmix.kim'
assert all(v!='flemmix.men' for v in f.get('domain_substitutions',{}).values())
assert f['domain_substitutions'].get('flemmix.men')=='flemmix.kim'
print('priority TV-year/domain-refresh regression tests passed')
