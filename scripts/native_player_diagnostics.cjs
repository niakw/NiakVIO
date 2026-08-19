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
});

function readerFailureClass(row = {}) {
  const state = String(row.state || '').toLowerCase();
  if (state === 'ready' || state === 'ended') return 'healthy';
  if (state === 'short_media') return 'short_media';
  const stage = String(row.failureStage || row.failure_stage || '').toLowerCase();
  if (READER_FAILURE_CLASSES[stage]) return READER_FAILURE_CLASSES[stage];
  const status = Number(row.httpStatus ?? row.http_status ?? 0);
  if ([401, 403, 407, 451].includes(status)) return 'playback_http_access';
  if ([404, 410].includes(status)) return 'playback_http_gone';
  if (status === 429) return 'playback_rate_limited';
  if (status >= 500 && status <= 599) return 'playback_http_upstream';
  if (state === 'timeout') return 'playback_timeout';
  if (state === 'error') return 'playback_player_error';
  return state ? 'playback_unknown' : 'unknown_failure';
}

function readerSignature(row = {}) {
  const cls = readerFailureClass(row);
  const status = Number(row.httpStatus ?? row.http_status ?? 0);
  const code = String(row.errorCode || row.error_code || '').slice(0, 96);
  const host = String(row.host || '').toLowerCase().slice(0, 160);
  return [cls, status || '-', code || '-', host || '-'].join(':');
}

function isReaderFailure(row = {}) {
  return readerFailureClass(row) !== 'healthy';
}

module.exports = { READER_FAILURE_CLASSES, readerFailureClass, readerSignature, isReaderFailure };
