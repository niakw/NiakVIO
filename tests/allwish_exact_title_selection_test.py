#!/usr/bin/env python3
from pathlib import Path

p = Path('scripts/provider_patches/allwish_current_runtime_v1.py')
s = p.read_text(encoding='utf-8')
assert 'NIAKVIO_ALLWISH_EXACT_TITLE_SELECTION_V70' in s
assert 'if(body===e)score=Math.max(score,320)' in s
assert 'else if(body.indexOf(e)>=0)score=Math.max(score,100)' in s
# The repair must stay generic: fixtures and observed current IDs are evidence, not runtime constants.
for forbidden in ('jujutsu-kaisen', '1103', 'aFhYa3RJ', 'bVdQSnky'):
    assert forbidden not in s, forbidden
print('allwish exact-title selection test passed')
