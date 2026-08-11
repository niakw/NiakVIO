#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'health-config.json').read_text(encoding='utf-8'))
source = (ROOT / 'scripts' / 'health_check.mjs').read_text(encoding='utf-8')

deep = config['modes']['deep']
assert deep.get('verify_fixture_duration_identity') is True
assert float(deep.get('minimum_fixture_duration_ratio')) == 0.55
assert float(deep.get('maximum_fixture_duration_ratio')) == 1.8
for mode in ('quick', 'availability', 'retry'):
    assert not config['modes'][mode].get('verify_fixture_duration_identity'), mode

fixtures = config['fixtures']
assert next(f for f in fixtures['movie'] if f['tmdbId'] == '157336')['expectedDurationMinutes'] == 169
assert next(f for f in fixtures['tv'] if f['tmdbId'] == '1396')['expectedDurationMinutes'] == 58
assert next(f for f in fixtures['anime'] if f['tmdbId'] == '95479')['expectedDurationMinutes'] == 24

assert 'function parseMp4MovieDurationSeconds(body)' in source
assert "body[index] !== 0x6d || body[index + 1] !== 0x76 || body[index + 2] !== 0x68 || body[index + 3] !== 0x64" in source
assert 'timescale = body.readUInt32BE(start + 20)' in source
assert 'duration = body.readUInt32BE(start + 24)' in source
assert 'timescale = body.readUInt32BE(start + 28)' in source
assert 'duration = readUInt64BEAsNumber(body, start + 32)' in source
assert 'async function probeStream(stream, mode, fixture = null)' in source
assert 'expectedDurationMinutes: fixture.expectedDurationMinutes ?? null' in source
assert source.count('probeStream(stream, modeConfig, normalizedFixture)') >= 2
assert 'durationIdentityRatio = mediaDurationSeconds / expectedDurationSeconds' in source
assert "durationIdentityMismatch ? 'duration_identity_mismatch'" in source
assert 'playbackVerified = false;' in source
assert 'payloadVerified = false;' in source

# The mismatch decision must be based on a measured media duration, never on a
# provider title alone, and must happen before the final playable classification.
parse_idx = source.index('function parseMp4MovieDurationSeconds(body)')
ratio_idx = source.index('durationIdentityRatio = mediaDurationSeconds / expectedDurationSeconds')
category_idx = source.index("durationIdentityMismatch ? 'duration_identity_mismatch'")
assert parse_idx < ratio_idx < category_idx

print('global media duration identity tests passed')
