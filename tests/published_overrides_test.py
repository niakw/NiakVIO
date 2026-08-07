#!/usr/bin/env python3
from __future__ import annotations
import json
import shutil
import subprocess
import sys
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
    (root/'override_text_utils.py').write_text((ROOT/'scripts/override_text_utils.py').read_text())
    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert not (root/'providers/movix.js').exists()

# A provider id must not match a longer sibling id while removing stale files.
# Regression: validating 4khdhub previously deleted 4khdhubnew because the
# cleanup used the broad glob ``4khdhub*.js``.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root/'providers').mkdir()
    (root/'provider-overrides.json').write_text(json.dumps({
        'domain_replacements': {},
        'provider_patches': {
            '4khdhub': {'replacements': {'old.example':'new.example'}},
            '4khdhubnew': {}
        }
    }))
    (root/'providers/4khdhub--aio--good.js').write_text('const x="new.example";')
    sibling = root/'providers/4khdhubnew--published-baseline--good.js'
    sibling.write_text('const x="old.example";')
    (root/'manifest.next.json').write_text(json.dumps({'scrapers':[
        {'id':'4khdhub','filename':'providers/4khdhub--aio--good.js'},
        {'id':'4khdhubnew','filename':'providers/4khdhubnew--published-baseline--good.js'}
    ]}))
    script=(ROOT/'scripts/validate_published_overrides.py').read_text().replace(
        'ROOT = Path(__file__).resolve().parents[1]', f'ROOT = Path({str(root)!r})')
    test_script=root/'validate.py'; test_script.write_text(script)
    (root/'override_text_utils.py').write_text((ROOT/'scripts/override_text_utils.py').read_text())
    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert sibling.exists(), '4khdhub validation deleted the distinct 4khdhubnew provider'

# Adaptive repairs are generated from live runtime evidence, so they are not
# static patch_profiles. Their provenance must nevertheless be accepted only
# for the known runtime strategy and only when its code marker exists in the
# exact published bundle. Arbitrary unknown runtime profile names remain fatal.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root/'providers').mkdir()
    (root/'provider-overrides.json').write_text(json.dumps({
        'domain_replacements': {},
        'provider_patches': {},
        'patch_profiles': {}
    }))
    provider = root/'providers/demo--nuvio--good.js'
    provider.write_text('/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V3 */\nmodule.exports={};\n')
    (root/'manifest.next.json').write_text(json.dumps({'scrapers':[
        {'id':'demo','filename':'providers/demo--nuvio--good.js'}
    ]}))
    provenance = {
        'providers': {
            'demo': {
                'local_patches': [{
                    'type':'patch_profile',
                    'profile':'adaptive_runtime_recovery',
                    'phase':'runtime',
                    'options':{'base_url':'https://demo.example'}
                }]
            }
        }
    }
    (root/'PROVENANCE.json').write_text(json.dumps(provenance))
    script=(ROOT/'scripts/validate_published_overrides.py').read_text().replace(
        'ROOT = Path(__file__).resolve().parents[1]', f'ROOT = Path({str(root)!r})')
    test_script=root/'validate.py'; test_script.write_text(script)
    (root/'override_text_utils.py').write_text((ROOT/'scripts/override_text_utils.py').read_text())

    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr + result.stdout

    provider.write_text('module.exports={};\n')
    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    assert result.returncode == 1
    assert 'NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V3' in result.stderr + result.stdout

    provider.write_text('/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V3 */\nmodule.exports={};\n')
    provenance['providers']['demo']['local_patches'][0]['profile'] = 'unknown_runtime_strategy'
    (root/'PROVENANCE.json').write_text(json.dumps(provenance))
    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    assert result.returncode == 1
    assert 'unknown profile unknown_runtime_strategy' in result.stderr + result.stdout

print('published override tests passed')
