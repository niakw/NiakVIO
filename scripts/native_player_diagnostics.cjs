#!/usr/bin/env node
'use strict';

const READER_FAILURE_CLASSES = Object.freeze({
  http_access: 'playback_http_access',
  http_gone: 'playback_http_gone',
  http_rate_limit: 'playback_rate_limited',
  http_upstream: 'playback_http_upstream',
  http_response: 'playback_http_response',
  timeout: 'playback_timeout',
  dns: 'playback_dns',
  tls: 'playback_tls',
  parser: 'playback_parser',
  decoder: 'playback_decoder',
  live_window: 'playback_live_window',
  io: 'playback_io',
  player_setup: 'playback_runtime_setup',
  player: 'playback_player_error',
  duration_identity: 'short_media',
  duration_unknown: 'playback_duration_unknown',
});

const CLIENT_RUNTIME_FAILURE_CLASSES = new Set([
  'playback_runtime_setup',
  'playback_player_error',
  'playback_decoder',
]);

const CLIENT_RUNTIME_ERROR_PATTERNS = [
  /java\.awt\.peer/i,
  /componentpeer/i,
  /inaccessibleobjectexception/i,
  /module[_ ]java\.desktop/i,
  /does[_ ]not[_ ]?["']?opens/i,
  /unable[_ ]to[_ ]make[_ ]field/i,
  /java[_ .]heap[_ ]space/i,
  /outofmemoryerror/i,
  /qemu.*(?:hang|shutdown|killed)/i,
  /runner.*(?:shutdown|cancel)/i,
];

const UNRESOLVED_MEDIA_FAILURE_CLASSES = new Set([
  'playback_video_format_unverified',
  'playback_audio_tracks_unverified',
  'playback_audio_languages_unverified',
  'playback_subtitle_tracks_unverified',
  'playback_subtitle_languages_unverified',
]);

const HARNESS_OBSERVATION_FAILURE_CLASSES = new Set([
  'playback_audio_ui_observer_empty',
  'playback_subtitle_ui_observer_empty',
]);

function normalizedLanguages(value) {
  const values = Array.isArray(value) ? value : String(value || '').split(/[|,\s]+/);
  return [...new Set(values.map((entry) => String(entry || '').trim().toLowerCase()).filter(Boolean))].sort();
}

function mediaTopologyFailureClass(row = {}) {
  const client = String(row.client || '').trim().toLowerCase();
  const expectedAudioCount = Number(row.transportAudioTrackCount ?? row.expectedAudioTrackCount ?? -1);
  const observedAudioCount = Number(row.audioTrackCount ?? row.audio_track_count ?? -1);
  if (Number.isFinite(expectedAudioCount) && expectedAudioCount > 0) {
    // On official NuvioTV, count=0 is emitted only after the Audio control was
    // found and opened. That control itself is rendered only when the production
    // UI owns at least one audio track, so zero here means the UiAutomator row
    // observer failed to materialize Compose semantics. Do not blame Media3 or
    // authorize provider repair from that contradictory observation.
    if (client === 'tv' && observedAudioCount === 0) {
      return 'playback_audio_ui_observer_empty';
    }
    if (!(Number.isFinite(observedAudioCount) && observedAudioCount >= expectedAudioCount)) {
      return 'playback_audio_tracks_unverified';
    }
    const expectedLanguages = normalizedLanguages(row.transportAudioTrackLanguages ?? row.expectedAudioTrackLanguages);
    if (expectedLanguages.length) {
      const observedLanguages = new Set(normalizedLanguages(row.audioTrackLanguages ?? row.audio_track_languages));
      if (expectedLanguages.some((language) => !observedLanguages.has(language))) {
        return 'playback_audio_languages_unverified';
      }
    }
  }

  const expectedSubtitleCount = Number(row.transportSubtitleTrackCount ?? row.expectedSubtitleTrackCount ?? -1);
  const observedSubtitleCount = Number(row.subtitleTrackCount ?? row.subtitle_track_count ?? -1);
  if (Number.isFinite(expectedSubtitleCount) && expectedSubtitleCount > 0) {
    // The TV subtitle overlay is a two-stage Compose language/source rail.
    // A zero source-row observation can be an accessibility/materialization
    // gap; keep the gate closed but classify the evidence layer correctly.
    if (client === 'tv' && observedSubtitleCount === 0) {
      return 'playback_subtitle_ui_observer_empty';
    }
    if (!(Number.isFinite(observedSubtitleCount) && observedSubtitleCount >= expectedSubtitleCount)) {
      return 'playback_subtitle_tracks_unverified';
    }
    const expectedLanguages = normalizedLanguages(row.transportSubtitleTrackLanguages ?? row.expectedSubtitleTrackLanguages);
    if (expectedLanguages.length) {
      const observedLanguages = new Set(normalizedLanguages(row.subtitleTrackLanguages ?? row.subtitle_track_languages));
      if (expectedLanguages.some((language) => !observedLanguages.has(language))) {
        return 'playback_subtitle_languages_unverified';
      }
    }
  }
  return '';
}

function readerFailureClass(row = {}) {
  const state = String(row.state || '').toLowerCase();
  const stage = String(row.failureStage || row.failure_stage || '').toLowerCase();
  const status = Number(row.httpStatus ?? row.http_status ?? 0);

  // A nominal READY event cannot override a *typed* terminal failure.
  if (state === 'short_media') return 'short_media';
  if (state === 'duration_unknown') return 'playback_duration_unknown';
  if (READER_FAILURE_CLASSES[stage]) return READER_FAILURE_CLASSES[stage];
  if ([401, 403, 407, 451].includes(status)) return 'playback_http_access';
  if ([404, 410].includes(status)) return 'playback_http_gone';
  if (status === 429) return 'playback_rate_limited';
  if (status >= 500 && status <= 599) return 'playback_http_upstream';
  if (state === 'ready' || state === 'ended') {
    // Official Android TV can signal READY from manifest/timeline before a
    // video track exists. A decoded format is mandatory in the TV player gate.
    // This failure proves missing playback evidence, not provider ownership.
    if (String(row.client || '').toLowerCase() === 'tv') {
      const width = Number(row.videoWidth ?? row.video_width ?? 0);
      const height = Number(row.videoHeight ?? row.video_height ?? 0);
      if (!(Number.isFinite(width) && Number.isFinite(height) && width > 0 && height > 0)) {
        return 'playback_video_format_unverified';
      }
    }
    const topologyFailure = mediaTopologyFailureClass(row);
    if (topologyFailure) return topologyFailure;
    if (stage && stage !== 'none' && stage !== 'unknown') return 'playback_unknown';
    return 'healthy';
  }
  if (state === 'timeout') return 'playback_timeout';
  if (state === 'error') return 'playback_player_error';
  return state ? 'playback_unknown' : 'unknown_failure';
}
function readerFailureDomain(row = {}) {
  const cls = readerFailureClass(row);
  if (cls === 'healthy') return 'healthy';
  if (HARNESS_OBSERVATION_FAILURE_CLASSES.has(cls)) return 'harness_observation';
  if (UNRESOLVED_MEDIA_FAILURE_CLASSES.has(cls)) return 'unresolved_media';

  if (CLIENT_RUNTIME_FAILURE_CLASSES.has(cls)) return 'client_runtime';
  const details = [
    row.errorClass, row.error_class,
    row.errorCode, row.error_code,
    row.exceptionChain, row.exception_chain,
  ].filter(Boolean).join(' ');
  if (CLIENT_RUNTIME_ERROR_PATTERNS.some((pattern) => pattern.test(details))) return 'client_runtime';
  return 'provider_stream';
}

function providerMutationEligible(row = {}) {
  return readerFailureDomain(row) === 'provider_stream';
}

function readerSignature(row = {}) {
  const cls = readerFailureClass(row);
  const status = Number(row.httpStatus ?? row.http_status ?? 0);
  const code = String(row.errorCode || row.error_code || '').slice(0, 96);
  const host = String(row.host || '').toLowerCase().slice(0, 160);
  const requestType = String(row.requestType || row.request_type || '').trim().toLowerCase().slice(0, 24);
  const base = [cls, status || '-', code || '-', host || '-'];
  // Keep legacy signatures stable when no route exists, but once the real Nuvio
  // request route is known it becomes part of the causal identity. This prevents
  // a provider's anime and tv failures from being learned as the same observation.
  return (requestType ? [requestType, ...base] : base).join(':');
}

function isReaderFailure(row = {}) {
  return readerFailureClass(row) !== 'healthy';
}

module.exports = {
  READER_FAILURE_CLASSES,
  CLIENT_RUNTIME_FAILURE_CLASSES,
  UNRESOLVED_MEDIA_FAILURE_CLASSES,
  HARNESS_OBSERVATION_FAILURE_CLASSES,
  mediaTopologyFailureClass,
  readerFailureClass,
  readerFailureDomain,
  providerMutationEligible,
  readerSignature,
  isReaderFailure,
};
