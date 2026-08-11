#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'scripts' / 'health_check.mjs').read_text(encoding='utf-8')

assert 'function readEbmlSize(body, offset)' in source
assert 'function parseMatroskaMetadata(body)' in source
assert '[0x2a, 0xd7, 0xb1]' in source
assert '[0x44, 0x89]' in source
assert '[0xb0]' in source
assert '[0xba]' in source
assert 'Math.abs(width.offset - height.offset) <= 192' in source
assert "kind === 'matroska' && mode.inspect_direct_dimensions === true" in source
assert 'verifiedHeights.push(...metadata.heights)' in source
assert 'mediaDurationSeconds = metadata.durationSeconds' in source
assert 'Range: `bytes=${tailStart}-${total - 1}`' in source

# Matroska duration must feed the same global duration-identity guard used by
# HLS/MP4; the direct branch cannot bypass it merely because the container is MKV.
matroska_idx = source.index("kind === 'matroska' && mode.inspect_direct_dimensions === true")
duration_set_idx = source.index('mediaDurationSeconds = metadata.durationSeconds', matroska_idx)
identity_idx = source.index('durationIdentityRatio = mediaDurationSeconds / expectedDurationSeconds')
assert matroska_idx < duration_set_idx < identity_idx

print('bounded Matroska metadata tests passed')
