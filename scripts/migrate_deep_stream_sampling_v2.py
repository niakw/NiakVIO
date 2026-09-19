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
    url_quality = "  const reported = qualityToHeight(`${stream.quality || ''} ${stream.title || ''} ${stream.url || ''}`);"
    if url_quality not in source:
        if old_quality not in source:
            raise SystemExit('health_check.mjs reported-quality anchor not found')
        source = source.replace(old_quality, url_quality, 1)

    old_helper = """function evenlySpacedSlice(items, count) {
  if (!items.length || count <= 0) return [];
  const wanted = Math.min(count, items.length);
  if (wanted === items.length) return [...items];
  if (wanted === 1) return [items[Math.floor(items.length / 2)]];
  const indexes = Array.from({ length: wanted }, (_, index) => (
    Math.round(index * (items.length - 1) / (wanted - 1))
  ));
  return indexes.map((index) => items[index]);
}
"""
    new_helper = """function evenlySpacedSlice(items, count) {
  if (!items.length || count <= 0) return [];
  const wanted = Math.min(count, items.length);
  if (wanted === items.length) return [...items];
  if (wanted === 1) return [items[Math.floor(items.length / 2)]];
  const indexes = Array.from({ length: wanted }, (_, index) => (
    Math.round(index * (items.length - 1) / (wanted - 1))
  ));
  return indexes.map((index) => items[index]);
}

function rankedDeepStreamCandidates(items, count) {
  if (!items.length || count <= 0) return [];
  const wanted = Math.min(count, items.length);
  const decorated = items.map((stream, index) => ({
    stream,
    index,
    claimedHeight: qualityToHeight(`${stream?.quality || ''} ${stream?.title || ''} ${stream?.url || ''}`) || 0,
  }));
  // Keep the first mirror in the candidate set because it is often the upstream
  // preferred choice, then spend the remaining bounded budget on the strongest
  // declared HD/4K candidates. Declared quality only selects what to probe; it
  // never passes activation until the media probe itself verifies playback.
  const selected = [decorated[0]];
  const rankedRest = decorated.slice(1).sort((left, right) => (
    right.claimedHeight - left.claimedHeight || left.index - right.index
  ));
  for (const row of rankedRest) {
    if (selected.length >= wanted) break;
    selected.push(row);
  }
  if (selected.length < wanted) {
    for (const stream of evenlySpacedSlice(items, wanted)) {
      if (selected.length >= wanted) break;
      if (!selected.some((row) => row.stream === stream)) {
        selected.push({ stream, index: items.indexOf(stream), claimedHeight: 0 });
      }
    }
  }
  return selected.map((row) => row.stream);
}
"""
    if 'function rankedDeepStreamCandidates(items, count)' not in source:
        if old_helper not in source:
            raise SystemExit('health_check.mjs sampling helper anchor not found')
        source = source.replace(old_helper, new_helper, 1)

    baseline_loop = """    const probes = [];
    for (const stream of streams.slice(0, Number(modeConfig.max_streams_to_probe || 1))) {
      probes.push(await probeStream(stream, modeConfig));
    }
"""
    even_loop = """    const probes = [];
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
    previous_adaptive_loop = """    const probes = [];
    const maxStreamsToProbe = Math.max(1, Number(modeConfig.max_streams_to_probe || 1));
    const adaptiveDeepSampling = requestedMode === 'deep' && modeConfig.probe_streams_adaptively === true;
    if (!adaptiveDeepSampling || maxStreamsToProbe <= 1 || streams.length <= 1) {
      for (const stream of streams.slice(0, maxStreamsToProbe)) {
        probes.push(await probeStream(stream, modeConfig));
      }
    } else {
      // Keep the common case cheap: probe the first mirror exactly as before.
      // Only fan out across the returned list when that first proof cannot meet
      // the unchanged quality threshold. This recovers providers whose first
      // mirror is SD/dead while a later mirror is HD/4K without tripling every
      // deep provider probe.
      const firstProbe = await probeStream(streams[0], modeConfig);
      probes.push(firstProbe);
      const minimumHeight = Math.max(1, Number(activationConfig.minimum_effective_height || 720));
      const firstHeight = Number(firstProbe.effective_height || 0);
      const firstSatisfiesQuality = firstProbe.playback_verified === true && firstHeight >= minimumHeight;
      if (!firstSatisfiesQuality) {
        const representatives = evenlySpacedSlice(streams, maxStreamsToProbe);
        for (const stream of representatives) {
          if (probes.length >= maxStreamsToProbe) break;
          if (stream === streams[0]) continue;
          probes.push(await probeStream(stream, modeConfig));
          if (probes.some((probe) => probe.playback_verified === true && Number(probe.effective_height || 0) >= minimumHeight)) break;
        }
      }
    }
"""
    adaptive_loop = """    const probes = [];
    const maxStreamsToProbe = Math.max(1, Number(modeConfig.max_streams_to_probe || 1));
    const adaptiveDeepSampling = requestedMode === 'deep' && modeConfig.probe_streams_adaptively === true;
    if (!adaptiveDeepSampling || maxStreamsToProbe <= 1 || streams.length <= 1) {
      for (const stream of streams.slice(0, maxStreamsToProbe)) {
        probes.push(await probeStream(stream, modeConfig));
      }
    } else {
      const minimumHeight = Math.max(1, Number(activationConfig.minimum_effective_height || 720));
      const candidates = rankedDeepStreamCandidates(streams, maxStreamsToProbe);
      for (const stream of candidates) {
        const probe = await probeStream(stream, modeConfig);
        probes.push(probe);
        // Do not pay for extra mirrors once a current, playable media endpoint
        // has actually met the unchanged HD quality threshold.
        if (probe.playback_verified === true && Number(probe.effective_height || 0) >= minimumHeight) break;
      }
    }
"""
    ranked_loop_already_applied = (
        'const candidates = rankedDeepStreamCandidates(streams, maxStreamsToProbe);' in source
        and "const adaptiveDeepSampling = requestedMode === 'deep' && modeConfig.probe_streams_adaptively === true;" in source
    )
    if not ranked_loop_already_applied:
        for old_loop in (previous_adaptive_loop, even_loop, baseline_loop):
            if old_loop in source:
                source = source.replace(old_loop, adaptive_loop, 1)
                break
        else:
            raise SystemExit('health_check.mjs stream-probe loop anchor not found')

    HEALTH.write_text(source, encoding='utf-8')

    cfg = load(CONFIG)
    deep = cfg.setdefault('modes', {}).setdefault('deep', {})
    deep['max_streams_to_probe'] = 3
    deep['probe_streams_adaptively'] = True
    deep.pop('probe_streams_evenly', None)
    for mode_name in ('quick', 'availability', 'retry'):
        mode = cfg.setdefault('modes', {}).setdefault(mode_name, {})
        mode.setdefault('max_streams_to_probe', 1)
        mode.pop('probe_streams_evenly', None)
        mode.pop('probe_streams_adaptively', None)
    dump(CONFIG, cfg)

    package = load(PACKAGE)
    command = package['scripts']['test']
    test = 'python3 tests/deep_stream_sampling_test.py'
    if test not in command:
        command += ' && ' + test
    package['scripts']['test'] = command
    dump(PACKAGE, package)

    print('deep stream sampling fixed: first + quality-ranked bounded adaptive probes; verified URL quality participates in evidence')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
