from __future__ import annotations
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'scripts'/'local'/'test_global_provider_repair.py'
spec=importlib.util.spec_from_file_location('global_repair',MODULE); assert spec and spec.loader
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def result(pid,source,audio=None,subs=None,height=1080,path=None):
    obs=[]
    if path:
        obs=[{'stage':'player','status':200,'infrastructure':False,'path_pattern':path}]
    return {'key':f'{pid}:{source}','canonical_id':pid,'source':source,'status':'healthy','score':90,'verified_max_height':height,'evidence':{'streams_playable':1,'payload_verified_streams':1},'tests':[{'fixture':{'mediaType':'movie','category':'movie'},'streams_returned':1,'streams_playable':1,'payload_verified_streams':1,'audio_languages':audio or [],'subtitle_languages':subs or [],'effective_max_height':height,'network_observations':obs}]}

known={'movix','purstream','goated'}
clean=m.row(result('purstream','aio',audio=['fr']),{},known)
assert clean['strictly_playable'] is True
assert clean['vf_eligible'] is True
assert clean['movie_vf']==1

contaminated=m.row(result('movix','aio',audio=['fr'],path='/api/purstream/movie/{id}/stream'),{},known)
assert contaminated['strictly_playable'] is False
assert contaminated['vf_eligible'] is False
assert contaminated['foreign_provider_routes']=='purstream'

vo4k=m.row(result('demo','vo',audio=['en'],height=2160),{},known|{'demo'})
vf1080=m.row(result('demo','vf',audio=['fr'],height=1080),{},known|{'demo'})
assert m.rank(vf1080,True)>m.rank(vo4k,True), 'VF movie proof must beat higher-resolution VO in VF selection'
assert m.rank(vo4k,False)>m.rank(vf1080,False), 'general selection may still prefer quality'
print('VF movie validation tests passed')
