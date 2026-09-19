#!/usr/bin/env node
'use strict';
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');

const ROOT = fs.realpathSync(path.resolve(__dirname, '..'));
const TEMP_ROOT = fs.realpathSync(os.tmpdir());
const args = process.argv.slice(2);
const providerBaseMode = args.includes('--provider-base');
const requested = args.find((value) => value !== '--provider-base') || '';
const requestedFile = path.resolve(requested);

function isWithin(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

let file = '';
try {
  file = fs.realpathSync(requestedFile);
} catch (_) {
  console.error('provider artifact missing:', requestedFile);
  process.exit(2);
}

const fileStat = fs.lstatSync(file);
if (!fileStat.isFile() || fileStat.isSymbolicLink()) {
  console.error('provider artifact must be a regular non-symlink file:', file);
  process.exit(2);
}
if (![ROOT, TEMP_ROOT].some((root) => isWithin(root, file))) {
  console.error('provider artifact path outside allowed roots:', file);
  process.exit(2);
}

function stripCommentsPreservingStrings(input) {
  let out = '';
  let quote = null;
  let escaped = false;
  for (let i = 0; i < input.length; i += 1) {
    const ch = input[i];
    const next = input[i + 1] || '';
    if (quote) {
      out += ch;
      if (escaped) {
        escaped = false;
      } else if (ch === '\\') {
        escaped = true;
      } else if (ch === quote) {
        quote = null;
      }
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      quote = ch;
      out += ch;
      continue;
    }
    if (ch === '/' && next === '/') {
      while (i < input.length && input[i] !== '\n' && input[i] !== '\r') i += 1;
      out += input[i] || '';
      continue;
    }
    if (ch === '/' && next === '*') {
      i += 2;
      while (i < input.length && !(input[i] === '*' && input[i + 1] === '/')) i += 1;
      i += 1;
      continue;
    }
    out += ch;
  }
  return out;
}

// Published provider bundles must be runtime-self-contained with respect to source
// repositories. GitHub remains valid in comments for provenance/licensing and in
// repository-side CI metadata, but executable provider code must never need a
// repository/raw-repository URL to discover a domain, API, route table or playback
// dependency. Keep this static: provider artifacts are never executed here.
const source = fs.readFileSync(file, 'utf8');
const executableSource = stripCommentsPreservingStrings(source);
const repositoryUrl = /https?:\/\/(?:raw\.githubusercontent\.com|github\.com|api\.github\.com|gist\.github\.com|gist\.githubusercontent\.com)(?:[/:?#]|$)/ig;
const repositoryMatches = [...executableSource.matchAll(repositoryUrl)].map((match) => match[0]);
if (!providerBaseMode && repositoryMatches.length) {
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
  providerBaseMode
    ? 'mode=provider-base-syntax repository_scan=observed repository_runtime_dependencies=maintenance-input-only syntax_timeout_ms=5000 execution=false network=false timers=false process=false require=false'
    : 'mode=syntax-only repository_scan=true repository_runtime_dependencies=false syntax_timeout_ms=5000 execution=false network=false timers=false process=false require=false',
);
