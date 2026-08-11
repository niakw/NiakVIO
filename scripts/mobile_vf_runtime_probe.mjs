#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/**
 * Targeted Nuvio Mobile compatibility probe for published VF movie providers.
 *
 * This deliberately uses the existing hardened provider_worker for network and
 * sandbox controls, but inserts a tiny adapter that accepts ONLY the positional
 * getStreams(tmdbId, mediaType, season, episode) contract used by current
 * Nuvio Mobile QuickJS. The worker's object-signature fallback therefore cannot
 * turn a Mobile-incompatible provider into a false positive.
 *
 * Returned stream URLs are never written to the report. A stream counts as
 * Android-player compatible only when a bounded network probe proves a direct
 * HLS/DASH/container payload rather than HTML/embed content.
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
const MANIFEST = path.resolve(process.env.NUVIO_MOBILE_MANIFEST || path.join(ROOT, 'vf', 'manifest.json'));
const OUTPUT = path.resolve(process.env.NUVIO_MOBILE_REPORT || path.join(ROOT, 'automation', 'mobile-vf-runtime.json'));
const DEFAULT_TARGETS = [
  'purstream', 'coflix', 'frenchstream', 'movix', 'flemmix', 'nakios',
  'streamzo', 'papadustream', 'goated', 'voiranime-rip', 'wookafr',
];
const requestedTargets = new Set(
  String(process.env.NUVIO_MOBILE_TARGETS || DEFAULT_TARGETS.join(','))
    .split(',').map((value) => value.trim().toLowerCase()).filter(Boolean),
);
const fixtures = [
  { tmdbId: '157336', mediaType: 'movie', title: 'Interstellar', year: 2014, label: 'Interstellar (2014)', category: 'movie' },
  { tmdbId: '577922', mediaType: 'movie', title: 'Tenet', year: 2020, label: 'Tenet (2020)', category: 'movie' },
];

function sanitize(value, limit = 300) {
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
  if (!resolved.startsWith(ROOT + path.sep)) return null;
  return resolved;
}

function resolveProviderExpression(providerPath) {
  return `
const loaded=require(${JSON.stringify(providerPath)});
let owner=loaded;
let fn=loaded&&loaded.getStreams;
if(typeof fn!=='function'&&loaded&&loaded.default){owner=loaded.default;fn=loaded.default.getStreams;}
if(typeof fn!=='function'&&typeof loaded==='function'){owner=null;fn=loaded;}
if(typeof fn!=='function')throw new Error('module does not export getStreams');
module.exports={getStreams:async function(id,type,season,episode){
  if(typeof id!=='string'||typeof type!=='string'){
    const error=new Error('NUVIO_MOBILE_POSITIONAL_CONTRACT');
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

async function runWorker(adapterPath, fixture, providerId) {
  const context = {
    providerId,
    locale: 'fr-FR',
    language: 'fr',
    languages: ['fr-FR', 'fr'],
    platform: 'android',
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
    const timer = setTimeout(() => child.kill('SIGKILL'), 55_000);
    child.on('close', (code, signal) => {
      clearTimeout(timer);
      const parsed = workerResult(stdout);
      resolve({
        code,
        signal,
        parsed,
        error: parsed ? null : sanitize(stderr || stdout || `worker exit ${code}`),
      });
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
    const contentType = response.headers.get('content-type') || '';
    if (!(status === 200 || status === 206)) return { playable: false, kind: `http_${status}`, host, status };
    const body = await readLimited(response);
    const classified = payloadKind(body, contentType, rawUrl);
    return { ...classified, host, status };
  } catch (error) {
    return { playable: false, kind: sanitize(error?.name || error?.code || error?.message || 'probe_error', 80), host, status: null };
  } finally {
    clearTimeout(timer);
  }
}

async function probeProvider(row, tempDir) {
  const providerId = String(row.id || '').toLowerCase();
  const providerPath = normalizeProviderPath(row.filename);
  if (!providerPath) return { id: providerId, manifest_enabled: row.enabled === true, loadable: false, reason: 'invalid_provider_path', fixtures: [] };
  try { await fs.access(providerPath); } catch {
    return { id: providerId, manifest_enabled: row.enabled === true, loadable: false, reason: 'provider_file_missing', fixtures: [] };
  }
  const adapterPath = path.join(tempDir, `${providerId.replace(/[^a-z0-9_-]/g, '_')}.cjs`);
  await fs.writeFile(adapterPath, resolveProviderExpression(providerPath), 'utf8');
  const fixtureResults = [];
  for (const fixture of fixtures) {
    const execution = await runWorker(adapterPath, fixture, providerId);
    const parsed = execution.parsed;
    const streams = Array.isArray(parsed?.streams) ? parsed.streams : [];
    const direct = [];
    for (const stream of streams.slice(0, 4)) direct.push(await probeDirectMedia(stream, { guardedFetch, fetchImpl: fetch, timeoutMs: 18000, maxRedirects: 5 }));
    fixtureResults.push({
      fixture: fixture.title,
      worker_ok: parsed?.ok === true,
      stream_count: Number(parsed?.stream_count || streams.length || 0),
      direct_playable_count: direct.filter((item) => item.playable).length,
      payload_kinds: [...new Set(direct.map((item) => item.kind))].sort(),
      media_hosts: [...new Set(direct.filter((item) => item.playable && item.host).map((item) => item.host))].sort(),
      invocation_names: [...new Set((parsed?.invocation_diagnostics || []).map((item) => item.name).filter(Boolean))],
      runtime_error_codes: [...new Set([
        parsed?.error_details?.code,
        ...(parsed?.runtime_errors || []).map((item) => item?.code),
      ].filter(Boolean).map((value) => sanitize(value, 100)))],
      error: execution.error,
    });
    if (fixtureResults.at(-1).direct_playable_count > 0) break;
  }
  const directMovieProof = fixtureResults.some((item) => item.direct_playable_count > 0);
  return {
    id: providerId,
    name: row.name || providerId,
    manifest_enabled: row.enabled === true,
    supported_movie: Array.isArray(row.supportedTypes) && row.supportedTypes.map((value) => String(value).toLowerCase()).includes('movie'),
    supports_external_player: row.supportsExternalPlayer === true,
    loadable: true,
    android_direct_movie_proof: directMovieProof,
    action: directMovieProof ? 'android-compatible-direct-media' : 'android-no-direct-movie-proof',
    fixtures: fixtureResults,
  };
}

async function main() {
  const manifest = JSON.parse(await fs.readFile(MANIFEST, 'utf8'));
  const rows = (manifest.scrapers || []).filter((row) => requestedTargets.has(String(row?.id || '').toLowerCase()));
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'nuvio-mobile-vf-'));
  const providers = [];
  try {
    for (const row of rows) providers.push(await probeProvider(row, tempDir));
  } finally {
    await fs.rm(tempDir, { recursive: true, force: true });
  }
  const report = {
    schema_version: 1,
    generated_at: new Date().toISOString(),
    release: manifest.version || null,
    runtime_contract: 'Nuvio Mobile QuickJS positional getStreams + native direct-media playback',
    fixtures: fixtures.map((fixture) => fixture.title),
    target_count: providers.length,
    direct_movie_proven: providers.filter((row) => row.android_direct_movie_proof).map((row) => row.id),
    no_direct_movie_proof: providers.filter((row) => !row.android_direct_movie_proof).map((row) => row.id),
    providers,
  };
  await fs.mkdir(path.dirname(OUTPUT), { recursive: true });
  await fs.writeFile(OUTPUT, JSON.stringify(report, null, 2) + '\n', 'utf8');
  process.stdout.write(JSON.stringify({
    release: report.release,
    targets: report.target_count,
    direct_movie_proven: report.direct_movie_proven,
    no_direct_movie_proof: report.no_direct_movie_proof,
  }, null, 2) + '\n');
}

main().catch((error) => {
  process.stderr.write(`mobile VF runtime probe failed: ${sanitize(error?.stack || error)}\n`);
  process.exit(1);
});
