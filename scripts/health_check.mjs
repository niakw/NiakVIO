#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/**
 * Execute and probe staged Nuvio provider candidates.
 *
 * Quick mode is report-only. Deep mode supplies the evidence used by the
 * publication policy. Complete media files are never downloaded and endpoint
 * URLs are never written to reports or logs.
 */

import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { inferSupportedTypes, roundRobin } = require('./provider_semantics.cjs');
const { guardedFetch } = require('./network_guard.cjs');

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const STAGE = path.resolve(process.env.NUVIO_STAGE || path.join(ROOT, 'staging'));
const CONFIG_PATH = path.resolve(process.env.NUVIO_HEALTH_CONFIG || path.join(ROOT, 'health-config.json'));
const OUTPUT_DIR = path.resolve(process.env.NUVIO_HEALTH_OUTPUT || STAGE);
const REGISTRY_PATH = path.resolve(process.env.NUVIO_CANDIDATES_PATH || path.join(STAGE, 'candidates.json'));
const RESULTS_FILENAME = String(process.env.NUVIO_HEALTH_RESULTS_FILENAME || 'health-results.json');
const WORKER_PATH = path.join(ROOT, 'scripts', 'provider_worker.cjs');
const DNS_PREFLIGHT_PATH = path.resolve(
  process.env.NUVIO_DNS_PREFLIGHT_RESULTS || path.join(OUTPUT_DIR, 'dns-preflight-report.json'),
);

const requestedMode = process.argv.includes('--retry')
  ? 'retry'
  : process.argv.includes('--availability')
    ? 'availability'
    : process.argv.includes('--deep')
      ? 'deep'
      : 'quick';

const registry = JSON.parse(await fs.readFile(REGISTRY_PATH, 'utf8'));
const config = JSON.parse(await fs.readFile(CONFIG_PATH, 'utf8'));
const modeConfig = config.modes?.[requestedMode] || config.modes?.quick || {};
const activationConfig = config.activation || {};
const executionConfig = config.execution_context || {};
const dnsPreflightConfig = config.dns_preflight || {};
const concurrency = Math.max(1, Number(config.concurrency || 4));
let dnsPreflightReport = null;
try {
  dnsPreflightReport = JSON.parse(await fs.readFile(DNS_PREFLIGHT_PATH, 'utf8'));
} catch (error) {
  if (dnsPreflightConfig.enabled !== false) {
    process.stderr.write(`[DNS WARN] preflight report unavailable: ${sanitizeError(error)}\n`);
  }
}
const dnsPreflightRows = Array.isArray(dnsPreflightReport?.providers) ? dnsPreflightReport.providers : [];
const dnsPreflightByKey = new Map(dnsPreflightRows.map((item) => [String(item.key || ''), item]));
const dnsPreflightBySourceCanonical = new Map(
  dnsPreflightRows.map((item) => [`${String(item.source || '')}:${String(item.canonical_id || '')}`, item]),
);
const dnsPreflightByCanonical = new Map();
for (const item of dnsPreflightRows) {
  const canonical = String(item.canonical_id || '');
  if (canonical && !dnsPreflightByCanonical.has(canonical)) dnsPreflightByCanonical.set(canonical, item);
}

const ACCEPTED_AUDIO = new Set(
  (activationConfig.accepted_audio_languages || ['fr', 'en']).map((value) => String(value).toLowerCase()),
);
const ACCEPTED_SUBTITLES = new Set(
  (activationConfig.accepted_subtitle_languages || ['fr', 'en']).map((value) => String(value).toLowerCase()),
);
const ANIME_ORIGINAL_AUDIO = new Set(
  (activationConfig.anime_original_audio_languages || ['ja']).map((value) => String(value).toLowerCase()),
);

function timeoutSignal(milliseconds) {
  return AbortSignal.timeout(Math.max(1000, Number(milliseconds)));
}

function sanitizeError(value) {
  return String(value || 'unknown error')
    .replace(/(?:https?|magnet|acestream|torrent):[^\s"']+/gi, '[endpoint]')
    .replace(/[\r\n\t]+/g, ' ')
    .slice(0, 700);
}

function median(values) {
  const cleaned = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!cleaned.length) return null;
  const middle = Math.floor(cleaned.length / 2);
  return cleaned.length % 2
    ? cleaned[middle]
    : Math.round((cleaned[middle - 1] + cleaned[middle]) / 2);
}

function qualityToHeight(value) {
  const text = String(value || '').toLowerCase();
  if (/\b(4k|uhd|2160p?)\b/.test(text)) return 2160;
  if (/\b(2k|1440p?)\b/.test(text)) return 1440;
  const matches = [...text.matchAll(/(?:^|\D)(2160|1440|1080|720|576|540|480|360|240)(?:p|\D|$)/g)];
  return matches.length ? Math.max(...matches.map((match) => Number(match[1]))) : null;
}

function normalizeLanguage(value) {
  if (!value) return null;
  const text = String(value).trim().toLowerCase();
  const aliases = new Map([
    ['english', 'en'], ['eng', 'en'], ['en-us', 'en'], ['en-gb', 'en'],
    ['french', 'fr'], ['français', 'fr'], ['francais', 'fr'], ['fre', 'fr'], ['fra', 'fr'],
    ['japanese', 'ja'], ['jpn', 'ja'], ['jp', 'ja'],
    ['hindi', 'hi'], ['spanish', 'es'], ['german', 'de'], ['italian', 'it'],
    ['portuguese', 'pt'], ['arabic', 'ar'], ['korean', 'ko'], ['chinese', 'zh'],
  ]);
  return aliases.get(text)
    || (text.match(/^[a-z]{2,3}(?:-[a-z]{2})?$/) ? text.slice(0, 2) : text.slice(0, 30));
}

function addLanguage(target, value) {
  const normalized = normalizeLanguage(value);
  if (normalized) target.add(normalized);
}

function inferLanguagesFromText(text, audioLanguages, subtitleLanguages) {
  const value = String(text || '').toLowerCase();
  if (/\b(vf|truefrench|french|français|francais)\b/.test(value)) addLanguage(audioLanguages, 'fr');
  if (/\b(english|eng|dual audio|multi audio)\b/.test(value)) addLanguage(audioLanguages, 'en');
  if (/\b(japanese|japonais|jpn|vo jap)\b/.test(value)) addLanguage(audioLanguages, 'ja');
  if (/\b(vostfr|sub(?:title)?s? fr|french sub)\b/.test(value)) addLanguage(subtitleLanguages, 'fr');
  if (/\b(vosta|english sub|sub(?:title)?s? en)\b/.test(value)) addLanguage(subtitleLanguages, 'en');
}

function parseAttributeList(value) {
  const result = {};
  for (const match of String(value || '').matchAll(/([A-Z0-9-]+)=("[^"]*"|[^,]*)/gi)) {
    result[match[1].toUpperCase()] = match[2].replace(/^"|"$/g, '');
  }
  return result;
}

function parseHls(text, baseUrl) {
  const verifiedHeights = [];
  const audioLanguages = new Set();
  const subtitleLanguages = new Set();
  const subtitleTracks = [];
  const codecs = new Set();
  const hdrFormats = new Set();
  const variants = [];
  const segments = [];
  let maxBandwidth = null;
  const lines = String(text || '').split(/\r?\n/);
  const valid = lines.some((line) => line.trim() === '#EXTM3U');

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (line.startsWith('#EXT-X-STREAM-INF:')) {
      const attrs = parseAttributeList(line.slice('#EXT-X-STREAM-INF:'.length));
      const resolution = String(attrs.RESOLUTION || '').match(/(\d+)x(\d+)/i);
      const bandwidth = Number(attrs['AVERAGE-BANDWIDTH'] || attrs.BANDWIDTH || 0) || 0;
      const next = lines.slice(index + 1).find((candidate) => candidate.trim() && !candidate.trim().startsWith('#'));
      if (resolution) verifiedHeights.push(Number(resolution[2]));
      if (bandwidth) maxBandwidth = Math.max(maxBandwidth || 0, bandwidth);
      for (const codec of String(attrs.CODECS || '').split(',').map((item) => item.trim()).filter(Boolean)) {
        codecs.add(codec);
      }
      if (attrs['VIDEO-RANGE']) hdrFormats.add(attrs['VIDEO-RANGE'].toUpperCase());
      if (next) {
        try {
          variants.push({
            url: new URL(next.trim(), baseUrl).href,
            height: resolution ? Number(resolution[2]) : null,
            bandwidth,
          });
        } catch {}
      }
    } else if (line.startsWith('#EXT-X-MEDIA:')) {
      const attrs = parseAttributeList(line.slice('#EXT-X-MEDIA:'.length));
      const type = String(attrs.TYPE || '').toUpperCase();
      if (type === 'AUDIO') addLanguage(audioLanguages, attrs.LANGUAGE || attrs.NAME);
      if (type === 'SUBTITLES') {
        const language = normalizeLanguage(attrs.LANGUAGE || attrs.NAME);
        addLanguage(subtitleLanguages, language);
        if (attrs.URI) {
          try {
            subtitleTracks.push({
              language,
              url: new URL(attrs.URI, baseUrl).href,
              headers: {},
            });
          } catch {}
        }
      }
    } else if (line && !line.startsWith('#')) {
      try { segments.push(new URL(line, baseUrl).href); } catch {}
    }
  }

  variants.sort((a, b) => (b.height || 0) - (a.height || 0) || b.bandwidth - a.bandwidth);
  return {
    valid,
    verifiedHeights,
    audioLanguages,
    subtitleLanguages,
    subtitleTracks,
    codecs,
    hdrFormats,
    maxBandwidth,
    bestVariant: variants[0] || null,
    firstSegment: segments[0] || null,
  };
}

function parseMpd(text) {
  const value = String(text || '');
  const verifiedHeights = [...value.matchAll(/\bheight=["'](\d+)["']/gi)].map((match) => Number(match[1]));
  const bandwidths = [...value.matchAll(/\bbandwidth=["'](\d+)["']/gi)].map((match) => Number(match[1]));
  const codecs = new Set([...value.matchAll(/\bcodecs=["']([^"']+)["']/gi)].map((match) => match[1]));
  const hdrFormats = new Set();
  if (/dolby\s*vision|dvh1|dvhe/i.test(value)) hdrFormats.add('DOLBY_VISION');
  if (/hdr10|smpte2084|pq/i.test(value)) hdrFormats.add('HDR10');
  if (/hlg/i.test(value)) hdrFormats.add('HLG');
  const audioLanguages = new Set();
  const subtitleLanguages = new Set();
  for (const match of value.matchAll(/<AdaptationSet\b[^>]*\b(?:lang|language)=["']([^"']+)["'][^>]*>/gi)) {
    const tag = match[0].toLowerCase();
    if (/contenttype=["']audio|mimetype=["']audio/i.test(tag)) addLanguage(audioLanguages, match[1]);
    if (/contenttype=["']text|mimetype=["'](?:text|application)/i.test(tag)) addLanguage(subtitleLanguages, match[1]);
  }
  return {
    valid: /<MPD[\s>]/i.test(value) && /<(Representation|AdaptationSet)\b/i.test(value),
    verifiedHeights,
    maxBandwidth: bandwidths.length ? Math.max(...bandwidths) : null,
    codecs,
    hdrFormats,
    audioLanguages,
    subtitleLanguages,
  };
}

async function readLimited(response, byteLimit) {
  if (!response.body) return Buffer.alloc(0);
  const reader = response.body.getReader();
  const chunks = [];
  let length = 0;
  try {
    while (length < byteLimit) {
      const { done, value } = await reader.read();
      if (done) break;
      const remaining = byteLimit - length;
      const slice = value.byteLength > remaining ? value.slice(0, remaining) : value;
      chunks.push(Buffer.from(slice));
      length += slice.byteLength;
      if (value.byteLength > remaining) break;
    }
  } finally {
    try { await reader.cancel(); } catch {}
  }
  return Buffer.concat(chunks);
}

function cleanHeaders(input = {}, rangeBytes = 262143) {
  const blocked = new Set(['host', 'content-length', 'connection', 'transfer-encoding']);
  const headers = {};
  for (const [key, value] of Object.entries(input || {})) {
    if (!blocked.has(String(key).toLowerCase()) && value != null) headers[key] = String(value);
  }
  headers.Range = headers.Range || `bytes=0-${Math.max(1023, rangeBytes)}`;
  headers['User-Agent'] = headers['User-Agent'] || 'Mozilla/5.0 Nuvio-Health-Check/5.12';
  return headers;
}

async function fetchProbe(url, headers, timeoutMs, byteLimit) {
  const started = Date.now();
  const response = await guardedFetch(fetch, url, {
    method: 'GET',
    headers: cleanHeaders(headers, byteLimit - 1),
    signal: timeoutSignal(timeoutMs),
  }, { maxRedirects: Number(modeConfig.max_redirects || 5) });
  const body = await readLimited(response, byteLimit);
  return {
    ok: response.ok || response.status === 206,
    status: response.status,
    contentType: response.headers.get('content-type') || '',
    finalUrl: response.url || url,
    body,
    latencyMs: Date.now() - started,
  };
}

function bodyKind(body, contentType) {
  const type = String(contentType || '').toLowerCase();
  const text = body.slice(0, 32768).toString('utf8').trim();
  if (text.startsWith('#EXTM3U')) return 'hls';
  if (/<MPD[\s>]/i.test(text)) return 'dash';
  if (/WEBVTT/i.test(text.slice(0, 100)) || /^\d+\s*\r?\n\d{2}:\d{2}:\d{2}/.test(text)) return 'subtitle';
  if (body.length >= 8 && body.slice(4, 8).toString('ascii') === 'ftyp') return 'mp4';
  if (body.length >= 4 && body[0] === 0x1a && body[1] === 0x45 && body[2] === 0xdf && body[3] === 0xa3) return 'matroska';
  if (body.length >= 376 && body[0] === 0x47 && body[188] === 0x47) return 'mpegts';
  if (type.includes('mpegurl')) return 'hls';
  if (type.includes('dash+xml')) return 'dash';
  if (type.includes('text/vtt') || type.includes('subrip')) return 'subtitle';
  if (type.startsWith('video/') || type.startsWith('audio/') || type.includes('octet-stream')) return 'media';
  if (type.includes('text/html') || /^<!doctype html|^<html/i.test(text)) return 'html';
  if (type.includes('json') || /^[{[]/.test(text)) return 'json';
  return body.length ? 'unknown' : 'empty';
}

function looksLikeChallenge(text) {
  return /cloudflare|attention required|checking your browser|verify you are human|captcha|access denied|just a moment|security check/i
    .test(String(text || ''));
}

function classifyHttp(result) {
  const kind = bodyKind(result.body, result.contentType);
  const text = result.body.slice(0, 65536).toString('utf8');
  if ([401, 403, 429, 451].includes(result.status) || (kind === 'html' && looksLikeChallenge(text))) {
    return { category: 'blocked', kind, endpointReachable: false };
  }
  if ([404, 410].includes(result.status)) return { category: 'not_found', kind, endpointReachable: false };
  if (result.status === 408 || result.status === 425 || result.status >= 500) {
    return { category: 'host_down', kind, endpointReachable: false };
  }
  if (!result.ok) return { category: 'http_error', kind, endpointReachable: false };
  if (kind === 'html' || kind === 'json' || kind === 'empty') {
    return {
      category: kind === 'html' && looksLikeChallenge(text) ? 'blocked' : 'invalid_payload',
      kind,
      endpointReachable: false,
    };
  }
  return { category: 'endpoint_reachable', kind, endpointReachable: true };
}

function classifyNetworkError(error) {
  const message = String(error?.message || error || '').toLowerCase();
  if (/timeout|timed out|aborted|enotfound|eai_again|econnrefused|econnreset|etimedout|network socket|certificate|tls|socket hang up/.test(message)) {
    return 'host_down';
  }
  return 'probe_error';
}

function isDisallowedProtocol(url) {
  try {
    return !['http:', 'https:'].includes(new URL(url).protocol);
  } catch {
    return true;
  }
}

async function probeSubtitle(subtitle, streamHeaders, mode) {
  if (!subtitle?.url || isDisallowedProtocol(subtitle.url)) return null;
  try {
    const response = await fetchProbe(
      subtitle.url,
      { ...(streamHeaders || {}), ...(subtitle.headers || {}) },
      Number(mode.stream_probe_timeout_ms || 12000),
      65536,
    );
    const classification = classifyHttp(response);
    return {
      language: normalizeLanguage(subtitle.language),
      reachable: classification.endpointReachable && ['subtitle', 'unknown'].includes(classification.kind),
      category: classification.category,
      kind: classification.kind,
      latency_ms: response.latencyMs,
    };
  } catch (error) {
    return {
      language: normalizeLanguage(subtitle.language),
      reachable: false,
      category: classifyNetworkError(error),
      kind: null,
      latency_ms: null,
    };
  }
}

async function probeStream(stream, mode) {
  const audioLanguages = new Set();
  const subtitleLanguages = new Set();
  const reportedHeights = [];
  const verifiedHeights = [];
  const codecs = new Set();
  const hdrFormats = new Set();
  const timeoutMs = Number(mode.stream_probe_timeout_ms || 12000);
  const sampleBytes = Number(mode.sample_bytes || 262144);
  let maxBandwidth = null;

  const reported = qualityToHeight(`${stream.quality || ''} ${stream.title || ''}`);
  if (reported) reportedHeights.push(reported);
  addLanguage(audioLanguages, stream.language);
  inferLanguagesFromText(`${stream.title || ''} ${stream.name || ''}`, audioLanguages, subtitleLanguages);
  for (const subtitle of stream.subtitles || []) addLanguage(subtitleLanguages, subtitle.language);
  for (const track of stream.audioTracks || []) addLanguage(audioLanguages, track.language);

  const advertisedSubtitleEntries = [...(stream.subtitles || [])];

  let parsedUrl;
  try {
    parsedUrl = new URL(stream.url);
    if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
      throw new Error(`disallowed protocol ${parsedUrl.protocol}`);
    }
  } catch (error) {
    return {
      endpoint_reachable: false,
      reachable: false,
      playback_verified: false,
      payload_verified: false,
      category: 'disallowed_or_invalid_url',
      error: sanitizeError(error),
      reportedHeights,
      verifiedHeights,
      audioLanguages: [...audioLanguages],
      subtitleLanguages: [...subtitleLanguages],
      accepted_audio_languages: [...audioLanguages].filter((value) => ACCEPTED_AUDIO.has(value)),
      accepted_subtitle_languages: [...subtitleLanguages].filter((value) => ACCEPTED_SUBTITLES.has(value)),
      accepted_subtitles_advertised: advertisedSubtitleEntries.filter((subtitle) => {
        const language = normalizeLanguage(subtitle?.language);
        return language && ACCEPTED_SUBTITLES.has(language);
      }).length,
      accepted_subtitles_reachable: 0,
      subtitles_advertised: advertisedSubtitleEntries.length,
      subtitles_reachable: 0,
      codecs: [],
      hdrFormats: [],
      host: null,
    };
  }

  try {
    const result = await fetchProbe(parsedUrl.href, stream.headers || {}, timeoutMs, sampleBytes);
    const classification = classifyHttp(result);
    const lowerPath = new URL(result.finalUrl).pathname.toLowerCase();
    const text = result.body.toString('utf8');
    let kind = classification.kind === 'unknown' ? 'direct' : classification.kind;
    let variantReachable = null;
    let segmentReachable = null;
    let payloadVerified = false;
    let playbackVerified = false;
    let directSignatureVerified = false;

    if (classification.endpointReachable && (lowerPath.includes('.m3u8') || kind === 'hls')) {
      kind = 'hls';
      const master = parseHls(text, result.finalUrl);
      payloadVerified = master.valid;
      verifiedHeights.push(...master.verifiedHeights);
      master.audioLanguages.forEach((value) => audioLanguages.add(value));
      master.subtitleLanguages.forEach((value) => subtitleLanguages.add(value));
      advertisedSubtitleEntries.push(...(master.subtitleTracks || []));
      master.codecs.forEach((value) => codecs.add(value));
      master.hdrFormats.forEach((value) => hdrFormats.add(value));
      maxBandwidth = master.maxBandwidth;

      let mediaPlaylist = master;
      if (master.bestVariant && mode.probe_best_variant) {
        try {
          const variant = await fetchProbe(master.bestVariant.url, stream.headers || {}, timeoutMs, 131072);
          const variantClass = classifyHttp(variant);
          const parsedVariant = parseHls(variant.body.toString('utf8'), variant.finalUrl);
          variantReachable = variantClass.endpointReachable && parsedVariant.valid;
          if (variantReachable) {
            mediaPlaylist = parsedVariant;
            mediaPlaylist.verifiedHeights.forEach((value) => verifiedHeights.push(value));
            mediaPlaylist.audioLanguages.forEach((value) => audioLanguages.add(value));
            mediaPlaylist.subtitleLanguages.forEach((value) => subtitleLanguages.add(value));
            advertisedSubtitleEntries.push(...(mediaPlaylist.subtitleTracks || []));
            mediaPlaylist.codecs.forEach((value) => codecs.add(value));
            mediaPlaylist.hdrFormats.forEach((value) => hdrFormats.add(value));
            maxBandwidth = Math.max(maxBandwidth || 0, mediaPlaylist.maxBandwidth || 0) || null;
          }
        } catch {
          variantReachable = false;
        }
      } else if (master.bestVariant) {
        variantReachable = null;
      } else {
        variantReachable = true;
      }

      if (mode.probe_first_segment) {
        if (mediaPlaylist.firstSegment) {
          try {
            const segment = await fetchProbe(mediaPlaylist.firstSegment, stream.headers || {}, timeoutMs, 65536);
            const segmentClass = classifyHttp(segment);
            segmentReachable = segmentClass.endpointReachable
              && !['html', 'json', 'empty', 'subtitle'].includes(segmentClass.kind);
          } catch {
            segmentReachable = false;
          }
        } else {
          segmentReachable = false;
        }
      }

      playbackVerified = payloadVerified
        && variantReachable !== false
        && (mode.probe_first_segment ? segmentReachable === true : true);
    } else if (classification.endpointReachable && (lowerPath.includes('.mpd') || kind === 'dash')) {
      kind = 'dash';
      const mpd = parseMpd(text);
      payloadVerified = mpd.valid;
      playbackVerified = mpd.valid;
      verifiedHeights.push(...mpd.verifiedHeights);
      mpd.audioLanguages.forEach((value) => audioLanguages.add(value));
      mpd.subtitleLanguages.forEach((value) => subtitleLanguages.add(value));
      mpd.codecs.forEach((value) => codecs.add(value));
      mpd.hdrFormats.forEach((value) => hdrFormats.add(value));
      maxBandwidth = mpd.maxBandwidth;
    } else if (classification.endpointReachable && ['mp4', 'matroska', 'mpegts'].includes(kind)) {
      directSignatureVerified = true;
      payloadVerified = true;
      playbackVerified = true;
    } else {
      payloadVerified = false;
      playbackVerified = false;
    }

    const acceptedSubtitleEntries = advertisedSubtitleEntries.filter((subtitle) => {
      const language = normalizeLanguage(subtitle?.language);
      return language && ACCEPTED_SUBTITLES.has(language);
    });
    const subtitlesToProbe = [
      ...acceptedSubtitleEntries,
      ...advertisedSubtitleEntries.filter((subtitle) => !acceptedSubtitleEntries.includes(subtitle)),
    ].slice(0, Math.max(0, Number(mode.max_subtitles_to_probe ?? 1)));

    const subtitleProbes = [];
    if (mode.probe_subtitles) {
      for (const subtitle of subtitlesToProbe) {
        const checked = await probeSubtitle(subtitle, stream.headers || {}, mode);
        if (checked) subtitleProbes.push(checked);
      }
    }
    const subtitlesReachable = subtitleProbes.filter((item) => item.reachable).length;
    const acceptedSubtitlesReachable = subtitleProbes.filter(
      (item) => item.reachable && item.language && ACCEPTED_SUBTITLES.has(item.language),
    ).length;
    const effectiveHeight = Math.max(
      0,
      ...verifiedHeights,
      ...(playbackVerified ? reportedHeights : []),
    ) || null;

    return {
      endpoint_reachable: classification.endpointReachable,
      reachable: playbackVerified,
      playback_verified: playbackVerified,
      payload_verified: payloadVerified,
      direct_signature_verified: directSignatureVerified,
      category: playbackVerified ? 'playable' : classification.category,
      http_status: result.status,
      kind,
      bytes_sampled: result.body.length,
      latency_ms: result.latencyMs,
      variant_reachable: variantReachable,
      segment_reachable: segmentReachable,
      reportedHeights,
      verifiedHeights,
      effective_height: effectiveHeight,
      maxBandwidth,
      codecs: [...codecs],
      hdrFormats: [...hdrFormats],
      audioLanguages: [...audioLanguages],
      subtitleLanguages: [...subtitleLanguages],
      accepted_audio_languages: [...audioLanguages].filter((value) => ACCEPTED_AUDIO.has(value)),
      accepted_subtitle_languages: [...subtitleLanguages].filter((value) => ACCEPTED_SUBTITLES.has(value)),
      accepted_subtitles_advertised: acceptedSubtitleEntries.length,
      accepted_subtitles_reachable: acceptedSubtitlesReachable,
      subtitles_advertised: advertisedSubtitleEntries.length,
      subtitles_reachable: subtitlesReachable,
      host: parsedUrl.hostname,
    };
  } catch (error) {
    return {
      endpoint_reachable: false,
      reachable: false,
      playback_verified: false,
      payload_verified: false,
      category: classifyNetworkError(error),
      error: sanitizeError(error),
      reportedHeights,
      verifiedHeights,
      effective_height: null,
      maxBandwidth,
      codecs: [...codecs],
      hdrFormats: [...hdrFormats],
      audioLanguages: [...audioLanguages],
      subtitleLanguages: [...subtitleLanguages],
      accepted_audio_languages: [...audioLanguages].filter((value) => ACCEPTED_AUDIO.has(value)),
      accepted_subtitle_languages: [...subtitleLanguages].filter((value) => ACCEPTED_SUBTITLES.has(value)),
      accepted_subtitles_advertised: advertisedSubtitleEntries.filter((subtitle) => {
        const language = normalizeLanguage(subtitle?.language);
        return language && ACCEPTED_SUBTITLES.has(language);
      }).length,
      accepted_subtitles_reachable: 0,
      subtitles_advertised: advertisedSubtitleEntries.length,
      subtitles_reachable: 0,
      host: parsedUrl.hostname,
    };
  }
}

function rotateSlice(items, start, count) {
  if (!items.length || count <= 0) return [];
  const output = [];
  const wanted = Math.min(count, items.length);
  for (let offset = 0; offset < wanted; offset += 1) {
    output.push(items[(start + offset) % items.length]);
  }
  return output;
}

function evenlySpacedSlice(items, count) {
  if (!items.length || count <= 0) return [];
  const wanted = Math.min(count, items.length);
  if (wanted === items.length) return [...items];
  if (wanted === 1) return [items[Math.floor(items.length / 2)]];
  const indexes = Array.from({ length: wanted }, (_, index) => (
    Math.round(index * (items.length - 1) / (wanted - 1))
  ));
  return indexes.map((index) => items[index]);
}

function withCategory(items, category) {
  return (items || []).map((item) => ({ ...item, category }));
}

function candidateProfile(candidate) {
  const types = inferSupportedTypes(candidate);
  const movieFixtures = withCategory(config.fixtures.movie, 'movie');
  const tvFixtures = withCategory(config.fixtures.tv, 'tv');
  const animeFixtures = withCategory(config.fixtures.anime, 'anime');
  const fixtureGroups = {
    movie: movieFixtures,
    tv: tvFixtures,
    anime: animeFixtures,
  };
  const requiredCategories = ['movie', 'tv', 'anime'].filter((type) => types.includes(type));
  const pool = roundRobin(requiredCategories.map((type) => fixtureGroups[type] || []));

  if (!pool.length) {
    return {
      types: ['movie', 'tv'],
      anime: false,
      pool: roundRobin([movieFixtures, tvFixtures]),
      requiredCategories: ['movie', 'tv'],
    };
  }
  return {
    types,
    anime: types.includes('anime'),
    pool,
    requiredCategories,
  };
}

function fixtureKey(fixture) {
  return [
    fixture.category || fixture.mediaType || 'unknown',
    String(fixture.tmdbId),
    fixture.season ?? '',
    fixture.episode ?? '',
  ].join(':');
}

function fixturesForCandidate(candidate) {
  const profile = candidateProfile(candidate);
  const limit = Math.max(1, Number(modeConfig.fixture_limit || 1));
  const period = requestedMode === 'retry'
    ? 60 * 60 * 1000
    : requestedMode === 'availability'
      ? 4 * 60 * 60 * 1000
      : 24 * 60 * 60 * 1000;
  const slot = Math.floor(Date.now() / period);
  const start = requestedMode === 'deep' ? 0 : slot % profile.pool.length;
  const fixtures = rotateSlice(profile.pool, start, limit);
  const selected = new Set(fixtures.map(fixtureKey));
  const remaining = profile.pool.filter((fixture) => !selected.has(fixtureKey(fixture)));
  const fallbackLimit = requestedMode === 'deep'
    ? Math.max(0, Number(modeConfig.fallback_fixture_limit || 0))
    : 0;
  const fallbackFixtures = evenlySpacedSlice(remaining, fallbackLimit);
  return { profile, fixtures, fallbackFixtures };
}

function providerLocale(candidate) {
  const metadata = candidate.metadata || {};
  const declared = Array.isArray(metadata.contentLanguage)
    ? metadata.contentLanguage.map((value) => normalizeLanguage(value)).filter(Boolean)
    : [];
  const text = `${candidate.canonical_id || ''} ${metadata.name || ''} ${metadata.description || ''}`.toLowerCase();
  let language = null;
  if (declared.includes('fr') && /\b(fr|french|français|francais|vf|vostfr|multi)\b/.test(text)) language = 'fr';
  if (!language) language = declared.find((value) => ACCEPTED_AUDIO.has(value) || ACCEPTED_SUBTITLES.has(value));
  if (!language) language = declared[0] || String(executionConfig.default_locale || 'en-US').split('-')[0];
  const localeMap = {
    fr: 'fr-FR', en: 'en-US', ja: 'ja-JP', hi: 'hi-IN', es: 'es-ES',
    de: 'de-DE', it: 'it-IT', pt: 'pt-BR', ar: 'ar-SA', ko: 'ko-KR', zh: 'zh-CN',
  };
  return localeMap[language] || `${language}-${language.toUpperCase()}`;
}

function executionContextForCandidate(candidate) {
  const locale = executionConfig.derive_locale_from_provider_metadata === false
    ? String(executionConfig.default_locale || 'en-US')
    : providerLocale(candidate);
  const language = locale.split('-')[0];
  const metadata = candidate.metadata || {};
  return {
    providerId: candidate.canonical_id,
    source: candidate.source,
    locale,
    languages: [...new Set([locale, language])],
    platform: String(executionConfig.default_platform || 'android'),
    injectAcceptLanguage: executionConfig.inject_accept_language !== false,
    settings: {},
    storage: {
      nuvio_provider_id: String(candidate.canonical_id || ''),
      nuvio_provider_source: String(candidate.source || ''),
      nuvio_content_language: language,
      nuvio_has_settings: String(Boolean(metadata.hasSettings)),
    },
    networkLimits: {
      maxFetches: Number(modeConfig.max_provider_fetches || 30),
      maxRedirects: Number(modeConfig.max_redirects || 5),
      maxResponseBytes: Number(modeConfig.max_provider_response_bytes || 5 * 1024 * 1024),
      maxTotalResponseBytes: Number(modeConfig.max_provider_total_response_bytes || 20 * 1024 * 1024),
      maxDistinctHosts: Number(modeConfig.max_provider_distinct_hosts || 20),
    },
  };
}

function runWorker(candidate, fixture) {
  return new Promise((resolve) => {
    const providerPath = path.join(STAGE, candidate.local_path);
    const timeoutMs = Number(modeConfig.provider_timeout_ms || 45000);
    const context = { ...executionContextForCandidate(candidate), fixtureMetadata: fixture };
    const child = spawn(process.execPath, [
      '--max-old-space-size=256',
      WORKER_PATH,
      providerPath,
      JSON.stringify(fixture),
      JSON.stringify(context),
    ], {
      cwd: ROOT,
      env: {
        PATH: process.env.PATH || '',
        HOME: process.env.HOME || '',
        NODE_PATH: path.join(ROOT, 'node_modules'),
        NODE_NO_WARNINGS: '1',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let settled = false;
    let stdout = '';
    let stderr = '';
    const finish = (value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(value);
    };
    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      finish({ ok: false, timeout: true, error: `provider exceeded ${timeoutMs} ms`, streams: [], stream_count: 0 });
    }, timeoutMs);

    const maxWorkerOutputBytes = 1024 * 1024;
    child.stdout.on('data', (chunk) => {
      if (Buffer.byteLength(stdout) < maxWorkerOutputBytes) stdout += chunk.toString().slice(0, maxWorkerOutputBytes - Buffer.byteLength(stdout));
    });
    child.stderr.on('data', (chunk) => {
      if (Buffer.byteLength(stderr) < 16384) stderr += chunk.toString().slice(0, 16384 - Buffer.byteLength(stderr));
    });
    child.on('error', (error) => finish({ ok: false, error: error.message, streams: [], stream_count: 0 }));
    child.on('close', () => {
      const marker = stdout.split(/\r?\n/).find((line) => line.startsWith('NUVIO_HEALTH_RESULT='));
      if (!marker) {
        finish({
          ok: false,
          error: `worker returned no result${stderr ? `: ${stderr.slice(0, 500)}` : ''}`,
          streams: [],
          stream_count: 0,
        });
        return;
      }
      try {
        finish(JSON.parse(marker.slice('NUVIO_HEALTH_RESULT='.length)));
      } catch (error) {
        finish({ ok: false, error: `invalid worker JSON: ${error.message}`, streams: [], stream_count: 0 });
      }
    });
  });
}

function statusFrom(worker, probes) {
  if ((worker.disallowed_stream_count || 0) > 0) return 'excluded';
  if (probes.some((probe) => probe.playback_verified)) return 'healthy';
  // Runtime validation is deliberately an access check, not a catalogue or
  // playback benchmark. Once a provider-owned host answered at HTTP level, the
  // editorial metadata gates decide whether it is worth publishing.
  if (worker.ok && worker.provider_server_accessible) return 'reachable';
  if (probes.some((probe) => probe.category === 'blocked')) return 'blocked';
  if (worker.ok && (worker.stream_count || 0) === 0) return 'no_streams';
  if (worker.ok && (worker.stream_count || 0) > 0) {
    const hard = probes.length > 0
      && probes.every((probe) => ['host_down', 'not_found'].includes(probe.category));
    return hard ? 'unavailable' : 'degraded';
  }
  if (worker.timeout || /timeout|enotfound|econnrefused|econnreset|network|fetch failed/i.test(String(worker.error || ''))) {
    return 'provider_unreachable';
  }
  return 'runtime_error';
}

function scoreTest(worker, probes, status) {
  if (status === 'excluded') return 0;
  if (requestedMode === 'availability' || requestedMode === 'retry') {
    if (status === 'healthy') return 100;
    if (status === 'blocked') return 45;
    if (status === 'reachable') return 75;
    if (status === 'degraded' || status === 'no_streams') return 25;
    return 0;
  }

  let score = 0;
  if (worker.ok) score += 10;
  if (status === 'reachable') return 75;
  if ((worker.stream_count || 0) > 0) score += 10;
  const playable = probes.filter((probe) => probe.playback_verified);
  if (playable.length > 0) score += 20;
  if (playable.length > 1) score += 10;
  if (playable.some((probe) => probe.payload_verified)) score += 10;
  if (playable.some((probe) => probe.segment_reachable === true || probe.direct_signature_verified || probe.kind === 'dash')) score += 10;

  const effectiveMax = Math.max(0, ...playable.map((probe) => probe.effective_height || 0));
  if (effectiveMax >= 2160) score += 15;
  else if (effectiveMax >= 1080) score += 12;
  else if (effectiveMax >= 720) score += 8;

  const acceptedAudio = new Set(playable.flatMap((probe) => probe.accepted_audio_languages || []));
  const acceptedSubtitles = new Set(playable.flatMap((probe) => probe.accepted_subtitle_languages || []));
  if (acceptedAudio.size || acceptedSubtitles.size) score += 8;
  if (
    playable.some((probe) => (probe.accepted_subtitles_reachable || 0) > 0)
    || acceptedAudio.size
  ) score += 5;

  const hosts = new Set(playable.map((probe) => probe.host).filter(Boolean));
  if (hosts.size >= 2) score += 5;
  const probeMedian = median(playable.map((probe) => probe.latency_ms));
  if (probeMedian != null && probeMedian <= 12000) score += 5;
  if (playable.some((probe) => (probe.codecs || []).length)) score += 2;
  if (playable.some((probe) => (probe.hdrFormats || []).length)) score += 2;

  if (status !== 'healthy') score = Math.min(score, 35);
  return Math.min(100, score);
}

function manifestClaims(candidate) {
  const metadata = candidate.metadata || {};
  const canonicalMetadata = candidate.canonical_metadata || {};
  const descriptions = [
    metadata.description,
    ...(Array.isArray(canonicalMetadata.descriptions) ? canonicalMetadata.descriptions : []),
  ].filter(Boolean).map((value) => String(value).trim()).filter(Boolean);
  const description = [...new Set(descriptions)].join(' ');
  const qualityMetadata = [metadata.quality, metadata.qualities, metadata.resolution, metadata.resolutions]
    .flat().filter((value) => value != null).join(' ');
  const text = `${candidate.canonical_id || ''} ${metadata.id || ''} ${metadata.name || ''} ${description} ${qualityMetadata}`
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const explicitHeight = qualityToHeight(text)
    || (/\b(?:full[ -]?hd|fhd)\b/.test(text) ? 1080 : null)
    || (/\b(?:high[ -]?quality|good[ -]?quality|bonne qualite|hd quality)\b/.test(text) ? 720 : null);
  const languages = new Set();
  const declaredLanguages = [
    ...(Array.isArray(metadata.contentLanguage) ? metadata.contentLanguage : []),
    ...(Array.isArray(canonicalMetadata.contentLanguage) ? canonicalMetadata.contentLanguage : []),
  ];
  for (const value of declaredLanguages) addLanguage(languages, value);
  if (/\b(vf|truefrench|french|francais|vostfr)\b/.test(text)) languages.add('fr');
  if (/\b(english|eng|dual[ -]?audio|multi[ -]?(?:language|langue))\b/.test(text)) languages.add('en');
  const types = inferSupportedTypes(candidate);
  const formats = [...new Set([
    ...(Array.isArray(metadata.formats) ? metadata.formats : []),
    ...(Array.isArray(canonicalMetadata.formats) ? canonicalMetadata.formats : []),
  ].map((v) => String(v).toLowerCase()))];
  const qualitySignals = [];
  if (explicitHeight) qualitySignals.push(`explicit_height:${explicitHeight}`);
  if (/\b(?:multi[ -]?quality|multiple quality|multi[ -]?resolution|multiple resolution)\b/.test(text)) qualitySignals.push('multiple_quality_options');
  if (/\b(?:direct links?|direct streams?|direct streaming|cdn direct|high[ -]?speed|lightning fast|fast streaming|streams? directs?|tres rapides?)\b/.test(text)) qualitySignals.push('direct_or_fast_delivery');
  if (/\b(?:multi[ -]?servers?|multiple (?:streaming )?servers?|server sources?)\b/.test(text)) qualitySignals.push('multiple_servers');
  if (/\b(?:gros catalogue|large catalogue|large catalog|big catalog|tres actif|very active|sorties du jour|latest .* daily|trending)\b/.test(text)) qualitySignals.push('catalogue_or_freshness');
  const accepted = [...languages].filter((value) => ACCEPTED_AUDIO.has(value) || ACCEPTED_SUBTITLES.has(value));
  const richLanguage = accepted.length >= 2 || /\b(?:vf|vostfr|dual|dubbed|subbed|multi[ -]?(?:language|langue)|multi)\b/.test(text);
  const usableFormat = formats.some((value) => ['mp4', 'mkv', 'm3u8', 'hls', 'dash', 'mpd'].includes(value));
  let curationScore = 0;
  if (explicitHeight || qualitySignals.includes('multiple_quality_options')) curationScore += 3;
  if (qualitySignals.includes('direct_or_fast_delivery') || qualitySignals.includes('multiple_servers')) curationScore += 2;
  if (qualitySignals.includes('catalogue_or_freshness')) curationScore += 1;
  if (accepted.length) curationScore += 2;
  if (richLanguage) curationScore += 1;
  if (usableFormat) curationScore += 1;
  if (description.length >= 8) curationScore += 1;
  return {
    max_height: explicitHeight,
    accepted_languages: [...languages].sort(),
    supported_types: [...new Set(types)].sort(),
    formats: [...new Set(formats)].sort(),
    description_present: description.length >= 8,
    curation_score: curationScore,
    quality_signals: [...new Set(qualitySignals)].sort(),
  };
}

function dnsPreflightForCandidate(candidate) {
  return dnsPreflightByKey.get(String(candidate.key || ''))
    || dnsPreflightBySourceCanonical.get(`${String(candidate.source || '')}:${String(candidate.canonical_id || '')}`)
    || dnsPreflightByCanonical.get(String(candidate.canonical_id || ''))
    || null;
}

function preflightOnlyResult(candidate, preflight) {
  const { profile } = fixturesForCandidate(candidate);
  const claims = manifestClaims(candidate);
  const decision = preflight?.decision || {};
  const status = decision.status === 'confirmed_french_block' ? 'blocked' : 'provider_unreachable';
  const score = status === 'blocked' ? 45 : 0;
  return {
    key: candidate.key,
    source: candidate.source,
    upstream_id: candidate.upstream_id,
    canonical_id: candidate.canonical_id,
    sha256: candidate.sha256,
    mode: requestedMode,
    status,
    ci_classification: 'inconclusive',
    score,
    dns_preflight: preflight,
    candidate_profile: {
      anime: profile.anime,
      supported_types: profile.types,
      required_fixture_categories: profile.requiredCategories,
      derived_locale: providerLocale(candidate),
      has_settings: Boolean(candidate.metadata?.hasSettings),
      manifest_claims: claims,
    },
    evidence: {
      primary_fixtures_tested: 0,
      fallback_fixtures_tested: 0,
      fallback_triggered: false,
      fixtures_tested: 0,
      total_fixtures_executed: 0,
      activation_fixture_phase: 'dns_preflight',
      healthy_fixtures: 0,
      healthy_fixture_ratio: 0,
      playable_fixtures: 0,
      required_fixture_categories: profile.requiredCategories,
      healthy_fixture_categories: [],
      streams_playable: 0,
      payload_verified_streams: 0,
      distinct_reachable_hosts: 0,
      reachable_hosts: [],
      verified_max_height: null,
      reported_max_height: null,
      effective_max_height: null,
      max_bandwidth: null,
      audio_languages: [],
      subtitle_languages: [],
      accepted_audio_languages: [],
      accepted_subtitle_languages: [],
      accepted_subtitles_advertised: 0,
      accepted_subtitles_reachable: 0,
      provider_median_latency_ms: null,
      stream_median_latency_ms: null,
      disallowed_streams: 0,
      provider_server_accessible: false,
      provider_server_successful_response: false,
      provider_server_hosts: [],
      provider_server_http_statuses: [],
      manifest_description_present: claims.description_present,
      manifest_supported_types: claims.supported_types,
      manifest_effective_height: claims.max_height,
      manifest_accepted_languages: claims.accepted_languages,
      manifest_formats: claims.formats,
      manifest_curation_score: claims.curation_score,
      manifest_quality_signals: claims.quality_signals,
      settings_profiles_tested: 0,
      settings_profiles_producing_streams: 0,
      selected_settings_profiles: [],
      selected_setting_keys: [],
      settings_diagnostics: [],
      dns_preflight_status: decision.status || 'unknown',
      dns_preflight_reason: decision.reason || null,
      dns_preflight_selected_resolver: decision.selected_resolver || null,
      dns_migration_candidate: decision.migration_candidate || null,
      runtime_skipped_by_dns_preflight: true,
    },
    verified_max_height: null,
    reported_max_height: null,
    max_bandwidth: null,
    audio_languages: [],
    subtitle_languages: [],
    codecs: [],
    hdr_formats: [],
    formats: [],
    hosts: [],
    host_results: [],
    response_categories: ['dns_preflight'],
    tests: [],
  };
}

async function testCandidate(candidate) {
  const dnsPreflight = dnsPreflightForCandidate(candidate);
  if (dnsPreflight && dnsPreflight.decision?.continue_runtime === false) {
    return preflightOnlyResult(candidate, dnsPreflight);
  }
  const fixtureResults = [];
  const { profile, fixtures, fallbackFixtures } = fixturesForCandidate(candidate);

  async function executeFixture(fixture, fixturePhase) {
    const normalizedFixture = {
      tmdbId: String(fixture.tmdbId),
      mediaType: fixture.mediaType,
      season: fixture.season ?? null,
      episode: fixture.episode ?? null,
      label: fixture.label || String(fixture.tmdbId),
      title: fixture.title || fixture.label || null,
      year: fixture.year ?? null,
      category: fixture.category || fixture.mediaType || 'unknown',
    };
    const worker = await runWorker(candidate, normalizedFixture);
    const streams = Array.isArray(worker.streams) ? worker.streams : [];
    const probes = [];
    for (const stream of streams.slice(0, Number(modeConfig.max_streams_to_probe || 1))) {
      probes.push(await probeStream(stream, modeConfig));
    }

    const status = statusFrom(worker, probes);
    const score = scoreTest(worker, probes, status);
    const playable = probes.filter((probe) => probe.playback_verified);
    const reachableHosts = [...new Set(playable.map((probe) => probe.host).filter(Boolean))].sort();
    const verifiedMax = Math.max(0, ...playable.flatMap((probe) => probe.verifiedHeights || [])) || null;
    const reportedMax = Math.max(0, ...playable.flatMap((probe) => probe.reportedHeights || [])) || null;
    const effectiveMax = Math.max(0, ...playable.map((probe) => probe.effective_height || 0)) || null;
    const maxBandwidth = Math.max(0, ...playable.map((probe) => probe.maxBandwidth || 0)) || null;

    fixtureResults.push({
      fixture: normalizedFixture,
      fixture_phase: fixturePhase,
      status,
      score,
      provider_duration_ms: worker.duration_ms || null,
      worker_ok: Boolean(worker.ok),
      execution_context: worker.environment_context || null,
      provider_server_accessible: Boolean(worker.provider_server_accessible),
      provider_server_successful_response: Boolean(worker.provider_server_successful_response),
      provider_server_hosts: Array.isArray(worker.provider_server_hosts) ? worker.provider_server_hosts : [],
      provider_server_http_statuses: Array.isArray(worker.provider_server_http_statuses) ? worker.provider_server_http_statuses : [],
      network_observations: Array.isArray(worker.network_observations) ? worker.network_observations.map((item) => ({ stage: item.stage || 'provider_fetch', host: item.host || null, method: item.method || 'GET', path_pattern: item.path_pattern || null, status: item.status ?? null, ok: Boolean(item.ok), duration_ms: item.duration_ms ?? null, infrastructure: Boolean(item.infrastructure), error: item.error ? sanitizeError(item.error) : null, synthetic_fixture_fallback: Boolean(item.synthetic_fixture_fallback) })) : [],
      settings_diagnostics: Array.isArray(worker.settings_diagnostics)
        ? worker.settings_diagnostics.map((item) => ({
            name: item?.name || 'unknown',
            setting_keys: Array.isArray(item?.setting_keys) ? item.setting_keys : [],
            stream_count: Number(item?.stream_count || 0),
            error: item?.error ? sanitizeError(item.error) : null,
          }))
        : [],
      streams_returned: streams.length,
      disallowed_streams: worker.disallowed_stream_count || 0,
      streams_probed: probes.length,
      endpoints_reachable: probes.filter((probe) => probe.endpoint_reachable).length,
      streams_reachable: playable.length,
      streams_playable: playable.length,
      payload_verified_streams: playable.filter((probe) => probe.payload_verified).length,
      segment_or_direct_verified_streams: playable.filter(
        (probe) => probe.segment_reachable === true || probe.direct_signature_verified || probe.kind === 'dash',
      ).length,
      distinct_reachable_hosts: reachableHosts.length,
      reachable_hosts: reachableHosts,
      verified_max_height: verifiedMax,
      reported_max_height: reportedMax,
      effective_max_height: effectiveMax,
      max_bandwidth: maxBandwidth,
      audio_languages: [...new Set(playable.flatMap((probe) => probe.audioLanguages || []))].sort(),
      subtitle_languages: [...new Set(playable.flatMap((probe) => probe.subtitleLanguages || []))].sort(),
      accepted_audio_languages: [...new Set(playable.flatMap((probe) => probe.accepted_audio_languages || []))].sort(),
      accepted_subtitle_languages: [...new Set(playable.flatMap((probe) => probe.accepted_subtitle_languages || []))].sort(),
      accepted_subtitles_advertised: playable.reduce((sum, probe) => sum + Number(probe.accepted_subtitles_advertised || 0), 0),
      accepted_subtitles_reachable: playable.reduce((sum, probe) => sum + Number(probe.accepted_subtitles_reachable || 0), 0),
      subtitles_advertised: playable.reduce((sum, probe) => sum + Number(probe.subtitles_advertised || 0), 0),
      subtitles_reachable: playable.reduce((sum, probe) => sum + Number(probe.subtitles_reachable || 0), 0),
      codecs: [...new Set(playable.flatMap((probe) => probe.codecs || []))].sort(),
      hdr_formats: [...new Set(playable.flatMap((probe) => probe.hdrFormats || []))].sort(),
      formats: [...new Set(playable.map((probe) => probe.kind).filter(Boolean))].sort(),
      host_results: probes
        .filter((probe) => probe.host)
        .map((probe) => ({
          host: probe.host,
          category: probe.category || null,
          reachable: Boolean(probe.playback_verified),
          endpoint_reachable: Boolean(probe.endpoint_reachable),
          http_status: probe.http_status || null,
          latency_ms: Number.isFinite(probe.latency_ms) ? probe.latency_ms : null,
          kind: probe.kind || null,
          payload_verified: Boolean(probe.payload_verified),
          playback_verified: Boolean(probe.playback_verified),
        })),
      response_categories: [...new Set(probes.map((probe) => probe.category).filter(Boolean))].sort(),
      median_probe_latency_ms: median(playable.map((probe) => probe.latency_ms)),
      error: worker.ok ? null : sanitizeError(worker.error),
      probe_errors: probes
        .filter((probe) => !probe.playback_verified && probe.error)
        .map((probe) => sanitizeError(probe.error))
        .slice(0, 3),
    });
  }

  for (const fixture of fixtures) await executeFixture(fixture, 'primary');

  const allPrimaryNoStreams = fixtureResults.length > 0
    && fixtureResults.every((item) => item.fixture_phase === 'primary' && item.status === 'no_streams');
  const useFallback = requestedMode === 'deep'
    && fallbackFixtures.length > 0
    && modeConfig.fallback_only_when_all_primary_no_streams !== false
    && allPrimaryNoStreams;
  if (useFallback) {
    for (const fixture of fallbackFixtures) await executeFixture(fixture, 'fallback');
  }

  const anyP2p = fixtureResults.some((item) => (item.disallowed_streams || 0) > 0 || item.status === 'excluded');
  let status;
  if (anyP2p) status = 'excluded';
  else if (fixtureResults.some((item) => item.status === 'healthy')) status = 'healthy';
  else {
    const priority = ['reachable', 'unavailable', 'degraded', 'blocked', 'no_streams', 'provider_unreachable', 'runtime_error'];
    status = priority.find((candidateStatus) => fixtureResults.some((item) => item.status === candidateStatus)) || 'runtime_error';
  }

  const activationTests = useFallback
    ? fixtureResults.filter((item) => item.fixture_phase === 'fallback')
    : fixtureResults.filter((item) => item.fixture_phase === 'primary');
  const healthyTests = fixtureResults.filter((item) => item.status === 'healthy');
  const activationHealthyTests = activationTests.filter((item) => item.status === 'healthy');
  const healthyAverage = activationHealthyTests.length
    ? activationHealthyTests.reduce((sum, item) => sum + Number(item.score || 0), 0) / activationHealthyTests.length
    : 0;
  // When every primary title returned no_streams, the fallback set becomes the
  // activation sample. Otherwise catalogue mismatch would permanently penalise
  // a provider even after several alternate titles proved playable.
  const coverageRatio = activationTests.length
    ? activationHealthyTests.length / activationTests.length
    : 0;
  const claims = manifestClaims(candidate);
  const score = status === 'healthy'
    ? Math.round(healthyAverage * 0.8 + coverageRatio * 20)
    : status === 'reachable' && claims.description_present && claims.max_height && claims.accepted_languages.length
      ? 75
      : Math.max(0, ...fixtureResults.map((item) => Number(item.score || 0)));

  const healthyCategories = [...new Set(activationHealthyTests.map((item) => item.fixture.category).filter(Boolean))].sort();
  const playableStreams = fixtureResults.reduce((sum, item) => sum + Number(item.streams_playable || 0), 0);
  const payloadVerifiedStreams = fixtureResults.reduce((sum, item) => sum + Number(item.payload_verified_streams || 0), 0);
  const playableFixtures = fixtureResults.filter((item) => Number(item.streams_playable || 0) > 0).length;
  const reachableHosts = [...new Set(healthyTests.flatMap((item) => item.reachable_hosts || []))].sort();
  const acceptedAudio = [...new Set(healthyTests.flatMap((item) => item.accepted_audio_languages || []))].sort();
  const acceptedSubtitles = [...new Set(healthyTests.flatMap((item) => item.accepted_subtitle_languages || []))].sort();
  const inconclusiveStatuses = new Set(activationConfig.inconclusive_statuses || ['no_streams', 'blocked', 'provider_unreachable', 'runtime_error']);
  const settingsProfileAttempts = fixtureResults.flatMap((item) =>
    Array.isArray(item.settings_diagnostics)
      ? item.settings_diagnostics.map((diag) => ({
          fixture: item.fixture?.label || item.fixture?.tmdbId || null,
          fixture_phase: item.fixture_phase,
          profile: diag.name || 'unknown',
          setting_keys: Array.isArray(diag.setting_keys) ? diag.setting_keys : [],
          stream_count: Number(diag.stream_count || 0),
          error: diag.error || null,
        }))
      : [],
  );
  const selectedProfiles = [...new Set(
    fixtureResults.map((item) => item.execution_context?.selected_settings_profile).filter(Boolean),
  )].sort();
  const selectedSettingKeys = [...new Set(
    fixtureResults.flatMap((item) => item.execution_context?.selected_setting_keys || []),
  )].sort();
  const settingsProfilesTestedTotal = settingsProfileAttempts.length;
  const settingsProfilesProducingStreams = settingsProfileAttempts.filter((item) => item.stream_count > 0).length;

  return {
    key: candidate.key,
    source: candidate.source,
    upstream_id: candidate.upstream_id,
    canonical_id: candidate.canonical_id,
    sha256: candidate.sha256,
    mode: requestedMode,
    status,
    ci_classification: status === 'excluded' || status === 'unavailable' || status === 'degraded'
      ? 'conclusive_failure'
      : inconclusiveStatuses.has(status)
        ? 'inconclusive'
        : status === 'healthy'
          ? 'conclusive_success'
          : 'unknown',
    score,
    dns_preflight: dnsPreflight,
    candidate_profile: {
      anime: profile.anime,
      supported_types: profile.types,
      required_fixture_categories: profile.requiredCategories,
      derived_locale: providerLocale(candidate),
      has_settings: Boolean(candidate.metadata?.hasSettings),
      manifest_claims: claims,
    },
    evidence: {
      primary_fixtures_tested: fixtureResults.filter((item) => item.fixture_phase === 'primary').length,
      fallback_fixtures_tested: fixtureResults.filter((item) => item.fixture_phase === 'fallback').length,
      fallback_triggered: useFallback,
      fixtures_tested: activationTests.length,
      total_fixtures_executed: fixtureResults.length,
      activation_fixture_phase: useFallback ? 'fallback' : 'primary',
      healthy_fixtures: activationHealthyTests.length,
      healthy_fixture_ratio: coverageRatio,
      playable_fixtures: playableFixtures,
      required_fixture_categories: profile.requiredCategories,
      healthy_fixture_categories: healthyCategories,
      streams_playable: playableStreams,
      payload_verified_streams: payloadVerifiedStreams,
      distinct_reachable_hosts: reachableHosts.length,
      reachable_hosts: reachableHosts,
      verified_max_height: Math.max(0, ...healthyTests.map((item) => item.verified_max_height || 0)) || null,
      reported_max_height: Math.max(0, ...healthyTests.map((item) => item.reported_max_height || 0)) || null,
      effective_max_height: Math.max(0, ...healthyTests.map((item) => item.effective_max_height || 0)) || null,
      max_bandwidth: Math.max(0, ...healthyTests.map((item) => item.max_bandwidth || 0)) || null,
      audio_languages: [...new Set(healthyTests.flatMap((item) => item.audio_languages || []))].sort(),
      subtitle_languages: [...new Set(healthyTests.flatMap((item) => item.subtitle_languages || []))].sort(),
      accepted_audio_languages: acceptedAudio,
      accepted_subtitle_languages: acceptedSubtitles,
      accepted_subtitles_advertised: healthyTests.reduce((sum, item) => sum + Number(item.accepted_subtitles_advertised || 0), 0),
      accepted_subtitles_reachable: healthyTests.reduce((sum, item) => sum + Number(item.accepted_subtitles_reachable || 0), 0),
      provider_median_latency_ms: median(healthyTests.map((item) => item.provider_duration_ms)),
      stream_median_latency_ms: median(healthyTests.map((item) => item.median_probe_latency_ms)),
      disallowed_streams: fixtureResults.reduce((sum, item) => sum + Number(item.disallowed_streams || 0), 0),
      provider_server_accessible: fixtureResults.some((item) => item.provider_server_accessible),
      provider_server_successful_response: fixtureResults.some((item) => item.provider_server_successful_response),
      provider_server_hosts: [...new Set(fixtureResults.flatMap((item) => item.provider_server_hosts || []))].sort(),
      provider_server_http_statuses: [...new Set(fixtureResults.flatMap((item) => item.provider_server_http_statuses || []))].sort((a, b) => a - b),
      manifest_description_present: claims.description_present,
      manifest_supported_types: claims.supported_types,
      manifest_effective_height: claims.max_height,
      manifest_accepted_languages: claims.accepted_languages,
      manifest_formats: claims.formats,
      manifest_curation_score: claims.curation_score,
      manifest_quality_signals: claims.quality_signals,
      settings_profiles_tested: settingsProfilesTestedTotal,
      settings_profiles_producing_streams: settingsProfilesProducingStreams,
      selected_settings_profiles: selectedProfiles,
      selected_setting_keys: selectedSettingKeys,
      settings_diagnostics: settingsProfileAttempts,
      dns_preflight_status: dnsPreflight?.decision?.status || null,
      dns_preflight_reason: dnsPreflight?.decision?.reason || null,
      dns_preflight_selected_resolver: dnsPreflight?.decision?.selected_resolver || null,
      dns_migration_candidate: dnsPreflight?.decision?.migration_candidate || null,
      runtime_skipped_by_dns_preflight: false,
    },
    verified_max_height: Math.max(0, ...fixtureResults.map((item) => item.verified_max_height || 0)) || null,
    reported_max_height: Math.max(0, ...fixtureResults.map((item) => item.reported_max_height || 0)) || null,
    max_bandwidth: Math.max(0, ...fixtureResults.map((item) => item.max_bandwidth || 0)) || null,
    audio_languages: [...new Set(fixtureResults.flatMap((item) => item.audio_languages || []))].sort(),
    subtitle_languages: [...new Set(fixtureResults.flatMap((item) => item.subtitle_languages || []))].sort(),
    codecs: [...new Set(fixtureResults.flatMap((item) => item.codecs || []))].sort(),
    hdr_formats: [...new Set(fixtureResults.flatMap((item) => item.hdr_formats || []))].sort(),
    formats: [...new Set(fixtureResults.flatMap((item) => item.formats || []))].sort(),
    hosts: [...new Set(fixtureResults.flatMap((item) => item.reachable_hosts || []))].sort(),
    host_results: fixtureResults.flatMap((item) => item.host_results || []),
    response_categories: [...new Set(fixtureResults.flatMap((item) => item.response_categories || []))].sort(),
    tests: fixtureResults,
  };
}

async function runPool(items, worker, limit) {
  const results = new Array(items.length);
  let nextIndex = 0;
  async function runner() {
    while (true) {
      const index = nextIndex;
      nextIndex += 1;
      if (index >= items.length) return;
      try {
        results[index] = await worker(items[index]);
      } catch (error) {
        const candidate = items[index];
        results[index] = {
          key: candidate.key,
          source: candidate.source,
          upstream_id: candidate.upstream_id,
          canonical_id: candidate.canonical_id,
          sha256: candidate.sha256,
          mode: requestedMode,
          status: 'runtime_error',
          score: 0,
          error: sanitizeError(error),
          evidence: {},
          tests: [],
        };
      }
      const result = results[index];
      process.stdout.write(`[${index + 1}/${items.length}] ${result.key}: ${result.status} (${result.score})\n`);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, () => runner()));
  return results;
}

const startedAt = new Date();
const results = await runPool(registry.candidates, testCandidate, concurrency);
const statuses = ['healthy', 'reachable', 'blocked', 'degraded', 'no_streams', 'provider_unreachable', 'runtime_error', 'unavailable', 'excluded'];
const report = {
  schema_version: 65,
  environment: 'github-actions-node',
  mode: requestedMode,
  generated_at: new Date().toISOString(),
  duration_seconds: Math.round((Date.now() - startedAt.getTime()) / 1000),
  candidate_count: results.length,
  excluded_during_discovery: registry.excluded_count || 0,
  dns_preflight: dnsPreflightReport ? {
    generated_at: dnsPreflightReport.generated_at || null,
    counts: dnsPreflightReport.counts || {},
    resolver_order: dnsPreflightReport.resolver_order || [],
    neutral_resolvers: dnsPreflightReport.neutral_resolvers || [],
  } : null,
  counts: Object.fromEntries(statuses.map((status) => [status, results.filter((item) => item.status === status).length])),
  results,
};
await fs.mkdir(OUTPUT_DIR, { recursive: true });
await fs.writeFile(path.join(OUTPUT_DIR, RESULTS_FILENAME), `${JSON.stringify(report, null, 2)}\n`);
process.stdout.write(`Health check complete (${requestedMode}): ${JSON.stringify(report.counts)}\n`);
