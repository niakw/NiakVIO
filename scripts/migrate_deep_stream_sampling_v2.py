#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / 'scripts' / 'health_check.mjs'
CONFIG = ROOT / 'health-config.json'
PACKAGE = ROOT / 'package.json'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    source = HEALTH.read_text(encoding='utf-8')

    old_quality = "  const reported = qualityToHeight(`${stream.quality || ''} ${stream.title || ''}`);"
    new_quality = "  const reported = qualityToHeight(`${stream.quality || ''} ${stream.title || ''} ${stream.url || ''}`);"
    if new_quality not in source:
        if old_quality not in source:
            raise SystemExit('health_check.mjs reported-quality anchor not found')
        source = source.replace(old_quality, new_quality, 1)

    old_loop = """    const probes = [];
    for (const stream of streams.slice(0, Number(modeConfig.max_streams_to_probe || 1))) {
      probes.push(await probeStream(stream, modeConfig));
    }
"""
    new_loop = """    const probes = [];
    const maxStreamsToProbe = Math.max(1, Number(modeConfig.max_streams_to_probe || 1));
    // Deep activation must not grade a multi-mirror provider on whichever row
    // happens to be first. Probe a bounded, evenly distributed sample so a
    // later high-quality mirror can satisfy the unchanged quality gate.
    const streamsToProbe = requestedMode === 'deep' && modeConfig.probe_streams_evenly === true
      ? evenlySpacedSlice(streams, maxStreamsToProbe)
      : streams.slice(0, maxStreamsToProbe);
    for (const stream of streamsToProbe) {
      probes.push(await probeStream(stream, modeConfig));
    }
"""
    if new_loop not in source:
        if old_loop not in source:
            raise SystemExit('health_check.mjs stream-probe loop anchor not found')
        source = source.replace(old_loop, new_loop, 1)

    HEALTH.write_text(source, encoding='utf-8')

    cfg = load(CONFIG)
    deep = cfg.setdefault('modes', {}).setdefault('deep', {})
    deep['max_streams_to_probe'] = 3
    deep['probe_streams_evenly'] = True
    # Quick/status runs remain intentionally cheap and report-only.
    for mode_name in ('quick', 'availability', 'retry'):
        mode = cfg.setdefault('modes', {}).setdefault(mode_name, {})
        mode.setdefault('max_streams_to_probe', 1)
        mode.pop('probe_streams_evenly', None)
    dump(CONFIG, cfg)

    package = load(PACKAGE)
    command = package['scripts']['test']
    test = 'python3 tests/deep_stream_sampling_test.py'
    if test not in command:
        command += ' && ' + test
    package['scripts']['test'] = command
    dump(PACKAGE, package)

    print('deep stream sampling fixed: 3 evenly-spaced rows; verified URL quality participates in evidence')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
