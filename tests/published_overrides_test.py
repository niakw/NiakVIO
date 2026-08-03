#!/usr/bin/env python3
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Static assertions ensure the true publish path has both defence-in-depth and
# a final tree guard, rather than only a staging-unit test.
promote = (ROOT / 'scripts/promote_candidates.py').read_text(encoding='utf-8')
workflow = (ROOT / '.github/workflows/sync.yml').read_text(encoding='utf-8')
assert 'apply_overrides(candidate["canonical_id"], staged_data)' in promote
assert 'python scripts/validate_published_overrides.py' in workflow

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root/'providers').mkdir()
    (root/'provider-overrides.json').write_text(json.dumps({
        'domain_replacements': {'old.example':'new.example'},
        'provider_patches': {'movix': {'replacements': {'old.example':'new.example'}}}
    }))
    (root/'providers/movix--aio--good.js').write_text('const x="new.example";')
    (root/'providers/movix.js').write_text('const x="old.example";')
    (root/'manifest.next.json').write_text(json.dumps({'scrapers':[{'id':'movix','filename':'providers/movix--aio--good.js'}]}))
    script=(ROOT/'scripts/validate_published_overrides.py').read_text().replace(
        'ROOT = Path(__file__).resolve().parents[1]', f'ROOT = Path({str(root)!r})')
    test_script=root/'validate.py'; test_script.write_text(script)
    result=subprocess.run(['python',str(test_script)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert not (root/'providers/movix.js').exists()

# Regression: a provider id that is a prefix of another provider id must never
# delete the longer provider's selected bundle (4khdhub vs 4khdhubnew).
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root/'providers').mkdir()
    (root/'provider-overrides.json').write_text(json.dumps({
        'domain_replacements': {},
        'provider_patches': {
            '4khdhub': {'replacements': {'4khdhub.one':'new4.hdhub4u.cl'}},
            '4khdhubnew': {}
        }
    }))
    (root/'providers/4khdhub--nuvio--good.js').write_text('const x="new4.hdhub4u.cl";')
    longer = root/'providers/4khdhubnew--aio--good.js'
    longer.write_text('const x="4khdhub.one";')
    (root/'manifest.next.json').write_text(json.dumps({'scrapers':[
        {'id':'4khdhub','filename':'providers/4khdhub--nuvio--good.js'},
        {'id':'4khdhubnew','filename':'providers/4khdhubnew--aio--good.js'}
    ]}))
    script=(ROOT/'scripts/validate_published_overrides.py').read_text().replace(
        'ROOT = Path(__file__).resolve().parents[1]', f'ROOT = Path({str(root)!r})')
    test_script=root/'validate.py'; test_script.write_text(script)
    result=subprocess.run(['python',str(test_script)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert longer.exists(), '4khdhub validation deleted the 4khdhubnew bundle'

print('published override tests passed')
