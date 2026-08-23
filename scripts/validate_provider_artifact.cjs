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

// Provider bundles are upstream-derived artifacts. Core artifact validation must
// never execute them in a credentialed runner and must not infer runtime exports
// from source spelling: many valid providers are obfuscated and expose getStreams
// only after their bootstrap executes. Runtime/export behavior is validated later
// by the isolated provider workers and native Labs. Here we prove only that the
// materialized JavaScript is syntactically valid, with a hard timeout and empty env.
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

console.log(
  'provider artifact validation passed:',
  path.basename(file),
  'mode=syntax-only syntax_timeout_ms=5000 execution=false network=false timers=false process=false require=false',
);
