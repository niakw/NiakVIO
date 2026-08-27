#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script=ROOT/'scripts/select_brain_targeted_probe.py'
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    manifest={'scrapers':[
        {'id':'movie-a','supportedTypes':['movie']},
        {'id':'series-a','supportedTypes':['tv','anime']},
        {'id':'anime-a','supportedTypes':['anime','movie']},
    ]}
    (td/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    (td/'repair.json').write_text(json.dumps({'proposals':[{'provider_id':'series-a'}]}),encoding='utf-8')
    out=td/'out.json'
    subprocess.run([sys.executable,str(script),'--manifest',str(td/'manifest.json'),'--repair-report',str(td/'repair.json'),'--json-out',str(out)],check=True)
    row=json.loads(out.read_text())
    assert row['provider']=='series-a' and row['declared_type']=='tv' and row['slug']=='breaking-bad-s01e01'
    subprocess.run([sys.executable,str(script),'--manifest',str(td/'manifest.json'),'--provider','anime-a','--json-out',str(out)],check=True)
    row=json.loads(out.read_text())
    assert row['declared_type']=='anime' and row['slug']=='jujutsu-kaisen-s01e01'
print('brain targeted probe selector test passed')
