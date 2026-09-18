#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'scripts'/'provider_patches'/'allanime_current_runtime_v1.py').read_text(encoding='utf-8')

assert 'https://ww2.aniwatch.fit' not in src
assert 'NIAKVIO_PROVIDER_MODEL.officialSite' in src
assert 'NIAKVIO_PROVIDER_MODEL.knownSite' in src
assert 'if(!BASE)return []' in src

print('AllAnime Domain Refresh authority contract passed')
