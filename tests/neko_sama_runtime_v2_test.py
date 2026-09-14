#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))

import neko_sama_runtime_v1 as neko

wrapper = neko._neko_wrapper()
assert neko.CONTRACT_MARKER in wrapper
assert 'indexOf("eplister")' in wrapper
assert 'server-group' in wrapper
assert 'player-iframe' in wrapper
assert '/?s=' in wrapper
assert 'nekoFollowHub' in wrapper
assert 'saison|saga' in wrapper
assert wrapper.count('async function neko(meta)') == 1
assert wrapper.count('NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1') == 1
print('neko-sama v2 search/season/eplister runtime contract passed')
