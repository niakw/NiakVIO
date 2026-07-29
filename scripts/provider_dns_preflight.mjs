#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/**
 * Resolve provider-owned domains through French ISP DNS servers before runtime
 * quality/scoring checks. HTTP requests are pinned to the IP returned by the
 * selected resolver while preserving the original Host header and TLS SNI.
 */

import dns from 'node:dns';
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import path from 'node:path';
import process from 'node:process';
import { promises as fs } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { isPrivateIp } = require('./network_guard.cjs');

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const INFRASTRUCTURE_HOST_PATTERNS = [
  /(^|\.)github\.com$/i,
  /(^|\.)githubusercontent\.com$/i,
  /(^|\.)themoviedb\.org$/i,
  /(^|\.)tmdb\.org$/i,
  /(^|\.)postimg\.cc$/i,
  /(^|\.)google\.com$/i,
  /(^|\.)googleapis\.com$/i,
  /(^|\.)gstatic\.com$/i,
  /(^|\.)jsdelivr\.net$/i,
  /(^|\.)unpkg\.com$/i,
  /(^|\.)npmjs\.(?:org|com)$/i,
  /(^|\.)cloudflare\.com$/i,
  /(^|\.)cloudflareinsights\.com$/i,
  /(^|\.)cloudfront\.net$/i,
  /(^|\.)cdnjs\.com$/i,
  /(^|\.)gravatar\.com$/i,
];
const REDIRECT_STATUSES = new Set([301, 302, 303, 307, 308]);
const BLOCK_PATTERNS = [
  /acc[eè]s[^\n]{0,90}(?:bloqu|interdit)/i,
  /(?:site|domaine|contenu)[^\n]{0,90}(?:bloqu|interdit)/i,
  /inaccessible depuis (?:votre|cette) connexion/i,
  /d[eé]cision (?:de justice|judiciaire)/i,
  /blocage (?:dns|administratif|judiciaire)/i,
  /access to this (?:website|site) (?:has been )?blocked/i,
  /this site has been blocked/i,
];



function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function globalpingHeaders(remoteConfig = {}) {
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    'User-Agent': 'niakw-nuvio-providers/GlobalpingDNSPreflight',
  };
  const token = process.env[String(remoteConfig.token_env || 'GLOBALPING_API_TOKEN')];
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function globalpingJson(url, init, remoteConfig = {}) {
  const timeoutMs = Math.max(3000, Number(remoteConfig.request_timeout_ms || 15000));
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal, headers: { ...globalpingHeaders(remoteConfig), ...(init?.headers || {}) } });
    const text = await response.text();
    let payload = null;
    try { payload = text ? JSON.parse(text) : {}; } catch { payload = { raw: text }; }
    if (!response.ok) {
      const error = new Error(`Globalping HTTP ${response.status}: ${String(payload?.message || payload?.error || text).slice(0, 300)}`);
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  } finally {
    clearTimeout(timer);
  }
}

async function runGlobalpingMeasurement(body, remoteConfig = {}) {
  const apiBase = String(remoteConfig.api_base || 'https://api.globalping.io/v1').replace(/\/$/, '');
  const created = await globalpingJson(`${apiBase}/measurements`, {
    method: 'POST',
    body: JSON.stringify(body),
  }, remoteConfig);
  const id = String(created?.id || '');
  if (!id) throw new Error('Globalping did not return a measurement id');
  const pollInterval = Math.max(500, Number(remoteConfig.poll_interval_ms || 1200));
  const deadline = Date.now() + Math.max(5000, Number(remoteConfig.measurement_timeout_ms || 30000));
  while (Date.now() < deadline) {
    const result = await globalpingJson(`${apiBase}/measurements/${encodeURIComponent(id)}`, { method: 'GET' }, remoteConfig);
    if (result?.status && result.status !== 'in-progress') return { id, payload: result };
    await sleep(pollInterval);
  }
  throw Object.assign(new Error(`Globalping measurement ${id} timed out`), { code: 'ETIMEOUT' });
}

function firstGlobalpingResult(payload) {
  return Array.isArray(payload?.results) ? payload.results[0] || null : null;
}

function globalpingProbeSummary(entry) {
  const probe = entry?.probe || {};
  return {
    country: probe.country || probe.location?.country || null,
    city: probe.city || probe.location?.city || null,
    network: probe.network || null,
    asn: probe.asn || null,
    tags: probe.tags || [],
  };
}

function parseGlobalpingDns(measurement, resolverName, resolverConfig) {
  const entry = firstGlobalpingResult(measurement.payload);
  if (!entry) {
    return { resolver: resolverName, servers: resolverConfig.servers || [], status: 'unavailable', addresses: [], errors: [{ family: 4, code: 'GLOBALPING_NO_PROBE_RESULT' }], transport: 'globalping', measurement_id: measurement.id };
  }
  const result = entry.result || {};
  const answers = Array.isArray(result.answers) ? result.answers : [];
  const addresses = [];
  for (const answer of answers) {
    const value = String(answer?.value || answer?.data || '').trim();
    const family = net.isIP(value);
    if ((family === 4 || family === 6) && !isPrivateIp(value)) addresses.push({ address: value, family });
  }
  const statusCode = String(result.statusCode || result.status || '').toUpperCase();
  const raw = String(result.rawOutput || '');
  const negative = /NXDOMAIN|NODATA|NOTFOUND/.test(statusCode) || /status:\s*(?:NXDOMAIN|NODATA)/i.test(raw);
  const unavailable = /SERVFAIL|REFUSED|TIMEOUT/.test(statusCode) || /timed out|no servers could be reached|connection refused/i.test(raw);
  return {
    resolver: resolverName,
    servers: resolverConfig.servers || [],
    status: addresses.length ? 'resolved' : negative ? 'negative' : unavailable ? 'unavailable' : 'error',
    addresses,
    errors: addresses.length ? [] : [{ family: 4, code: statusCode || 'GLOBALPING_DNS_EMPTY' }],
    transport: 'globalping',
    measurement_id: measurement.id,
    probe: globalpingProbeSummary(entry),
    raw_status: statusCode || null,
  };
}

function headersToObject(value) {
  if (!value) return {};
  if (!Array.isArray(value)) return typeof value === 'object' ? value : {};
  const output = {};
  for (const item of value) {
    const name = String(item?.name || item?.key || '').toLowerCase();
    if (name) output[name] = item?.value;
  }
  return output;
}

function parseGlobalpingHttp(measurement, originalHost) {
  const entry = firstGlobalpingResult(measurement.payload);
  if (!entry) return { status: 'unreachable', http_status: null, final_host: normalizeHost(originalHost), redirects: [], body_excerpt: '', attempts: [], error: 'GLOBALPING_NO_PROBE_RESULT', transport: 'globalping', measurement_id: measurement.id };
  const result = entry.result || {};
  const raw = String(result.rawOutput || '');
  const headers = headersToObject(result.headers);
  const status = Number(result.statusCode || result.status || (raw.match(/HTTP\/\S+\s+(\d{3})/i) || [])[1]) || null;
  const location = String(headers.location || (raw.match(/^location:\s*(\S+)/im) || [])[1] || '');
  const redirects = [];
  let finalHost = normalizeHost(originalHost);
  if (location) {
    try {
      const next = new URL(location, `https://${originalHost}/`);
      finalHost = normalizeHost(next.hostname);
      redirects.push({ from: normalizeHost(originalHost), to: finalHost, status });
    } catch {}
  }
  const blockPattern = BLOCK_PATTERNS.find((pattern) => pattern.test(raw));
  const blocked = status === 451 || Boolean(blockPattern);
  const reachable = Number.isInteger(status) && status < 500 && !blocked;
  return {
    status: blocked ? 'blocked' : reachable ? 'reachable' : 'http_error',
    http_status: status,
    final_host: finalHost,
    redirects,
    body_excerpt: raw.replace(/\s+/g, ' ').slice(0, 700),
    block_signal: blockPattern?.source || (status === 451 ? 'http_451' : null),
    attempts: [{ host: normalizeHost(originalHost), status, ok: reachable, transport: 'globalping' }],
    transport: 'globalping',
    measurement_id: measurement.id,
    probe: globalpingProbeSummary(entry),
  };
}

export function createGlobalpingDependencies(preflightConfig, injected = {}) {
  const remoteConfig = preflightConfig.remote_probe || {};
  const runMeasurement = injected.runMeasurement || runGlobalpingMeasurement;
  const dnsCache = new Map();
  const httpCache = new Map();
  const magicTable = remoteConfig.location_magic || {};

  async function runAtFirstAvailableLocation(bodyFactory, resolverName) {
    const candidates = Array.isArray(magicTable[resolverName]) ? magicTable[resolverName] : [magicTable[resolverName] || `France+${resolverName}+eyeball`];
    let lastError = null;
    for (const magic of candidates.filter(Boolean)) {
      try {
        return await runMeasurement(bodyFactory(String(magic)), remoteConfig);
      } catch (error) {
        lastError = error;
        if (![400, 404, 422].includes(Number(error?.status))) break;
      }
    }
    throw lastError || new Error(`No Globalping location available for ${resolverName}`);
  }

  async function resolveFn(host, resolverConfig, options = preflightConfig) {
    if (resolverConfig?.kind !== 'french_isp' || remoteConfig.enabled === false) {
      return resolveWithResolver(host, resolverConfig, options);
    }
    const key = `${resolverConfig.name}:${normalizeHost(host)}`;
    if (!dnsCache.has(key)) {
      dnsCache.set(key, (async () => {
        try {
          const resolver = String((resolverConfig.servers || [])[0] || '');
          const measurement = await runAtFirstAvailableLocation((magic) => ({
            type: 'dns',
            target: normalizeHost(host),
            locations: [{ magic }],
            limit: 1,
            measurementOptions: { query: { type: 'A' }, resolver, protocol: 'UDP' },
          }), resolverConfig.name);
          return parseGlobalpingDns(measurement, resolverConfig.name, resolverConfig);
        } catch (error) {
          if (remoteConfig.fallback_to_direct === true) return resolveWithResolver(host, resolverConfig, options);
          return { resolver: resolverConfig.name, servers: resolverConfig.servers || [], status: 'unavailable', addresses: [], errors: [{ family: 4, code: compactError(error) }], transport: 'globalping', error: compactError(error) };
        }
      })());
    }
    return dnsCache.get(key);
  }

  async function probeFn(host, resolverConfig, options = preflightConfig) {
    if (resolverConfig?.kind !== 'french_isp' || remoteConfig.enabled === false) {
      return probeHttpThroughResolver(host, resolverConfig, options, { resolveHost: (targetHost) => resolveFn(targetHost, resolverConfig, options) });
    }
    const key = `${resolverConfig.name}:${normalizeHost(host)}`;
    if (!httpCache.has(key)) {
      httpCache.set(key, (async () => {
        try {
          const dnsResult = await resolveFn(host, resolverConfig, options);
          if (!dnsResult.measurement_id) return { status: 'unreachable', http_status: null, final_host: normalizeHost(host), redirects: [], body_excerpt: '', attempts: [], error: 'GLOBALPING_DNS_MEASUREMENT_MISSING', transport: 'globalping' };
          const measurement = await runMeasurement({
            type: 'http',
            target: `https://${normalizeHost(host)}/`,
            locations: [{ magic: dnsResult.measurement_id }],
            limit: 1,
            measurementOptions: { request: { method: 'GET' } },
          }, remoteConfig);
          return parseGlobalpingHttp(measurement, host);
        } catch (error) {
          return { status: 'unreachable', http_status: null, final_host: normalizeHost(host), redirects: [], body_excerpt: '', attempts: [], error: compactError(error), transport: 'globalping' };
        }
      })());
    }
    return httpCache.get(key);
  }

  return { resolveFn, probeFn, dnsCache, httpCache };
}

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith('--')) continue;
    const key = value.slice(2);
    const next = argv[index + 1];
    if (next && !next.startsWith('--')) {
      args[key] = next;
      index += 1;
    } else {
      args[key] = true;
    }
  }
  return args;
}

function normalizeHost(value) {
  return String(value || '')
    .trim()
    .replace(/^https?:\/\//i, '')
    .replace(/^\[|\]$/g, '')
    .split(/[/:?#]/, 1)[0]
    .replace(/^www\./i, '')
    .toLowerCase();
}

function isInfrastructureHost(host) {
  const normalized = normalizeHost(host);
  return !normalized || INFRASTRUCTURE_HOST_PATTERNS.some((pattern) => pattern.test(normalized));
}

function validPublicHost(host) {
  const normalized = normalizeHost(host);
  const codeSuffixes = new Set([
    'assign', 'catch', 'constructor', 'default', 'env', 'exports', 'finally',
    'length', 'log', 'map', 'prototype', 'reject', 'resolve', 'status', 'then',
  ]);
  const suffix = normalized.split('.').at(-1);
  if (!normalized || codeSuffixes.has(suffix) || normalized === 'localhost' || normalized.endsWith('.localhost')) return false;
  if (net.isIP(normalized)) return !isPrivateIp(normalized);
  if (!/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}$/i.test(normalized)) return false;
  return !isInfrastructureHost(normalized);
}

function hostFromValue(value) {
  try {
    const parsed = new URL(String(value));
    return normalizeHost(parsed.hostname);
  } catch {
    const host = normalizeHost(value);
    return validPublicHost(host) ? host : null;
  }
}

function baseBrand(host) {
  const labels = normalizeHost(host).split('.').filter(Boolean);
  if (labels.length < 2) return labels[0] || '';
  const disposable = new Set(['www', 'api', 'cdn', 'static', 'media', 'stream', 'player', 'app', 'www1', 'www2']);
  const useful = labels.slice(0, -1).filter((label) => !disposable.has(label));
  return useful.at(-1) || labels.at(-2) || '';
}

function addDomain(scores, host, points, evidence) {
  const normalized = normalizeHost(host);
  if (!validPublicHost(normalized)) return;
  const current = scores.get(normalized) || { host: normalized, score: 0, evidence: new Set() };
  current.score += points;
  current.evidence.add(evidence);
  scores.set(normalized, current);
}

export function extractCandidateDomains(candidate, sourceText, overrides = {}, limit = 4) {
  const scores = new Map();
  const canonicalId = String(candidate?.canonical_id || '').toLowerCase();
  const patch = overrides?.provider_patches?.[canonicalId] || {};

  const fixedApi = patch?.fixed_endpoint?.api;
  if (fixedApi) addDomain(scores, hostFromValue(fixedApi), 160, 'fixed_endpoint');
  for (const value of Object.values(patch?.runtime_domain_replacements || {})) {
    addDomain(scores, hostFromValue(value), 140, 'runtime_domain_override');
  }
  for (const value of Object.values(patch?.replacements || {})) {
    addDomain(scores, hostFromValue(value), 120, 'provider_replacement');
  }
  for (const value of patch?.required_values || []) {
    addDomain(scores, hostFromValue(value), 110, 'required_value');
  }

  const metadata = candidate?.metadata || {};
  for (const field of ['website', 'homepage', 'url']) {
    if (metadata[field]) addDomain(scores, hostFromValue(metadata[field]), 100, `metadata_${field}`);
  }
  if (metadata.logo) addDomain(scores, hostFromValue(metadata.logo), 25, 'metadata_logo');
  const description = String(metadata.description || '');
  for (const match of description.matchAll(/https?:\/\/[^\s"'<>]+/gi)) {
    addDomain(scores, hostFromValue(match[0]), 90, 'metadata_description_url');
  }
  for (const match of description.matchAll(/(?:^|[^@\w-])((?:[a-z0-9-]+\.)+[a-z]{2,24})(?=$|[^\w-])/gi)) {
    addDomain(scores, match[1], 60, 'metadata_description_domain');
  }

  const text = String(sourceText || '');
  for (const match of text.matchAll(/https?:\/\/[^\s"'`<>\\]+/gi)) {
    const host = hostFromValue(match[0]);
    addDomain(scores, host, 35, 'javascript_url');
  }
  for (const match of text.matchAll(/(?:^|[^@\w-])((?:[a-z0-9-]+\.)+[a-z]{2,24})(?=$|[^\w-])/gi)) {
    addDomain(scores, match[1], 12, 'javascript_domain');
  }

  return [...scores.values()]
    .map((item) => ({ host: item.host, score: item.score, evidence: [...item.evidence].sort() }))
    .sort((left, right) => right.score - left.score || left.host.localeCompare(right.host))
    .slice(0, Math.max(1, Number(limit || 4)));
}

function compactError(error) {
  return String(error?.code || error?.message || error || 'unknown_error').slice(0, 160);
}

export async function resolveWithResolver(host, resolverConfig, options = {}) {
  const timeout = Math.max(300, Number(options.query_timeout_ms || options.timeoutMs || 2500));
  const tries = Math.max(1, Number(options.dns_tries || options.tries || 1));
  const resolver = new dns.promises.Resolver({ timeout, tries });
  resolver.setServers((resolverConfig?.servers || []).map(String));
  const addresses = [];
  const errors = [];

  const queries = [[4, 'resolve4'], [6, 'resolve6']].map(async ([family, method]) => {
    try {
      const result = await resolver[method](host);
      return { family, result: result || [] };
    } catch (error) {
      return { family, error: compactError(error) };
    }
  });
  for (const query of await Promise.all(queries)) {
    if (query.error) {
      errors.push({ family: query.family, code: query.error });
      continue;
    }
    for (const address of query.result) {
      if (!isPrivateIp(address)) addresses.push({ address, family: query.family });
    }
  }

  const unique = [];
  const seen = new Set();
  for (const record of addresses) {
    const key = `${record.family}:${record.address}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(record);
    }
  }
  const codes = errors.map((item) => item.code);
  const explicitNegative = codes.length > 0 && codes.every((code) => /ENOTFOUND|ENODATA|NOTFOUND|NODATA/i.test(code));
  const transportFailure = codes.length > 0 && codes.every((code) => /ETIMEOUT|ECONNREFUSED|SERVFAIL|EAI_AGAIN|ECANCELLED/i.test(code));
  return {
    resolver: resolverConfig?.name || null,
    servers: resolverConfig?.servers || [],
    status: unique.length ? 'resolved' : explicitNegative ? 'negative' : transportFailure ? 'unavailable' : 'error',
    addresses: unique,
    errors,
  };
}

function makeLookup(record) {
  return (_hostname, options, callback) => {
    let resolvedOptions = options;
    let done = callback;
    if (typeof options === 'function') {
      done = options;
      resolvedOptions = {};
    }
    if (resolvedOptions?.all) {
      done(null, [{ address: record.address, family: record.family }]);
    } else {
      done(null, record.address, record.family);
    }
  };
}

function requestOnce(url, record, options = {}) {
  return new Promise((resolve) => {
    const client = url.protocol === 'https:' ? https : http;
    const timeoutMs = Math.max(500, Number(options.http_timeout_ms || options.timeoutMs || 7000));
    const maxBodyBytes = Math.max(1024, Number(options.max_body_bytes || options.maxBodyBytes || 131072));
    const request = client.request({
      protocol: url.protocol,
      hostname: url.hostname,
      port: url.port || undefined,
      path: `${url.pathname || '/'}${url.search || ''}`,
      method: 'GET',
      lookup: makeLookup(record),
      servername: url.hostname,
      rejectUnauthorized: true,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; NuvioProviderDNSPreflight/1.0)',
        Accept: 'text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.6',
        Connection: 'close',
      },
    }, (response) => {
      const chunks = [];
      let total = 0;
      response.on('data', (chunk) => {
        if (total >= maxBodyBytes) return;
        const remaining = maxBodyBytes - total;
        const slice = chunk.length > remaining ? chunk.subarray(0, remaining) : chunk;
        chunks.push(slice);
        total += slice.length;
      });
      response.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf8');
        const blockPattern = BLOCK_PATTERNS.find((pattern) => pattern.test(body));
        resolve({
          ok: true,
          status: response.statusCode || null,
          headers: response.headers,
          body,
          block_detected: Boolean(blockPattern) || response.statusCode === 451,
          block_signal: blockPattern?.source || (response.statusCode === 451 ? 'http_451' : null),
        });
      });
    });
    request.setTimeout(timeoutMs, () => request.destroy(Object.assign(new Error('request timeout'), { code: 'ETIMEOUT' })));
    request.on('error', (error) => resolve({ ok: false, error: compactError(error), status: null, headers: {}, body: '' }));
    request.end();
  });
}

export async function probeHttpThroughResolver(initialHost, resolverConfig, options = {}, dependencies = {}) {
  const resolveHost = dependencies.resolveHost || ((host) => resolveWithResolver(host, resolverConfig, options));
  const performRequest = dependencies.performRequest || requestOnce;
  const maxRedirects = Math.max(0, Number(options.max_redirects || options.maxRedirects || 4));
  const schemes = options.schemes || ['https:', 'http:'];
  const attempts = [];

  for (const scheme of schemes) {
    let current = new URL(`${scheme}//${initialHost}/`);
    const redirects = [];
    for (let redirectCount = 0; redirectCount <= maxRedirects; redirectCount += 1) {
      const dnsResult = await resolveHost(current.hostname);
      const publicAddresses = (dnsResult.addresses || []).filter((record) => !isPrivateIp(record.address));
      const ipv4Addresses = publicAddresses.filter((record) => Number(record.family) === 4);
      const ipv6Addresses = publicAddresses.filter((record) => Number(record.family) === 6);
      // GitHub-hosted runners do not consistently expose outbound IPv6. Prefer IPv4
      // for the local HTTP fallback and only use IPv6 when explicitly enabled.
      const safeAddresses = [
        ...ipv4Addresses,
        ...(options.allow_ipv6_http === true ? ipv6Addresses : []),
      ].slice(0, 3);
      if (!safeAddresses.length) {
        attempts.push({ scheme, host: current.hostname, dns_status: dnsResult.status, error: 'no_public_address' });
        break;
      }

      let response = null;
      let selectedRecord = null;
      for (const record of safeAddresses) {
        response = await performRequest(current, record, options);
        attempts.push({
          scheme,
          host: current.hostname,
          ip_family: record.family,
          status: response.status,
          ok: Boolean(response.ok),
          error: response.error || null,
          block_detected: Boolean(response.block_detected),
        });
        if (response.ok) {
          selectedRecord = record;
          break;
        }
      }
      if (!response?.ok || !selectedRecord) break;

      const location = response.headers?.location;
      if (REDIRECT_STATUSES.has(Number(response.status)) && location && redirectCount < maxRedirects) {
        const next = new URL(String(location), current);
        redirects.push({ from: current.hostname, to: normalizeHost(next.hostname), status: response.status });
        current = next;
        continue;
      }

      const reachable = Number.isInteger(response.status) && response.status < 500 && !response.block_detected;
      return {
        status: response.block_detected ? 'blocked' : reachable ? 'reachable' : 'http_error',
        http_status: response.status,
        final_host: normalizeHost(current.hostname),
        redirects,
        body_excerpt: String(response.body || '').replace(/\s+/g, ' ').slice(0, 500),
        block_signal: response.block_signal || null,
        attempts,
      };
    }
  }
  return { status: 'unreachable', http_status: null, final_host: normalizeHost(initialHost), redirects: [], body_excerpt: '', attempts };
}

function urlsFromText(text) {
  const output = [];
  for (const match of String(text || '').matchAll(/https?:\/\/[^\s"'<>]+/gi)) {
    try { output.push(new URL(match[0])); } catch {}
  }
  return output;
}

export function discoverMigrationCandidates(originalHost, probeResults, domainHints = []) {
  const originalBrand = baseBrand(originalHost);
  const candidates = new Map();
  const add = (host, points, evidence) => {
    const normalized = normalizeHost(host);
    if (!validPublicHost(normalized) || normalized === normalizeHost(originalHost)) return;
    const item = candidates.get(normalized) || { host: normalized, confidence: 0, evidence: new Set() };
    item.confidence += points;
    item.evidence.add(evidence);
    candidates.set(normalized, item);
  };

  for (const probe of probeResults || []) {
    for (const redirect of probe?.http?.redirects || []) {
      add(redirect.to, 65, `http_redirect_${redirect.status}`);
    }
    for (const url of urlsFromText(probe?.http?.body_excerpt || '')) {
      add(url.hostname, 35, 'page_url_hint');
    }
  }
  for (const hint of domainHints || []) add(hint.host || hint, 15, 'provider_artifact_hint');

  return [...candidates.values()]
    .map((item) => {
      const sameBrand = Boolean(originalBrand && baseBrand(item.host) === originalBrand);
      return {
        host: item.host,
        confidence: Math.min(100, item.confidence + (sameBrand ? 25 : 0)),
        same_brand: sameBrand,
        evidence: [...item.evidence].sort(),
      };
    })
    .filter((item) => item.same_brand)
    .sort((left, right) => right.confidence - left.confidence || left.host.localeCompare(right.host));
}

function summarizeFailureKind(checks) {
  const dnsStatuses = checks.map((item) => item.dns?.status).filter(Boolean);
  const httpStatuses = checks.map((item) => item.http?.status).filter(Boolean);
  if (httpStatuses.includes('blocked')) return 'blocked';
  if (dnsStatuses.includes('negative')) return 'negative';
  if (dnsStatuses.every((status) => status === 'unavailable')) return 'unavailable';
  return 'error';
}

export async function checkDomainAcrossResolvers(host, preflightConfig, dependencies = {}) {
  const resolverTable = preflightConfig.resolvers || {};
  const frenchOrder = [preflightConfig.primary_french_isp, ...(preflightConfig.fallback_french_isps || [])].filter(Boolean);
  const neutralOrder = preflightConfig.neutral_resolvers || [];
  const resolveFn = dependencies.resolveFn || resolveWithResolver;
  const probeFn = dependencies.probeFn || probeHttpThroughResolver;
  const frenchChecks = [];

  for (const name of frenchOrder) {
    const resolverConfig = { name, ...(resolverTable[name] || {}) };
    const dnsResult = await resolveFn(host, resolverConfig, preflightConfig);
    let httpResult = null;
    if ((dnsResult.addresses || []).length) {
      httpResult = await probeFn(host, resolverConfig, preflightConfig, {
        resolveHost: (targetHost) => resolveFn(targetHost, resolverConfig, preflightConfig),
      });
    }
    const check = { isp: name, dns: dnsResult, http: httpResult };
    frenchChecks.push(check);
    if (httpResult?.status === 'reachable') {
      return {
        host,
        status: name === preflightConfig.primary_french_isp ? 'accessible_primary_french_isp' : 'accessible_french_fallback',
        selected_resolver: name,
        continue_runtime: true,
        french_checks: frenchChecks,
        neutral_checks: [],
        migration_candidates: [],
      };
    }
  }

  const neutralChecks = [];
  for (const name of neutralOrder) {
    const resolverConfig = { name, ...(resolverTable[name] || {}) };
    const dnsResult = await resolveFn(host, resolverConfig, preflightConfig);
    let httpResult = null;
    if ((dnsResult.addresses || []).length) {
      httpResult = await probeFn(host, resolverConfig, preflightConfig, {
        resolveHost: (targetHost) => resolveFn(targetHost, resolverConfig, preflightConfig),
      });
    }
    const check = { resolver: name, dns: dnsResult, http: httpResult };
    neutralChecks.push(check);
    if (httpResult?.status === 'reachable') break;
  }

  const neutralReachable = neutralChecks.some((item) => item.http?.status === 'reachable');
  const explicitFrenchFailure = frenchChecks.some((item) => ['negative'].includes(item.dns?.status) || item.http?.status === 'blocked');
  const allFrenchUnavailable = frenchChecks.length > 0 && frenchChecks.every((item) => item.dns?.status === 'unavailable');
  const domainHints = dependencies.domainHints || [];
  const migrationCandidates = neutralReachable
    ? discoverMigrationCandidates(host, neutralChecks, domainHints)
    : [];

  if (neutralReachable && explicitFrenchFailure) {
    return {
      host,
      status: 'confirmed_french_dns_or_http_block',
      selected_resolver: null,
      continue_runtime: false,
      french_failure_kind: summarizeFailureKind(frenchChecks),
      french_checks: frenchChecks,
      neutral_checks: neutralChecks,
      migration_candidates: migrationCandidates.map((item) => ({ ...item, original_host: host })),
    };
  }
  if (neutralReachable && allFrenchUnavailable) {
    return {
      host,
      status: 'french_resolvers_inconclusive',
      selected_resolver: neutralChecks.find((item) => item.http?.status === 'reachable')?.resolver || null,
      continue_runtime: preflightConfig.continue_on_inconclusive !== false,
      french_checks: frenchChecks,
      neutral_checks: neutralChecks,
      migration_candidates: migrationCandidates.map((item) => ({ ...item, original_host: host })),
    };
  }
  if (neutralReachable) {
    return {
      host,
      status: 'accessible_neutral_only',
      selected_resolver: neutralChecks.find((item) => item.http?.status === 'reachable')?.resolver || null,
      continue_runtime: preflightConfig.continue_on_inconclusive !== false,
      french_checks: frenchChecks,
      neutral_checks: neutralChecks,
      migration_candidates: migrationCandidates.map((item) => ({ ...item, original_host: host })),
    };
  }
  const allNeutralUnavailable = neutralChecks.length > 0
    && neutralChecks.every((item) => item.dns?.status === 'unavailable');
  const allNeutralNegative = neutralChecks.length > 0
    && neutralChecks.every((item) => item.dns?.status === 'negative');
  if (allFrenchUnavailable && allNeutralUnavailable) {
    return {
      host,
      status: 'all_custom_resolvers_unavailable',
      selected_resolver: null,
      continue_runtime: preflightConfig.continue_on_inconclusive !== false,
      french_checks: frenchChecks,
      neutral_checks: neutralChecks,
      migration_candidates: migrationCandidates.map((item) => ({ ...item, original_host: host })),
    };
  }
  if (allNeutralNegative && explicitFrenchFailure) {
    return {
      host,
      status: 'globally_unreachable',
      selected_resolver: null,
      continue_runtime: preflightConfig.continue_on_global_unreachable === true,
      french_checks: frenchChecks,
      neutral_checks: neutralChecks,
      migration_candidates: migrationCandidates.map((item) => ({ ...item, original_host: host })),
    };
  }
  return {
    host,
    status: 'resolver_or_http_inconclusive',
    selected_resolver: null,
    continue_runtime: preflightConfig.continue_on_inconclusive !== false,
    french_checks: frenchChecks,
    neutral_checks: neutralChecks,
    migration_candidates: migrationCandidates.map((item) => ({ ...item, original_host: host })),
  };
}

export function providerDecision(domainResults, preflightConfig) {
  if (!domainResults.length) {
    return { status: 'no_provider_domain_detected', continue_runtime: true, reason: 'no_static_provider_domain' };
  }
  const frenchPass = domainResults.find((item) => ['accessible_primary_french_isp', 'accessible_french_fallback'].includes(item.status));
  if (frenchPass) {
    return { status: 'pass', continue_runtime: true, reason: frenchPass.status, selected_resolver: frenchPass.selected_resolver };
  }
  const migration = domainResults
    .flatMap((item) => item.migration_candidates || [])
    .filter((item) => item.same_brand && item.confidence >= Number(preflightConfig?.migration_discovery?.minimum_confidence || 80))
    .sort((left, right) => right.confidence - left.confidence)[0] || null;
  const confirmedBlock = domainResults.some((item) => item.status === 'confirmed_french_dns_or_http_block');
  if (confirmedBlock) {
    return {
      status: 'confirmed_french_block',
      continue_runtime: preflightConfig.skip_runtime_on_confirmed_french_block === false,
      reason: migration ? 'confirmed_block_with_migration_candidate' : 'confirmed_block_without_safe_migration',
      migration_candidate: migration,
    };
  }
  if (domainResults.every((item) => item.status === 'globally_unreachable')) {
    return {
      status: 'globally_unreachable',
      continue_runtime: preflightConfig.continue_on_global_unreachable === true,
      reason: 'all_french_and_neutral_resolvers_confirmed_unreachable',
      migration_candidate: migration,
    };
  }
  return {
    status: 'inconclusive',
    continue_runtime: preflightConfig.continue_on_inconclusive !== false,
    reason: 'french_isp_resolvers_unavailable_or_neutral_only',
    migration_candidate: migration,
  };
}

async function runCli() {
  const args = parseArgs(process.argv.slice(2));
  const stage = path.resolve(args.stage || process.env.NUVIO_STAGE || path.join(ROOT, 'staging'));
  const registryPath = path.resolve(args.registry || process.env.NUVIO_CANDIDATES_PATH || path.join(stage, 'candidates.json'));
  const configPath = path.resolve(args.config || process.env.NUVIO_HEALTH_CONFIG || path.join(ROOT, 'health-config.json'));
  const outputPath = path.resolve(args.output || process.env.NUVIO_DNS_PREFLIGHT_RESULTS || path.join(ROOT, 'health-output', 'dns-preflight-report.json'));
  const [registry, config, overrides] = await Promise.all([
    fs.readFile(registryPath, 'utf8').then(JSON.parse),
    fs.readFile(configPath, 'utf8').then(JSON.parse),
    fs.readFile(path.join(ROOT, 'provider-overrides.json'), 'utf8').then(JSON.parse),
  ]);
  const preflightConfig = config.dns_preflight || {};
  if (preflightConfig.enabled === false) {
    const disabled = { schema_version: 1, enabled: false, generated_at: new Date().toISOString(), providers: [] };
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, `${JSON.stringify(disabled, null, 2)}\n`);
    return;
  }

  const providers = [];
  const concurrency = Math.max(1, Math.min(8, Number(preflightConfig.concurrency || 3)));
  const candidates = Array.isArray(registry.candidates) ? registry.candidates : [];
  const frenchResolverNames = [preflightConfig.primary_french_isp, ...(preflightConfig.fallback_french_isps || [])].filter(Boolean);
  const remoteDependencies = createGlobalpingDependencies(preflightConfig);
  const resolverTransport = frenchResolverNames.map((name) => ({
    resolver: name,
    status: preflightConfig.remote_probe?.enabled === false ? 'direct' : 'globalping',
    location_magic: preflightConfig.remote_probe?.location_magic?.[name] || [],
  }));
  const frenchResolverTransportAvailable = preflightConfig.remote_probe?.enabled !== false;
  let nextIndex = 0;
  const results = new Array(candidates.length);

  async function worker() {
    while (true) {
      const index = nextIndex++;
      if (index >= candidates.length) return;
      const candidate = candidates[index];
      try {
        const providerPath = path.resolve(stage, String(candidate.local_path || ''));
        const sourceText = await fs.readFile(providerPath, 'utf8');
        const domainHints = extractCandidateDomains(candidate, sourceText, overrides, preflightConfig.max_domains_per_provider || 4);
        const domainResults = [];
        for (const hint of domainHints) {
          domainResults.push(await checkDomainAcrossResolvers(hint.host, preflightConfig, { domainHints, resolveFn: remoteDependencies.resolveFn, probeFn: remoteDependencies.probeFn }));
          if (domainResults.at(-1)?.status.startsWith('accessible_')) break;
        }
        const decision = providerDecision(domainResults, preflightConfig);
        results[index] = {
          key: candidate.key,
          source: candidate.source,
          canonical_id: candidate.canonical_id,
          sha256: candidate.sha256,
          domain_hints: domainHints,
          domains: domainResults,
          decision,
        };
        process.stdout.write(`[DNS ${index + 1}/${candidates.length}] ${candidate.key}: ${decision.status}\n`);
      } catch (error) {
        results[index] = {
          key: candidate.key,
          source: candidate.source,
          canonical_id: candidate.canonical_id,
          sha256: candidate.sha256,
          domain_hints: [],
          domains: [],
          decision: { status: 'preflight_error', continue_runtime: true, reason: compactError(error) },
        };
        process.stderr.write(`[DNS WARN] ${candidate.key}: ${compactError(error)}\n`);
      }
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, candidates.length || 1) }, () => worker()));
  providers.push(...results.filter(Boolean));
  const counts = {};
  for (const item of providers) counts[item.decision.status] = (counts[item.decision.status] || 0) + 1;
  const report = {
    schema_version: 1,
    enabled: true,
    generated_at: new Date().toISOString(),
    candidate_count: providers.length,
    resolver_order: frenchResolverNames,
    resolver_transport: {
      control_domain: 'example.com',
      french_isp_transport_available: frenchResolverTransportAvailable,
      mode: preflightConfig.remote_probe?.enabled === false ? 'direct' : 'globalping',
      checks: resolverTransport,
    },
    neutral_resolvers: preflightConfig.neutral_resolvers || [],
    counts,
    providers,
  };
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(`DNS preflight complete: ${JSON.stringify(counts)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  runCli().catch((error) => {
    process.stderr.write(`DNS preflight failed: ${compactError(error)}\n`);
    process.exitCode = 1;
  });
}
