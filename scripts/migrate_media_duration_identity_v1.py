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

    duration_helper_anchor = '''function contentRangeTotal(value) {
  const match = String(value || '').match(/bytes\\s+\\d+-\\d+\\/(\\d+)/i);
  return match ? Number(match[1]) : null;
}
'''
    duration_helper = '''function readUInt64BEAsNumber(body, offset) {
  if (!Buffer.isBuffer(body) || offset < 0 || offset + 8 > body.length) return null;
  const high = body.readUInt32BE(offset);
  const low = body.readUInt32BE(offset + 4);
  const value = high * 4294967296 + low;
  return Number.isSafeInteger(value) ? value : null;
}

function parseMp4MovieDurationSeconds(body) {
  if (!Buffer.isBuffer(body) || body.length < 40) return null;
  // Movie Header (mvhd) stores the media timescale and complete movie duration.
  // Scan only the bounded head/tail samples already fetched by the probe.
  for (let index = 4; index + 36 <= body.length; index += 1) {
    if (body[index] !== 0x6d || body[index + 1] !== 0x76 || body[index + 2] !== 0x68 || body[index + 3] !== 0x64) continue;
    const start = index - 4;
    const size = body.readUInt32BE(start);
    if (size < 32 || start + Math.min(size, 40) > body.length) continue;
    const version = body[start + 8];
    let timescale = null;
    let duration = null;
    if (version === 0 && start + 28 <= body.length) {
      timescale = body.readUInt32BE(start + 20);
      duration = body.readUInt32BE(start + 24);
    } else if (version === 1 && start + 40 <= body.length) {
      timescale = body.readUInt32BE(start + 28);
      duration = readUInt64BEAsNumber(body, start + 32);
    }
    if (!Number.isFinite(timescale) || timescale <= 0 || !Number.isFinite(duration) || duration <= 0) continue;
    const seconds = duration / timescale;
    if (Number.isFinite(seconds) && seconds >= 1 && seconds <= 1_209_600) return seconds;
  }
  return null;
}

'''
    if 'function parseMp4MovieDurationSeconds(body)' not in source:
        if duration_helper_anchor not in source:
            raise SystemExit('health_check.mjs contentRangeTotal anchor not found')
        source = source.replace(duration_helper_anchor, duration_helper + duration_helper_anchor, 1)

    old_signature = 'async function probeStream(stream, mode) {'
    new_signature = 'async function probeStream(stream, mode, fixture = null) {'
    if new_signature not in source:
        if old_signature not in source:
            raise SystemExit('health_check.mjs probeStream signature anchor not found')
        source = source.replace(old_signature, new_signature, 1)

    old_direct = '''      if (kind === 'mp4' && mode.inspect_direct_dimensions === true) {
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
'''
    new_direct = '''      if (kind === 'mp4' && mode.inspect_direct_dimensions === true) {
        verifiedHeights.push(...parseMp4TrackHeights(result.body));
        mediaDurationSeconds = parseMp4MovieDurationSeconds(result.body);
        if (!verifiedHeights.length || mediaDurationSeconds == null) {
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
              if (tail.ok) {
                if (!verifiedHeights.length) verifiedHeights.push(...parseMp4TrackHeights(tail.body));
                if (mediaDurationSeconds == null) mediaDurationSeconds = parseMp4MovieDurationSeconds(tail.body);
              }
            } catch {}
          }
        }
      }
'''
    direct_duration_already_applied = (
        'function parseMp4MovieDurationSeconds(body)' in source
        and 'mediaDurationSeconds = parseMp4MovieDurationSeconds(result.body);' in source
        and 'mediaDurationSeconds == null' in source
    )
    if not direct_duration_already_applied:
        if new_direct not in source:
            if old_direct not in source:
                raise SystemExit('health_check.mjs direct MP4 inspection anchor not found')
            source = source.replace(old_direct, new_direct, 1)

    subtitle_anchor = '''    const acceptedSubtitleEntries = advertisedSubtitleEntries.filter((subtitle) => {
'''
    duration_guard = '''    let durationIdentityMismatch = false;
    let durationIdentityRatio = null;
    const expectedDurationMinutes = Number(fixture?.expectedDurationMinutes || 0);
    const expectedDurationSeconds = expectedDurationMinutes > 0 ? expectedDurationMinutes * 60 : null;
    if (
      playbackVerified
      && mode.verify_fixture_duration_identity === true
      && expectedDurationSeconds
      && Number.isFinite(mediaDurationSeconds)
      && mediaDurationSeconds > 0
    ) {
      durationIdentityRatio = mediaDurationSeconds / expectedDurationSeconds;
      const minimumRatio = Math.max(0.05, Number(mode.minimum_fixture_duration_ratio || 0.55));
      const maximumRatio = Math.max(minimumRatio, Number(mode.maximum_fixture_duration_ratio || 1.8));
      if (durationIdentityRatio < minimumRatio || durationIdentityRatio > maximumRatio) {
        durationIdentityMismatch = true;
        playbackVerified = false;
        payloadVerified = false;
      }
    }

'''
    if 'let durationIdentityMismatch = false;' not in source:
        if subtitle_anchor not in source:
            raise SystemExit('health_check.mjs duration guard insertion anchor not found')
        source = source.replace(subtitle_anchor, duration_guard + subtitle_anchor, 1)

    old_category = "      category: playbackVerified ? 'playable' : (shortVodPreview ? 'short_vod_preview' : classification.category),"
    new_category = "      category: playbackVerified ? 'playable' : (durationIdentityMismatch ? 'duration_identity_mismatch' : (shortVodPreview ? 'short_vod_preview' : classification.category)),"
    if new_category not in source:
        if old_category not in source:
            raise SystemExit('health_check.mjs category anchor not found')
        source = source.replace(old_category, new_category, 1)

    old_duration_fields = '''      media_duration_seconds: mediaDurationSeconds,
      minimum_vod_duration_seconds: minimumVodDurationSeconds,
      short_vod_preview: shortVodPreview,
'''
    new_duration_fields = '''      media_duration_seconds: mediaDurationSeconds,
      expected_duration_seconds: expectedDurationSeconds,
      duration_identity_ratio: durationIdentityRatio,
      duration_identity_mismatch: durationIdentityMismatch,
      minimum_vod_duration_seconds: minimumVodDurationSeconds,
      short_vod_preview: shortVodPreview,
'''
    if new_duration_fields not in source:
        if old_duration_fields not in source:
            raise SystemExit('health_check.mjs duration result fields anchor not found')
        source = source.replace(old_duration_fields, new_duration_fields, 1)

    old_normalized = '''      year: fixture.year ?? null,
      category: fixture.category || fixture.mediaType || 'unknown',
'''
    new_normalized = '''      year: fixture.year ?? null,
      category: fixture.category || fixture.mediaType || 'unknown',
      expectedDurationMinutes: fixture.expectedDurationMinutes ?? null,
'''
    if new_normalized not in source:
        if old_normalized not in source:
            raise SystemExit('health_check.mjs normalized fixture anchor not found')
        source = source.replace(old_normalized, new_normalized, 1)

    source = source.replace('probeStream(stream, modeConfig)', 'probeStream(stream, modeConfig, normalizedFixture)')
    HEALTH.write_text(source, encoding='utf-8')

    cfg = load(CONFIG)
    deep = cfg.setdefault('modes', {}).setdefault('deep', {})
    deep['verify_fixture_duration_identity'] = True
    deep['minimum_fixture_duration_ratio'] = 0.55
    deep['maximum_fixture_duration_ratio'] = 1.8
    for mode_name in ('quick', 'availability', 'retry'):
        mode = cfg.setdefault('modes', {}).setdefault(mode_name, {})
        mode.pop('verify_fixture_duration_identity', None)
        mode.pop('minimum_fixture_duration_ratio', None)
        mode.pop('maximum_fixture_duration_ratio', None)

    references = {
        ('movie', '157336'): 169,
        ('tv', '1396'): 58,
        ('anime', '95479'): 24,
    }
    for category, fixtures in cfg.get('fixtures', {}).items():
        for fixture in fixtures:
            minutes = references.get((category, str(fixture.get('tmdbId') or '')))
            if minutes is not None:
                fixture['expectedDurationMinutes'] = minutes
    dump(CONFIG, cfg)

    package = load(PACKAGE)
    command = package['scripts']['test']
    test = 'python3 tests/media_duration_identity_test.py'
    if test not in command:
        command += ' && ' + test
    package['scripts']['test'] = command
    dump(PACKAGE, package)

    print('global media duration identity enabled for deep HLS/MP4 representative fixtures')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
