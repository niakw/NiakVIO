#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
import { BRAIN_CONTROL_PLANE_VERSION, planRepair } from '../src/repair-brain.mjs';
import { classifySystemicExtraction, extractionExecutionKey } from '../src/runtime-systemic.mjs';

const require = createRequire(import.meta.url);
const {
  readerFailureClass,
  readerFailureDomain,
  providerMutationEligible,
  readerSignature,
  isReaderFailure,
} = require('../../scripts/native_player_diagnostics.cjs');
const { assessNativeEvidence } = require('../../scripts/native_evidence_completeness.cjs');

const args = process.argv.slice(2);
const outputIndex = args.indexOf('--output');
const outputPath = outputIndex >= 0 && args[outputIndex + 1]
  ? path.resolve(args[outputIndex + 1])
  : path.resolve('targeted-reader-brain.json');
const clientShaIndex = args.indexOf('--official-client-sha');
const clientShaValue = clientShaIndex >= 0 ? args[clientShaIndex + 1] : '';
if (clientShaIndex >= 0 && !/^[0-9a-f]{40}$/.test(String(clientShaValue || ''))) {
  throw new Error('official native client SHA must be a complete lower-case commit hash');
}
const officialClientSha = clientShaIndex >= 0 ? clientShaValue : '';
const logPaths = args.filter((value, index) => (
  index !== outputIndex && index !== outputIndex + 1 && value !== '--output'
  && (clientShaIndex < 0 || (index !== clientShaIndex && index !== clientShaIndex + 1))
  && value !== '--official-client-sha'
)).map((value) => path.resolve(value));
const nonblockingSmoke = process.env.NIAKVIO_BRAIN_NONBLOCKING === '1';
const RUNTIME_ERROR_SENTINEL = '__NIAKVIO_RUNTIME_ERROR__';

function decode(value) {
  if (!value) return '';
  let text = String(value).replace(/-/g, '+').replace(/_/g, '/');
  while (text.length % 4) text += '=';
  try { return Buffer.from(text, 'base64').toString('utf8'); } catch { return ''; }
}
function fields(line) {
  const out = {};
  const re = /([A-Za-z0-9_]+)=([^\s]+)/g;
  let match;
  while ((match = re.exec(line)) !== null) out[match[1]] = match[2];
  return out;
}
function safeText(value, max = 420) {
  return String(value || '')
    .replace(/https?:\/\/\S+/gi, '<url>')
    .replace(/(?:(?:authorization|cookie|token|secret)\s*[:=]\s*)\S+/gi, 'credential=<redacted>')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}
function providerLoadFailureClass(reason) {
  const value = String(reason || '').trim().toLowerCase();
  if (value === 'missing_after_repository_install') return 'provider_repository_load_missing';
  if (value === 'metadata_mismatch' || value === 'metadata_or_code_mismatch') return 'provider_repository_metadata_mismatch';
  return 'provider_repository_load_error';
}
function providerLoadRepair(issue) {
  if (issue.failureClass === 'provider_repository_load_missing') {
    return {
      layer: 'repository',
      providerJsMutationAllowed: false,
      coreOrManifestProposalAllowed: true,
      actions: [
        'verify the provider filename is reachable from the exact pinned manifest SHA',
        'compare the official client platform filter and provider id reconstruction',
        'verify Nuvio downloaded and cached the provider code',
        'repair repository/Core loading before touching provider JS',
        're-run the same official repository installation on the affected device',
      ],
    };
  }
  if (issue.failureClass === 'provider_repository_metadata_mismatch') {
    return {
      layer: 'manifest_contract',
      providerJsMutationAllowed: false,
      coreOrManifestProposalAllowed: true,
      actions: [
        'diff canonical manifest enabled/types against the model reconstructed by Nuvio',
        'inspect manifest parser normalization and cached provider reconstruction',
        'repair manifest/Core adapter semantics instead of provider stream logic',
        're-run cross-device repository loading before publication',
      ],
    };
  }
  return {
    layer: 'repository',
    providerJsMutationAllowed: false,
    coreOrManifestProposalAllowed: true,
    actions: [
      'inspect the first observed repository/provider loading failure',
      'verify manifest download, provider download and cache reconstruction independently',
      'repair the loading layer before provider JS mutation',
      're-run official repository loading on the same device',
    ],
  };
}
function routeKey(row) {
  return `${String(row.provider || '').toLowerCase()}\u0000${row.requestType}\u0000${row.fixture}`;
}
function extractionSignature(row) {
  return `${row.requestType}:media_extraction_gap:${String(row.provider || '').toLowerCase()}:${row.fixture}`;
}
function runtimeExecutionKey(row) {
  return [
    String(row.client || 'unknown').trim().toLowerCase(),
    String(row.fixture || 'unknown'),
    String(row.provider || '').trim().toLowerCase(),
    String(row.requestType || 'unknown').trim().toLowerCase(),
  ].join('\u0000');
}

function mediaProbeKey(row) {
  return [
    Number.isInteger(Number(row.sourceLogIndex)) ? Number(row.sourceLogIndex) : -1,
    String(row.client || 'unknown').trim().toLowerCase(),
    String(row.fixture || 'unknown').trim().toLowerCase(),
    String(row.provider || '').trim().toLowerCase(),
    String(row.requestType || 'unknown').trim().toLowerCase(),
    Number(row.index || 0),
  ].join('\u0000');
}

const evidence = assessNativeEvidence(logPaths);
const readerRows = [];
const resultRows = [];
const providerLoadObservations = [];
const appSelectionObservations = [];
const quickJsDiagnostics = [];
const quickJsPromiseControls = [];
const nativeExecutionDiagnostics = [];
const terminalTransportDiagnostics = [];
const prePlayerMediaRootTransitions = [];
const prePlayerFetchHostOutcomes = [];
const transportTopologyByMedia = new Map();
const TERMINAL_TRANSPORT_KINDS = new Set(['hls', 'dash', 'video', 'html', 'unknown']);
const TERMINAL_TRANSPORT_STATES = new Set(['dead', 'error']);

const PROMISE_CONTROL_STATUSES = new Set(['bridge_ok', 'promise_delivery_gap', 'baseline_failed']);
const QUICKJS_PHASES = new Set(['call', 'result', 'error', 'missing_export']);
const QUICKJS_ERROR_CATEGORIES = new Set([
  'none', 'reference_error', 'type_error', 'syntax_error', 'timeout',
  'network_error', 'http_error', 'unspecified_js_exception',
]);
const APP_SELECTION_REASONS = new Set([
  'plugins_globally_disabled', 'scraper_disabled_locally',
  'unsupported_media_type', 'not_selected_by_app',
]);
const runtimeSentinelByKey = new Map();
for (const [sourceLogIndex, file] of logPaths.entries()) {
  if (!fs.existsSync(file)) continue;
  // Raw signed URLs exist only in this process-local map. The emitted report
  // retains no URL/host/token, only a route-bound transition classification.
  let activeProviderRoute = null;
  // Ephemeral, route-scoped fact: a native provider received an HLS playlist
  // before returning zero. Never export the signed URL or infer the owner here.
  let hlsPlaylist2xxDuringRoute = false;
  let prePlayerFetchSequence = 0;
  const mediaRootStatuses = new Map();
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const beginAt = raw.indexOf('FIELD_NATIVE_PROVIDER_BEGIN ');
    if (beginAt >= 0) {
      const b = fields(raw.slice(beginAt).trim());
      const provider = decode(b.provider64).trim().toLowerCase();
      const fixture = String(b.fixture || '').trim().toLowerCase();
      const requestType = String(b.request_type || '').trim().toLowerCase();
      hlsPlaylist2xxDuringRoute = false;
      prePlayerFetchSequence = 0;
      activeProviderRoute = (
        b.client === 'tv'
        && /^[a-z0-9][a-z0-9_-]{0,95}$/.test(provider)
        && /^[a-z0-9][a-z0-9-]{0,95}$/.test(fixture)
        && ['movie', 'tv', 'anime'].includes(requestType)
      ) ? {client: 'tv', provider, fixture, requestType} : null;
    }

    if (activeProviderRoute) {
      // Preserve the HTTP reason phrase emitted by official PluginRuntime (200 OK / 403 Forbidden).
      // Former code only parsed status+url and silently lost real native causal evidence.
      const match = /Fetch result:\s*([0-9]{3})(?:\s+[A-Za-z-]+){0,3}\s+url=(\S+)/.exec(raw);
      if (match) {
        const status = Number(match[1]);
        const url = String(match[2] || '');
        prePlayerFetchSequence += 1;
        let parsedUrl = null;
        try {
          parsedUrl = new URL(url);
        } catch (_) {
          parsedUrl = null;
        }
        if (parsedUrl && Number.isInteger(status) && status >= 200 && status <= 599) {
          const rawHost = String(parsedUrl.hostname || '').trim().toLowerCase();
          const pathname = String(parsedUrl.pathname || '/');
          const kind = /\.m3u8$/i.test(pathname)
            ? 'hls'
            : /(?:\/embed(?:[-/]|$)|\/e\/[^/]+)/i.test(pathname)
              ? 'player-page'
              : '';
          const host = kind === 'player-page' ? rawHost : '';
          const hostSafe = kind === 'hls'
            || /^(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/.test(host);
          const routeKey = runtimeExecutionKey(activeProviderRoute);
          if (
            kind && hostSafe
            && prePlayerFetchHostOutcomes.filter((row) =>
              runtimeExecutionKey(row) === routeKey).length < 12
          ) {
            prePlayerFetchHostOutcomes.push({
              ...activeProviderRoute,
              source: 'plugin-runtime-fetch-sequence',
              phase: 'provider-runtime-pre-player',
              kind,
              sequence: Math.min(999, prePlayerFetchSequence),
              host,
              httpStatus: status,
              proofAuthority: false, publicationAuthority: false,
              nativePlaybackAuthority: false, providerJsMutationAllowed: false,
            });
          }
        }
        if (/\.m3u8(?:[?#]|$)/i.test(url) && Number.isInteger(status)) {
          if (status >= 200 && status < 300) hlsPlaylist2xxDuringRoute = true;
          const route = runtimeExecutionKey(activeProviderRoute);
          const key = route + '\u0000' + url;
          const previous = mediaRootStatuses.get(key) || [];
          if (
            status === 403
            && previous.some((value) => value >= 200 && value < 300)
            && !prePlayerMediaRootTransitions.some((row) =>
              runtimeExecutionKey(row) === route
              && row.pattern === 'same_media_root_2xx_then_403')
          ) {
            prePlayerMediaRootTransitions.push({
              ...activeProviderRoute,
              source: 'plugin-runtime-fetch-sequence',
              kind: 'hls',
              pattern: 'same_media_root_2xx_then_403',
              phase: 'provider-runtime-pre-player',
              proofAuthority: false, publicationAuthority: false,
              nativePlaybackAuthority: false, providerJsMutationAllowed: false,
            });
          }
          previous.push(status);
          mediaRootStatuses.set(key, previous.slice(-4));
        }
      }
    }
    const loadAt = raw.indexOf('FIELD_NATIVE_PROVIDER_LOAD_ERROR ');
    if (loadAt >= 0) {
      const f = fields(raw.slice(loadAt).trim());
      const reason = safeText(f.reason || decode(f.error64) || 'unknown', 240);
      const failureClass = providerLoadFailureClass(reason);
      providerLoadObservations.push({
        client: f.client || 'unknown',
        fixture: f.fixture || 'unknown',
        provider: decode(f.provider64).toLowerCase(),
        reason,
        failureClass,
      });
    }

    // This is the official PluginManager.enabledScrapers + supportsType gate,
    // not a provider extraction failure. Whitelist every field; never persist
    // arbitrary log content, credentials, URLs, or invented success authority.
    const selectionAt = raw.indexOf('FIELD_NATIVE_PROVIDER_APP_SELECTION ');
    if (selectionAt >= 0) {
      const f = fields(raw.slice(selectionAt).trim());
      const provider = decode(f.provider64).trim().toLowerCase();
      const requestType = String(f.request_type || '').trim().toLowerCase();
      const fixture = String(f.fixture || '').trim();
      const eligible = f.eligible === 'true';
      const reason = eligible ? 'selected' : String(f.reason || '');
      if (
        f.client === 'tv'
        && /^[a-z0-9][a-z0-9_-]{0,95}$/.test(provider)
        && /^[a-z0-9][a-z0-9-]{0,95}$/.test(fixture)
        && ['movie', 'tv', 'anime'].includes(requestType)
        && (eligible || APP_SELECTION_REASONS.has(reason))
      ) {
        appSelectionObservations.push({
          client: 'tv', fixture, provider, requestType,
          eligible,
          reason,
          pluginsEnabled: f.plugins_enabled === 'true' ? true
            : f.plugins_enabled === 'false' ? false : null,
          runtimeEnabled: f.runtime_enabled === 'true' ? true
            : f.runtime_enabled === 'false' ? false : null,
          manifestEnabled: f.manifest_enabled === 'true' ? true
            : f.manifest_enabled === 'false' ? false : null,
          supportedType: f.supported_type === 'true' ? true
            : f.supported_type === 'false' ? false : null,
          proofAuthority: false, publicationAuthority: false,
          providerJsMutationAllowed: false,
        });
      }
    }

    const quickAt = raw.indexOf('FIELD_NATIVE_QUICKJS_DIAGNOSTIC ');
    if (quickAt >= 0) {
      const f = fields(raw.slice(quickAt).trim());
      const provider = decode(f.provider64).trim().toLowerCase();
      const phase = String(f.phase || '');
      const category = String(f.category || '');
      const requestType = String(f.request_type || '');
      const fixture = String(f.fixture || '');
      if (
        ['tv', 'mobile', 'desktop'].includes(f.client)
        && /^[a-z0-9][a-z0-9_-]{0,95}$/.test(provider)
        && /^[a-z0-9][a-z0-9-]{0,95}$/.test(fixture)
        && QUICKJS_PHASES.has(phase)
        && QUICKJS_ERROR_CATEGORIES.has(category)
        && ['unknown', 'movie', 'tv', 'anime'].includes(requestType)
        && /^\d{1,3}$/.test(String(f.count || ''))
      ) {
        quickJsDiagnostics.push({
          client: f.client, provider, fixture, phase, category,
          requestType, count: Math.min(100, Number(f.count)),
          proofAuthority: false, publicationAuthority: false,
          nativePlaybackAuthority: false, providerJsMutationAllowed: false,
        });
      }
    }

    const promiseAt = raw.indexOf('FIELD_NATIVE_TV_PROMISE_CONTROL ');
    if (promiseAt >= 0) {
      const f = fields(raw.slice(promiseAt).trim());
      const sync = Number(f.sync_count);
      const awaited = Number(f.async_count);
      const fixture = String(f.fixture || '');
      if (f.client === 'tv' && f.test_only === 'true'
          && f.provider_media === 'false' && f.proof_authority === 'false'
          && /^[a-z0-9][a-z0-9-]{0,95}$/.test(fixture)
          && /^-?[0-9]{1,2}$/.test(String(f.sync_count || ''))
          && /^-?[0-9]{1,2}$/.test(String(f.async_count || ''))
          && sync >= -1 && sync <= 8 && awaited >= -1 && awaited <= 8) {
        const status = sync !== 1 ? 'baseline_failed'
          : awaited !== 1 ? 'promise_delivery_gap' : 'bridge_ok';
        if (PROMISE_CONTROL_STATUSES.has(status)) {
          quickJsPromiseControls.push({
            client: 'tv', fixture, status,
            proofAuthority: false, publicationAuthority: false,
            nativePlaybackAuthority: false, providerJsMutationAllowed: false,
          });
        }
      }
    }

    const executionErrorAt = raw.indexOf('FIELD_NATIVE_ERROR ');
    if (executionErrorAt >= 0) {
      const f = fields(raw.slice(executionErrorAt).trim());
      const provider = decode(f.provider64).trim().toLowerCase();
      const errorText = decode(f.error64).trim();
      const fixture = String(f.fixture || '');
      const requestType = String(f.request_type || '').toLowerCase();
      const duration = Number(f.duration_ms);
      const hardTimeout = /^provider_hard_timeout_ms=([0-9]{1,6})$/.exec(errorText);
      if (f.client === 'tv'
          && /^[a-z0-9][a-z0-9_-]{0,95}$/.test(provider)
          && /^[a-z0-9][a-z0-9-]{0,95}$/.test(fixture)
          && ['movie', 'tv', 'anime'].includes(requestType)
          && f.route_mode === 'declared'
          && hardTimeout && Number(hardTimeout[1]) >= 1000
          && Number(hardTimeout[1]) <= 180000
          && Number.isFinite(duration) && duration >= 1000
          && duration <= 180000) {
        nativeExecutionDiagnostics.push({
          client: 'tv', provider, fixture, requestType,
          failureClass: 'provider_hard_timeout',
          observedDurationMs: Math.floor(duration),
          configuredTimeoutMs: Number(hardTimeout[1]),
          proofAuthority: false, publicationAuthority: false,
          nativePlaybackAuthority: false, providerJsMutationAllowed: false,
        });
      }
      // Any provider execution error terminates pre-player sequence authority.
      activeProviderRoute = null;
    }

    const resultAt = raw.indexOf('FIELD_NATIVE_RESULT ');
    if (resultAt >= 0) {
      const f = fields(raw.slice(resultAt).trim());
      const returnedCount = Math.max(0, Number(f.count ?? f.returned ?? 0) || 0);
      const elapsedMs = Number(f.duration_ms);
      // This signal is intentionally only a temporal correlation. A 2xx HLS
      // reply plus a completed 0-stream result near a common 25s JS budget
      // calls for Core/ProviderBase/runtime discrimination, not a provider
      // mutation or a decoded-playback claim.
      if (
        activeProviderRoute && hlsPlaylist2xxDuringRoute
        && f.client === 'tv' && f.route_mode === 'declared'
        && f.enabled === 'true' && returnedCount === 0
        && Number.isFinite(elapsedMs) && elapsedMs >= 24000 && elapsedMs <= 32000
        && decode(f.provider64).trim().toLowerCase() === activeProviderRoute.provider
        && String(f.fixture || '').trim().toLowerCase() === activeProviderRoute.fixture
        && String(f.request_type || '').trim().toLowerCase() === activeProviderRoute.requestType
      ) {
        prePlayerMediaRootTransitions.push({
          ...activeProviderRoute,
          source: 'plugin-runtime-fetch-sequence',
          kind: 'hls',
          pattern: 'hls_playlist_2xx_near_25s_zero_preplayer',
          phase: 'provider-runtime-pre-player',
          proofAuthority: false, publicationAuthority: false,
          nativePlaybackAuthority: false, providerJsMutationAllowed: false,
        });
      }
      resultRows.push({
        client: f.client || 'unknown',
        fixture: f.fixture || 'unknown',
        provider: decode(f.provider64),
        requestType: String(f.request_type || 'unknown').toLowerCase(),
        routeMode: String(f.route_mode || 'declared').toLowerCase(),
        enabled: f.enabled === 'true',
        count: returnedCount,
      });
      activeProviderRoute = null;
    }

    // Network probe is independent of the official player. Never claim that
    // its status is a decoded playback failure, but preserve terminal HTTP
    // errors as a source/run-bounded diagnosis (no media URL, host or headers).
    const transportAt = raw.indexOf('FIELD_NATIVE_TRANSPORT ');
    if (transportAt >= 0) {
      const t = fields(raw.slice(transportAt).trim());
      const provider = decode(t.provider64).trim().toLowerCase();
      const fixture = String(t.fixture || '').trim().toLowerCase();
      const requestType = String(t.request_type || '').trim().toLowerCase();
      const status = Number(t.status);
      const index = Number(t.index);
      const state = String(t.state || '');
      const kind = String(t.kind || '');
      if (
        ['tv', 'mobile', 'desktop'].includes(String(t.client || '').toLowerCase())
        && provider && fixture && ['movie', 'tv', 'anime'].includes(requestType)
        && Number.isInteger(index) && index >= 0 && index <= 40
      ) {
        transportTopologyByMedia.set(mediaProbeKey({
          sourceLogIndex, client: t.client, fixture, provider, requestType, index,
        }), {
          transportAudioTrackCount: Number.isFinite(Number(t.audio_track_count)) ? Number(t.audio_track_count) : -1,
          transportAudioTrackLanguages: decode(t.audio_track_languages64),
          transportSubtitleTrackCount: Number.isFinite(Number(t.subtitle_track_count)) ? Number(t.subtitle_track_count) : -1,
          transportSubtitleTrackLanguages: decode(t.subtitle_track_languages64),
        });
      }
      if (t.client === 'tv' && t.route_mode === 'declared'
          && /^[a-z0-9][a-z0-9_-]{0,95}$/.test(provider)
          && /^[a-z0-9][a-z0-9-]{0,95}$/.test(fixture)
          && ['movie', 'tv', 'anime'].includes(requestType)
          && TERMINAL_TRANSPORT_STATES.has(state)
          && TERMINAL_TRANSPORT_KINDS.has(kind)
          && Number.isInteger(index) && index >= 0 && index <= 40
          && Number.isInteger(status) && status >= 400 && status <= 599) {
        terminalTransportDiagnostics.push({
          client: 'tv', fixture, provider, requestType, index,
          source: 'independent-terminal-transport-probe',
          state, kind, httpStatus: status,
          proofAuthority: false, publicationAuthority: false,
          nativePlaybackAuthority: false, providerJsMutationAllowed: false,
        });
      }
    }

    const rowAt = raw.indexOf('FIELD_NATIVE_ROW ');
  if (rowAt >= 0) {
    const f = fields(raw.slice(rowAt).trim());
    const type = decode(f.type64);
    const title = decode(f.title64);
    if (type === RUNTIME_ERROR_SENTINEL || title === RUNTIME_ERROR_SENTINEL) {
      const observation = {
        client: f.client || 'unknown',
        fixture: f.fixture || 'unknown',
        provider: decode(f.provider64),
        requestType: String(f.request_type || 'unknown').toLowerCase(),
        routeMode: String(f.route_mode || 'declared').toLowerCase(),
        index: Number(f.index || 0),
        state: 'runtime_error',
        failureClass: 'client_runtime_error',
        failureDomain: 'client_runtime',
        providerMutationEligible: false,
        failureStage: 'provider_runtime',
        httpStatus: 0,
        errorCode: 'RUNTIME_ERROR_SENTINEL',
        host: '',
        durationSeconds: null,
        loadBytes: 0,
        loadDurationMs: 0,
        observationLayer: 'runtime',
      };
      runtimeSentinelByKey.set(runtimeExecutionKey(observation), observation);
    }
  }

    const marker = raw.indexOf('FIELD_NATIVE_PLAYER ');
    if (marker < 0) continue;
    const f = fields(raw.slice(marker).trim());
    const row = {
      sourceLogIndex,
      client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider: decode(f.provider64),
      requestType: String(f.request_type || 'unknown').toLowerCase(),
      routeMode: String(f.route_mode || 'declared').toLowerCase(),
      index: Number(f.index || 0), state: f.state || 'unknown', engine: f.engine || 'unknown',
      httpStatus: Number(f.http_status || 0), failureStage: f.failure_stage || 'unknown',
      durationSeconds: Number(f.duration_seconds || 0) || null, host: decode(f.host64),
      errorClass: safeText(decode(f.error_class64), 180), errorCode: safeText(decode(f.error_code64), 120),
      exceptionChain: safeText(decode(f.exception_chain64), 800), responseHeaderNames: safeText(decode(f.response_header_names64), 360),
      loadBytes: Math.max(0, Number(f.load_bytes || 0) || 0),
      loadDurationMs: Math.max(0, Number(f.load_duration_ms || 0) || 0),
      mediaDataType: Number.isFinite(Number(f.media_data_type)) ? Number(f.media_data_type) : -1,
      trackType: Number.isFinite(Number(f.track_type)) ? Number(f.track_type) : -1,
      videoWidth: Number.isInteger(Number(f.video_width)) && Number(f.video_width) > 0
        ? Math.min(16384, Number(f.video_width)) : 0,
      videoHeight: Number.isInteger(Number(f.video_height)) && Number(f.video_height) > 0
        ? Math.min(16384, Number(f.video_height)) : 0,
      audioTrackCount: Number.isInteger(Number(f.audio_track_count))
        ? Math.min(64, Math.max(-1, Number(f.audio_track_count))) : -1,
      audioTrackLanguages: decode(f.audio_track_languages64),
      subtitleTrackCount: Number.isInteger(Number(f.subtitle_track_count))
        ? Math.min(64, Math.max(-1, Number(f.subtitle_track_count))) : -1,
      subtitleTrackLanguages: decode(f.subtitle_track_languages64),
    };
    readerRows.push(row);
  }
}

for (const row of readerRows) {
  Object.assign(row, transportTopologyByMedia.get(mediaProbeKey(row)) || {});
  row.failureClass = readerFailureClass(row);
  row.failureDomain = readerFailureDomain(row);
  row.providerMutationEligible = providerMutationEligible(row);
  row.signature = readerSignature({ ...row, requestType: row.requestType });
}

const runtimeSentinelObservations = [...runtimeSentinelByKey.values()];
const brainReaderRows = readerRows.filter((row) => !runtimeSentinelByKey.has(runtimeExecutionKey(row)));
const runtimeSentinelReaderRows = readerRows.filter((row) => runtimeSentinelByKey.has(runtimeExecutionKey(row)));
const brainResultRows = resultRows.filter((row) => !runtimeSentinelByKey.has(runtimeExecutionKey(row)));

const declaredRows = brainReaderRows.filter((row) => row.routeMode !== 'capability_probe');
const capabilityRows = brainReaderRows.filter((row) => row.routeMode === 'capability_probe');
const failures = declaredRows.filter(isReaderFailure);
const providerEligibleFailures = failures.filter((row) => row.providerMutationEligible);
const harnessObservationFailures = failures.filter((row) => row.failureDomain === 'harness_observation');
const clientRuntimeFailures = [
  ...failures.filter((row) => !row.providerMutationEligible && row.failureDomain !== 'harness_observation'),
  ...runtimeSentinelObservations,
];
const declaredHealthy = declaredRows.filter((row) => !isReaderFailure(row));
const capabilityFailures = capabilityRows.filter(isReaderFailure);
const capabilityHealthy = capabilityRows.filter((row) => !isReaderFailure(row));

const declaredResultRows = brainResultRows.filter((row) => row.routeMode !== 'capability_probe');
const capabilityResultRows = brainResultRows.filter((row) => row.routeMode === 'capability_probe');
const enabledDeclaredResults = declaredResultRows.filter((row) => row.enabled);
const extractionFailures = enabledDeclaredResults.filter((row) => row.count === 0);
const extractionHealthy = enabledDeclaredResults.filter((row) => row.count > 0);
const ignoredDisabledExtractionFailures = declaredResultRows.filter((row) => !row.enabled && row.count === 0);
const systemicExtraction = classifySystemicExtraction(enabledDeclaredResults);
const systemicExtractionKeys = systemicExtraction.systemicExecutionKeys;
const systemicExtractionFailures = extractionFailures.filter((row) => systemicExtractionKeys.has(extractionExecutionKey(row)));
const providerExtractionFailures = extractionFailures.filter((row) => !systemicExtractionKeys.has(extractionExecutionKey(row)));

const readerPlans = evidence.complete ? providerEligibleFailures.map((row) => {
  const failureEvidence = {
    invoked: true,
    signature: row.signature,
    request: { mediaType: row.requestType },
    stages: {
      reader: {
        attempted: true,
        observed: true,
        state: row.state,
        failureClass: row.failureClass,
        failureStage: row.failureStage,
        httpStatus: row.httpStatus,
        errorCode: row.errorCode,
        errorClass: row.errorClass,
        durationSeconds: row.durationSeconds,
        loadBytes: row.loadBytes,
        loadDurationMs: row.loadDurationMs,
        mediaDataType: row.mediaDataType,
        trackType: row.trackType,
      },
    },
  };
  const plan = planRepair(failureEvidence, { signature: row.signature, maxHypotheses: 3 });
  return {
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: row.index,
    state: row.state, failureClass: row.failureClass, failureDomain: row.failureDomain,
    providerMutationEligible: true, failureStage: row.failureStage,
    httpStatus: row.httpStatus, errorCode: row.errorCode, errorClass: row.errorClass,
    host: row.host, durationSeconds: row.durationSeconds,
    loadBytes: row.loadBytes, loadDurationMs: row.loadDurationMs,
    mediaDataType: row.mediaDataType, trackType: row.trackType,
    signature: row.signature, action: plan.action, exitReason: plan.exitReason,
    hypotheses: plan.hypotheses.map((hypothesis) => ({
      id: hypothesis.id,
      capabilities: [...(hypothesis.capabilities || [])],
      actions: [...(hypothesis.actions || [])],
    })),
  };
}) : [];

const extractionPlans = evidence.complete ? providerExtractionFailures.map((row) => {
  const signature = extractionSignature(row);
  const failureEvidence = {
    invoked: true,
    signature,
    request: { mediaType: row.requestType },
    stages: { media: { attempted: true, found: false } },
  };
  const plan = planRepair(failureEvidence, { signature, maxHypotheses: 3 });
  return {
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: -1,
    state: 'empty', failureClass: plan.failureClass, failureDomain: 'provider_extraction',
    providerMutationEligible: true, failureStage: 'media_extraction',
    httpStatus: 0, errorCode: '', errorClass: '', host: '', durationSeconds: null,
    loadBytes: 0, loadDurationMs: 0, mediaDataType: -1, trackType: -1, returnedCount: 0,
    signature, action: plan.action, exitReason: plan.exitReason,
    hypotheses: plan.hypotheses.map((hypothesis) => ({
      id: hypothesis.id,
      capabilities: [...(hypothesis.capabilities || [])],
      actions: [...(hypothesis.actions || [])],
    })),
  };
}) : [];
const systemicExtractionPlans = evidence.complete ? systemicExtractionFailures.map((row) => {
  const signature = `${row.requestType}:runtime_contract_drift:${String(row.client || 'unknown').toLowerCase()}:${row.fixture}`;
  const plan = planRepair({
    invoked: true,
    contractDrift: true,
    signature,
    request: { mediaType: row.requestType },
  }, { signature, maxHypotheses: 3 });
  return {
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: -1,
    state: 'empty', failureClass: 'runtime_contract_drift', failureDomain: 'client_runtime',
    providerMutationEligible: false, coreOrManifestProposalAllowed: true,
    failureStage: 'provider_runtime_compat', returnedCount: 0, signature,
    action: plan.action, exitReason: plan.exitReason,
    hypotheses: plan.hypotheses.map((hypothesis) => ({
      id: hypothesis.id,
      capabilities: [...(hypothesis.capabilities || [])],
      actions: [...(hypothesis.actions || [])],
    })),
  };
}) : [];
const plans = [...readerPlans, ...extractionPlans];

const appSelectionIssues = evidence.complete
  ? appSelectionObservations.filter((row) => !row.eligible).map((row) => ({
      client: row.client,
      provider: row.provider,
      fixture: row.fixture,
      requestType: row.requestType,
      failureClass: {
        plugins_globally_disabled: 'client_plugins_globally_disabled',
        scraper_disabled_locally: 'client_scraper_disabled_locally',
        unsupported_media_type: 'client_scraper_media_type_filtered',
        not_selected_by_app: 'client_plugin_selection_mismatch',
      }[row.reason],
      reason: row.reason,
      layer: row.reason === 'unsupported_media_type' ? 'manifest_contract'
        : 'client_state',
      providerJsMutationAllowed: false,
      coreOrManifestProposalAllowed: false,
      proofAuthority: false,
      publicationAuthority: false,
      actions: [
        'inspect actual installed manifest, app plugin switch and persisted enabled state',
        'compare the media-type eligibility and current canonical projection',
        'respect user-disabled plugins and do not patch provider JS or force enable',
        'repeat exact-source native app selection before extraction/decoder assessment',
      ],
    }))
  : [];
const providerLoadIssues = evidence.complete ? [
  ...providerLoadObservations.map((row) => ({
    ...row,
    ...providerLoadRepair(row),
  })),
  ...appSelectionIssues,
] : [];

const playerHealthyByRoute = new Map();
for (const row of declaredHealthy) {
  const key = routeKey(row);
  if (!playerHealthyByRoute.has(key)) playerHealthyByRoute.set(key, new Set());
  playerHealthyByRoute.get(key).add(row.client);
}
const extractionHealthyByRoute = new Map();
for (const row of extractionHealthy) {
  const key = routeKey(row);
  if (!extractionHealthyByRoute.has(key)) extractionHealthyByRoute.set(key, new Set());
  extractionHealthyByRoute.get(key).add(row.client);
}
const consensusGrouped = new Map();
for (const plan of plans) {
  const key = `${plan.provider}\u0000${plan.requestType}\u0000${plan.fixture}\u0000${plan.failureClass}`;
  if (!consensusGrouped.has(key)) consensusGrouped.set(key, { plan, clients: new Set() });
  consensusGrouped.get(key).clients.add(plan.client);
}
const crossClientProviderFailures = [...consensusGrouped.values()].filter(({ plan, clients }) => {
  const key = routeKey(plan);
  const healthy = plan.failureClass === 'media_extraction_gap'
    ? extractionHealthyByRoute.get(key)
    : playerHealthyByRoute.get(key);
  return clients.size >= 2 && !(healthy?.size > 0);
});
const providerLearningAllowed = evidence.complete && crossClientProviderFailures.length > 0;

const grouped = new Map();
for (const plan of plans) {
  const key = `${plan.provider}\u0000${plan.requestType}\u0000${plan.failureClass}`;
  if (!grouped.has(key)) grouped.set(key, []);
  grouped.get(key).push(plan);
}
const priorities = [...grouped.values()]
  .map((rows) => ({
    provider: rows[0].provider,
    requestType: rows[0].requestType,
    failureClass: rows[0].failureClass,
    occurrences: rows.length,
    clients: [...new Set(rows.map((row) => row.client))].sort(),
    fixtures: [...new Set(rows.map((row) => row.fixture))].sort(),
    firstHypothesis: rows[0].hypotheses[0]?.id || null,
    signatures: [...new Set(rows.map((row) => row.signature))].slice(0, 12),
  }))
  .sort((a, b) => b.occurrences - a.occurrences || a.provider.localeCompare(b.provider));

const loadGrouped = new Map();
for (const issue of providerLoadIssues) {
  const key = `${issue.provider}\u0000${issue.failureClass}`;
  if (!loadGrouped.has(key)) loadGrouped.set(key, []);
  loadGrouped.get(key).push(issue);
}
const providerLoadPriorities = [...loadGrouped.values()]
  .map((rows) => ({
    provider: rows[0].provider,
    failureClass: rows[0].failureClass,
    layer: rows[0].layer,
    occurrences: rows.length,
    clients: [...new Set(rows.map((row) => row.client))].sort(),
    fixtures: [...new Set(rows.map((row) => row.fixture))].sort(),
    providerJsMutationAllowed: false,
    coreOrManifestProposalAllowed: evidence.complete,
    actions: rows[0].actions,
  }))
  .sort((a, b) => b.occurrences - a.occurrences || a.provider.localeCompare(b.provider));

const playerObservations = brainReaderRows.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, index: row.index,
  state: row.state, failureClass: row.failureClass, failureDomain: row.failureDomain,
  providerMutationEligible: row.providerMutationEligible, failureStage: row.failureStage,
  httpStatus: row.httpStatus, errorCode: row.errorCode, host: row.host,
  durationSeconds: row.durationSeconds, loadBytes: row.loadBytes, loadDurationMs: row.loadDurationMs,
  playerVideoFormatObserved: row.videoWidth > 0 && row.videoHeight > 0,
  playerAudioTrackCount: row.audioTrackCount,
  playerAudioTrackLanguages: row.audioTrackLanguages,
  playerSubtitleTrackCount: row.subtitleTrackCount,
  playerSubtitleTrackLanguages: row.subtitleTrackLanguages,
  transportAudioTrackCount: row.transportAudioTrackCount ?? -1,
  transportAudioTrackLanguages: row.transportAudioTrackLanguages || '',
  transportSubtitleTrackCount: row.transportSubtitleTrackCount ?? -1,
  transportSubtitleTrackLanguages: row.transportSubtitleTrackLanguages || '',
  observationLayer: 'player',
}));
const extractionObservations = providerExtractionFailures.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, index: -1,
  state: 'empty', failureClass: 'media_extraction_gap', failureDomain: 'provider_extraction',
  providerMutationEligible: true, failureStage: 'media_extraction',
  httpStatus: 0, errorCode: '', host: '', durationSeconds: null, loadBytes: 0, loadDurationMs: 0,
  returnedCount: 0, observationLayer: 'extraction',
}));
const systemicExtractionObservations = systemicExtractionFailures.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, index: -1,
  state: 'empty', failureClass: 'runtime_contract_drift', failureDomain: 'client_runtime',
  providerMutationEligible: false, failureStage: 'provider_runtime_compat',
  httpStatus: 0, errorCode: '', host: '', durationSeconds: null, loadBytes: 0, loadDurationMs: 0,
  returnedCount: 0, observationLayer: 'runtime',
}));
const extractionHealthyObservations = extractionHealthy.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, returnedCount: row.count,
  observationLayer: 'extraction', state: 'non_empty', failureClass: 'healthy',
}));
// No reader can be reached after a genuine zero-stream execution. Requiring
// evidence.complete here discarded exactly the diagnostic needed to understand
// why there was no media. Keep only matched official app-selection + execution
// observations; this is hypothesis-only learning, never provider mutation or
// successful-reader authority.
const nativeSelectedRoutes = new Set(appSelectionObservations
  .filter((row) => row.eligible === true)
  .map((row) => [row.client, row.fixture, row.provider, row.requestType].join('\\0')));
const nativeZeroRoutes = new Set(resultRows
  .filter((row) => row.enabled === true && row.count === 0 && row.routeMode === 'declared')
  .map((row) => [row.client, row.fixture, String(row.provider).toLowerCase(), row.requestType].join('\\0')));
const quickJsUnverifiedObservations = quickJsDiagnostics.filter((row) => {
  if (!(row.phase === 'error' || row.phase === 'missing_export'
    || (row.phase === 'result' && row.count === 0))) return false;
  const key = [row.client, row.fixture, row.provider, row.requestType].join('\\0');
  return nativeSelectedRoutes.has(key) && nativeZeroRoutes.has(key);
}).map((row) => ({
  client: row.client,
  provider: row.provider,
  fixture: row.fixture,
  requestType: row.requestType,
  observationLayer: 'native_quickjs',
  state: row.phase,
  failureClass: row.phase === 'missing_export' ? 'native_quickjs_missing_export'
    : row.phase === 'error' ? 'native_quickjs_exception'
    : 'native_quickjs_zero_stream',
  failureDomain: 'client_provider_execution_unresolved',
  providerMutationEligible: false,
  category: row.category,
  count: row.count,
  routeMode: 'declared',
  diagnosticOnly: true,
  nativeReaderEvidenceComplete: evidence.complete,
  proofAuthority: false,
  publicationAuthority: false,
  nativePlaybackAuthority: false,
}));
const observations = [
  ...playerObservations, ...extractionObservations,
  ...systemicExtractionObservations, ...runtimeSentinelObservations,
  ...quickJsUnverifiedObservations,
];
const providerMap = new Map();
function ensureProviderOutcome(provider) {
  const key = String(provider || '').toLowerCase();
  if (!providerMap.has(key)) {
    providerMap.set(key, {
      provider: key, observed: 0, healthy: 0, failures: 0,
      providerEligibleFailures: 0, clientRuntimeFailures: 0, harnessObservationFailures: 0,
      extractionExecutions: 0, extractionHealthy: 0, extractionFailures: 0,
      capabilityProbes: 0, capabilityHealthy: 0, capabilityFailures: 0,
      loadFailures: 0, loadFailureClasses: {}, nativeExecutionTimeouts: 0,
      failureClasses: {}, clients: new Set(), fixtures: new Set(), requestTypes: new Set(),
    });
  }
  return providerMap.get(key);
}
for (const row of playerObservations) {
  const current = ensureProviderOutcome(row.provider);
  current.observed += 1;
  current.clients.add(row.client);
  current.fixtures.add(row.fixture);
  current.requestTypes.add(row.requestType);
  if (row.routeMode === 'capability_probe') {
    current.capabilityProbes += 1;
    if (row.failureClass === 'healthy') current.capabilityHealthy += 1;
    else current.capabilityFailures += 1;
  } else if (row.failureClass === 'healthy') {
    current.healthy += 1;
  } else {
    current.failures += 1;
    if (row.providerMutationEligible) current.providerEligibleFailures += 1;
    else if (row.failureDomain === 'harness_observation') current.harnessObservationFailures += 1;
    else current.clientRuntimeFailures += 1;
    current.failureClasses[row.failureClass] = Number(current.failureClasses[row.failureClass] || 0) + 1;
  }
}
for (const row of enabledDeclaredResults) {
  const current = ensureProviderOutcome(row.provider);
  current.extractionExecutions += 1;
  current.clients.add(row.client);
  current.fixtures.add(row.fixture);
  current.requestTypes.add(row.requestType);
  if (row.count > 0) current.extractionHealthy += 1;
  else {
    current.extractionFailures += 1;
    current.failures += 1;
    if (systemicExtractionKeys.has(extractionExecutionKey(row))) {
      current.clientRuntimeFailures += 1;
      current.failureClasses.runtime_contract_drift = Number(current.failureClasses.runtime_contract_drift || 0) + 1;
    } else {
      current.providerEligibleFailures += 1;
      current.failureClasses.media_extraction_gap = Number(current.failureClasses.media_extraction_gap || 0) + 1;
    }
  }
}
for (const row of runtimeSentinelObservations) {
  const current = ensureProviderOutcome(row.provider);
  current.observed += 1;
  current.failures += 1;
  current.clientRuntimeFailures += 1;
  current.failureClasses.client_runtime_error = Number(current.failureClasses.client_runtime_error || 0) + 1;
  current.clients.add(row.client);
  current.fixtures.add(row.fixture);
  current.requestTypes.add(row.requestType);
}
// A selected, attempted provider with a hard native timeout must remain
// visible in Brain provider outcomes even when there is no FIELD_NATIVE_RESULT,
// no media row and therefore no reader. This is an *unattributed runtime
// diagnostic*, not an extractor or provider-mutation authorization. The
// independent Android-TV feedback ingester retains the same redacted event.
const seenNativeExecution = new Set();
for (const row of nativeExecutionDiagnostics) {
  const key = [row.client, row.provider, row.fixture, row.requestType, row.failureClass].join('\u0000');
  if (seenNativeExecution.has(key)) continue;
  seenNativeExecution.add(key);
  const current = ensureProviderOutcome(row.provider);
  current.observed += 1;
  current.failures += 1;
  current.nativeExecutionTimeouts += 1;
  current.failureClasses.provider_hard_timeout = Number(current.failureClasses.provider_hard_timeout || 0) + 1;
  current.clients.add(row.client);
  current.fixtures.add(row.fixture);
  current.requestTypes.add(row.requestType);
}
for (const issue of providerLoadIssues) {
  const current = ensureProviderOutcome(issue.provider);
  current.loadFailures += 1;
  current.loadFailureClasses[issue.failureClass] = Number(current.loadFailureClasses[issue.failureClass] || 0) + 1;
  current.clients.add(issue.client);
  current.fixtures.add(issue.fixture);
}
const providerOutcomes = [...providerMap.values()].map((row) => ({
  provider: row.provider,
  observed: row.observed,
  healthy: row.healthy,
  failures: row.failures,
  providerEligibleFailures: row.providerEligibleFailures,
  clientRuntimeFailures: row.clientRuntimeFailures,
  harnessObservationFailures: row.harnessObservationFailures,
  extractionExecutions: row.extractionExecutions,
  extractionHealthy: row.extractionHealthy,
  extractionFailures: row.extractionFailures,
  capabilityProbes: row.capabilityProbes,
  capabilityHealthy: row.capabilityHealthy,
  capabilityFailures: row.capabilityFailures,
  loadFailures: row.loadFailures,
  loadFailureClasses: row.loadFailureClasses,
  nativeExecutionTimeouts: row.nativeExecutionTimeouts,
  failureClasses: row.failureClasses,
  clients: [...row.clients].sort(),
  fixtures: [...row.fixtures].sort(),
  requestTypes: [...row.requestTypes].sort(),
})).sort((a, b) => b.loadFailures - a.loadFailures || b.failures - a.failures || a.provider.localeCompare(b.provider));

const capabilityProbes = capabilityRows.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, index: row.index,
  state: row.state, healthy: !isReaderFailure(row), failureClass: row.failureClass,
  failureDomain: row.failureDomain, providerMutationEligible: false,
  failureStage: row.failureStage, httpStatus: row.httpStatus,
  durationSeconds: row.durationSeconds,
  promotionEligibleFromReaderAlone: false,
}));

const payload = {
  schemaVersion: 5,
  officialClientSha,
  generatedAt: new Date().toISOString(),
  brainVersion: BRAIN_CONTROL_PLANE_VERSION,
  evidenceComplete: evidence.complete,
  evidenceProblems: evidence.problems,
  evidenceStats: evidence.stats,
  readerObserved: readerRows.length,
  runtimeErrorSentinelObserved: runtimeSentinelObservations.length,
  runtimeErrorSentinelReaderRowsExcluded: runtimeSentinelReaderRows.length,
  readerDeclaredObserved: declaredRows.length,
  readerHealthy: declaredHealthy.length,
  readerFailures: failures.length,
  providerEligibleReaderFailures: providerEligibleFailures.length,
  clientRuntimeReaderFailures: clientRuntimeFailures.length,
  harnessObservationReaderFailures: harnessObservationFailures.length,
  extractionResultObserved: enabledDeclaredResults.length,
  extractionHealthy: extractionHealthy.length,
  extractionFailures: extractionFailures.length,
  providerExtractionFailures: providerExtractionFailures.length,
  clientRuntimeExtractionFailures: systemicExtractionFailures.length,
  systemicExtractionGroupCount: systemicExtraction.systemicGroups.length,
  ignoredDisabledExtractionFailures: ignoredDisabledExtractionFailures.length,
  capabilityResultObserved: capabilityResultRows.length,
  crossClientProviderFailureGroups: crossClientProviderFailures.length,
  capabilityProbeObserved: capabilityRows.length,
  capabilityProbeHealthy: capabilityHealthy.length,
  capabilityProbeFailures: capabilityFailures.length,
  providerLoadObservedFailures: providerLoadObservations.length,
  providerLoadActionableFailures: providerLoadObservations.length,
  appSelectionObserved: appSelectionObservations.length,
  appSelectionFailures: appSelectionIssues.length,
  quickJsDiagnosticObserved: quickJsDiagnostics.length,
  nativeExecutionDiagnosticObserved: nativeExecutionDiagnostics.length,
  terminalTransportDiagnosticObserved: terminalTransportDiagnostics.length,
  prePlayerMediaRootTransitionObserved: prePlayerMediaRootTransitions.length,
  prePlayerFetchHostOutcomeObserved: prePlayerFetchHostOutcomes.length,
  quickJsUnverifiedObserved: quickJsUnverifiedObservations.length,
  readerLoadErrorEvidence: brainReaderRows.filter((row) => row.loadDurationMs > 0 || row.loadBytes > 0 || row.httpStatus > 0).length,
  observations,
  extractionHealthyObservations,
  systemicExtractionGroups: systemicExtraction.systemicGroups,
  clientRuntimeExtractionPlans: systemicExtractionPlans,
  providerLoadObservations,
  quickJsDiagnostics,
  quickJsPromiseControls,
  nativeExecutionDiagnostics,
  terminalTransportDiagnostics,
  prePlayerMediaRootTransitions,
  prePlayerFetchHostOutcomes,
  quickJsUnverifiedObservations,
  appSelectionObservations,
  appSelectionIssues,
  providerLoadIssues,
  providerOutcomes,
  capabilityProbes,
  plans,
  priorities,
  providerLoadPriorities,
  policy: {
    evidenceUsable: evidence.complete,
    learningAllowed: providerLearningAllowed,
    providerLearningAllowed,
    repairPlanningAllowed: providerLearningAllowed,
    providerMutationRequiresCrossClientConsensus: true,
    clientRuntimeFailureLearningAllowed: false,
    clientRuntimeExtractionLearningAllowed: false,
    coreRuntimeCompatibilityProposalAllowed: evidence.complete && systemicExtractionFailures.length > 0,
    runtimeErrorSentinelLearningAllowed: false,
    repositoryLearningAllowed: evidence.complete && providerLoadObservations.length > 0,
    clientSelectionDiagnosticLearningAllowed: evidence.complete && appSelectionIssues.length > 0,
    quickJsDiagnosticLearningAllowed: quickJsUnverifiedObservations.length > 0,
    quickJsDiagnosticProviderMutationAllowed: false,
    clientSelectionProviderJsMutationAllowed: false,
    providerLoadJsMutationAllowed: false,
    coreOrManifestLoadProposalAllowed: evidence.complete && providerLoadObservations.length > 0,
    capabilityLearningAllowed: false,
    capabilityPromotionRequiresIdentityProof: true,
    disabledProviderExtractionLearningAllowed: false,
    productionWritesAllowed: false,
    publicationAllowed: false,
    requireFreshNativeReaderProofAfterRepair: true,
    nonblockingSmoke,
  },
  privacy: 'No raw URLs, query tokens, cookie values, authorization values or response-header values are persisted.',
};
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2) + '\n');
console.log(
  `FIELD_NATIVE_READER_BRAIN evidence_complete=${payload.evidenceComplete} observed=${payload.readerObserved} ` +
  `declared=${payload.readerDeclaredObserved} healthy=${payload.readerHealthy} failures=${payload.readerFailures} ` +
  `provider_eligible_failures=${payload.providerEligibleReaderFailures} extraction_failures=${payload.extractionFailures} ` +
  `provider_extraction_failures=${payload.providerExtractionFailures} systemic_extraction_failures=${payload.clientRuntimeExtractionFailures} ` +
  `client_runtime_failures=${payload.clientRuntimeReaderFailures} runtime_sentinels=${payload.runtimeErrorSentinelObserved} ` +
  `cross_client_provider_groups=${payload.crossClientProviderFailureGroups} ` +
  `provider_load_failures=${payload.providerLoadActionableFailures} app_selection_failures=${payload.appSelectionFailures} quickjs_unverified=${payload.quickJsUnverifiedObserved} quickjs_promise_controls=${quickJsPromiseControls.length} capability_probes=${payload.capabilityProbeObserved} ` +
  `capability_probe_healthy=${payload.capabilityProbeHealthy} capability_probe_failures=${payload.capabilityProbeFailures} ` +
  `priorities=${priorities.length} provider_load_priorities=${providerLoadPriorities.length} provider_outcomes=${providerOutcomes.length} ` +
  `nonblocking_smoke=${nonblockingSmoke}`
);
if (!evidence.complete) {
  for (const problem of evidence.problems.slice(0, 80)) console.log(`FIELD_NATIVE_READER_BRAIN_EVIDENCE_INCOMPLETE ${problem}`);
}
for (const priority of providerLoadPriorities.slice(0, 40)) console.log(`FIELD_NATIVE_READER_BRAIN_LOAD_PRIORITY ${JSON.stringify(priority)}`);
for (const priority of priorities.slice(0, 40)) console.log(`FIELD_NATIVE_READER_BRAIN_PRIORITY ${JSON.stringify(priority)}`);
if (!evidence.complete && !nonblockingSmoke) process.exitCode = 2;