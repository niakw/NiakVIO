#!/usr/bin/env python3
from pathlib import Path

p=Path(__file__).resolve().parents[1]/'tests/global_stream_presentation_pipeline_test.py'
text=p.read_text(encoding='utf-8')
if 'tmdbUrls' not in text:
    text=text.replace('let tmdbCalls=0;\nlet mediaCalls=0;','let tmdbCalls=0;\nlet tmdbUrls=[];\nlet mediaCalls=0;',1)
    text=text.replace("    tmdbCalls++;\n    return {","    tmdbCalls++;\n    tmdbUrls.push(url);\n    return {",1)
    text=text.replace('console.log(JSON.stringify({row:row,tmdbCalls:tmdbCalls,mediaCalls:mediaCalls}));','console.log(JSON.stringify({row:row,tmdbCalls:tmdbCalls,tmdbUrls:tmdbUrls,mediaCalls:mediaCalls,cacheKeys:Object.keys(global.__nuvioTmdbMetadataCacheV1||{})}));',1)
    p.write_text(text,encoding='utf-8')
for needle in ('let tmdbUrls=[];','tmdbUrls.push(url);','cacheKeys:Object.keys(global.__nuvioTmdbMetadataCacheV1||{})'):
    if needle not in p.read_text(encoding='utf-8'):
        raise AssertionError(needle)
print('PRESENTATION_PIPELINE_DIAGNOSTICS_V1_OK')
