#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
apply_path = root / 'scripts/apply_provider_overrides.py'
text = apply_path.read_text(encoding='utf-8')
old = '''            options = dict(media_policy.get("options") or {})
            before = text
            text = _apply_patch_script(text, provider_id, patch_script, options, None)
'''
new = '''            options = dict(media_policy.get("options") or {})
            provider_options = script_options.get(patch_script)
            if provider_options is not None:
                if not isinstance(provider_options, dict):
                    raise ValueError(
                        f"provider_patches.{provider_id}.patch_script_options[{patch_script!r}] must be an object"
                    )
                options.update(provider_options)
            before = text
            text = _apply_patch_script(text, provider_id, patch_script, options, None)
'''
if old not in text:
    raise SystemExit('media policy option merge target not found')
text = text.replace(old, new, 1)
apply_path.write_text(text, encoding='utf-8')

test_path = root / 'tests/scoped_playback_context_regression_test.py'
test = test_path.read_text(encoding='utf-8')
if 'media policy must propagate provider-scoped options' not in test:
    test += r'''

# Integration contract: global media enrichment must receive provider-scoped
# options. This is what lets StreamZo retain its proven browser context without
# synthesizing the same headers for unrelated providers.
import sys
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('apply_provider_overrides_scoped_test', ROOT/'scripts/apply_provider_overrides.py')
assert spec and spec.loader
apply_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply_mod)

captured = []
def capture_patch(text, provider_id, patch_script, options, profile_name):
    captured.append((provider_id, patch_script, dict(options)))
    return text + f"\n/* capture:{provider_id}:{patch_script} */\n"
apply_mod._apply_patch_script = capture_patch

apply_mod.apply_overrides('streamzo', b'module.exports={getStreams:async()=>[]};\n', phase='discovery')
streamzo_media = [opts for pid,path,opts in captured if pid == 'streamzo' and path.endswith('global_media_enrichment_v1.py')]
assert streamzo_media, captured
assert streamzo_media[-1].get('default_user_agent','').startswith('Mozilla/5.0'), streamzo_media[-1]

captured.clear()
apply_mod.apply_overrides('cineby', b'module.exports={getStreams:async()=>[]};\n', phase='discovery')
ordinary_media = [opts for pid,path,opts in captured if pid == 'cineby' and path.endswith('global_media_enrichment_v1.py')]
assert ordinary_media, captured
assert not ordinary_media[-1].get('default_user_agent'), ordinary_media[-1]
# media policy must propagate provider-scoped options
'''
    test_path.write_text(test, encoding='utf-8')

print('scoped media-policy option propagation staged')
