#!/usr/bin/env node
'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');

const WINDOWS_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36';
const HEALTH_PREFIX = 'NUVIO_HEALTH_RESULT=';
const DEFAULT_TIMEOUT_MS = 70_000;
const DEFAULT_PLAYBACK_TIMEOUT_MS = 18_000;

const CLIENTS = Object.freeze({
  tv: {
    id: 'nuvio-tv',
    repository: 'NuvioMedia/NuvioTV',
    branch: 'dev',
    runtimeGroup: 'tv',
    platform: 'android-tv',
    runtimeFile: 'app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt',
    supportFiles: [],
  },
  desktop: {
    id: 'nuvio-desktop',
    repository: 'NuvioMedia/NuvioDesktop',
    branch: 'Dev',
    runtimeGroup: 'compose',
    platform: 'windows',
    runtimeFile: 'composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt',
    supportFiles: ['composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/network/FetchBridge.kt'],
  },
  mobile: {
    id: 'nuvio-mobile',
    repository: 'NuvioMedia/NuvioMobile',
    branch: 'cmp-rewrite',
    runtimeGroup: 'compose',
    platform: 'android',
    runtimeFile: 'composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt',
    supportFiles: ['composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/network/FetchBridge.kt'],
  },
});

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith('--')) continue;
    const key = arg.slice(2).replace(/-/g, '_');
    const next = argv[i + 1];
    if (next == null || next.startsWith('--')) out[key] = true;
    else { out[key] = next; i += 1; }
  }
  return out;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function normalizeProviderIds(value) {
  if (Array.isArray(value)) return value.map(String).map((v) => v.trim()).filter(Boolean);
  return String(value || '').split(',').map((v) => v.trim()).filter(Boolean);
}

function normalizeProviderId(value) {
  return String(value || '').trim().toLowerCase();
}

async function mapLimit(values, requestedLimit, worker) {
  const input = Array.from(values || []);
  const limit = Math.max(1, Math.min(Number(requestedLimit || 1), input.length || 1));
  const output = new Array(input.length);
  let cursor = 0;
  async function runNext() {
    while (cursor < input.length) {
      const index = cursor;
      cursor += 1;
      output[index] = await worker(input[index], index);
    }
  }
  await Promise.all(Array.from({ length: limit }, () => runNext()));
  return output;
}

function resolveProvider(manifest, providerId) {
  const needle = String(providerId || '').trim().toLowerCase();
  if (!needle) throw new Error('empty provider id');
  const rows = Array.isArray(manifest?.scrapers) ? manifest.scrapers : [];
  const row = rows.find((item) => [item?.id, item?.name]
    .filter(Boolean)
    .some((value) => String(value).trim().toLowerCase() === needle));
  if (!row) throw new Error(`provider not found in manifest: ${providerId}`);
  if (!row.filename) throw new Error(`provider has no filename: ${providerId}`);
  return row;
}

function sanitizeText(value, limit = 200) {
  return String(value == null ? '' : value)
    .replace(/(?:https?|magnet|acestream|torrent):[^\s"']+/gi, '[endpoint]')
    .replace(/[\r\n\t]+/g, ' ')
    .slice(0, limit);
}

function tailText(previous, chunk, limit) {
  const combined = String(previous || '') + String(chunk || '');
  return combined.length > limit ? combined.slice(combined.length - limit) : combined;
}

function safeHost(rawUrl) {
  try { return new URL(String(rawUrl || '')).hostname.toLowerCase(); } catch { return null; }
}

function streamFingerprint(stream) {
  return sha256(String(stream?.url || '')).slice(0, 16);
}

function summarizeStream(stream, index) {
  return {
    index,
    stream_id: streamFingerprint(stream),
    host: safeHost(stream?.url),
    name: sanitizeText(stream?.name, 120) || null,
    title: sanitizeText(stream?.title, 200) || null,
    quality: sanitizeText(stream?.quality, 80) || null,
    language: sanitizeText(stream?.language, 80) || null,
    header_names: Object.keys(stream?.headers || {}).map(String).sort(),
    subtitle_count: Array.isArray(stream?.subtitles) ? stream.subtitles.length : 0,
  };
}

function normalizeIdentity(value) {
  try {
    return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  } catch {
    return String(value ?? '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  }
}

function identityTokens(value) {
  const noise = new Set(['the', 'a', 'an', 'le', 'la', 'les', 'un', 'une', 'de', 'des', 'du', 'of', 'and', 'et', 'film', 'movie', 'stream', 'streaming', 'watch', 'play', 'player', 'server', 'serveur', 'source', 'mirror', 'direct', 'download', 'telecharger', 'file', 'video', 'quality', 'web', 'ep', 'episode', 'season', 'saison', 'sibnet', 'vidmoly', 'sendvid', 'uqload', 'streamzo', 'anime', 'sama', 'mugiwara', 'toflix', 'french', 'manga', 'vf', 'vff', 'vostfr', 'vo', 'english', 'truefrench', 'hd', 'uhd', 'fhd', 'sd']);
  return normalizeIdentity(value).split(/\s+/).filter((token) => token.length > 1 && !noise.has(token) && !/^\d{3,4}p$/.test(token) && !/^\d{4}$/.test(token));
}

function streamIdentity(stream, fixture) {
  const aliases = [fixture?.title, fixture?.label, ...(Array.isArray(fixture?.aliases) ? fixture.aliases : [])].filter(Boolean);
  const forbiddenAliases = (Array.isArray(fixture?.forbiddenAliases) ? fixture.forbiddenAliases : []).map(normalizeIdentity).filter(Boolean);
  const expected = aliases.map(normalizeIdentity).filter(Boolean);
  const expectedTokens = new Set(aliases.flatMap(identityTokens));
  const label = String(stream?.title || stream?.description || stream?.filename || stream?.name || '').trim();
  const normalized = normalizeIdentity(label);
  const mediaType = String(fixture?.mediaType || fixture?.type || 'movie').toLowerCase();
  const wantedSeason = Number(fixture?.season || 0);
  const wantedEpisode = Number(fixture?.episode || 0);
  const seasonEpisode = /(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(label)
    || /(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(label);
  const episodeOnly = /(?:^|\D)(?:episode|ep)\s*0*(\d{1,4})(?:\D|$)/i.exec(label);
  if (mediaType === 'movie' && seasonEpisode) return { status: 'contradiction', reason: 'movie_row_is_episode' };
  if (seasonEpisode && (mediaType === 'tv' || mediaType === 'anime')) {
    const season = Number(seasonEpisode[1] || 0);
    const episode = Number(seasonEpisode[2] || 0);
    if ((wantedSeason && season && season !== wantedSeason) || (wantedEpisode && episode && episode !== wantedEpisode)) {
      return { status: 'contradiction', reason: 'wrong_season_episode' };
    }
    return { status: 'match', reason: 'season_episode_match' };
  }
  if (episodeOnly && (mediaType === 'tv' || mediaType === 'anime')) {
    const episode = Number(episodeOnly[1] || 0);
    if (wantedEpisode && episode && episode !== wantedEpisode) return { status: 'contradiction', reason: 'wrong_episode' };
    if (wantedEpisode && episode === wantedEpisode) return { status: 'match', reason: 'episode_match' };
  }
  if (normalized && forbiddenAliases.some((alias) => normalized.includes(alias))) return { status: 'contradiction', reason: 'forbidden_title_alias' };
  if (normalized && expected.some((alias) => normalized.includes(alias))) return { status: 'match', reason: 'expected_title_alias' };
  const rowTokens = identityTokens(label);
  if (rowTokens.length >= 2 && expectedTokens.size) {
    const overlap = rowTokens.filter((token) => expectedTokens.has(token));
    if (overlap.length === 0) return { status: 'contradiction', reason: 'strong_title_mismatch' };
  }
  return { status: 'unknown', reason: 'insufficient_identity_metadata' };
}

function executionGroups(clientNames) {
  const groups = new Map();
  for (const clientName of clientNames) {
    const client = CLIENTS[clientName];
    if (!client) throw new Error(`unknown client profile: ${clientName}`);
    if (!groups.has(client.runtimeGroup)) groups.set(client.runtimeGroup, []);
    groups.get(client.runtimeGroup).push(clientName);
  }
  return [...groups.entries()].map(([runtimeGroup, clients]) => ({ runtimeGroup, clients }));
}

function verifyRuntimeContract(clientName, clientRoot) {
  const client = CLIENTS[clientName];
  const runtimePath = path.join(clientRoot, clientName, client.runtimeFile);
  if (!fs.existsSync(runtimePath)) {
    return { ok: false, reason: 'runtime_file_missing', runtime_path: runtimePath };
  }
  const source = fs.readFileSync(runtimePath, 'utf8');
  const supportPaths = (client.supportFiles || []).map((relative) => path.join(clientRoot, clientName, relative));
  const missingSupport = supportPaths.filter((supportPath) => !fs.existsSync(supportPath));
  const supportSource = supportPaths.filter((supportPath) => fs.existsSync(supportPath)).map((supportPath) => fs.readFileSync(supportPath, 'utf8')).join('\n');
  const combined = `${source}\n${supportSource}`;
  const positionalCall = /getStreams\s*\(\s*(?:args\.tmdbId|\$tmdbIdArg|tmdbIdArg)\s*,\s*(?:args\.mediaType|\$mediaTypeArg|mediaTypeArg)/.test(source)
    || /getStreams\s*\(\s*tmdbId\s*,\s*mediaType\s*,\s*season\s*,\s*episode\s*\)/.test(source);
  const timeout60s = /60_000L/.test(source) || /60_000/.test(source);
  const defaultUa = combined.includes(WINDOWS_UA);
  const fetchBridge = /__native_fetch/.test(combined);
  return {
    ok: positionalCall && timeout60s && defaultUa && fetchBridge && missingSupport.length === 0,
    positional_get_streams: positionalCall,
    timeout_60s: timeout60s,
    default_user_agent: defaultUa,
    native_fetch_bridge: fetchBridge,
    missing_support_files: missingSupport,
    sha256: sha256(source),
    support_sha256: supportSource ? sha256(supportSource) : null,
    runtime_path: runtimePath,
  };
}

function clientHead(clientName, clientRoot) {
  const headFile = path.join(clientRoot, clientName, '.nuvio-lab-head');
  if (!fs.existsSync(headFile)) return null;
  return fs.readFileSync(headFile, 'utf8').trim() || null;
}

function buildWorkerContext(runtimeGroup, fixture, config) {
  const clientName = runtimeGroup === 'tv' ? 'tv' : 'desktop';
  const client = CLIENTS[clientName];
  return {
    locale: config.locale || 'fr-FR',
    languages: config.languages || ['fr-FR', 'fr'],
    platform: client.platform,
    userAgent: WINDOWS_UA,
    injectAcceptLanguage: false,
    maxSettingsProfiles: Math.max(1, Math.min(Number(config.max_settings_profiles || 4), 8)),
    fixtureMetadata: fixture,
    settings: config.settings && typeof config.settings === 'object' ? config.settings : {},
    storage: {},
    networkLimits: {
      maxFetches: Math.max(1, Math.min(Number(config.max_fetches || 35), 60)),
      maxResponseBytes: Math.max(65536, Math.min(Number(config.max_response_bytes || 5 * 1024 * 1024), 8 * 1024 * 1024)),
      maxTotalResponseBytes: Math.max(262144, Math.min(Number(config.max_total_response_bytes || 20 * 1024 * 1024), 32 * 1024 * 1024)),
      maxDistinctHosts: Math.max(1, Math.min(Number(config.max_distinct_hosts || 20), 30)),
      maxRedirects: Math.max(1, Math.min(Number(config.max_redirects || 5), 8)),
    },
    clientRuntimeLab: {
      runtimeGroup,
      invocationContract: 'positional-compatible',
      upstreamClients: runtimeGroup === 'tv' ? ['nuvio-tv'] : ['nuvio-desktop', 'nuvio-mobile'],
    },
  };
}

function parseWorkerOutput(stdout) {
  const lines = String(stdout || '').split(/\r?\n/).filter(Boolean);
  const line = [...lines].reverse().find((value) => value.startsWith(HEALTH_PREFIX));
  if (!line) throw new Error('provider worker did not emit a health result');
  return JSON.parse(line.slice(HEALTH_PREFIX.length));
}

function runProviderWorker(root, providerPath, fixture, context, timeoutMs = DEFAULT_TIMEOUT_MS) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [
      path.join(root, 'scripts/provider_worker.cjs'),
      providerPath,
      JSON.stringify(fixture),
      JSON.stringify(context),
    ], {
      cwd: root,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env },
    });
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => child.kill('SIGKILL'), timeoutMs);
    child.stdout.on('data', (chunk) => { stdout = tailText(stdout, chunk.toString(), 8 * 1024 * 1024); });
    child.stderr.on('data', (chunk) => { stderr = tailText(stderr, chunk.toString(), 512 * 1024); });
    child.on('close', (code, signal) => {
      clearTimeout(timer);
      try {
        const result = parseWorkerOutput(stdout);
        resolve({ result, code, signal, stderr: sanitizeText(stderr, 1000) || null });
      } catch (error) {
        resolve({
          result: { ok: false, error: sanitizeText(error.message, 500), stream_count: 0, streams: [], network_observations: [] },
          code,
          signal,
          stderr: sanitizeText(stderr, 1000) || null,
        });
      }
    });
  });
}

async function probeStreams(root, streams, fixture, config) {
  const { guardedFetch } = require(path.join(root, 'scripts/network_guard.cjs'));
  const { probeDirectMedia } = require(path.join(root, 'scripts/direct_media_probe.cjs'));
  const maxStreams = Math.max(1, Math.min(Number(config.max_streams_per_runtime || 3), 6));
  const timeoutMs = Math.max(3000, Math.min(Number(config.playback_timeout_ms || DEFAULT_PLAYBACK_TIMEOUT_MS), 30_000));
  const selected = Array.isArray(streams) ? streams.slice(0, maxStreams) : [];
  const results = [];
  for (let index = 0; index < selected.length; index += 1) {
    const stream = selected[index];
    const started = Date.now();
    let probe;
    try {
      probe = await probeDirectMedia(stream, {
        guardedFetch,
        fetchImpl: globalThis.fetch,
        timeoutMs,
        maxRedirects: Math.max(1, Math.min(Number(config.max_redirects || 5), 8)),
      });
    } catch (error) {
      probe = { playable: false, inconclusive: true, kind: sanitizeText(error?.name || error?.message || error, 100), status: null, host: safeHost(stream?.url) };
    }
    results.push({
      ...summarizeStream(stream, index),
      identity: streamIdentity(stream, fixture),
      playable: Boolean(probe?.playable),
      inconclusive: Boolean(probe?.inconclusive),
      kind: sanitizeText(probe?.kind, 120) || null,
      status: Number.isInteger(probe?.status) ? probe.status : null,
      duration_ms: Date.now() - started,
      hls_master: probe?.hls_master ?? null,
      hls_variant_playable: probe?.hls_variant_playable ?? null,
      hls_segment_playable: probe?.hls_segment_playable ?? null,
      hls_audio_playable: probe?.hls_audio_playable ?? null,
    });
  }
  return results;
}

function classify(runtime, probes) {
  if (!runtime?.ok) return 'runtime_error';
  if (!Number(runtime.stream_count || 0)) return 'runtime_empty';
  if (probes.some((row) => row.playable && row.identity?.status === 'contradiction')) return 'wrong_content';
  if (probes.some((row) => row.playable)) return 'playable';
  if (probes.some((row) => row.inconclusive)) return 'playback_inconclusive';
  return 'media_unplayable';
}

function summarizePolicy(providers, clients, config = {}) {
  const requestedClients = Array.from(clients || []);
  const targetTotal = Math.max(1, Number(config.policy?.target_total || 10));
  const minimumVf = Math.max(1, Number(config.policy?.minimum_vf || 3));
  const requireIdentityMatch = config.policy?.require_identity_match === true;
  const qualified = (providers || []).filter((provider) => (
    provider.manifest_enabled
    && requestedClients.length > 0
    && requestedClients.every((clientName) => provider.clients?.[clientName]?.verdict === 'playable')
    && (!requireIdentityMatch || requestedClients.every((clientName) => provider.clients?.[clientName]?.identity_status === 'verified'))
  ));
  const verifiedTotal = qualified.length;
  const verifiedVf = qualified.filter((provider) => provider.is_vf).length;
  const identityVerified = qualified.filter((provider) => requestedClients.every((clientName) => provider.clients?.[clientName]?.identity_status === 'verified'));
  const totalTargetMet = verifiedTotal >= targetTotal;
  const vfMinimumMet = verifiedVf >= minimumVf;
  const objectiveMet = totalTargetMet && vfMinimumMet;
  return {
    target_total: targetTotal,
    minimum_vf: minimumVf,
    verified_total: verifiedTotal,
    verified_vf: verifiedVf,
    identity_verified_total: identityVerified.length,
    identity_verified_provider_ids: identityVerified.map((provider) => provider.id),
    total_target_met: totalTargetMet,
    vf_minimum_met: vfMinimumMet,
    objective_met: objectiveMet,
    advisory_only: config.policy?.blocking !== true,
    blocking_pass: config.policy?.blocking !== true || objectiveMet,
    require_identity_match: requireIdentityMatch,
    status: !vfMinimumMet ? 'vf_shortfall' : (totalTargetMet ? 'target_met' : 'vf_met_total_shortfall'),
    qualified_provider_ids: qualified.map((provider) => provider.id),
    qualified_vf_provider_ids: qualified.filter((provider) => provider.is_vf).map((provider) => provider.id),
    qualification: `enabled in manifest.json, playable on every requested Nuvio client profile${requireIdentityMatch ? ', and carrying positive work identity evidence' : ''}`,
  };
}

function summarizeNetwork(rows) {
  const input = Array.isArray(rows) ? rows : [];
  return input.slice(0, 80).map((row) => ({
    stage: sanitizeText(row?.stage, 80) || null,
    host: sanitizeText(row?.host, 160) || null,
    method: sanitizeText(row?.method, 20) || null,
    path_pattern: sanitizeText(row?.path_pattern, 180) || null,
    status: Number.isInteger(row?.status) ? row.status : null,
    ok: Boolean(row?.ok),
    duration_ms: Number(row?.duration_ms || 0),
    error_code: sanitizeText(row?.error_code, 100) || null,
    error: sanitizeText(row?.error, 200) || null,
  }));
}

function markdown(report) {
  const lines = [
    '# Nuvio client lab',
    '',
    `Fixture: **${sanitizeText(report.fixture.title || report.fixture.tmdbId, 120)}** (${report.fixture.mediaType}, TMDb ${report.fixture.tmdbId})`,
    '',
    '## 10 total / 3 VF coverage',
    '',
    '| Metric | Verified | Rule | Met |',
    '|---|---:|---:|---|',
    `| Total providers | ${report.policy.verified_total} | target ${report.policy.target_total} | ${report.policy.total_target_met ? 'yes' : 'no'} |`,
    `| VF providers | ${report.policy.verified_vf} | minimum ${report.policy.minimum_vf} | ${report.policy.vf_minimum_met ? 'yes' : 'no'} |`,
    `| Explicit work identity | ${report.policy.identity_verified_total} | diagnostic only | n/a |`,
    '',
    `Coverage status: **${report.policy.status}**. Both thresholds are advisory objectives; a shortfall never invalidates the work or the lab run.`,
    '',
    `A provider is counted only when it is ${report.policy.qualification}.`,
    '',
    '| Provider | VF | Counted | Client | Identity | Runtime streams | Playable probes | Verdict |',
    '|---|---:|---:|---:|---|---:|---:|---|',
  ];
  for (const provider of report.providers) {
    const counted = report.policy.qualified_provider_ids.includes(provider.id);
    for (const clientName of report.clients) {
      const row = provider.clients[clientName];
      lines.push(`| ${provider.id} | ${provider.is_vf ? 'yes' : 'no'} | ${counted ? 'yes' : 'no'} | ${clientName} | ${row.identity_status} | ${row.runtime_stream_count} | ${row.playable_probe_count}/${row.probes.length} | **${row.verdict}** |`);
    }
  }
  lines.push('', '## Client contracts', '');
  for (const clientName of report.clients) {
    const c = report.client_contracts[clientName];
    lines.push(`- ${clientName}: ${c.ok ? 'OK' : 'DRIFT'}${c.head ? ` @ ${c.head.slice(0, 12)}` : ''}`);
  }
  lines.push('', '> Stream URLs and header values are intentionally not written to the report; only hosts, URL fingerprints, status codes and media proof are retained.');
  return `${lines.join('\n')}\n`;
}

async function runLab(root, config, options = {}) {
  const manifestPath = path.resolve(root, config.manifest || 'manifest.json');
  const manifest = readJson(manifestPath);
  const fixture = {
    tmdbId: String(config.fixture?.tmdbId || config.tmdbId || ''),
    mediaType: String(config.fixture?.mediaType || config.mediaType || 'movie'),
    title: config.fixture?.title || config.title || null,
    year: config.fixture?.year ?? config.year ?? null,
    label: config.fixture?.label || null,
    category: config.fixture?.category || config.fixture?.mediaType || config.mediaType || 'movie',
    season: config.fixture?.season ?? config.season ?? null,
    episode: config.fixture?.episode ?? config.episode ?? null,
  };
  if (!fixture.tmdbId) throw new Error('fixture.tmdbId is required');

  const providerIds = normalizeProviderIds(config.providers || config.provider_ids || config.provider_id);
  if (!providerIds.length) throw new Error('at least one provider id is required');
  const clients = normalizeProviderIds(config.clients || ['tv', 'desktop', 'mobile']);
  for (const clientName of clients) if (!CLIENTS[clientName]) throw new Error(`unknown client profile: ${clientName}`);

  const clientsRoot = path.resolve(root, options.clientsRoot || config.clients_root || '.nuvio-client-lab/clients');
  const clientContracts = {};
  for (const clientName of clients) {
    const verification = verifyRuntimeContract(clientName, clientsRoot);
    clientContracts[clientName] = { ...verification, head: clientHead(clientName, clientsRoot) };
  }
  if ((options.requireClientSources || config.require_client_sources) && Object.values(clientContracts).some((row) => !row.ok)) {
    const failed = Object.entries(clientContracts).filter(([, row]) => !row.ok).map(([name]) => name).join(', ');
    throw new Error(`Nuvio client runtime contract verification failed: ${failed}`);
  }

  const runtimeGroups = executionGroups(clients);
  const vfManifestPath = path.resolve(root, config.vf_manifest || 'vf/manifest.json');
  const vfProviderIds = fs.existsSync(vfManifestPath)
    ? new Set((readJson(vfManifestPath).scrapers || [])
      .filter((row) => row.enabled !== false)
      .map((row) => normalizeProviderId(row.id || row.name)))
    : new Set();
  const providers = await mapLimit(providerIds, config.provider_concurrency || 4, async (providerId) => {
    const manifestRow = resolveProvider(manifest, providerId);
    const providerPath = path.resolve(root, manifestRow.filename);
    if (!fs.existsSync(providerPath)) throw new Error(`provider file missing: ${manifestRow.filename}`);
    const providerRecord = {
      id: String(manifestRow.id || providerId),
      name: String(manifestRow.name || manifestRow.id || providerId),
      filename: manifestRow.filename,
      manifest_enabled: manifestRow.enabled !== false,
      is_vf: vfProviderIds.has(normalizeProviderId(manifestRow.id || manifestRow.name || providerId)),
      source_sha256: sha256(fs.readFileSync(providerPath)),
      runtime_groups: {},
      clients: {},
    };

    for (const group of runtimeGroups) {
      const context = buildWorkerContext(group.runtimeGroup, fixture, config);
      const worker = await runProviderWorker(root, providerPath, fixture, context, Number(config.provider_timeout_ms || DEFAULT_TIMEOUT_MS));
      const runtime = worker.result || {};
      const probes = await probeStreams(root, runtime.streams || [], fixture, config);
      providerRecord.runtime_groups[group.runtimeGroup] = {
        ok: Boolean(runtime.ok),
        worker_exit_code: worker.code ?? null,
        worker_signal: worker.signal ?? null,
        duration_ms: Number(runtime.duration_ms || 0),
        stream_count: Number(runtime.stream_count || 0),
        provider_server_accessible: Boolean(runtime.provider_server_accessible),
        provider_server_successful_response: Boolean(runtime.provider_server_successful_response),
        provider_server_hosts: Array.isArray(runtime.provider_server_hosts) ? runtime.provider_server_hosts : [],
        provider_server_http_statuses: Array.isArray(runtime.provider_server_http_statuses) ? runtime.provider_server_http_statuses : [],
        network_observations: summarizeNetwork(runtime.network_observations),
        error: sanitizeText(runtime.error, 500) || null,
        stderr: worker.stderr,
        probes,
      };
      for (const clientName of group.clients) {
        providerRecord.clients[clientName] = {
          runtime_group: group.runtimeGroup,
          runtime_ok: Boolean(runtime.ok),
          runtime_stream_count: Number(runtime.stream_count || 0),
          playable_probe_count: probes.filter((row) => row.playable).length,
          inconclusive_probe_count: probes.filter((row) => row.inconclusive).length,
          identity_match_count: probes.filter((row) => row.playable && row.identity?.status === 'match').length,
          identity_contradiction_count: probes.filter((row) => row.playable && row.identity?.status === 'contradiction').length,
          identity_status: probes.some((row) => row.playable && row.identity?.status === 'contradiction')
            ? 'contradiction'
            : (probes.some((row) => row.playable && row.identity?.status === 'match') ? 'verified' : 'unknown'),
          verdict: classify(runtime, probes),
          probes,
        };
      }
    }
    return providerRecord;
  });

  const policy = summarizePolicy(providers, clients, config);

  return {
    schema_version: 2,
    generated_at: new Date().toISOString(),
    host: { platform: os.platform(), node: process.version },
    fixture,
    clients,
    client_contracts: clientContracts,
    policy,
    providers,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const root = path.resolve(args.root || process.cwd());
  let config;
  if (args.config) config = readJson(path.resolve(root, args.config));
  else {
    config = {
      providers: args.providers || args.provider_id,
      fixture: {
        tmdbId: args.tmdb_id,
        mediaType: args.media_type || 'movie',
        title: args.title || null,
        year: args.year ? Number(args.year) : null,
        season: args.season ? Number(args.season) : null,
        episode: args.episode ? Number(args.episode) : null,
      },
      clients: args.clients ? normalizeProviderIds(args.clients) : ['tv', 'desktop', 'mobile'],
      max_streams_per_runtime: args.max_streams ? Number(args.max_streams) : undefined,
    };
  }
  const report = await runLab(root, config, {
    clientsRoot: args.clients_root,
    requireClientSources: Boolean(args.require_client_sources),
  });
  const outPath = path.resolve(root, args.out || config.out || '.nuvio-client-lab/report.json');
  const mdPath = path.resolve(root, args.markdown || config.markdown || '.nuvio-client-lab/report.md');
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.mkdirSync(path.dirname(mdPath), { recursive: true });
  fs.writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
  fs.writeFileSync(mdPath, markdown(report));
  process.stdout.write(markdown(report));
  if (config.enforce_policy && !report.policy.blocking_pass) process.exitCode = 2;
}

module.exports = {
  CLIENTS,
  WINDOWS_UA,
  buildWorkerContext,
  classify,
  executionGroups,
  mapLimit,
  markdown,
  normalizeProviderIds,
  parseArgs,
  parseWorkerOutput,
  resolveProvider,
  safeHost,
  sanitizeText,
  streamFingerprint,
  streamIdentity,
  summarizePolicy,
  summarizeStream,
  tailText,
  verifyRuntimeContract,
};

if (require.main === module) {
  main().catch((error) => {
    process.stderr.write(`nuvio client lab failed: ${sanitizeText(error?.stack || error?.message || error, 2000)}\n`);
    process.exitCode = 1;
  });
}
