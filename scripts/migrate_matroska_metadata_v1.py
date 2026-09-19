#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / 'scripts' / 'health_check.mjs'
PACKAGE = ROOT / 'package.json'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    source = HEALTH.read_text(encoding='utf-8')

    anchor = '''function parseMp4TrackHeights(body) {
'''
    helpers = r'''function readEbmlSize(body, offset) {
  if (!Buffer.isBuffer(body) || offset < 0 || offset >= body.length) return null;
  const first = body[offset];
  if (!first) return null;
  let length = 1;
  let marker = 0x80;
  while (length <= 8 && !(first & marker)) { marker >>= 1; length += 1; }
  if (length > 8 || offset + length > body.length) return null;
  let value = first & (marker - 1);
  for (let index = 1; index < length; index += 1) value = value * 256 + body[offset + index];
  return { length, value };
}

function readUnsignedBe(body, offset, length) {
  if (!Buffer.isBuffer(body) || length < 1 || length > 6 || offset < 0 || offset + length > body.length) return null;
  let value = 0;
  for (let index = 0; index < length; index += 1) value = value * 256 + body[offset + index];
  return Number.isSafeInteger(value) ? value : null;
}

function readFloatBe(body, offset, length) {
  if (!Buffer.isBuffer(body) || offset < 0 || offset + length > body.length) return null;
  if (length === 4) return body.readFloatBE(offset);
  if (length === 8) return body.readDoubleBE(offset);
  return null;
}

function findEbmlValues(body, idBytes, decoder, limit = 24) {
  const values = [];
  if (!Buffer.isBuffer(body) || !Array.isArray(idBytes) || !idBytes.length) return values;
  outer: for (let offset = 0; offset + idBytes.length + 1 < body.length; offset += 1) {
    for (let index = 0; index < idBytes.length; index += 1) {
      if (body[offset + index] !== idBytes[index]) continue outer;
    }
    const size = readEbmlSize(body, offset + idBytes.length);
    if (!size || size.value < 1 || size.value > 8) continue;
    const valueOffset = offset + idBytes.length + size.length;
    if (valueOffset + size.value > body.length) continue;
    const value = decoder(body, valueOffset, size.value, offset);
    if (value != null && Number.isFinite(value)) values.push({ value, offset });
    if (values.length >= limit) break;
  }
  return values;
}

function parseMatroskaMetadata(body) {
  if (!Buffer.isBuffer(body) || body.length < 64) return { heights: [], durationSeconds: null };
  const widths = findEbmlValues(body, [0xb0], (buffer, offset, length) => readUnsignedBe(buffer, offset, length))
    .filter((row) => row.value >= 64 && row.value <= 16384);
  const heightsRaw = findEbmlValues(body, [0xba], (buffer, offset, length) => readUnsignedBe(buffer, offset, length))
    .filter((row) => row.value >= 64 && row.value <= 16384);
  // PixelWidth (B0) and PixelHeight (BA) live close together inside the same
  // Matroska Video TrackEntry. Requiring a plausible nearby width avoids
  // treating an arbitrary BA byte in media payload as a video dimension.
  const heights = heightsRaw
    .filter((height) => widths.some((width) => Math.abs(width.offset - height.offset) <= 192))
    .map((row) => Math.round(row.value));

  const scales = findEbmlValues(body, [0x2a, 0xd7, 0xb1], (buffer, offset, length) => readUnsignedBe(buffer, offset, length));
  const durations = findEbmlValues(body, [0x44, 0x89], (buffer, offset, length) => readFloatBe(buffer, offset, length))
    .filter((row) => row.value > 0 && row.value < 1e12);
  const timecodeScale = scales.length ? scales[0].value : 1_000_000;
  const durationSeconds = durations.length ? durations[0].value * timecodeScale / 1_000_000_000 : null;
  return {
    heights: [...new Set(heights)].filter((value) => value >= 64 && value <= 16384),
    durationSeconds: Number.isFinite(durationSeconds) && durationSeconds >= 1 && durationSeconds <= 1_209_600 ? durationSeconds : null,
  };
}

'''
    if 'function parseMatroskaMetadata(body)' not in source:
        if anchor not in source:
            raise SystemExit('health_check.mjs MP4 helper anchor not found')
        source = source.replace(anchor, helpers + anchor, 1)

    old_direct = '''      if (kind === 'mp4' && mode.inspect_direct_dimensions === true) {
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
      } else if (kind === 'matroska' && mode.inspect_direct_dimensions === true) {
        let metadata = parseMatroskaMetadata(result.body);
        verifiedHeights.push(...metadata.heights);
        mediaDurationSeconds = metadata.durationSeconds;
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
                metadata = parseMatroskaMetadata(tail.body);
                if (!verifiedHeights.length) verifiedHeights.push(...metadata.heights);
                if (mediaDurationSeconds == null) mediaDurationSeconds = metadata.durationSeconds;
              }
            } catch {}
          }
        }
      }
'''
    if new_direct not in source:
        if old_direct not in source:
            raise SystemExit('health_check.mjs direct media inspection anchor not found')
        source = source.replace(old_direct, new_direct, 1)

    HEALTH.write_text(source, encoding='utf-8')

    package = load(PACKAGE)
    command = package['scripts']['test']
    test = 'python3 tests/matroska_metadata_test.py'
    if test not in command:
        command += ' && ' + test
    package['scripts']['test'] = command
    dump(PACKAGE, package)

    print('bounded Matroska EBML dimensions and duration inspection enabled in deep validation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
