#!/usr/bin/env node
'use strict';
const path = require('node:path');
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');

const file = path.resolve(process.argv[2] || '');
if (!file || !fs.existsSync(file)) {
  console.error('provider artifact missing:', file);
  process.exit(2);
}

// Provider bundles are upstream-derived artifacts. Artifact validation must never
// execute their top-level code inside a credentialed Core job: legitimate bundles
// may require Nuvio-provided modules, while malicious/broken bundles could perform
// network/process/timer work or keep the event loop alive. Runtime behavior is
// tested later by the dedicated isolated provider workers and native Labs.
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
const getStreamsContracts = [
  /\b(?:async\s+)?function\s+getStreams\s*\(/,
  /\b(?:const|let|var)\s+getStreams\s*=\s*(?:async\s*)?(?:function\b|(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>)/,
  /\b(?:globalThis|global|self)\.getStreams\s*=/,
  /\b(?:module\.exports|exports)\.getStreams\s*=/,
  /\bmodule\.exports\s*=\s*\{[\s\S]{0,4000}?\bgetStreams\b[\s\S]{0,4000}?\}/,
];
if (!getStreamsContracts.some((pattern) => pattern.test(code))) {
  console.error('getStreams contract missing:', path.basename(file));
  process.exit(1);
}

console.log(
  'provider artifact validation passed:',
  path.basename(file),
  'mode=static-only syntax_timeout_ms=5000 execution=false network=false timers=false process=false require=false',
);
