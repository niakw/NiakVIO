#!/usr/bin/env python3
"""Movie/tv/anime repair proof must use its actual immutable media fixtures."""
import copy
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import evaluate_brain_llm_force_candidates as verify

movie=verify.strict_repair_fixture_contract('mallumv')
assert set(key[0] for key in movie)=={'movie'}, movie
assert ('movie','157336') in movie, movie
assert verify.strict_repair_fixture_contract('animekai')
assert {'anime','tv'} == {key[0] for key in verify.strict_repair_fixture_contract('animekai')}
assert len(verify.strict_repair_fixture_contract(None))==2
assert {key[1] for key in verify.strict_repair_fixture_contract(None)}=={'95479','280049'}

def observation(spec,category, probes=()):
    fixture={**copy.deepcopy(spec),'category':category}
    count=len(probes)
    return {'fixture':fixture,'status':'healthy' if count else 'no_streams',
            'streams_returned':count,'streams_playable':count,
            'streams_probed':count,'identity_verified_streams':count,
            'identity_unverified_streams':0,
            'identity_contradiction_count':0,'duration_identity_mismatch_count':0,
            'host_results':list(probes)}

key, spec=next(iter(movie.items()))
probe={
    'host':'media.example.org','http_status':200,'kind':'hls',
    'bytes_sampled':4096,'playback_verified':True,'payload_verified':True,
    'direct_signature_verified':False,'variant_reachable':True,
    'segment_reachable':True,'audio_manifest_reachable':True,
    'audio_segment_reachable':True,'duration_identity_authoritative':True,
    'duration_identity_mismatch':False,'short_vod_preview':False,
    'media_duration_seconds':10140,'expected_duration_seconds':10140,
    'content_identity_status':'match','content_identity_reason':'fixture_duration_match',
    'media_decode':{'attempted':True,'outcome':'decoded','framesDecoded':1}}
before={'tests':[observation(spec,key[0])]}
after={'tests':[observation(spec,key[0],[probe])]}
with patch.dict(os.environ,{'NIAKVIO_REQUIRE_DECODE_PROOF':'1'}):
    ok, reason, facts=verify.decoded_repair_gate(before,after,'MALLUMV')
    assert ok and reason=='decoded_repair_fixture_improvement',(reason,facts)
    assert facts['improvedFixtures']==[spec['label']]
    assert not facts['unresolvedFixtures']
    # A URL which was counted "playable" without strict terminal decode is
    # not a decoded control. Genuine decoding of that same URL is a new proof.
    opaque_before=copy.deepcopy(after)
    opaque_before['tests'][0]['host_results'][0]['media_decode']=None
    gained, gained_reason, gained_facts=verify.decoded_repair_gate(opaque_before,after,'MALLUMV')
    assert gained and gained_reason=='decoded_repair_fixture_improvement',(gained_reason,gained_facts)
    assert gained_facts['improvedFixtures']==[spec['label']]
    assert verify.decoded_repair_gate(before,after)[1]=='decoded_repair_fixture_contract'
    wrong=copy.deepcopy(after)
    wrong['tests'][0]['fixture']['tmdbId']='95479'
    assert verify.decoded_repair_gate(before,wrong,'MALLUMV')[1]=='decoded_repair_fixture_contract'
    wrong=copy.deepcopy(after)
    wrong['tests'][0]['fixture']['expectedDurationMinutes']=24
    assert verify.decoded_repair_gate(before,wrong,'MALLUMV')[1]=='decoded_repair_fixture_contract'
    short=copy.deepcopy(after)
    short['tests'][0]['host_results'][0]['media_duration_seconds']=1440
    assert verify.decoded_repair_gate(before,short,'MALLUMV')[1]=='decoded_repair_no_new_fixture_control'
    wrong=copy.deepcopy(after)
    wrong['tests'][0]['host_results'][0]['media_decode']=None
    assert verify.decoded_repair_gate(before,wrong,'MALLUMV')[1]=='decoded_repair_no_new_fixture_control'

    configs=[]
    def fake_health(**options):
        configs.append(verify.load(options['health_config']))
        return {'results':[]}
    with tempfile.TemporaryDirectory() as directory,patch.object(verify.deep,'run_health',side_effect=fake_health):
        root=Path(directory)
        verify.health_provider(root/'baseline',root/'before', 'MALLUMV')
        verify.health_provider(root/'candidate',root/'after','MALLUMV')
    # Brain evidence must not silently erase the trusted movie and TV identities.
    # A provider/candidate cannot substitute an unregistered TMDB/episode ID.
    movie_summary=verify.fixture_summary({'tests':[observation(spec,'movie')]})
    assert movie_summary[0]['tmdbId']=='157336',movie_summary
    tv_spec=next(f for f in verify.load(ROOT/'health-config.json')['fixtures']['tv']
                 if f['tmdbId']=='1396')
    tv_summary=verify.fixture_summary({'tests':[observation(tv_spec,'tv')]})
    assert tv_summary[0]['tmdbId']=='1396',tv_summary
    assert tv_summary[0]['season']==1 and tv_summary[0]['episode']==1
    # The first evidence pass can have no decoded media at all; it still must
    # carry trusted work identity, not erase the TMDB coordinates.
    with patch.dict(os.environ, {'NIAKVIO_REQUIRE_DECODE_PROOF':'0'}):
        undecoded_summary=verify.fixture_summary({'tests':[observation(tv_spec,'tv')]})
    assert undecoded_summary[0]['tmdbId']=='1396',undecoded_summary
    assert undecoded_summary[0]['season']==1
    assert undecoded_summary[0]['episode']==1
    assert 'decodedMediaControls' not in undecoded_summary[0]
    anime_spec=next(f for f in verify.load(ROOT/'health-config.json')['fixtures']['anime']
                    if f['tmdbId']=='95479')
    anime_summary=verify.fixture_summary({'tests':[observation(anime_spec,'anime')]})
    assert anime_summary[0]['tmdbId']=='95479',anime_summary
    forged=copy.deepcopy(tv_spec)
    forged['tmdbId']='999999999'
    wrong_summary=verify.fixture_summary({'tests':[observation(forged,'tv')]})
    assert wrong_summary[0]['tmdbId']==''
    assert wrong_summary[0]['season'] is None and wrong_summary[0]['episode'] is None
    season_spoof=copy.deepcopy(tv_spec)
    season_spoof['season']=0
    wrong_summary=verify.fixture_summary({'tests':[observation(season_spoof,'tv')]})
    assert wrong_summary[0]['tmdbId']=='' and wrong_summary[0]['episode'] is None
    assert configs[0]==configs[1]
    assert [x['tmdbId'] for x in configs[0]['fixtures']['movie']]==['157336']
    assert configs[0]['fixtures']['anime']==[]
    assert configs[0]['fixtures']['tv']==[]
    assert configs[0]['modes']['deep']['verify_media_decode'] is True

print('BRAIN_CATEGORY_STRICT_DECODE_OK movie fixture baseline/candidate exact + no regression')
