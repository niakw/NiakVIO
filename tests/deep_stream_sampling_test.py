#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'health-config.json').read_text(encoding='utf-8'))
source = (ROOT / 'scripts' / 'health_check.mjs').read_text(encoding='utf-8')

deep = config['modes']['deep']
assert int(deep['max_streams_to_probe']) == 3
assert deep.get('probe_streams_adaptively') is True
assert not deep.get('probe_streams_evenly')
for mode_name in ('quick', 'availability', 'retry'):
    mode = config['modes'][mode_name]
    assert int(mode.get('max_streams_to_probe', 1)) <= 1, mode_name
    assert not mode.get('probe_streams_evenly'), mode_name
    assert not mode.get('probe_streams_adaptively'), mode_name

assert 'function rankedDeepStreamCandidates(items, count)' in source
assert "qualityToHeight(`${stream?.quality || ''} ${stream?.title || ''} ${stream?.url || ''}`)" in source
assert 'right.claimedHeight - left.claimedHeight || left.index - right.index' in source
assert 'const candidates = rankedDeepStreamCandidates(streams, maxStreamsToProbe);' in source
assert 'probe.playback_verified === true && Number(probe.effective_height || 0) >= minimumHeight' in source
assert "qualityToHeight(`${stream.quality || ''} ${stream.title || ''} ${stream.url || ''}`)" in source

# Claimed quality is only a probe-selection hint. The activation shortcut must
# still require the network/media probe to verify playback and effective height.
rank_index = source.index('right.claimedHeight - left.claimedHeight')
verify_index = source.index('probe.playback_verified === true && Number(probe.effective_height || 0) >= minimumHeight')
assert rank_index < verify_index

print('deep quality-ranked adaptive stream sampling tests passed')
