#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'finalize_domain_refresh.py'


def dump(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')


with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td)
    before = {
        'version': '5.19.0',
        'scrapers': [
            {'id': 'alpha', 'version': '1.2.3', 'filename': 'providers/alpha--old.js'},
            {'id': 'beta', 'version': '2.0.0', 'filename': 'providers/beta--same.js'},
        ],
    }
    current = {
        'version': '5.19.0',
        'scrapers': [
            {'id': 'alpha', 'version': '1.2.3', 'filename': 'providers/alpha--new.js'},
            {'id': 'beta', 'version': '2.0.0', 'filename': 'providers/beta--same.js'},
        ],
    }
    before_path = root / 'before.json'
    dump(before_path, before)
    dump(root / 'manifest.json', current)
    dump(root / 'vf/manifest.json', {'version': '5.19.0', 'scrapers': [{'id': 'alpha', 'version': '1.2.3', 'filename': '../providers/alpha--new.js'}]})
    dump(root / 'package.json', {'version': '5.19.0'})
    dump(root / 'sources.json', {'manifest_version': '5.19.0', 'repository': {'manifest_version': '5.19.0'}})

    script = SCRIPT.read_text(encoding='utf-8').replace(
        'ROOT = Path(__file__).resolve().parents[1]',
        f'ROOT = Path({str(root)!r})',
    )
    local_script = root / 'finalize.py'
    local_script.write_text(script, encoding='utf-8')
    subprocess.run(['python', str(local_script), '--before-manifest', str(before_path)], check=True)

    finalized = json.loads((root / 'manifest.json').read_text())
    entries = {row['id']: row for row in finalized['scrapers']}
    assert finalized['version'] == '5.19.1'
    assert entries['alpha']['version'] == '1.2.4'
    assert entries['beta']['version'] == '2.0.0'
    assert json.loads((root / 'vf/manifest.json').read_text())['version'] == '5.19.1'
    assert json.loads((root / 'package.json').read_text())['version'] == '5.19.1'
    assert json.loads((root / 'sources.json').read_text())['manifest_version'] == '5.19.1'

print('domain refresh finalizer test passed')
