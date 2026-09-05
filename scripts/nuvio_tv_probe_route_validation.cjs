#!/usr/bin/env node
'use strict';

// Live route-evidence wrapper around the canonical TMDB-aware Nuvio probe.
// It records the request that was actually issued while Provider.getStreams()
// traverses the provider contract: method, header names, body field names, final
// URL, HTTP status and content type. The canonical probe subsequently performs
// media/playback verification; those network calls must NOT become Provider
// route/DATA evidence or distort route coverage.
// Sensitive values are never emitted.

function safeUrl(raw) {
  try {
    const url = new URL(String(raw || ''));
    for (const name of [...url.searchParams.keys()]) {
      if (/api[_-]?key|token|auth|signature|sig|secret|password/i.test(name)) {
        url.searchParams.set(name, '<redacted>');
      }
    }
    return url.toString();
  } catch {
    return String(raw || '').slice(0, 700);
  }
}

function headerNames(input, init) {
  const names = new Set();
  function collect(headers) {
    if (!headers) return;
    try {
      if (typeof headers.forEach === 'function') {
        headers.forEach((_value, key) => names.add(String(key).toLowerCase()));
        return;
      }
    } catch {}
    if (Array.isArray(headers)) {
      for (const row of headers) {
        if (Array.isArray(row) && row.length) names.add(String(row[0]).toLowerCase());
      }
      return;
    }
    if (typeof headers === 'object') {
      for (const key of Object.keys(headers)) names.add(String(key).toLowerCase());
    }
  }
  try { collect(input && typeof input === 'object' ? input.headers : null); } catch {}
  try { collect(init?.headers); } catch {}
  return [...names].sort().slice(0, 40);
}

function bodyShape(body) {
  if (body == null) return { kind: 'none', fields: [] };
  try {
    if (typeof URLSearchParams !== 'undefined' && body instanceof URLSearchParams) {
      return { kind: 'form', fields: [...new Set([...body.keys()].map(String))].sort().slice(0, 40) };
    }
  } catch {}
  try {
    if (typeof FormData !== 'undefined' && body instanceof FormData) {
      return { kind: 'multipart', fields: [...new Set([...body.keys()].map(String))].sort().slice(0, 40) };
    }
  } catch {}
  if (typeof body !== 'string') return { kind: typeof body, fields: [] };
  const text = body.trim();
  if (!text) return { kind: 'empty', fields: [] };
  try {
    const value = JSON.parse(text);
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return { kind: 'json', fields: Object.keys(value).sort().slice(0, 40) };
    }
  } catch {}
  if (text.includes('=')) {
    try {
      const params = new URLSearchParams(text);
      const fields = [...new Set([...params.keys()].map(String))].sort().slice(0, 40);
      if (fields.length) return { kind: 'form', fields };
    } catch {}
  }
  return { kind: 'text', fields: [] };
}

function requestPhase() {
  // nuvio_tv_probe_v2.cjs calls inspectStream()/inspectHlsChild() only AFTER
  // Provider.getStreams() returned. Those calls validate the returned media,
  // they are not part of the provider's route plan. Keep the classification
  // local to our own canonical probe filename to avoid accidentally classifying
  // a provider helper with a similar function name.
  try {
    const stack = String(new Error().stack || '');
    if (/\bat (?:inspectStream|inspectHlsChild)\b[^\n]*nuvio_tv_probe_v2\.cjs/i.test(stack)) {
      return 'playback';
    }
  } catch {}
  return 'provider';
}

const originalFetch = globalThis.fetch;
const routeTrace = [];
let playbackRequestCount = 0;
if (typeof originalFetch === 'function') {
  globalThis.fetch = async function niakvioRouteEvidenceFetch(input, init) {
    const started = Date.now();
    const phase = requestPhase();
    const requestUrl = safeUrl(
      typeof input === 'string' || input instanceof URL ? input : input?.url
    );
    const method = String(init?.method || input?.method || 'GET').toUpperCase();
    const shape = bodyShape(init?.body);
    const evidence = {
      url: requestUrl,
      method,
      network_phase: phase,
      header_names: headerNames(input, init),
      body_kind: shape.kind,
      body_fields: shape.fields,
      status: 0,
      final_url: requestUrl,
      content_type: null,
      duration_ms: 0,
    };
    try {
      const response = await originalFetch.call(this, input, init);
      evidence.status = Number(response?.status || 0);
      evidence.final_url = safeUrl(response?.url || requestUrl);
      try { evidence.content_type = response?.headers?.get?.('content-type') || null; } catch {}
      evidence.duration_ms = Date.now() - started;
      if (phase === 'playback') playbackRequestCount += 1;
      else routeTrace.push(evidence);
      return response;
    } catch (error) {
      evidence.error = String(error?.name || 'Error');
      evidence.duration_ms = Date.now() - started;
      if (phase === 'playback') playbackRequestCount += 1;
      else routeTrace.push(evidence);
      throw error;
    }
  };
}

// The canonical bridge enriches the provider result first, then calls this outer
// writer. Add the higher-fidelity provider-route evidence to the same final JSON
// object. Playback proof remains in the canonical media/identity result.
const nativeWrite = process.stdout.write.bind(process.stdout);
process.stdout.write = function niakvioRouteEvidenceWrite(chunk, encoding, callback) {
  let text = String(chunk ?? '');
  const trimmed = text.trim();
  if (trimmed.startsWith('{')) {
    try {
      const value = JSON.parse(trimmed);
      if (Object.prototype.hasOwnProperty.call(value, 'playable_stream_count')) {
        value.route_validation = {
          schema_version: 2,
          request_count: routeTrace.length,
          playback_request_count: playbackRequestCount,
          fetches: routeTrace.slice(0, 100),
        };
        text = JSON.stringify(value) + '\n';
      }
    } catch {}
  }
  return nativeWrite(text, encoding, callback);
};

require('./nuvio_tv_probe_tmdb_ci.cjs');
