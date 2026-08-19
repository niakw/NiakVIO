#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const { readerFailureClass, readerSignature, isReaderFailure } = require('../scripts/native_player_diagnostics.cjs');

assert.equal(readerFailureClass({ state: 'ready' }), 'healthy');
assert.equal(readerFailureClass({ state: 'ended' }), 'healthy');
assert.equal(readerFailureClass({ state: 'short_media', failureStage: 'duration_identity' }), 'short_media');
assert.equal(readerFailureClass({ state: 'error', failureStage: 'http_access', httpStatus: 403 }), 'playback_http_access');
assert.equal(readerFailureClass({ state: 'error', httpStatus: 404 }), 'playback_http_gone');
assert.equal(readerFailureClass({ state: 'error', httpStatus: 429 }), 'playback_rate_limited');
assert.equal(readerFailureClass({ state: 'timeout' }), 'playback_timeout');
assert.equal(readerFailureClass({ state: 'error', failureStage: 'parser' }), 'playback_parser');
assert.equal(readerFailureClass({ state: 'error', failureStage: 'decoder' }), 'playback_decoder');
assert.equal(isReaderFailure({ state: 'ready' }), false);
assert.equal(isReaderFailure({ state: 'error', httpStatus: 403 }), true);
const legacySignature = readerSignature({ state: 'error', failureStage: 'http_access', httpStatus: 403, errorCode: 'ERROR_CODE_IO_BAD_HTTP_STATUS', host: 'zipdisk.example' });
assert.equal(legacySignature, 'playback_http_access:403:ERROR_CODE_IO_BAD_HTTP_STATUS:zipdisk.example');
const tvSignature = readerSignature({ state: 'error', failureStage: 'http_access', httpStatus: 403, errorCode: 'ERROR_CODE_IO_BAD_HTTP_STATUS', host: 'zipdisk.example', requestType: 'tv' });
const animeSignature = readerSignature({ state: 'error', failureStage: 'http_access', httpStatus: 403, errorCode: 'ERROR_CODE_IO_BAD_HTTP_STATUS', host: 'zipdisk.example', requestType: 'anime' });
assert.equal(tvSignature, 'tv:playback_http_access:403:ERROR_CODE_IO_BAD_HTTP_STATUS:zipdisk.example');
assert.equal(animeSignature, 'anime:playback_http_access:403:ERROR_CODE_IO_BAD_HTTP_STATUS:zipdisk.example');
assert.notEqual(tvSignature, animeSignature);
console.log('native player diagnostics taxonomy tests passed');
