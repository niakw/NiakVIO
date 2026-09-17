#!/usr/bin/env python3
from pathlib import Path

s = Path('scripts/provider_patches/animesalt_current_runtime_v1.py').read_text(encoding='utf-8')
assert 'NIAKVIO_ANIMESALT_CURRENT_RUNTIME_V1' in s
assert 'NIAKVIO_ANIMESALT_REFERER_ONLY_PLAYER_V72' in s
assert '/series/' in s
assert r'\/episode\/' in s
assert 'headers:{Referer:episodeUrl}' in s
assert 'Origin:' not in s
assert 'officialSite||m.knownSite' in s
for forbidden in ('jujutsu', '95479', '0a09c8844ba8f0936c20bd791130d6b6', 'as-cdn26.top'):
    assert forbidden not in s, forbidden
print('animesalt current runtime test passed')
