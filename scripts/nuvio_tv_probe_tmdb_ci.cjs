#!/usr/bin/env node
'use strict';

// CI-only bridge for the Node-compatible Nuvio probe. The TMDB credential is
// exposed only during provider module initialization so Core can capture it in
// its closure. The bridge then removes the visible credential before getStreams
// runs. Providers request metadata dynamically through Core getTmdbData(); no
// metadata context is pre-hydrated by this harness.
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');

const key = String(process.env.TMDB_API_KEY || '').trim();
const token = String(process.env.TMDB_ACCESS_TOKEN || '').trim();
if (!key && !token) {
  console.error('FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=missing_tmdb_credential');
  process.exit(78);
}

function expose(name, value, writable = false) {
  if (value == null || value === '') return;
  try {
    Object.defineProperty(globalThis, name, {
      value,
      configurable: true,
      writable,
      enumerable: false,
    });
  } catch {
    globalThis[name] = value;
  }
}

function clearVisibleCredential() {
  for (const name of ['TMDB_API_KEY', 'TMDB_ACCESS_TOKEN']) {
    try { delete globalThis[name]; } catch {}
    try {
      if (Object.prototype.hasOwnProperty.call(globalThis, name)) globalThis[name] = undefined;
    } catch {}
  }
}

function safeUrl(raw) {
  try {
    const url = new URL(String(raw || ''));
    for (const name of [...url.searchParams.keys()]) {
      if (/api[_-]?key|token|auth|signature|sig|secret/i.test(name)) url.searchParams.set(name, '<redacted>');
    }
    return url.toString();
  } catch {
    return String(raw || '').slice(0, 500);
  }
}

function providerModel(providerPath) {
  try {
    const text = fs.readFileSync(providerPath, 'utf8');
    const marker = 'const NIAKVIO_PROVIDER_MODEL = Object.freeze(';
    const at = text.indexOf(marker);
    if (at < 0) return null;
    const start = at + marker.length;
    let depth = 0, quote = '', escaped = false;
    for (let i = start; i < text.length; i += 1) {
      const ch = text[i];
      if (quote) {
        if (escaped) escaped = false;
        else if (ch === '\\') escaped = true;
        else if (ch === quote) quote = '';
        continue;
      }
      if (ch === '"') { quote = ch; continue; }
      if (ch === '{' || ch === '[') depth += 1;
      else if (ch === '}' || ch === ']') depth -= 1;
      else if (ch === ')' && depth === 0) return JSON.parse(text.slice(start, i));
    }
  } catch {}
  return null;
}

function routeKind(route) {
  const value = String(route || '').toLowerCase();
  if (/search|recherche|[?&](?:s|q|query|keyword|story)=/.test(value)) return 'search';
  if (/player|watch|embed|play/.test(value)) return 'player';
  if (/api|stream|source/.test(value)) return 'api';
  if (/detail|movie|film|serie|series|anime|catalogue|title|episode|season|saison/.test(value)) return 'detail';
  return 'unknown';
}

function sanitizeProviderValueTraceRow(raw) {
  if (!raw || typeof raw !== 'object') return null;
  const index = Number(raw.stepIndex);
  return {
    stage: String(raw.stage || '').slice(0, 64),
    lane: String(raw.lane || '').slice(0, 32),
    provider_id: String(raw.providerId || '').slice(0, 160),
    step_index: Number.isInteger(index) && index >= -1 && index <= 7 ? index : null,
    route: String(raw.route || '').slice(0, 240),
  };
}

function providerValueTrace() {
  return sanitizeProviderValueTraceRow(globalThis.__nuvioProviderValueTraceV18);
}

function providerValueTraceHistory() {
  const rows = Array.isArray(globalThis.__nuvioProviderValueTraceHistoryV21)
    ? globalThis.__nuvioProviderValueTraceHistoryV21 : [];
  return rows.slice(-48).map(sanitizeProviderValueTraceRow).filter(Boolean);
}

function debugStage(model, fixture, fetchTrace, result) {
  const type = String(fixture.mediaType || fixture.type || 'movie').toLowerCase();
  const supported = Array.isArray(model?.supportedTypes) ? model.supportedTypes.map((x) => String(x).toLowerCase()) : [];
  const typeAllowed = !supported.length || supported.includes(type) || (type === 'tv' && supported.includes('anime'));
  if (!typeAllowed) return 'gate_type_capability';
  const routes = Array.isArray(model?.routes) ? model.routes : [];
  const runtimePlan = !!model?.apiRecipe || routes.some((r) => ['search', 'detail', 'player', 'api'].includes(routeKind(r)));
  if (!runtimePlan) return 'gate_runtime_plan_missing';
  if (Number(result?.raw_stream_count || 0) > 0) return 'provider_returned_streams';
  if (!fetchTrace.length && (!model?.sourceRuntimeFamily || model.sourceRuntimeFamily === 'unknown')) return 'gate_source_family_unknown';
  if (!fetchTrace.length) return 'provider_zero_before_network';
  const providerFetches = fetchTrace.filter((row) => !/api\.themoviedb\.org/i.test(row.url));
  if (!providerFetches.length) return 'provider_zero_before_provider_network';
  const meaningful = providerFetches.filter((row) => /^https?:\/\//i.test(String(row?.url || '')));
  if (!meaningful.length) return 'provider_network_zero_result';
  const terminal = meaningful[meaningful.length - 1];
  if (terminal?.challenge) return 'provider_waf_challenge';
  if (terminal?.error) return 'provider_network_exception';
  if (Number(terminal?.status || 0) >= 400) return 'provider_network_http_error';
  // A successful-looking terminal request must not erase a challenge reached one
  // step earlier (for example a 200 HTML Turnstile page followed by a harmless
  // asset/fallback fetch). Terminal hard failures still keep causal precedence.
  if (meaningful.some((row) => row?.challenge)) return 'provider_waf_challenge';
  return 'provider_network_zero_result';
}

const providerPath = path.resolve(String(process.argv[2] || ''));
if (!providerPath) {
  console.error('FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=missing_provider_path');
  process.exit(78);
}
const model = providerModel(providerPath);
let fixture = {};
try { fixture = JSON.parse(process.argv[3] || '{}'); } catch { fixture = {}; }

// Trace every network call before any provider code executes. TMDB query secrets
// are redacted from evidence while provider request/response URLs and methods
// remain visible. Bodies, cookies and request headers are never persisted.
const originalFetch = globalThis.fetch;
const trace = [];

function safeShapeKey(value) {
  const key = String(value || '').slice(0, 48);
  return /^[A-Za-z_][A-Za-z0-9_.:-]{0,47}$/.test(key) ? key : '';
}
function jsonShape(value) {
  const top = Array.isArray(value) ? 'array' : (value === null ? 'null' : typeof value);
  const out = { kind: 'json', top };
  const keys = obj => Object.keys(obj || {}).map(safeShapeKey).filter(Boolean).slice(0, 16);
  if (Array.isArray(value)) {
    out.lengthBucket = value.length === 0 ? '0' : value.length === 1 ? '1' : value.length <= 10 ? '2-10' : '11+';
    const first = value.find(item => item && typeof item === 'object' && !Array.isArray(item));
    if (first) out.itemKeys = keys(first);
    return out;
  }
  if (!value || typeof value !== 'object') return out;
  out.keys = keys(value);
  for (const name of ['data','results','result','episode','shows','sources','links']) {
    const child = value[name];
    if (Array.isArray(child)) {
      out[name + 'Type'] = 'array';
      const first = child.find(item => item && typeof item === 'object' && !Array.isArray(item));
      if (first) out[name + 'ItemKeys'] = keys(first);
    } else if (child && typeof child === 'object') {
      out[name + 'Type'] = 'object';
      out[name + 'Keys'] = keys(child);
    }
  }
  return out;
}
function structuralTokens(raw, attribute, limit) {
  const counts = new Map();
  const re = attribute === 'class'
    ? /\bclass\s*=\s*["']([^"']{1,512})["']/gi
    : /\bid\s*=\s*["']([^"']{1,512})["']/gi;
  let match;
  while ((match = re.exec(raw)) !== null && counts.size < 256) {
    const values = attribute === 'class' ? String(match[1] || '').split(/\\s+/) : [String(match[1] || '')];
    for (const value of values) {
      const token = String(value || '').trim();
      if (!/^[A-Za-z][A-Za-z0-9_-]{1,47}$/.test(token)) continue;
      counts.set(token, (counts.get(token) || 0) + 1);
    }
  }
  return [...counts.entries()]
    .sort((a, b) => (b[1] - a[1]) || a[0].localeCompare(b[0]))
    .slice(0, limit)
    .map(([token]) => token);
}
function structuralClassFacts(raw, tokens, limit) {
  const out = [];
  const source = String(raw || '');
  const allowSignals = [
    ['movie', /\bmovies?\b/i],
    ['series', /\bseries\b/i],
    ['season', /\bseason\b/i],
    ['episode', /\bepisode\b/i],
    ['download', /\bdownload\b/i],
    ['4k', /\b(?:4k|2160p|uhd)\b/i],
    ['1080p', /\b1080p\b/i],
    ['720p', /\b720p\b/i],
    ['year', /\b(?:19|20)\d{2}\b/],
  ];
  for (const token of (tokens || []).slice(0, Math.max(0, limit || 0))) {
    if (!/^[A-Za-z][A-Za-z0-9_-]{1,47}$/.test(String(token || ''))) continue;
    const esc = String(token).replace(/[-/\\^$*+?.()|[\]{}]/g, '\\    const esc = String(token).replace(/[-/\\^$*+?.()|[\]{}]/g, '\\function textShape(contentType, body) {
');
');
    const openRe = new RegExp('<([a-z0-9]+)\\b([^>]*\\bclass\\s*=\\s*["\'][^"\']*\\b' + esc + '\\b[^"\']*["\'][^>]*)>', 'gi');
    let match, count = 0, selfHref = 0, nestedAnchors = 0;
    const tags = new Set(), signals = new Set();
    while ((match = openRe.exec(source)) !== null && count < 12) {
      count += 1;
      tags.add(String(match[1] || '').toLowerCase());
      if (/\bhref\s*=/i.test(String(match[2] || ''))) selfHref += 1;
      const start = match.index;
      const stop = Math.min(source.length, start + 4096);
      const sample = source.slice(start, stop);
      nestedAnchors += Math.min(12, (sample.match(/<a\b/gi) || []).length);
      const text = sample.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 2048);
      for (const [name, re] of allowSignals) if (re.test(text)) signals.add(name);
    }
    if (!count) continue;
    out.push({
      token: String(token),
      count,
      tags: [...tags].slice(0, 4),
      selfHref,
      nestedAnchors: Math.min(24, nestedAnchors),
      signals: [...signals],
    });
  }
  return out;
}

function textShape(contentType, body) {
  const raw = String(body || '').slice(0, 65536);
  const low = raw.toLowerCase();
  const count = re => Math.min(99, (raw.match(re) || []).length);
  if (/text\/html/i.test(contentType)) {
    const classTokens = structuralTokens(raw,'class',16);
    return {kind:'html',sampleBytes:raw.length,forms:count(/<form\b/gi),iframes:count(/<iframe\b/gi),videos:count(/<video\b/gi),sources:count(/<source\b/gi),scripts:count(/<script\b/gi),anchors:count(/<a\b/gi),classTokens,idTokens:structuralTokens(raw,'id',12),classFacts:structuralClassFacts(raw,classTokens,8),markers:[
      /__next_data__/i.test(raw)?'next-data':'',
      /application\/ld\+json/i.test(raw)?'json-ld':'',
      /(?:player|embed)/i.test(low)?'player':'',
      /download/i.test(low)?'download':'',
      /episode/i.test(low)?'episode':'',
      /\.m3u8(?:[?"'<>\s]|$)/i.test(raw)?'hls-literal':'',
      /\.mp4(?:[?"'<>\s]|$)/i.test(raw)?'mp4-literal':''
    ].filter(Boolean)};
  }
  if (/(?:application|text)\/(?:javascript|x-javascript|ecmascript)/i.test(contentType)) {
    return {kind:'javascript',sampleBytes:raw.length,functions:count(/\bfunction\b/g),fetchCalls:count(/\bfetch\s*\(/g),markers:[
      /\bturnstile\b/i.test(low)?'turnstile':'',
      /(?:iframe|embed)/i.test(low)?'embed':'',
      /\.m3u8(?:[?"'<>\s]|$)/i.test(raw)?'hls-literal':'',
      /\.mp4(?:[?"'<>\s]|$)/i.test(raw)?'mp4-literal':''
    ].filter(Boolean)};
  }
  return null;
}
if (typeof originalFetch === 'function') {
  globalThis.fetch = async function tracedFetch(input, init) {
    const started = Date.now();
    const url = safeUrl(typeof input === 'string' || input instanceof URL ? input : input?.url);
    const method = String(init?.method || (input && typeof input === 'object' && input.method) || 'GET').toUpperCase().slice(0, 12);
    try {
      const response = await originalFetch.call(this, input, init);
      let contentType = '';
      let challenge = '';
      let responseShape = null;
      const status = Number(response?.status || 0);
      try { contentType = String(response?.headers?.get?.('content-type') || '').split(';')[0].slice(0, 96); } catch {}
      // Interactive anti-bot pages can legitimately answer HTTP 200. Inspect only
      // bounded HTML/JS clones; response bodies remain ephemeral and are never stored.
      if ((status >= 200 && status < 300) || [403, 429, 503].includes(status)) {
        let server = '', cfRay = '', cfMitigated = '', body = '';
        try {
          server = String(response?.headers?.get?.('server') || '').toLowerCase();
          cfRay = String(response?.headers?.get?.('cf-ray') || '');
          cfMitigated = String(response?.headers?.get?.('cf-mitigated') || '').toLowerCase();
        } catch {}
        const htmlBody = /text\/html/i.test(contentType);
        const scriptBody = /(?:application|text)\/(?:javascript|x-javascript|ecmascript)/i.test(contentType);
        if (htmlBody || scriptBody) {
          try { body = String(await response.clone().text()).slice(0, 65536); } catch {}
          responseShape = textShape(contentType, body);
        } else if (/application\/json/i.test(contentType)) {
          try {
            const rawJson = String(await response.clone().text()).slice(0, 131072);
            responseShape = jsonShape(JSON.parse(rawJson));
          } catch {
            responseShape = { kind: 'json', top: 'unparsed' };
          }
        }
        const bodyLower = body.toLowerCase();
        // Explicit Turnstile wiring in a provider-loaded JS asset is strong
        // evidence of the same interactive gate even when the HTML itself is 200
        // and marker-free. Generic challenge prose remains HTML-only.
        const turnstileMarker = /cf-turnstile-response|challenges\.cloudflare\.com\/turnstile|\bturnstile\b/.test(bodyLower);
        const marker = turnstileMarker || (htmlBody && /just a moment|checking your browser|verify you are human|attention required|captcha|challenge-platform|cf-browser-verification|security check/.test(bodyLower));
        if (cfMitigated === 'challenge' || marker) {
          challenge = (turnstileMarker || cfRay || server.includes('cloudflare') || cfMitigated === 'challenge') ? 'cloudflare' : 'generic';
        }
      }
      trace.push({
        url,
        response_url: safeUrl(response?.url || url),
        method,
        status,
        content_type: contentType,
        challenge,
        response_shape: responseShape,
        duration_ms: Date.now() - started,
      });
      return response;
    } catch (error) {
      trace.push({ url, response_url: '', method, status: 0, duration_ms: Date.now() - started, error: String(error?.name || 'Error') });
      throw error;
    }
  };
}

// Core captures these during provider module initialization. A loader hook
// removes both globals immediately after the generated provider module returns.
expose('TMDB_API_KEY', key);
expose('TMDB_ACCESS_TOKEN', token);
const nativeLoad = Module._load;
let providerLoaded = false;
Module._load = function niakvioCoreCredentialBootstrap(request, parent, isMain) {
  let resolved = '';
  try { resolved = path.resolve(Module._resolveFilename(request, parent, isMain)); } catch {}
  const value = nativeLoad.apply(this, arguments);
  if (!providerLoaded && resolved === providerPath) {
    providerLoaded = true;
    clearVisibleCredential();
    Module._load = nativeLoad;
    const coreReady = typeof globalThis.__nuvioCoreGetTmdbDataV1 === 'function';
    console.error(
      `FIELD_TMDB_PROBE_CONTEXT state=${coreReady ? 'core_ready' : 'infra_error'} ` +
      `credential_visible=false metadata_hydrated=false dynamic=true core_capability=${coreReady}`
    );
  }
  return value;
};

const originalWrite = process.stdout.write.bind(process.stdout);
process.stdout.write = function debugWrite(chunk, encoding, callback) {
  let text = String(chunk ?? '');
  const trimmed = text.trim();
  if (trimmed.startsWith('{')) {
    try {
      const value = JSON.parse(trimmed);
      if (Object.prototype.hasOwnProperty.call(value, 'playable_stream_count')) {
        const modelSummary = model ? {
          strategy: model.strategy || null,
          source_runtime_family: model.sourceRuntimeFamily || 'unknown',
          reconstruction_state: model.reconstructionState || null,
          identity_mode: model.identityInput?.mode || null,
          requires_tmdb_before_run: model.identityInput?.requiresTmdbBeforeRun === true,
          supported_types: model.supportedTypes || [],
          route_count: Array.isArray(model.routes) ? model.routes.length : 0,
          route_kinds: [...new Set((model.routes || []).map(routeKind))],
          has_api_recipe: !!model.apiRecipe,
          official_site: model.officialSite || null,
          official_hub: model.officialHub || null,
          official_api: model.officialApi || null,
        } : null;
        value.debug = {
          stage: debugStage(model, fixture, trace, value),
          model: modelSummary,
          tmdb_core_capability: typeof globalThis.__nuvioCoreGetTmdbDataV1 === 'function',
          tmdb_credential_visible_after_load: !!(globalThis.TMDB_API_KEY || globalThis.TMDB_ACCESS_TOKEN),
          tmdb_context_prehydrated: false,
          provider_value_trace_v18: providerValueTrace(),
          provider_value_trace_history_v21: providerValueTraceHistory(),
          provider_runtime_dispatch_error_v1: (() => {
            try {
              const row = globalThis.__niakvioProviderRuntimeDispatchErrorV1;
              if (!row || typeof row !== 'object') return null;
              return {
                provider: String(row.provider || '').slice(0, 80),
                name: String(row.name || 'Error').slice(0, 80),
                message: String(row.message || '').slice(0, 400),
              };
            } catch { return null; }
          })(),
          fetch_count: trace.length,
          provider_fetch_count: trace.filter((row) => !/api\.themoviedb\.org/i.test(row.url)).length,
          fetches: trace.slice(0, 40),
        };
        text = JSON.stringify(value) + '\n';
      }
    } catch {}
  }
  return originalWrite(text, encoding, callback);
};

try {
  require('./nuvio_tv_probe_v2.cjs');
} catch (error) {
  clearVisibleCredential();
  Module._load = nativeLoad;
  console.error(`FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=bridge_failure error=${error?.name || 'Error'}`);
  process.exit(78);
}
