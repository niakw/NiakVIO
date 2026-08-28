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
reapply = (ROOT / 'scripts/reapply_published_overrides.py').read_text(encoding='utf-8')
assert 'parser.add_argument(\n        "--primary",' in reapply
assert 'parser.add_argument(\n        "--skip-secondary",' in reapply
assert 'primary_path = (ROOT / primary_arg).resolve()' in reapply
assert 'secondary_paths = () if args.skip_secondary else SECONDARY' in reapply
assert 'python scripts/reapply_published_overrides.py --primary manifest.next.json --skip-secondary' in workflow
post_promotion = workflow.index('Reapply durable overrides after candidate promotion')
pending_reapply = workflow.index('python scripts/reapply_published_overrides.py --primary manifest.next.json --skip-secondary', post_promotion)
pending_validate = workflow.index('python scripts/validate_published_overrides.py', pending_reapply)
assert post_promotion < pending_reapply < pending_validate

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

# During a two-phase publication transaction, a bundle can be absent from the
# pending manifest while still being authoritative through the published
# manifest, LKG or provenance. Validation must never delete such a bundle just
# because it still contains an old domain; prune owns deletion after all
# references converge.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root/'providers').mkdir()
    (root/'provider-overrides.json').write_text(json.dumps({
        'domain_replacements': {},
        'provider_patches': {
            'coflix': {'replacements': {'old.example':'new.example'}}
        },
        'patch_profiles': {}
    }))
    pending = root/'providers/coflix--nuvio--pending.js'
    pending.write_text('const x="new.example";')
    protected = root/'providers/coflix--nuvio--48239f7b107a98b2.js'
    protected.write_text('const x="old.example";')
    (root/'manifest.next.json').write_text(json.dumps({'scrapers':[
        {'id':'coflix','filename':'providers/coflix--nuvio--pending.js'}
    ]}))
    (root/'manifest.json').write_text(json.dumps({'scrapers':[
        {'id':'coflix','filename':'providers/coflix--nuvio--48239f7b107a98b2.js'}
    ]}))
    (root/'PROVENANCE.json').write_text(json.dumps({'providers':{
        'coflix': {
            'published_filename':'providers/coflix--nuvio--48239f7b107a98b2.js',
            'canonical_source_filename':'providers/coflix--nuvio--48239f7b107a98b2.js',
            'local_patches':[]
        }
    }}))
    (root/'provider-lkg.json').write_text(json.dumps({'providers':{
        'coflix': {'filename':'providers/coflix--nuvio--48239f7b107a98b2.js'}
    }}))
    script=(ROOT/'scripts/validate_published_overrides.py').read_text().replace(
        'ROOT = Path(__file__).resolve().parents[1]', f'ROOT = Path({str(root)!r})')
    test_script=root/'validate.py'; test_script.write_text(script)
    (root/'override_text_utils.py').write_text((ROOT/'scripts/override_text_utils.py').read_text())
    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert protected.exists(), 'validator deleted a bundle still protected by the publication transaction'
    assert pending.exists()

# Stale-file removal must use exact provider-id boundaries so a provider id
# cannot match a longer sibling id.
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
    provider.write_text('/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4 */\nmodule.exports={};\n')
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
    adaptive_output = result.stderr + result.stdout
    assert result.returncode == 1, adaptive_output
    assert 'NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4' in adaptive_output, adaptive_output

    provider.write_text('/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4 */\nmodule.exports={};\n')
    provenance['providers']['demo']['local_patches'][0]['profile'] = 'unknown_runtime_strategy'
    (root/'PROVENANCE.json').write_text(json.dumps(provenance))
    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    unknown_output = result.stderr + result.stdout
    assert result.returncode == 1, unknown_output
    assert 'unknown profile unknown_runtime_strategy' in unknown_output, unknown_output

# Revisioned adaptive runtime profiles must validate against their own
# immutable marker. V5 is not a V4 alias and must never be downgraded.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root/'providers').mkdir()
    (root/'provider-overrides.json').write_text(json.dumps({
        'domain_replacements': {},
        'provider_patches': {},
        'patch_profiles': {}
    }))
    provider = root/'providers/demo--nuvio--v5.js'
    provider.write_text('/* NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5:test */\nmodule.exports={};\n')
    (root/'manifest.next.json').write_text(json.dumps({'scrapers':[
        {'id':'demo','filename':'providers/demo--nuvio--v5.js'}
    ]}))
    provenance = {'providers': {'demo': {'local_patches': [{
        'type':'patch_profile',
        'profile':'adaptive_runtime_recovery',
        'phase':'runtime',
        'revision':5,
        'options':{'base_url':'https://demo.example'}
    }]}}}
    (root/'PROVENANCE.json').write_text(json.dumps(provenance))
    script=(ROOT/'scripts/validate_published_overrides.py').read_text().replace(
        'ROOT = Path(__file__).resolve().parents[1]', f'ROOT = Path({str(root)!r})')
    test_script=root/'validate.py'; test_script.write_text(script)
    (root/'override_text_utils.py').write_text((ROOT/'scripts/override_text_utils.py').read_text())

    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr + result.stdout

    provider.write_text('module.exports={};\n')
    result=subprocess.run([sys.executable,str(test_script)],capture_output=True,text=True)
    output=result.stderr + result.stdout
    assert result.returncode == 1, output
    assert 'NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5' in output, output

# A runtime repair rejected by the deep loop must not poison a preserved
# previously-published artifact. The preservation path is explicit in
# provenance, and the absence of the immutable runtime marker proves that the
# old runtime patch record is stale. It is removed and audited. The same marker
# absence outside this preservation path remains fatal in the test above.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root/'providers').mkdir()
    (root/'provider-overrides.json').write_text(json.dumps({
        'domain_replacements': {},
        'provider_patches': {},
        'patch_profiles': {}
    }))
    provider = root/'providers/movies4u--nuvio--preserved.js'
    provider.write_text('module.exports={};\n')
    (root/'manifest.next.json').write_text(json.dumps({'scrapers':[
        {'id':'movies4u','filename':'providers/movies4u--nuvio--preserved.js'}
    ]}))
    provenance = {
        'providers': {
            'movies4u': {
                'activation_mode':'preserved_current_ci_uncertain',
                'preserved_reason':'ci_uncertain_kept_last_published_artifact',
                'local_patches':[{
                    'type':'patch_profile',
                    'profile':'adaptive_runtime_recovery',
                    'phase':'runtime',
                    'options':{'base_url':'https://new3.movies4u.clinic'}
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
    normalized=json.loads((root/'PROVENANCE.json').read_text())
    record=normalized['providers']['movies4u']
    assert record['local_patches'] == []
    assert record['discarded_stale_patch_records'] == [{
        'type':'patch_profile',
        'profile':'adaptive_runtime_recovery',
        'phase':'runtime',
        'reason':'marker_absent_from_preserved_artifact'
    }]
    assert 'discarded stale preserved runtime provenance: movies4u:adaptive_runtime_recovery' in result.stdout

print('published override tests passed')