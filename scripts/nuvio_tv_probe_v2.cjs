#!/usr/bin/env node
'use strict';

const path = require('node:path');
const { webcrypto } = require('node:crypto');
const { streamIdentity } = require('./nuvio_client_lab.cjs');

const ASSET_EXT = /\.(?:woff2?|ttf|otf|eot|css|js|mjs|map|png|jpe?g|gif|svg|ico|webmanifest|json|xml|vtt|srt)(?:[?#]|$)/i;
const REJECT_HOSTS = /(?:^|\.)(?:twitter\.com|x\.com|twimg\.com|google\.com|googleusercontent\.com|gitlab\.com|github\.com|facebook\.com|instagram\.com)$/i;
const DEMO_PATH = /(?:chrome\/static\/videos|sticky\/videos|static\/money|grok-|radar_promo|big[_-]?buck[_-]?bunny|sample[-_]?videos)/i;

class MemoryStorage {
  constructor(seed = {}) { this.map = new Map(Object.entries(seed).map(([k, v]) => [String(k), String(v)])); }
  get length() { return this.map.size; }
  key(index) { return [...this.map.keys()][Number(index)] ?? null; }
  getItem(key) { return this.map.has(String(key)) ? this.map.get(String(key)) : null; }
  setItem(key, value) { this.map.set(String(key), String(value)); }
  removeItem(key) { this.map.delete(String(key)); }
  clear() { this.map.clear(); }
}

function define(name, value) {
  try { Object.defineProperty(globalThis, name, { value, configurable: true, writable: true, enumerable: true }); }
  catch { globalThis[name] = value; }
}

function installRuntime(settings = {}) {
  if (!globalThis.crypto) define('crypto', webcrypto);
  if (!globalThis.atob) define('atob', (value) => Buffer.from(String(value), 'base64').toString('binary'));
  if (!globalThis.btoa) define('btoa', (value) => Buffer.from(String(value), 'binary').toString('base64'));
  define('SCRAPER_SETTINGS', Object.freeze({ ...settings }));
  define('__NUVIO_PROVIDER_SETTINGS__', Object.freeze({ ...settings }));
  define('navigator', {
    userAgent: 'Mozilla/5.0 (Linux; Android 14; Android TV) AppleWebKit/537.36 Chrome/131 Safari/537.36 NuvioTV',
    language: 'fr-FR', languages: ['fr-FR', 'fr', 'en'], platform: 'android', product: 'ReactNative', onLine: true,
  });
  if (!globalThis.window) define('window', globalThis);
  if (!globalThis.self) define('self', globalThis);
  define('localStorage', new MemoryStorage());
  define('sessionStorage', new MemoryStorage());
  define('location', { href: 'https://app.nuvio.local/', origin: 'https://app.nuvio.local', protocol: 'https:', hostname: 'app.nuvio.local', pathname: '/', search: '', hash: '' });
  define('document', {
    cookie: '', location: globalThis.location,
    createElement: () => ({ style: {}, setAttribute() {}, getAttribute() { return null; } }),
    querySelector() { return null; }, querySelectorAll() { return []; },
  });
  define('Platform', { OS: 'android', select: (choices) => choices?.android ?? choices?.default });
}

function exportedProvider(moduleValue) {
  const candidates = [moduleValue, moduleValue?.default, moduleValue?.provider, globalThis.__provider, globalThis.provider, globalThis];
  return candidates.find((value) => value && typeof value.getStreams === 'function') || null;
}

function rowsFrom(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === 'object') {
    for (const key of ['streams', 'results', 'data']) if (Array.isArray(value[key])) return value[key];
  }
  return [];
}

function headerObject(value) {
  if (!value || typeof value !== 'object') return {};
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [String(key), String(item)]));
}

function urlRejected(raw) {
  const url = String(raw || '').trim();
  if (!/^https?:\/\//i.test(url) || ASSET_EXT.test(url) || DEMO_PATH.test(url)) return true;
  try { return REJECT_HOSTS.test(new URL(url).hostname); }
  catch { return true; }
}

function binaryKind(buffer) {
  if (!buffer?.length) return null;
  if (buffer.length >= 12 && buffer.subarray(4, 8).toString('ascii') === 'ftyp') return 'mp4';
  if (buffer.length >= 4 && buffer[0] === 0x1a && buffer[1] === 0x45 && buffer[2] === 0xdf && buffer[3] === 0xa3) return 'matroska';
  if (buffer.length >= 188 && buffer[0] === 0x47 && (buffer.length < 376 || buffer[188] === 0x47)) return 'mpegts';
  return null;
}

function parseHlsAttributes(value) {
  const out = {};
  for (const match of String(value || '').matchAll(/([A-Z0-9-]+)=("[^"]*"|[^,]*)/gi)) {
    out[match[1].toUpperCase()] = String(match[2] || '').replace(/^"|"$/g, '');
  }
  return out;
}

function absoluteUrl(raw, base) {
  try { return new URL(String(raw || '').trim(), base).toString(); }
  catch { return null; }
}

function hlsGraph(text, baseUrl) {
  const lines = String(text || '').split(/\r?\n/).map((line) => line.trim());
  const variants = [];
  const externalAudio = [];
  let audioGroups = 0;
  let durationSeconds = 0;
  let durationEntryCount = 0;
  let isVod = false;
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (/^#EXTINF\s*:/i.test(line)) {
      const duration = Number(line.slice(line.indexOf(':') + 1).split(',')[0]);
      if (Number.isFinite(duration) && duration >= 0) {
        durationSeconds += duration;
        durationEntryCount += 1;
      }
    } else if (/^#EXT-X-ENDLIST\s*$/i.test(line)) {
      isVod = true;
    } else if (/^#EXT-X-STREAM-INF\s*:/i.test(line)) {
      for (let next = index + 1; next < lines.length; next += 1) {
        const candidate = lines[next];
        if (!candidate) continue;
        if (candidate.startsWith('#')) continue;
        const url = absoluteUrl(candidate, baseUrl);
        if (url && !variants.includes(url)) variants.push(url);
        break;
      }
    } else if (/^#EXT-X-MEDIA\s*:/i.test(line)) {
      const attrs = parseHlsAttributes(line.slice(line.indexOf(':') + 1));
      if (String(attrs.TYPE || '').toUpperCase() !== 'AUDIO') continue;
      audioGroups += 1;
      if (attrs.URI) {
        const url = absoluteUrl(attrs.URI, baseUrl);
        if (url && !externalAudio.includes(url)) externalAudio.push(url);
      }
    }
  }
  return { variants, externalAudio, audioGroups, durationSeconds: durationEntryCount ? durationSeconds : null, isVod };
}

async function inspectHlsChild(url, headers) {
  try {
    const response = await fetch(url, { headers, redirect: 'follow', signal: AbortSignal.timeout(16000) });
    if (!response.ok) return { playable: false, status: response.status, error: `http_${response.status}` };
    const text = (await response.text()).replace(/^\uFEFF/, '').trimStart();
    if (!text.startsWith('#EXTM3U')) return { playable: false, status: response.status, error: 'child_not_extm3u' };
    const hasMedia = /#EXTINF\s*:/i.test(text) || /#EXT-X-PART\s*:/i.test(text) || /#EXT-X-STREAM-INF\s*:/i.test(text) || /#EXT-X-MAP\s*:/i.test(text);
    const graph = hlsGraph(text, response.url || url);
    return {
      playable: hasMedia,
      status: response.status,
      error: hasMedia ? null : 'child_header_only',
      media_duration_seconds: graph.durationSeconds,
      is_vod: graph.isVod,
    };
  } catch (error) {
    return { playable: false, status: null, error: `${error?.name || 'Error'}: ${error?.message || error}` };
  }
}

async function inspectStream(row) {
  const url = String(row?.url || '').trim();
  const result = {
    url,
    playable: false,
    kind: null,
    status: null,
    content_type: null,
    starts_extm3u: false,
    binary_signature: null,
    hls_master: false,
    hls_variant_count: 0,
    hls_audio_group_count: 0,
    hls_external_audio_count: 0,
    hls_variant_playable: null,
    hls_external_audio_playable: null,
    media_duration_seconds: null,
    error: null,
  };
  if (urlRejected(url)) { result.error = 'rejected_asset_or_demo'; return result; }
  const headers = headerObject(row.headers);
  if (!headers.Accept) headers.Accept = '*/*';
  if (!headers['User-Agent']) headers['User-Agent'] = globalThis.navigator.userAgent;
  if (!/\.m3u8(?:[?#]|$)/i.test(url) && !headers.Range) headers.Range = 'bytes=0-262143';
  try {
    const response = await fetch(url, { headers, redirect: 'follow', signal: AbortSignal.timeout(20000) });
    result.status = response.status;
    result.content_type = response.headers.get('content-type') || '';
    const buffer = Buffer.from(await response.arrayBuffer());
    const text = buffer.subarray(0, 262144).toString('utf8').replace(/^\uFEFF/, '').trimStart();
    result.starts_extm3u = text.startsWith('#EXTM3U');
    result.binary_signature = binaryKind(buffer);
    const type = result.content_type.toLowerCase();
    if (result.starts_extm3u) {
      result.kind = 'hls';
      const graph = hlsGraph(text, response.url || url);
      result.media_duration_seconds = graph.durationSeconds;
      result.hls_master = graph.variants.length > 0 || /#EXT-X-STREAM-INF\s*:/i.test(text);
      result.hls_variant_count = graph.variants.length;
      result.hls_audio_group_count = graph.audioGroups;
      result.hls_external_audio_count = graph.externalAudio.length;
      const hlsHasMedia = /#EXTINF\s*:/i.test(text) || /#EXT-X-PART\s*:/i.test(text) || /#EXT-X-MAP\s*:/i.test(text);
      if (!result.hls_master && !hlsHasMedia) {
        result.error = 'hls_header_only';
        return result;
      }
      if (result.hls_master) {
        if (!graph.variants.length) {
          result.error = 'hls_master_without_variant';
          return result;
        }
        const variant = await inspectHlsChild(graph.variants[0], headers);
        result.hls_variant_playable = variant.playable;
        if (Number.isFinite(variant.media_duration_seconds) && variant.media_duration_seconds > 0) {
          result.media_duration_seconds = variant.media_duration_seconds;
        }
        if (!variant.playable) {
          result.error = `hls_variant_${variant.error || 'invalid'}`;
          return result;
        }
        if (graph.externalAudio.length) {
          const audio = await inspectHlsChild(graph.externalAudio[0], headers);
          result.hls_external_audio_playable = audio.playable;
          if (!audio.playable) {
            result.error = `hls_audio_${audio.error || 'invalid'}`;
            return result;
          }
        }
      }
      result.playable = true;
    }
    else if (/application\/dash\+xml/.test(type) || /<MPD[\s>]/i.test(text.slice(0, 4096))) { result.playable = true; result.kind = 'dash'; }
    else if (result.binary_signature) { result.playable = response.ok || response.status === 206; result.kind = result.binary_signature; }
    else if (/^video\//.test(type) && !/^text\//.test(type)) { result.playable = response.ok || response.status === 206; result.kind = type.split('/')[1] || 'video'; }
    else if (/text\/html|application\/xhtml/.test(type) || /^<!doctype html|^<html/i.test(text)) result.error = 'html_not_media';
    else if (!response.ok) result.error = `http_${response.status}`;
    else result.error = 'unrecognized_media';
  } catch (error) {
    result.error = `${error?.name || 'Error'}: ${error?.message || error}`;
  }
  return result;
}

async function main() {
  const [providerArg, fixtureArg = '{}', settingsArg = '{}'] = process.argv.slice(2);
  if (!providerArg) throw new Error('usage: nuvio_tv_probe_v2.cjs <provider.js> <fixture-json> <settings-json>');
  const fixture = JSON.parse(fixtureArg);
  const settings = JSON.parse(settingsArg);
  installRuntime(settings);
  const providerPath = path.resolve(providerArg);
  delete require.cache[providerPath];
  const loaded = require(providerPath);
  const provider = exportedProvider(loaded);
  if (!provider) throw new Error('provider does not export getStreams');
  const started = Date.now();
  let raw;
  let runtimeError = null;
  try {
    raw = await provider.getStreams(String(fixture.tmdbId || fixture.id || ''), String(fixture.mediaType || fixture.type || 'movie'), fixture.season ?? null, fixture.episode ?? null);
  } catch (error) {
    runtimeError = `${error?.name || 'Error'}: ${error?.message || error}`;
    raw = [];
  }
  const rows = rowsFrom(raw).filter((row) => row && typeof row === 'object' && row.url && !urlRejected(row.url)).slice(0, 16);
  const media = await Promise.all(rows.map((row) => inspectStream(row)));
  const inspected = rows.map((row, index) => {
    const metadataIdentity = streamIdentity(row, fixture);
    const mediaResult = media[index];
    const expectedMinutes = Number(fixture?.expectedDurationMinutes || 0);
    const expectedSeconds = expectedMinutes > 0 ? expectedMinutes * 60 : null;
    const measuredSeconds = Number(mediaResult?.media_duration_seconds || 0);
    let durationIdentity = { status: 'unknown', reason: 'duration_unavailable', ratio: null };
    if (expectedSeconds && Number.isFinite(measuredSeconds) && measuredSeconds > 0) {
      const ratio = measuredSeconds / expectedSeconds;
      durationIdentity = (ratio < 0.55 || ratio > 1.8)
        ? { status: 'contradiction', reason: 'fixture_duration_mismatch', ratio }
        : { status: 'match', reason: 'fixture_duration_match', ratio };
    }
    let identity = metadataIdentity;
    if (metadataIdentity.status !== 'contradiction' && durationIdentity.status === 'contradiction') {
      identity = durationIdentity;
    } else if (metadataIdentity.status === 'unknown' && durationIdentity.status === 'match') {
      identity = durationIdentity;
    }
    return { row, media: mediaResult, identity, metadata_identity: metadataIdentity, duration_identity: durationIdentity };
  });
  const playable = inspected.filter((item) => item.media.playable);
  const identityContradictions = playable.filter((item) => item.identity.status === 'contradiction');
  const identityVerified = playable.filter((item) => item.identity.status === 'match');
  const identityUnknown = playable.filter((item) => item.identity.status === 'unknown');
  const strictComplete = playable.length > 0
    && identityVerified.length === playable.length
    && identityContradictions.length === 0
    && identityUnknown.length === 0;
  process.stdout.write(JSON.stringify({
    ok: !runtimeError && strictComplete,
    duration_ms: Date.now() - started,
    runtime_error: runtimeError,
    raw_stream_count: rows.length,
    playable_stream_count: playable.length,
    content_verified_count: identityVerified.length,
    identity_verified_count: identityVerified.length,
    identity_unverified_count: identityUnknown.length,
    identity_contradiction_count: identityContradictions.length,
    streams: inspected,
  }) + '\n');
  process.exitCode = !runtimeError && strictComplete ? 0 : 2;
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
