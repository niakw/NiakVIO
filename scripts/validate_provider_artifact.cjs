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

// Published provider bundles must be runtime-self-contained with respect to source
// repositories. GitHub remains valid for provenance, licensing, maintenance and
// CI discovery, but a player must never need a repository/raw-repository URL to
// discover a provider domain, API, route table or any other playback dependency.
// Keep this static: provider artifacts are upstream-derived and are never executed
// by this validator.
const source = fs.readFileSync(file, 'utf8');
const repositoryUrl = /https?:\/\/(?:raw\.githubusercontent\.com|github\.com|api\.github\.com|gist\.github\.com|gist\.githubusercontent\.com)(?:[/:?#]|$)/ig;
const repositoryMatches = [...source.matchAll(repositoryUrl)].map((match) => match[0]);
if (repositoryMatches.length) {
  const hosts = [...new Set(repositoryMatches.map((value) => {
    try { return new URL(value).hostname.toLowerCase(); } catch (_) { return value; }
  }))];
  console.error(
    'provider runtime repository dependency forbidden:',
    path.basename(file),
    `hosts=${hosts.join(',')}`,
    'policy=repository-links-maintenance-only',
  );
  process.exit(1);
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
  'mode=syntax-only repository_scan=true repository_runtime_dependencies=false syntax_timeout_ms=5000 execution=false network=false timers=false process=false require=false',
);
