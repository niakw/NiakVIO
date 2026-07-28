#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/* Execute one untrusted Nuvio provider in a disposable child process.
 *
 * This worker runs only inside the read-only test job. Provider console output is
 * suppressed so temporary endpoint URLs are not copied into public Action logs.
 * A small browser/React-Native compatibility surface is installed because some
 * providers return [] under plain Node even though they work in Nuvio/Hermes.
 */

const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const { webcrypto } = require('node:crypto');
const { guardedFetch } = require('./network_guard.cjs');
const Module = require('node:module');

const networkObservations = [];
function installModuleRestrictions() {
  const blocked = new Set([
    'child_process', 'node:child_process', 'cluster', 'node:cluster',
    'worker_threads', 'node:worker_threads', 'inspector', 'node:inspector',
    'repl', 'node:repl', 'vm', 'node:vm', 'module', 'node:module',
  ]);
  const originalLoad = Module._load;
  Module._load = function restrictedLoad(request, parent, isMain) {
    if (blocked.has(String(request))) throw new Error(`provider module blocked: ${request}`);
    return originalLoad.call(this, request, parent, isMain);
  };
}

function wrapLimitedResponse(response, perResponseLimit, consumeBytes) {
  const checked = async (reader) => {
    const value = await reader();
    const bytes = Buffer.isBuffer(value) ? value.length
      : value instanceof ArrayBuffer ? value.byteLength
      : ArrayBuffer.isView(value) ? value.byteLength
      : Buffer.byteLength(typeof value === 'string' ? value : JSON.stringify(value));
    if (bytes > perResponseLimit) throw new Error(`response body exceeds limit (${bytes} bytes)`);
    consumeBytes(bytes);
    return value;
  };
  return new Proxy(response, {
    get(target, prop, receiver) {
      if (prop === 'text') return () => checked(() => target.text());
      if (prop === 'json') return () => checked(async () => JSON.parse(await target.text()));
      if (prop === 'arrayBuffer') return () => checked(() => target.arrayBuffer());
      if (prop === 'blob') return () => checked(() => target.blob());
      return Reflect.get(target, prop, receiver);
    },
  });
}

function safeHost(value) {
  try { return new URL(typeof value === 'string' ? value : value.url).hostname.toLowerCase(); } catch { return null; }
}
function safeRequestMetadata(input, init = {}) {
  try {
    const raw = typeof input === 'string' ? input : input?.url;
    const url = new URL(raw);
    const method = String(init?.method || (typeof Request !== 'undefined' && input instanceof Request ? input.method : 'GET') || 'GET').toUpperCase();
    const parts = url.pathname.split('/').filter(Boolean);
    const normalized = parts.map((part) => {
      if (/^\d+$/.test(part)) return '{id}';
      if (/^[0-9a-f]{16,}$/i.test(part)) return '{token}';
      if (/^[A-Za-z0-9_-]{28,}$/.test(part)) return '{token}';
      if (/^s\d+e\d+$/i.test(part)) return '{episode}';
      if (/^\d{4}$/.test(part)) return '{year}';
      return part.length > 48 ? '{value}' : part;
    });
    let pathPattern = '/' + normalized.join('/');
    if (url.pathname.endsWith('/') && pathPattern !== '/') pathPattern += '/';
    if (url.search) {
      const keys = [...url.searchParams.keys()].slice(0, 12).sort();
      if (keys.length) pathPattern += `?${keys.map((key) => `${key}={value}`).join('&')}`;
    }
    return { host: url.hostname.toLowerCase(), method, path_pattern: pathPattern || '/' };
  } catch {
    return { host: safeHost(input), method: String(init?.method || 'GET').toUpperCase(), path_pattern: null };
  }
}

function inferRequestStage(pathPattern) {
  const value = String(pathPattern || '').toLowerCase();
  if (!value || value === '/') return 'origin_probe';
  if (/search|recherche|query|ajax|api\/.*search/.test(value)) return 'search';
  if (/embed|player|watch|video|stream|iframe/.test(value)) return 'player';
  if (/season|saison|episode|{episode}/.test(value)) return 'episode';
  return 'content_lookup';
}

function isInfrastructureHost(host) {
  if (!host) return true;
  const exact = new Set([
    'api.themoviedb.org',
    'raw.githubusercontent.com',
    'api.github.com',
    'graphql.anilist.co',
    'api.jikan.moe',
    'api.tvmaze.com',
    'api.imdbapi.dev',
    'cdn.jsdelivr.net',
    'unpkg.com',
  ]);
  return exact.has(host)
    || host.endsWith('.githubusercontent.com')
    || host.endsWith('.themoviedb.org')
    || host.endsWith('.anilist.co');
}

function emit(payload) {
  process.stdout.write(`NUVIO_HEALTH_RESULT=${JSON.stringify(payload)}\n`);
}

class MemoryStorage {
  constructor(seed = {}) {
    this.values = new Map(
      Object.entries(seed || {}).map(([key, value]) => [String(key), String(value)]),
    );
  }

  get length() { return this.values.size; }
  key(index) { return [...this.values.keys()][Number(index)] ?? null; }
  getItem(key) { return this.values.has(String(key)) ? this.values.get(String(key)) : null; }
  setItem(key, value) { this.values.set(String(key), String(value)); }
  removeItem(key) { this.values.delete(String(key)); }
  clear() { this.values.clear(); }
}

function defineGlobal(name, value) {
  try {
    Object.defineProperty(globalThis, name, {
      value,
      configurable: true,
      enumerable: true,
      writable: true,
    });
  } catch {
    try { globalThis[name] = value; } catch {}
  }
}


function syntheticTmdbResponse(input, fixture = {}) {
  try {
    const raw = typeof input === 'string' ? input : input?.url;
    const url = new URL(raw);
    if (url.hostname.toLowerCase() !== 'api.themoviedb.org') return null;
    const type = String(fixture.mediaType || fixture.type || 'movie').toLowerCase() === 'tv' ? 'tv' : 'movie';
    const id = String(fixture.tmdbId || fixture.id || '');
    if (!id || !url.pathname.includes(`/${type}/${id}`)) return null;
    const title = String(fixture.title || fixture.label || '').replace(/\s*\(\d{4}\)\s*$/, '').trim();
    if (!title) return null;
    const year = Number(fixture.year) || null;
    let payload;
    if (url.pathname.endsWith('/alternative_titles')) {
      payload = type === 'tv'
        ? { id: Number(id), results: [{ iso_3166_1: 'FR', title, type: '' }] }
        : { id: Number(id), titles: [{ iso_3166_1: 'FR', title, type: '' }] };
    } else if (url.pathname.endsWith('/translations')) {
      payload = { id: Number(id), translations: [
        { iso_3166_1: 'FR', iso_639_1: 'fr', name: 'Français', english_name: 'French', data: type === 'tv' ? { name: title, overview: '', homepage: '', tagline: '' } : { title, overview: '', homepage: '', tagline: '' } },
        { iso_3166_1: 'US', iso_639_1: 'en', name: 'English', english_name: 'English', data: type === 'tv' ? { name: title, overview: '', homepage: '', tagline: '' } : { title, overview: '', homepage: '', tagline: '' } },
      ] };
    } else {
      payload = type === 'tv'
        ? { id: Number(id), name: title, original_name: title, first_air_date: year ? `${year}-01-01` : '', origin_country: ['US'], original_language: 'en' }
        : { id: Number(id), title, original_title: title, release_date: year ? `${year}-01-01` : '', original_language: 'en' };
    }
    return new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'content-type': 'application/json; charset=utf-8', 'x-nuvio-fixture-fallback': '1' },
    });
  } catch {
    return null;
  }
}

function installPolyfills(context = {}) {
  if (!globalThis.crypto) defineGlobal('crypto', webcrypto);
  if (!globalThis.atob) defineGlobal('atob', (value) => Buffer.from(String(value), 'base64').toString('binary'));
  if (!globalThis.btoa) defineGlobal('btoa', (value) => Buffer.from(String(value), 'binary').toString('base64'));

  const locale = String(context.locale || 'en-US');
  const languages = Array.isArray(context.languages) && context.languages.length
    ? context.languages.map(String)
    : [locale, locale.split('-')[0]];
  const platform = String(context.platform || 'android');
  const userAgent = String(
    context.userAgent
      || `Nuvio-Health-Check/5.12 (${platform}; ${locale}; ReactNative-compatible)`,
  );

  defineGlobal('navigator', {
    userAgent,
    language: locale,
    languages,
    platform,
    product: 'ReactNative',
    onLine: true,
  });
  if (!globalThis.window) defineGlobal('window', globalThis);
  if (!globalThis.self) defineGlobal('self', globalThis);

  const storageSeed = context.storage && typeof context.storage === 'object'
    ? context.storage
    : {};
  if (!globalThis.localStorage) defineGlobal('localStorage', new MemoryStorage(storageSeed));
  if (!globalThis.sessionStorage) defineGlobal('sessionStorage', new MemoryStorage(storageSeed));

  if (!globalThis.location) {
    defineGlobal('location', {
      href: 'https://app.nuvio.local/',
      origin: 'https://app.nuvio.local',
      protocol: 'https:',
      hostname: 'app.nuvio.local',
      pathname: '/',
      search: '',
      hash: '',
    });
  }
  if (!globalThis.document) {
    defineGlobal('document', {
      cookie: '',
      location: globalThis.location,
      createElement: () => ({
        style: {},
        setAttribute() {},
        getAttribute() { return null; },
      }),
      querySelector() { return null; },
      querySelectorAll() { return []; },
    });
  }

  defineGlobal('__NUVIO_PROVIDER_CONTEXT__', Object.freeze({ ...context }));
  defineGlobal('__NUVIO_PROVIDER_SETTINGS__', Object.freeze({ ...(context.settings || {}) }));
  defineGlobal('Platform', { OS: platform, select: (choices) => choices?.[platform] ?? choices?.default });

  if (typeof globalThis.fetch === 'function') {
    const nativeFetch = globalThis.fetch.bind(globalThis);
    const maxFetches = Math.max(1, Number(context.networkLimits?.maxFetches || 30));
    const maxResponseBytes = Math.max(65536, Number(context.networkLimits?.maxResponseBytes || 5 * 1024 * 1024));
    let fetchCount = 0;
    let totalResponseBytes = 0;
    const maxTotalResponseBytes = Math.max(maxResponseBytes, Number(context.networkLimits?.maxTotalResponseBytes || 20 * 1024 * 1024));
    const contactedHosts = new Set();
    const maxDistinctHosts = Math.max(1, Number(context.networkLimits?.maxDistinctHosts || 20));
    defineGlobal('fetch', async (input, init = {}) => {
      fetchCount += 1;
      if (fetchCount > maxFetches) throw new Error(`provider fetch limit exceeded (${maxFetches})`);
      const inherited = (typeof Request !== 'undefined' && input instanceof Request) ? input.headers : undefined;
      const headers = new Headers(init.headers || inherited || {});
      if (context.injectAcceptLanguage !== false && !headers.has('Accept-Language')) headers.set('Accept-Language', languages.join(','));
      if (!headers.has('User-Agent')) headers.set('User-Agent', userAgent);
      const requestMeta = safeRequestMetadata(input, init);
      const host = requestMeta.host;
      if (host) contactedHosts.add(host);
      if (contactedHosts.size > maxDistinctHosts) throw new Error(`provider distinct-host limit exceeded (${maxDistinctHosts})`);
      const requestStage = inferRequestStage(requestMeta.path_pattern);
      const started = Date.now();
      try {
        let response;
        let synthetic = false;
        try {
          response = await guardedFetch(nativeFetch, input, { ...init, headers }, { maxRedirects: context.networkLimits?.maxRedirects || 5 });
        } catch (networkError) {
          response = syntheticTmdbResponse(input, context.fixtureMetadata || {});
          if (!response) throw networkError;
          synthetic = true;
        }
        if (!response.ok) {
          const fallback = syntheticTmdbResponse(input, context.fixtureMetadata || {});
          if (fallback) { response = fallback; synthetic = true; }
        }
        const declaredLength = Number(response.headers.get('content-length') || 0);
        if (declaredLength > maxResponseBytes) throw new Error(`response body exceeds limit (${declaredLength} bytes)`);
        networkObservations.push({ stage: requestStage, host, method: requestMeta.method, path_pattern: requestMeta.path_pattern, status: response.status, ok: response.ok, duration_ms: Date.now() - started, infrastructure: isInfrastructureHost(host), synthetic_fixture_fallback: synthetic });
        return wrapLimitedResponse(response, maxResponseBytes, (bytes) => {
          totalResponseBytes += bytes;
          if (totalResponseBytes > maxTotalResponseBytes) throw new Error(`provider cumulative response limit exceeded (${maxTotalResponseBytes} bytes)`);
        });
      } catch (error) {
        networkObservations.push({ stage: requestStage, host, method: requestMeta.method, path_pattern: requestMeta.path_pattern, status: null, ok: false, duration_ms: Date.now() - started, infrastructure: isInfrastructureHost(host), error: String(error?.message || error).slice(0, 180) });
        throw error;
      }
    });
  }
}


function suppressProviderLogs() {
  const noop = () => {};
  console.log = noop;
  console.info = noop;
  console.debug = noop;
  console.warn = noop;
  console.error = noop;
}

async function loadProvider(filePath) {
  installModuleRestrictions();
  try {
    return require(filePath);
  } catch (requireError) {
    try {
      return await import(pathToFileURL(filePath).href + `?health=${Date.now()}`);
    } catch (importError) {
      const error = new Error(`require failed: ${requireError.message}; import failed: ${importError.message}`);
      error.cause = importError;
      throw error;
    }
  }
}

function findGetStreams(moduleValue) {
  const candidates = [moduleValue, moduleValue && moduleValue.default, moduleValue && moduleValue.module];
  for (const candidate of candidates) {
    if (candidate && typeof candidate.getStreams === 'function') return candidate.getStreams;
    if (typeof candidate === 'function') return candidate;
  }
  return null;
}

function p2pReason(stream) {
  if (!stream || typeof stream !== 'object') return null;
  const url = typeof stream.url === 'string' ? stream.url.trim().toLowerCase() : '';
  if (/^(magnet|torrent|acestream|sop):/.test(url)) return 'disallowed P2P protocol';

  const disallowedKeys = /^(infohash|info_hash|magnet|torrent|torrenturl|p2p|peer|peers)$/i;
  for (const [key, value] of Object.entries(stream)) {
    if (disallowedKeys.test(key) && value != null && String(value).trim()) {
      return `disallowed P2P field: ${key}`;
    }
  }
  const hints = stream.behaviorHints;
  if (hints && typeof hints === 'object') {
    const text = JSON.stringify(hints).toLowerCase();
    if (/infohash|magnet|torrent|p2p|peer/.test(text)) return 'disallowed P2P behavior hint';
  }
  return null;
}

function sanitizeHeaders(headers) {
  if (!headers || typeof headers !== 'object' || Array.isArray(headers)) return {};
  return Object.fromEntries(
    Object.entries(headers)
      .filter(([key, value]) => typeof key === 'string' && value != null)
      .slice(0, 30)
      .map(([key, value]) => [key, String(value).slice(0, 2000)]),
  );
}

function sanitizeStream(stream) {
  if (!stream || typeof stream !== 'object') return { stream: null, disallowed: null };
  const disallowed = p2pReason(stream);
  if (disallowed) return { stream: null, disallowed };

  const url = typeof stream.url === 'string' ? stream.url.trim() : '';
  if (!url) return { stream: null, disallowed: null };
  return {
    disallowed: null,
    stream: {
      name: typeof stream.name === 'string' ? stream.name.slice(0, 200) : null,
      title: typeof stream.title === 'string' ? stream.title.slice(0, 500) : null,
      url,
      quality: stream.quality == null ? null : String(stream.quality).slice(0, 100),
      size: stream.size == null ? null : String(stream.size).slice(0, 100),
      language: stream.language == null ? null : String(stream.language).slice(0, 100),
      headers: sanitizeHeaders(stream.headers),
      subtitles: Array.isArray(stream.subtitles)
        ? stream.subtitles.slice(0, 30).map((subtitle) => ({
            language: subtitle && (subtitle.language || subtitle.lang || subtitle.label || subtitle.name),
            url: subtitle && (subtitle.url || subtitle.file),
            headers: sanitizeHeaders(subtitle && subtitle.headers),
          }))
        : [],
      audioTracks: Array.isArray(stream.audioTracks)
        ? stream.audioTracks.slice(0, 30).map((track) => ({
            language: track && (track.language || track.lang || track.label || track.name),
          }))
        : [],
    },
  };
}


function scalar(value) {
  return ['string', 'number', 'boolean'].includes(typeof value) ? value : undefined;
}

function settingsProfiles(moduleValue, sourceText, context) {
  const profiles = [{ name: 'empty', settings: {} }];
  const defaults = {};
  const alternatives = [];
  const seen = new Set();

  function visit(value, depth = 0) {
    if (!value || depth > 5 || seen.has(value)) return;
    if (typeof value === 'object' || typeof value === 'function') seen.add(value);
    if (Array.isArray(value)) {
      for (const item of value.slice(0, 100)) visit(item, depth + 1);
      return;
    }
    if (typeof value !== 'object' && typeof value !== 'function') return;
    const key = value.key || value.id || value.name || value.settingKey;
    const def = value.defaultValue ?? value.default ?? value.value;
    if (typeof key === 'string' && scalar(def) !== undefined) defaults[key] = def;
    const options = value.options || value.values || value.choices;
    if (typeof key === 'string' && Array.isArray(options)) {
      const vals = options.map((x) => scalar(x?.value ?? x?.id ?? x)).filter((x) => x !== undefined).slice(0, 6);
      if (vals.length) alternatives.push([key, vals]);
    }
    for (const prop of ['settings','settingsSchema','schema','config','configuration','preferences','fields','items','defaultSettings']) {
      if (value[prop]) visit(value[prop], depth + 1);
    }
    if (depth < 2) {
      for (const [k,v] of Object.entries(value).slice(0, 100)) {
        if (/setting|config|schema|preference/i.test(k)) visit(v, depth + 1);
      }
    }
  }
  visit(moduleValue);
  visit(moduleValue?.default);

  // Conservative fallback for minified providers: extract literal key/default pairs.
  const pairRe = /(?:key|id|name|settingKey)\s*:\s*['\"]([^'\"]{1,80})['\"][\s\S]{0,240}?(?:defaultValue|default|value)\s*:\s*(true|false|-?\d+(?:\.\d+)?|['\"][^'\"]{0,160}['\"])/g;
  let match;
  while ((match = pairRe.exec(sourceText))) {
    let val = match[2];
    if (/^['\"]/.test(val)) val = val.slice(1,-1);
    else if (val === 'true' || val === 'false') val = val === 'true';
    else val = Number(val);
    defaults[match[1]] ??= val;
  }

  const contextual = context.settings && typeof context.settings === 'object' ? context.settings : {};
  const base = { ...defaults, ...contextual };
  if (Object.keys(base).length) profiles.push({ name: 'defaults', settings: base });

  // Some providers do not query their server until title/year metadata is
  // available in settings. Exercise that path during every deep check instead
  // of treating an empty-settings result as representative.
  const fixture = context.fixtureMetadata && typeof context.fixtureMetadata === 'object'
    ? context.fixtureMetadata
    : {};
  const fixtureSettings = {};
  for (const key of ['title', 'year', 'label', 'category', 'mediaType']) {
    const value = scalar(fixture[key]);
    if (value !== undefined && value !== '') fixtureSettings[key] = value;
  }
  if (Object.keys(fixtureSettings).length) {
    profiles.push({ name: 'fixture_metadata', settings: { ...base, ...fixtureSettings } });
  }

  for (const [key, vals] of alternatives.slice(0, 12)) {
    for (const val of vals.slice(0, 4)) profiles.push({ name: `option:${key}=${String(val)}`, settings: { ...base, [key]: val } });
  }
  const unique = [];
  const fingerprints = new Set();
  for (const profile of profiles.slice(0, 30)) {
    const fp = JSON.stringify(profile.settings, Object.keys(profile.settings).sort());
    if (!fingerprints.has(fp)) { fingerprints.add(fp); unique.push(profile); }
  }
  return unique;
}

function installSettingsAccessors(settings) {
  defineGlobal('__NUVIO_PROVIDER_SETTINGS__', Object.freeze({ ...settings }));
  defineGlobal('getProviderSettings', async () => ({ ...settings }));
  defineGlobal('getSettings', async () => ({ ...settings }));
  defineGlobal('providerSettings', { ...settings });
  defineGlobal('AsyncStorage', {
    async getItem(key) { const v = settings[key]; return v == null ? null : (typeof v === 'string' ? v : JSON.stringify(v)); },
    async setItem() {}, async removeItem() {}, async clear() {},
    async multiGet(keys) { return keys.map((k) => [k, settings[k] == null ? null : JSON.stringify(settings[k])]); },
  });
  for (const [key, value] of Object.entries(settings)) {
    try { globalThis.localStorage?.setItem(key, typeof value === 'string' ? value : JSON.stringify(value)); } catch {}
  }
}

async function invokeProvider(getStreams, fixture, settings) {
  installSettingsAccessors(settings);
  const positional = [String(fixture.tmdbId), fixture.mediaType, fixture.season ?? null, fixture.episode ?? null];
  const attempts = [
    () => getStreams(...positional, settings),
    () => getStreams({ tmdbId: String(fixture.tmdbId), mediaType: fixture.mediaType, type: fixture.mediaType, season: fixture.season ?? null, episode: fixture.episode ?? null, settings }),
    () => getStreams(...positional),
  ];
  let lastError;
  for (const attempt of attempts) {
    try {
      const value = await attempt();
      if (Array.isArray(value) && value.length) return value;
      if (Array.isArray(value) && !lastError) lastError = null;
    } catch (error) { lastError = error; }
  }
  if (lastError) throw lastError;
  return [];
}

async function main() {
  const [, , providerArg, fixtureArg, contextArg] = process.argv;
  if (!providerArg || !fixtureArg) throw new Error('provider path and fixture JSON are required');

  const context = contextArg ? JSON.parse(contextArg) : {};
  installPolyfills(context);
  suppressProviderLogs();

  const providerPath = path.resolve(providerArg);
  const fixture = JSON.parse(fixtureArg);
  const startedAt = Date.now();
  const loaded = await loadProvider(providerPath);
  const getStreams = findGetStreams(loaded);
  if (!getStreams) throw new Error('module does not export getStreams');

  const sourceText = fs.readFileSync(providerPath, 'utf8');
  const profiles = settingsProfiles(loaded, sourceText, context);
  let value = [];
  let selectedProfile = profiles[0];
  const profileResults = [];
  for (const profile of profiles) {
    try {
      const candidateValue = await invokeProvider(getStreams, fixture, profile.settings);
      profileResults.push({ name: profile.name, setting_keys: Object.keys(profile.settings), stream_count: Array.isArray(candidateValue) ? candidateValue.length : 0 });
      if (Array.isArray(candidateValue) && candidateValue.length > value.length) { value = candidateValue; selectedProfile = profile; }
      if (value.length > 0) break;
    } catch (error) {
      profileResults.push({ name: profile.name, setting_keys: Object.keys(profile.settings), stream_count: 0, error: String(error.message || error).slice(0, 300) });
    }
  }

  const streams = [];
  const disallowedReasons = [];
  if (Array.isArray(value)) {
    for (const item of value.slice(0, 120)) {
      const sanitized = sanitizeStream(item);
      if (sanitized.disallowed) disallowedReasons.push(sanitized.disallowed);
      if (sanitized.stream) streams.push(sanitized.stream);
      if (streams.length >= 100) break;
    }
  }

  emit({
    ok: true,
    duration_ms: Date.now() - startedAt,
    stream_count: streams.length,
    disallowed_stream_count: disallowedReasons.length,
    disallowed_reasons: [...new Set(disallowedReasons)].slice(0, 10),
    environment_context: {
      locale: context.locale || 'en-US',
      platform: context.platform || 'android',
      browser_shims: true,
      settings_profiles_tested: profileResults.length,
      selected_settings_profile: selectedProfile.name,
      selected_setting_keys: Object.keys(selectedProfile.settings),
    },
    settings_diagnostics: profileResults,
    network_observations: networkObservations.slice(0, 80),
    network_limits: context.networkLimits || null,
    // A server is accessible when it answered at the HTTP layer, even with a
    // non-2xx status. 401/403/404/429/5xx still prove DNS, TLS and the remote
    // service are reachable; only DNS/connection/timeout failures do not.
    provider_server_accessible: networkObservations.some((item) =>
      !item.infrastructure && Number.isInteger(item.status) && item.status >= 100 && item.status <= 599
    ),
    provider_server_successful_response: networkObservations.some((item) => !item.infrastructure && item.ok),
    provider_server_hosts: [...new Set(networkObservations.filter((item) => !item.infrastructure && item.host).map((item) => item.host))].sort(),
    provider_server_http_statuses: [...new Set(networkObservations.filter((item) => !item.infrastructure && Number.isInteger(item.status)).map((item) => item.status))].sort((a, b) => a - b),
    streams,
  });
}

async function runFixtureFallbackSelfTest() {
  const fixture = { tmdbId: '577922', mediaType: 'movie', title: 'Tenet', year: 2020 };
  const details = syntheticTmdbResponse('https://api.themoviedb.org/3/movie/577922?api_key=test', fixture);
  const alternatives = syntheticTmdbResponse('https://api.themoviedb.org/3/movie/577922/alternative_titles?api_key=test', fixture);
  const translations = syntheticTmdbResponse('https://api.themoviedb.org/3/movie/577922/translations?api_key=test', fixture);
  if (!details || !alternatives || !translations) throw new Error('fixture fallback did not match TMDb routes');
  const detailsJson = await details.json();
  const alternativesJson = await alternatives.json();
  const translationsJson = await translations.json();
  if (detailsJson.title !== 'Tenet' || detailsJson.release_date !== '2020-01-01') throw new Error('invalid fixture details fallback');
  if (!Array.isArray(alternativesJson.titles) || alternativesJson.titles[0]?.title !== 'Tenet') throw new Error('invalid alternatives fallback');
  if (!Array.isArray(translationsJson.translations) || translationsJson.translations[0]?.data?.title !== 'Tenet') throw new Error('invalid translations fallback');
  if (syntheticTmdbResponse('https://example.com/3/movie/577922', fixture) !== null) throw new Error('fallback matched a non-TMDb host');
  process.stdout.write('provider fixture fallback tests passed\n');
}

const entry = process.argv[2] === '--self-test-fixture-fallback'
  ? runFixtureFallbackSelfTest()
  : main();

entry
  .catch((error) => {
    emit({
      ok: false,
      error: error && error.message ? String(error.message).slice(0, 2000) : String(error),
      stream_count: 0,
      disallowed_stream_count: 0,
      network_observations: networkObservations.slice(0, 80),
      provider_server_accessible: networkObservations.some((item) => !item.infrastructure && Number.isInteger(item.status)),
      provider_server_successful_response: networkObservations.some((item) => !item.infrastructure && item.ok),
      provider_server_hosts: [...new Set(networkObservations.filter((item) => !item.infrastructure && item.host).map((item) => item.host))].sort(),
      provider_server_http_statuses: [...new Set(networkObservations.filter((item) => !item.infrastructure && Number.isInteger(item.status)).map((item) => item.status))].sort((a, b) => a - b),
      streams: [],
    });
  })
  .finally(() => {
    setTimeout(() => process.exit(0), 10).unref();
  });
