#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'health-config.json').read_text(encoding='utf-8'))
source = (ROOT / 'scripts' / 'health_check.mjs').read_text(encoding='utf-8')

deep = config['modes']['deep']
assert int(deep['max_streams_to_probe']) == 3
assert deep.get('probe_streams_evenly') is True
for mode_name in ('quick', 'availability', 'retry'):
    mode = config['modes'][mode_name]
    assert int(mode.get('max_streams_to_probe', 1)) <= 1, mode_name
    assert not mode.get('probe_streams_evenly'), mode_name

assert "const streamsToProbe = requestedMode === 'deep' && modeConfig.probe_streams_evenly === true" in source
assert '? evenlySpacedSlice(streams, maxStreamsToProbe)' in source
assert ': streams.slice(0, maxStreamsToProbe);' in source
assert "qualityToHeight(`${stream.quality || ''} ${stream.title || ''} ${stream.url || ''}`)" in source

# The helper must sample the whole returned list rather than only its prefix.
assert 'Math.round(index * (items.length - 1) / (wanted - 1))' in source
# With 10 mirrors and three probes this expression selects 0, 5 and 9 in JS,
# which captures the observed late 2160p StreamZo mirror without probing all 10.

print('deep representative stream sampling tests passed')
