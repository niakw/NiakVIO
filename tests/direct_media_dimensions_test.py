#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'health-config.json').read_text(encoding='utf-8'))
source = (ROOT / 'scripts' / 'health_check.mjs').read_text(encoding='utf-8')

assert config['modes']['deep'].get('inspect_direct_dimensions') is True
for name in ('quick', 'availability', 'retry'):
    assert not config['modes'][name].get('inspect_direct_dimensions'), name

assert 'function parseMp4TrackHeights(body)' in source
assert 'body.readUInt32BE(widthOffset) / 65536' in source
assert 'body.readUInt32BE(heightOffset) / 65536' in source
assert "contentRange: response.headers.get('content-range') || null" in source
assert 'const total = contentRangeTotal(result.contentRange);' in source
assert 'Range: `bytes=${tailStart}-${total - 1}`' in source
assert "if (kind === 'mp4' && mode.inspect_direct_dimensions === true)" in source

# The tail request stays bounded to the configured sample size. With global
# duration identity enabled it is needed whenever either dimensions or movie
# duration are missing from the first Range sample.
first_parse = source.index('verifiedHeights.push(...parseMp4TrackHeights(result.body));')
legacy_guard = 'if (!verifiedHeights.length) {'
extended_guard = 'if (!verifiedHeights.length || mediaDurationSeconds == null) {'
assert legacy_guard in source or extended_guard in source
guard = extended_guard if extended_guard in source else legacy_guard
tail_guard = source.index(guard, first_parse)
tail_fetch = source.index('Range: `bytes=${tailStart}-${total - 1}`', tail_guard)
assert first_parse < tail_guard < tail_fetch

print('bounded direct MP4 dimension tests passed')
