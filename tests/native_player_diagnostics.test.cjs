#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const {
  readerFailureClass,
  readerFailureDomain,
  providerMutationEligible,
  readerSignature,
  isReaderFailure,
} = require('../scripts/native_player_diagnostics.cjs');

assert.equal(readerFailureClass({ state: 'ready' }), 'healthy');
assert.equal(readerFailureClass({ state: 'ended' }), 'healthy');
assert.equal(readerFailureClass({ client: 'tv', state: 'ready', videoWidth: 0, videoHeight: 0 }), 'playback_video_format_unverified');
assert.equal(readerFailureClass({ client: 'tv', state: 'ended', videoWidth: 1920, videoHeight: 0 }), 'playback_video_format_unverified');
assert.equal(readerFailureClass({ client: 'tv', state: 'ready', videoWidth: 1280, videoHeight: 720 }), 'healthy');
assert.equal(readerFailureClass({ client: 'tv', state: 'ready', videoWidth: 1280, videoHeight: 720, httpStatus: 403 }), 'playback_http_access');
assert.equal(readerFailureClass({ client: 'tv', state: 'ready', videoWidth: 1280, videoHeight: 720, failureStage: 'decoder' }), 'playback_decoder');

assert.equal(readerFailureClass({ client: 'tv', state: 'ready' }), 'playback_video_format_unverified');
assert.equal(readerFailureDomain({ client: 'tv', state: 'ready', videoWidth: 0, videoHeight: 0 }), 'unresolved_media');
assert.equal(providerMutationEligible({ client: 'tv', state: 'ready', videoWidth: 0, videoHeight: 0 }), false);
assert.equal(isReaderFailure({ client: 'tv', state: 'ready', videoWidth: 0, videoHeight: 0 }), true);
assert.equal(isReaderFailure({ client: 'tv', state: 'ready', videoWidth: 1920, videoHeight: 1080 }), false);
assert.equal(readerFailureClass({ state: 'short_media', failureStage: 'duration_identity' }), 'short_media');
assert.equal(readerFailureClass({ state: 'error', failureStage: 'http_access', httpStatus: 403 }), 'playback_http_access');
assert.equal(readerFailureClass({ state: 'error', httpStatus: 404 }), 'playback_http_gone');
assert.equal(readerFailureClass({ state: 'error', httpStatus: 429 }), 'playback_rate_limited');
assert.equal(readerFailureClass({ state: 'timeout' }), 'playback_timeout');
assert.equal(readerFailureClass({ state: 'error', failureStage: 'parser' }), 'playback_parser');
assert.equal(readerFailureClass({ state: 'error', failureStage: 'decoder' }), 'playback_decoder');
assert.equal(isReaderFailure({ state: 'ready' }), false);
assert.equal(isReaderFailure({ state: 'error', httpStatus: 403 }), true);

assert.equal(readerFailureDomain({ state: 'error', failureStage: 'http_access', httpStatus: 403 }), 'provider_stream');
assert.equal(providerMutationEligible({ state: 'error', failureStage: 'parser' }), true);
assert.equal(readerFailureDomain({ state: 'error', failureStage: 'decoder' }), 'client_runtime');
assert.equal(providerMutationEligible({ state: 'error', failureStage: 'decoder' }), false);
assert.equal(readerFailureDomain({
  state: 'error',
  failureStage: 'player',
  exceptionChain: 'Unable_to_make_field_transient_volatile_java.awt.peer.ComponentPeer_java.awt.Component.peer_accessible:_module_java.desktop_does_not_"opens_java.awt"_to_unnamed',
}), 'client_runtime');
assert.equal(providerMutationEligible({
  state: 'error',
  failureStage: 'http_access',
  httpStatus: 403,
  exceptionChain: 'java.lang.reflect.InaccessibleObjectException module java.desktop does not "opens java.awt"',
}), false);

const legacySignature = readerSignature({ state: 'error', failureStage: 'http_access', httpStatus: 403, errorCode: 'ERROR_CODE_IO_BAD_HTTP_STATUS', host: 'zipdisk.example' });
assert.equal(legacySignature, 'playback_http_access:403:ERROR_CODE_IO_BAD_HTTP_STATUS:zipdisk.example');
const tvSignature = readerSignature({ state: 'error', failureStage: 'http_access', httpStatus: 403, errorCode: 'ERROR_CODE_IO_BAD_HTTP_STATUS', host: 'zipdisk.example', requestType: 'tv' });
const animeSignature = readerSignature({ state: 'error', failureStage: 'http_access', httpStatus: 403, errorCode: 'ERROR_CODE_IO_BAD_HTTP_STATUS', host: 'zipdisk.example', requestType: 'anime' });
assert.equal(tvSignature, 'tv:playback_http_access:403:ERROR_CODE_IO_BAD_HTTP_STATUS:zipdisk.example');
assert.equal(animeSignature, 'anime:playback_http_access:403:ERROR_CODE_IO_BAD_HTTP_STATUS:zipdisk.example');
assert.notEqual(tvSignature, animeSignature);
console.log('native player diagnostics taxonomy tests passed');
