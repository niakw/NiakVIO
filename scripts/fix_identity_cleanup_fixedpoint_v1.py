#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/apply_core_identity_ownership_cleanup.py')
text = path.read_text(encoding='utf-8')
old = '''def main() -> int:\n    patch_core_identity_zero_year_episodic()\n'''
new = '''def main() -> int:\n    identity = read("scripts/provider_patches/global_stream_identity_v1.py")\n    if "cross-client-shared-tmdb-owner-zero-episodic-year-v11" in identity:\n        validate_source_state()\n        print("CORE_IDENTITY_OWNERSHIP_CLEANUP_OK episodic_year_influence=0 already_current=true")\n        return 0\n    patch_core_identity_zero_year_episodic()\n'''
if new in text:
    print('IDENTITY_CLEANUP_FIXEDPOINT_ALREADY_PRESENT')
elif text.count(old) == 1:
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('IDENTITY_CLEANUP_FIXEDPOINT_APPLIED')
else:
    raise SystemExit(f'identity cleanup main anchor count={text.count(old)}')
