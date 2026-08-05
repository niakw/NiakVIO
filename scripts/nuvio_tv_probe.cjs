#!/usr/bin/env node
'use strict';

const path = require('node:path');
const { webcrypto } = require('node:crypto');

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

async function inspectStream(row) {
  const url = String(row?.url || '').trim();
  const result = { url, playable: false, kind: null, status: null, content_type: null, starts_extm3u: false, error: null };
  if (!/^https?:\/\//i.test(url)) { result.error = 'missing_http_url'; return result; }
  const headers = headerObject(row.headers);
  if (!headers.Accept) headers.Accept = '*/*';
  if (!headers['User-Agent']) headers['User-Agent'] = globalThis.navigator.userAgent;
  if (!/\.m3u8(?:[?#]|$)/i.test(url) && !headers.Range) headers.Range = 'bytes=0-65535';
  try {
    const response = await fetch(url, { headers, redirect: 'follow', signal: AbortSignal.timeout(20000) });
    result.status = response.status;
    result.content_type = response.headers.get('content-type') || '';
    const buffer = Buffer.from(await response.arrayBuffer());
    const text = buffer.subarray(0, 131072).toString('utf8').replace(/^\uFEFF/, '').trimStart();
    result.starts_extm3u = text.startsWith('#EXTM3U');
    const type = result.content_type.toLowerCase();
    if (result.starts_extm3u) { result.playable = true; result.kind = 'hls'; }
    else if (/application\/dash\+xml/.test(type) || /<MPD[\s>]/i.test(text.slice(0, 2048))) { result.playable = true; result.kind = 'dash'; }
    else if (/^video\//.test(type) || /octet-stream|matroska/.test(type) || buffer.subarray(4, 8).toString('ascii') === 'ftyp' || buffer.subarray(0, 4).equals(Buffer.from([0x1a, 0x45, 0xdf, 0xa3]))) {
      result.playable = response.ok || response.status === 206; result.kind = 'file';
    } else if (/text\/html|application\/xhtml/.test(type) || /^<!doctype html|^<html/i.test(text)) {
      result.error = 'html_not_media';
    } else if (!response.ok) result.error = `http_${response.status}`;
    else result.error = 'unrecognized_media';
  } catch (error) {
    result.error = `${error?.name || 'Error'}: ${error?.message || error}`;
  }
  return result;
}

async function main() {
  const [providerArg, fixtureArg = '{}', settingsArg = '{}'] = process.argv.slice(2);
  if (!providerArg) throw new Error('usage: nuvio_tv_probe.cjs <provider.js> <fixture-json> <settings-json>');
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
    // Exact NuvioTV contract: four positional arguments. Settings are global.
    raw = await provider.getStreams(String(fixture.tmdbId || fixture.id || ''), String(fixture.mediaType || fixture.type || 'movie'), fixture.season ?? null, fixture.episode ?? null);
  } catch (error) {
    runtimeError = `${error?.name || 'Error'}: ${error?.message || error}`;
    raw = [];
  }
  const rows = rowsFrom(raw).filter((row) => row && typeof row === 'object' && row.url);
  const inspected = [];
  for (const row of rows.slice(0, 20)) inspected.push({ row, media: await inspectStream(row) });
  const playable = inspected.filter((item) => item.media.playable);
  process.stdout.write(JSON.stringify({
    ok: !runtimeError && playable.length > 0,
    duration_ms: Date.now() - started,
    runtime_error: runtimeError,
    raw_stream_count: rows.length,
    playable_stream_count: playable.length,
    streams: inspected,
  }) + '\n');
  process.exitCode = playable.length ? 0 : 2;
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
