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

    old_fetch_return = '''  return {
    ok: response.ok || response.status === 206,
    status: response.status,
    contentType: response.headers.get('content-type') || '',
    finalUrl: response.url || url,
    body,
    latencyMs: Date.now() - started,
  };
'''
    new_fetch_return = '''  return {
    ok: response.ok || response.status === 206,
    status: response.status,
    contentType: response.headers.get('content-type') || '',
    contentLength: response.headers.get('content-length') || null,
    contentRange: response.headers.get('content-range') || null,
    finalUrl: response.url || url,
    body,
    latencyMs: Date.now() - started,
  };
'''
    if new_fetch_return not in source:
        if old_fetch_return not in source:
            raise SystemExit('health_check.mjs fetchProbe return anchor not found')
        source = source.replace(old_fetch_return, new_fetch_return, 1)

    helper_anchor = '''function looksLikeChallenge(text) {
'''
    helper = '''function parseMp4TrackHeights(body) {
  const heights = [];
  if (!Buffer.isBuffer(body) || body.length < 96) return heights;
  // Track Header boxes carry width/height as unsigned 16.16 fixed-point
  // values. Searching a bounded Range sample avoids needing a full MP4 parser
  // or downloading the media payload.
  for (let index = 4; index + 100 <= body.length; index += 1) {
    if (body[index] !== 0x74 || body[index + 1] !== 0x6b || body[index + 2] !== 0x68 || body[index + 3] !== 0x64) continue;
    const start = index - 4;
    const size = body.readUInt32BE(start);
    if (size < 92 || start + Math.min(size, 104) > body.length) continue;
    const version = body[start + 8];
    const widthOffset = version === 1 ? start + 96 : start + 84;
    const heightOffset = version === 1 ? start + 100 : start + 88;
    if (heightOffset + 4 > body.length) continue;
    const width = body.readUInt32BE(widthOffset) / 65536;
    const height = body.readUInt32BE(heightOffset) / 65536;
    if (width >= 64 && width <= 16384 && height >= 64 && height <= 16384) {
      heights.push(Math.round(height));
    }
  }
  return heights;
}

function contentRangeTotal(value) {
  const match = String(value || '').match(/bytes\\s+\\d+-\\d+\\/(\\d+)/i);
  return match ? Number(match[1]) : null;
}

'''
    if 'function parseMp4TrackHeights(body)' not in source:
        if helper_anchor not in source:
            raise SystemExit('health_check.mjs challenge helper anchor not found')
        source = source.replace(helper_anchor, helper + helper_anchor, 1)

    old_direct = '''    } else if (classification.endpointReachable && ['mp4', 'matroska', 'mpegts'].includes(kind)) {
      directSignatureVerified = true;
      payloadVerified = true;
      playbackVerified = true;
    } else {
'''
    new_direct = '''    } else if (classification.endpointReachable && ['mp4', 'matroska', 'mpegts'].includes(kind)) {
      directSignatureVerified = true;
      payloadVerified = true;
      playbackVerified = true;
      if (kind === 'mp4' && mode.inspect_direct_dimensions === true) {
        verifiedHeights.push(...parseMp4TrackHeights(result.body));
        if (!verifiedHeights.length) {
          const total = contentRangeTotal(result.contentRange);
          if (Number.isFinite(total) && total > sampleBytes) {
            try {
              const tailStart = Math.max(0, total - sampleBytes);
              const tail = await fetchProbe(
                result.finalUrl,
                { ...(stream.headers || {}), Range: `bytes=${tailStart}-${total - 1}` },
                timeoutMs,
                sampleBytes,
              );
              if (tail.ok) verifiedHeights.push(...parseMp4TrackHeights(tail.body));
            } catch {}
          }
        }
      }
    } else {
'''
    already_applied = (
        'function parseMp4TrackHeights(body)' in source
        and "kind === 'mp4' && mode.inspect_direct_dimensions === true" in source
        and "contentRange: response.headers.get('content-range') || null" in source
        and 'verifiedHeights.push(...parseMp4TrackHeights(result.body))' in source
    )
    if not already_applied:
        if new_direct not in source:
            if old_direct not in source:
                raise SystemExit('health_check.mjs direct media branch anchor not found')
            source = source.replace(old_direct, new_direct, 1)

    HEALTH.write_text(source, encoding='utf-8')

    cfg = load(CONFIG)
    cfg.setdefault('modes', {}).setdefault('deep', {})['inspect_direct_dimensions'] = True
    for name in ('quick', 'availability', 'retry'):
        cfg.setdefault('modes', {}).setdefault(name, {}).pop('inspect_direct_dimensions', None)
    dump(CONFIG, cfg)

    package = load(PACKAGE)
    command = package['scripts']['test']
    test = 'python3 tests/direct_media_dimensions_test.py'
    if test not in command:
        command += ' && ' + test
    package['scripts']['test'] = command
    dump(PACKAGE, package)

    print('bounded MP4 dimension inspection enabled for deep validation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
