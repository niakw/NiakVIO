#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'scripts'/'provider_patches'/'vostfree_dle_uqload_runtime_v1.py').read_text(encoding='utf-8')

assert 'if(type==="tv")type="anime";' in src
assert 'if(type!=="anime")return null;' in src
assert src.index('if(type==="tv")type="anime";') < src.index('if(type!=="anime")return null;')
print('Vostfree anime semantic / tv transport alias contract passed')
