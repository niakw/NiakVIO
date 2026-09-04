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
  if (providerFetches.some((row) => Number(row.status) >= 400)) return 'provider_network_http_error';
  if (providerFetches.some((row) => row.error)) return 'provider_network_exception';
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
// are redacted from evidence while provider URLs/statuses remain visible.
const originalFetch = globalThis.fetch;
const trace = [];
if (typeof originalFetch === 'function') {
  globalThis.fetch = async function tracedFetch(input, init) {
    const started = Date.now();
    const url = safeUrl(typeof input === 'string' || input instanceof URL ? input : input?.url);
    try {
      const response = await originalFetch.call(this, input, init);
      trace.push({ url, status: Number(response?.status || 0), duration_ms: Date.now() - started });
      return response;
    } catch (error) {
      trace.push({ url, status: 0, duration_ms: Date.now() - started, error: String(error?.name || 'Error') });
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
          fetch_count: trace.length,
          provider_fetch_count: trace.filter((row) => !/api\.themoviedb\.org/i.test(row.url)).length,
          fetches: trace.slice(0, 30),
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
