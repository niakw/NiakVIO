#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/**
 * Bounded cross-platform runtime probe for the published general manifest.
 *
 * The current Nuvio Mobile and Desktop clients execute plugin getStreams with
 * the same positional QuickJS contract. We exercise three runtime profiles:
 * android, ios and desktop. Desktop covers Windows/macOS/Linux because those
 * clients share the same JVM QuickJS runtime and FetchBridge; OS-specific
 * manifest filtering is validated separately.
 *
 * A provider is NEVER marked broken merely because a title returns zero
 * streams. Platform blocking requires a conclusive failure: two representative
 * movie fixtures both return non-playable payloads, or both runtime executions
 * fail. Returned stream URLs are never persisted in the report.
 */
import { promises as fs } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import process from 'node:process';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { guardedFetch } = require('./network_guard.cjs');
const { probeDirectMedia } = require('./direct_media_probe.cjs');

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WORKER = path.join(ROOT, 'scripts', 'provider_worker.cjs');
const MANIFEST = path.resolve(process.env.NUVIO_PLATFORM_MANIFEST || path.join(ROOT, 'manifest.json'));
const OUTPUT = path.resolve(process.env.NUVIO_PLATFORM_REPORT || path.join(ROOT, 'automation', 'platform-runtime-matrix.json'));
const PROFILES = ['android', 'ios', 'desktop'];
const CONCURRENCY = Math.max(1, Math.min(8, Number(process.env.NUVIO_PLATFORM_CONCURRENCY || 5)));
const FIXTURES = [
  { tmdbId: '157336', mediaType: 'movie', title: 'Interstellar', year: 2014, label: 'Interstellar (2014)', category: 'movie' },
  { tmdbId: '577922', mediaType: 'movie', title: 'Tenet', year: 2020, label: 'Tenet (2020)', category: 'movie' },
];

function sanitize(value, limit = 240) {
  return String(value || '')
    .replace(/(?:https?|magnet|acestream|torrent):[^\s"']+/gi, '[endpoint]')
    .replace(/[\r\n\t]+/g, ' ')
    .slice(0, limit);
}

function normalizeProviderPath(filename) {
  let value = String(filename || '').trim();
  while (value.startsWith('../')) value = value.slice(3);
  if (!value || /^(?:https?:)?\/\//i.test(value)) return null;
  const resolved = path.resolve(ROOT, value);
  return resolved.startsWith(ROOT + path.sep) ? resolved : null;
}

function strictPositionalAdapter(providerPath) {
  return `
const loaded=require(${JSON.stringify(providerPath)});
let owner=loaded;
let fn=loaded&&loaded.getStreams;
if(typeof fn!=='function'&&loaded&&loaded.default){owner=loaded.default;fn=loaded.default.getStreams;}
if(typeof fn!=='function'&&typeof loaded==='function'){owner=null;fn=loaded;}
if(typeof fn!=='function')throw new Error('module does not export getStreams');
module.exports={getStreams:async function(id,type,season,episode){
  if(typeof id!=='string'||typeof type!=='string'){
    const error=new Error('NUVIO_POSITIONAL_CONTRACT');
    error.code='NUVIO_INVALID_REQUEST_ARGUMENT';
    throw error;
  }
  return fn.call(owner,id,type,season,episode);
}};
`;
}

function workerResult(stdout) {
  const lines = String(stdout || '').split(/\r?\n/).filter((line) => line.startsWith('NUVIO_HEALTH_RESULT='));
  if (!lines.length) return null;
  try { return JSON.parse(lines.at(-1).slice('NUVIO_HEALTH_RESULT='.length)); } catch { return null; }
}

async function runWorker(adapterPath, fixture, providerId, profile) {
  const context = {
    providerId,
    locale: 'fr-FR',
    language: 'fr',
    languages: ['fr-FR', 'fr'],
    platform: profile,
    maxSettingsProfiles: 6,
    fixtureMetadata: fixture,
    settings: {},
    storage: {},
    networkLimits: {
      maxFetches: 32,
      maxRedirects: 5,
      maxResponseBytes: 2_000_000,
      maxTotalResponseBytes: 8_000_000,
      maxDistinctHosts: 20,
    },
  };
  return await new Promise((resolve) => {
    const child = spawn(process.execPath, [WORKER, adapterPath, JSON.stringify(fixture), JSON.stringify(context)], {
      cwd: ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    const timer = setTimeout(() => child.kill('SIGKILL'), 50_000);
    child.on('close', (code, signal) => {
      clearTimeout(timer);
      const parsed = workerResult(stdout);
      resolve({ code, signal, parsed, error: parsed ? null : sanitize(stderr || stdout || `worker exit ${code}`) });
    });
  });
}

async function readLimited(response, limit = 196_608) {
  if (!response.body) return Buffer.alloc(0);
  const reader = response.body.getReader();
  const chunks = [];
  let length = 0;
  try {
    while (length < limit) {
      const { done, value } = await reader.read();
      if (done) break;
      const remaining = limit - length;
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

function payloadKind(buffer, contentType, url) {
  const type = String(contentType || '').toLowerCase();
  const text = buffer.subarray(0, 196_608).toString('utf8').replace(/^\uFEFF/, '').trimStart();
  if (/text\/html|application\/xhtml|application\/json|text\/plain/.test(type) && !text.startsWith('#EXTM3U')) {
    return { playable: false, kind: 'non_media_document' };
  }
  if (text.startsWith('#EXTM3U')) return { playable: true, kind: 'hls' };
  if (/^<\?xml[\s\S]*?<MPD[\s>]|^<MPD[\s>]/i.test(text) || /application\/(?:dash\+xml|mpd)/.test(type)) {
    return { playable: true, kind: 'dash' };
  }
  if (buffer.length >= 12 && buffer.subarray(4, 8).toString('ascii') === 'ftyp') return { playable: true, kind: 'mp4' };
  if (buffer.length >= 4 && buffer[0] === 0x1a && buffer[1] === 0x45 && buffer[2] === 0xdf && buffer[3] === 0xa3) {
    return { playable: true, kind: 'matroska_webm' };
  }
  if (buffer.length >= 376 && buffer[0] === 0x47 && buffer[188] === 0x47) return { playable: true, kind: 'mpegts' };
  if (type.startsWith('video/') || type.startsWith('audio/')) return { playable: true, kind: type.split(';')[0] };
  if (/application\/(?:octet-stream|mp4|x-mpegurl|vnd\.apple\.mpegurl)/.test(type)) {
    return { playable: true, kind: type.split(';')[0] };
  }
  if (/\.(?:m3u8|mpd|mp4|mkv|webm)(?:$|[?#])/i.test(String(url || '')) && buffer.length > 0 && !/<html[\s>]/i.test(text.slice(0, 2000))) {
    return { playable: true, kind: 'media_extension_payload' };
  }
  return { playable: false, kind: 'unverified_payload' };
}

async function probeDirectStream(stream) {
  const rawUrl = String(stream?.url || '');
  if (!/^https?:\/\//i.test(rawUrl)) return { playable: false, kind: 'unsupported_url', host: null, status: null };
  let host = null;
  try { host = new URL(rawUrl).hostname.toLowerCase(); } catch { return { playable: false, kind: 'invalid_url', host: null, status: null }; }
  const headers = { ...(stream.headers || {}) };
  const manifestLike = /\.(?:m3u8|mpd)(?:$|[?#])/i.test(rawUrl);
  if (!manifestLike && !Object.keys(headers).some((key) => key.toLowerCase() === 'range')) headers.Range = 'bytes=0-196607';
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 18_000);
  try {
    const response = await guardedFetch(fetch, rawUrl, { method: 'GET', headers, signal: controller.signal }, { maxRedirects: 5 });
    const status = response.status;
    if (!(status === 200 || status === 206)) return { playable: false, kind: `http_${status}`, host, status };
    const body = await readLimited(response);
    return { ...payloadKind(body, response.headers.get('content-type') || '', rawUrl), host, status };
  } catch (error) {
    return { playable: false, kind: sanitize(error?.name || error?.code || error?.message || 'probe_error', 80), host, status: null };
  } finally {
    clearTimeout(timer);
  }
}

function classifyFixture(parsed, execution, direct) {
  const streams = Array.isArray(parsed?.streams) ? parsed.streams : [];
  const streamCount = Number(parsed?.stream_count || streams.length || 0);
  const directCount = direct.filter((item) => item.playable).length;
  let classification = 'inconclusive_empty';
  if (!parsed || parsed.ok !== true) classification = 'runtime_error';
  else if (directCount > 0) classification = 'direct_playable';
  else if (direct.some((item) => item.inconclusive === true)) classification = 'inconclusive_network';
  else if (streamCount > 0) classification = 'non_playable_payload';
  return {
    worker_ok: parsed?.ok === true,
    stream_count: streamCount,
    direct_playable_count: directCount,
    classification,
    payload_kinds: [...new Set(direct.map((item) => item.kind))].sort(),
    media_hosts: [...new Set(direct.filter((item) => item.playable && item.host).map((item) => item.host))].sort(),
    invocation_names: [...new Set((parsed?.invocation_diagnostics || []).map((item) => item.name).filter(Boolean))],
    runtime_error_codes: [...new Set([
      parsed?.error_details?.code,
      ...(parsed?.runtime_errors || []).map((item) => item?.code),
    ].filter(Boolean).map((value) => sanitize(value, 100)))],
    error: execution.error,
  };
}

function classifyProfile(fixtures) {
  if (fixtures.some((item) => item.classification === 'direct_playable')) return 'compatible_direct';
  if (fixtures.length >= 2 && fixtures.every((item) => item.classification === 'non_playable_payload')) return 'conclusive_non_playable';
  if (fixtures.length >= 2 && fixtures.every((item) => item.classification === 'runtime_error')) return 'conclusive_runtime_error';
  return 'inconclusive';
}

async function probeProvider(row, profile, tempDir) {
  const id = String(row.id || '').toLowerCase();
  const providerPath = normalizeProviderPath(row.filename);
  if (!providerPath) return { id, profile, classification: 'conclusive_runtime_error', reason: 'invalid_provider_path', fixtures: [] };
  try { await fs.access(providerPath); } catch {
    return { id, profile, classification: 'conclusive_runtime_error', reason: 'provider_file_missing', fixtures: [] };
  }
  const adapterPath = path.join(tempDir, `${profile}-${id.replace(/[^a-z0-9_-]/g, '_')}.cjs`);
  await fs.writeFile(adapterPath, strictPositionalAdapter(providerPath), 'utf8');
  const results = [];
  for (const fixture of FIXTURES) {
    const execution = await runWorker(adapterPath, fixture, id, profile);
    const parsed = execution.parsed;
    const streams = Array.isArray(parsed?.streams) ? parsed.streams : [];
    const direct = [];
    for (const stream of streams.slice(0, 4)) direct.push(await probeDirectMedia(stream, { guardedFetch, fetchImpl: fetch, timeoutMs: 18000, maxRedirects: 5 }));
    results.push({ fixture: fixture.title, ...classifyFixture(parsed, execution, direct) });
  }
  return { id, profile, classification: classifyProfile(results), fixtures: results };
}

async function mapLimit(items, limit, fn) {
  const output = new Array(items.length);
  let cursor = 0;
  async function worker() {
    while (true) {
      const index = cursor++;
      if (index >= items.length) return;
      output[index] = await fn(items[index], index);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, () => worker()));
  return output;
}

async function main() {
  const manifest = JSON.parse(await fs.readFile(MANIFEST, 'utf8'));
  const rows = (manifest.scrapers || []).filter((row) =>
    row?.enabled === true && Array.isArray(row.supportedTypes) && row.supportedTypes.map((value) => String(value).toLowerCase()).includes('movie')
  );
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'nuvio-platform-runtime-'));
  const byId = new Map(rows.map((row) => [String(row.id || '').toLowerCase(), {
    id: String(row.id || '').toLowerCase(),
    name: row.name || row.id,
    manifest_enabled: row.enabled === true,
    supports_external_player: row.supportsExternalPlayer === true,
    supported_types: row.supportedTypes || [],
    profiles: {},
  }]));
  try {
    for (const profile of PROFILES) {
      const results = await mapLimit(rows, CONCURRENCY, (row) => probeProvider(row, profile, tempDir));
      for (const result of results) byId.get(result.id).profiles[profile] = result;
    }
  } finally {
    await fs.rm(tempDir, { recursive: true, force: true });
  }
  const providers = [...byId.values()];
  const report = {
    schema_version: 2,
    generated_at: new Date().toISOString(),
    release: manifest.version || null,
    manifest: path.relative(ROOT, MANIFEST).replaceAll('\\', '/'),
    runtime_contract: 'QuickJS positional getStreams(tmdbId, mediaType, season, episode)',
    desktop_covers: ['windows', 'macos', 'linux'],
    fixtures: FIXTURES.map((fixture) => fixture.title),
    target_count: providers.length,
    providers,
  };
  await fs.mkdir(path.dirname(OUTPUT), { recursive: true });
  await fs.writeFile(OUTPUT, JSON.stringify(report, null, 2) + '\n', 'utf8');
  const summary = Object.fromEntries(PROFILES.map((profile) => [profile, {
    direct: providers.filter((row) => row.profiles[profile]?.classification === 'compatible_direct').length,
    broken: providers.filter((row) => String(row.profiles[profile]?.classification || '').startsWith('conclusive_')).length,
    inconclusive: providers.filter((row) => row.profiles[profile]?.classification === 'inconclusive').length,
  }]));
  process.stdout.write(JSON.stringify({ release: report.release, targets: report.target_count, summary }, null, 2) + '\n');
}

main().catch((error) => {
  process.stderr.write(`platform runtime probe failed: ${sanitize(error?.stack || error)}\n`);
  process.exit(1);
});
