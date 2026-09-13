'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const providerPath = path.resolve(__dirname, '../providers/streamflix.js');
const source = fs.readFileSync(providerPath, 'utf8');
const errors = [];

class FailingWebSocket {
  close() {}
  send() {}
  set onopen(fn) { this._onopen = fn; }
  set onmessage(fn) { this._onmessage = fn; }
  set onclose(fn) { this._onclose = fn; }
  set onerror(fn) {
    this._onerror = fn;
    Promise.resolve().then(() => fn(new Error('expected websocket failure')));
  }
}

function response(json) {
  return {
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => json,
  };
}

async function fetchMock(url) {
  const value = String(url);
  if (value.includes('api.themoviedb.org')) {
    return response({ name: 'Timerless Show', first_air_date: '2024-01-01' });
  }
  if (value.endsWith('/data.json')) {
    return response({
      data: [{
        moviename: 'Timerless Show',
        moviekey: 'timerless-show',
        movieduration: '1 Season',
      }],
    });
  }
  if (value.endsWith('/config/config-streamflixapp.json')) {
    return response({ premium: ['https://cdn.example/'], movies: [] });
  }
  throw new Error(`unexpected fetch ${value}`);
}

const moduleBox = { exports: {} };
const sandbox = {
  module: moduleBox,
  exports: moduleBox.exports,
  require(specifier) {
    if (specifier === 'cheerio-without-node-native') return {};
    throw new Error(`unexpected require ${specifier}`);
  },
  fetch: fetchMock,
  WebSocket: FailingWebSocket,
  console: {
    log() {},
    warn() {},
    error(...args) { errors.push(args.map(String).join(' ')); },
  },
};

// Intentionally DO NOT expose setTimeout or clearTimeout in this runtime.
vm.createContext(sandbox);
vm.runInContext(source, sandbox, { filename: providerPath });

(async () => {
  const streams = await moduleBox.exports.getStreams('12345', 'tv', 1, 1);
  assert.equal(Array.isArray(streams), true);
  assert.equal(streams.length, 1, 'expected the normal TV fallback stream');
  assert.match(streams[0].url, /timerless-show\/s1\/episode1\.mkv$/);

  const websocketFailure = errors.find(line => line.includes('WebSocket failed, using fallback:')) || '';
  assert.match(websocketFailure, /WebSocket error/);
  assert.doesNotMatch(websocketFailure, /setTimeout is not defined|clearTimeout is not defined|ReferenceError/);
  assert.equal(errors.some(line => /setTimeout is not defined|clearTimeout is not defined/.test(line)), false);

  process.stdout.write('PASS streamflix timerless runtime: normal WebSocket fallback, no timer ReferenceError\n');
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
