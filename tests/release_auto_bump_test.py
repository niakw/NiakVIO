#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script=ROOT/'scripts/bump_release_patch_if_manifest_changed.py'
with tempfile.TemporaryDirectory() as tmp:
    t=Path(tmp); old=t/'old.json'; new=t/'new.json'
    old.write_text(json.dumps({'name':'x','version':'5.19.3','scrapers':[{'id':'dahmermovies'}]}))
    new.write_text(json.dumps({'name':'x','version':'5.19.3','scrapers':[]}))
    r=subprocess.run([sys.executable,str(script),'--previous',str(old),'--manifest',str(new)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    assert json.loads(new.read_text())['version']=='5.19.4'
    # Already advanced candidates are not double-bumped.
    new.write_text(json.dumps({'name':'x','version':'5.20.0','scrapers':[]}))
    r=subprocess.run([sys.executable,str(script),'--previous',str(old),'--manifest',str(new)],capture_output=True,text=True)
    assert r.returncode==0
    assert json.loads(new.read_text())['version']=='5.20.0'
print('automatic release bump tests passed')
