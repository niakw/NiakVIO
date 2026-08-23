#!/usr/bin/env node
'use strict';
const path = require('node:path');
const fs = require('node:fs');
const vm = require('node:vm');
const { spawnSync } = require('node:child_process');

const file = path.resolve(process.argv[2] || '');
if (!file || !fs.existsSync(file)) {
  console.error('provider artifact missing:', file);
  process.exit(2);
}

// Syntax validation stays in a separate bounded process. Never require a provider
// bundle in this CI process: provider code is upstream-derived and the Core job can
// carry repository credentials. Direct require() also lets top-level timers keep the
// validator alive forever. Both are unacceptable for artifact validation.
const syntax = spawnSync(process.execPath, ['--check', file], {
  encoding: 'utf8',
  timeout: 5000,
  env: {},
});
if (syntax.error && syntax.error.code === 'ETIMEDOUT') {
  console.error('provider syntax validation timed out:', path.basename(file));
  process.exit(1);
}
if (syntax.status !== 0) {
  process.stderr.write(syntax.stderr || syntax.stdout || 'syntax validation failed\n');
  process.exit(1);
}

const code = fs.readFileSync(file, 'utf8');
const quietConsole = Object.freeze({
  log() {}, info() {}, warn() {}, error() {}, debug() {},
});
const moduleObject = { exports: {} };
const sandbox = {
  module: moduleObject,
  exports: moduleObject.exports,
  console: quietConsole,
  URL,
  URLSearchParams,
  TextEncoder,
  TextDecoder,
  Buffer,
  atob: globalThis.atob,
  btoa: globalThis.btoa,
};
sandbox.globalThis = sandbox;
sandbox.global = sandbox;
sandbox.self = sandbox;

try {
  const context = vm.createContext(sandbox, {
    name: `provider-validation:${path.basename(file)}`,
    codeGeneration: { strings: false, wasm: false },
  });
  const script = new vm.Script(code, { filename: file, displayErrors: true });
  script.runInContext(context, { timeout: 2000, breakOnSigint: true });
  const mod = moduleObject.exports;
  const getStreams = mod && typeof mod.getStreams === 'function'
    ? mod.getStreams
    : typeof sandbox.getStreams === 'function'
      ? sandbox.getStreams
      : null;
  if (typeof getStreams !== 'function') throw new Error('getStreams export missing');
} catch (error) {
  console.error(error && error.stack || error);
  process.exit(1);
}

console.log('provider artifact validation passed:', path.basename(file), 'sandbox=vm timeout_ms=2000 network=false timers=false process=false require=false');
