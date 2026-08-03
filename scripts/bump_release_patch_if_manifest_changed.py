#!/usr/bin/env python3
"""Bump the release patch when a newly promoted manifest changes client-visible data.

Nuvio clients may cache a manifest/provider set by release version. Publishing
new filenames, enabled states, supported types or removing providers under the
same version can therefore leave stale providers visible. This script compares
against the manifest currently published in Git and bumps once, only when the
candidate has changed and has not already advanced its version.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
SEMVER=re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

def load(path: Path): return json.loads(path.read_text(encoding='utf-8'))
def semver(value: str):
    m=SEMVER.fullmatch(str(value or '').strip())
    if not m: raise ValueError(f'invalid semantic version: {value!r}')
    return tuple(map(int,m.groups()))
def comparable(value: dict):
    clone=dict(value); clone.pop('version',None); return clone

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--previous',required=True); ap.add_argument('--manifest',default='manifest.json')
    args=ap.parse_args(); previous_path=Path(args.previous); manifest_path=Path(args.manifest)
    previous=load(previous_path); candidate=load(manifest_path)
    old=semver(previous.get('version')); current=semver(candidate.get('version'))
    changed=comparable(previous)!=comparable(candidate)
    if changed and current <= old:
        current=(old[0],old[1],old[2]+1)
        candidate['version']='.'.join(map(str,current))
        manifest_path.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f"manifest changed; release bumped to {candidate['version']}")
    else:
        print(f"manifest {'changed' if changed else 'unchanged'}; release remains {candidate.get('version')}")
    return 0
if __name__=='__main__': raise SystemExit(main())
