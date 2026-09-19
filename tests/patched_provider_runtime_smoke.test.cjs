'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const validator = path.join(root, 'scripts', 'validate_provider_artifact.cjs');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
const rows = (manifest.scrapers || []).filter((row) => row && typeof row === 'object');
const disabledCount = rows.filter(
  (row) => row.enabled === false && String(row.filename || '').includes('--nuvio--'),
).length;
const files = [...new Set(
  rows
    .filter((row) => row.enabled !== false)
    .map((row) => String(row.filename || ''))
    .filter((relative) => relative.startsWith('providers/') && relative.includes('--nuvio--') && relative.endsWith('.js')),
)].sort();

if (!files.length) {
  console.log(`patched provider artifact smoke skipped (0 enabled referenced artifacts, disabled_skipped=${disabledCount})`);
  process.exit(0);
}

/*
 * Core publication smoke is intentionally non-executing.
 *
 * validate_provider_artifact.cjs is the canonical Core boundary: it proves that
 * each published bundle is a regular in-repository JavaScript artifact, contains
 * no executable repository dependency, and passes bounded node --check syntax.
 *
 * Provider execution/export discovery belongs to provider_worker.cjs plus
 * Health/Quick/Deep/native Labs, which install the real Nuvio compatibility
 * surface, guarded network and bounded evidence policy. Requiring provider
 * bundles directly here is both redundant and less representative of production.
 */
for (const relative of files) {
  const file = path.join(root, relative);
  const child = spawnSync(process.execPath, [validator, file], {
    cwd: root,
    encoding: 'utf8',
    timeout: 10000,
    maxBuffer: 256 * 1024,
    env: {},
  });

  if (child.error && child.error.code === 'ETIMEDOUT') {
    throw new Error(`${relative}: canonical artifact smoke exceeded 10s`);
  }
  if (child.error) {
    throw new Error(`${relative}: canonical artifact smoke failed to start: ${child.error.message}`);
  }
  if (child.signal) {
    throw new Error(`${relative}: canonical artifact smoke terminated by ${child.signal}`);
  }
  if (child.status !== 0) {
    const detail = String(child.stderr || child.stdout || '').trim().slice(0, 2000);
    throw new Error(`${relative}: canonical artifact smoke failed${detail ? `\n${detail}` : ''}`);
  }
}

console.log(
  `patched provider artifact smoke passed (${files.length} enabled referenced artifact(s), disabled_skipped=${disabledCount}, execution=false, runtime_execution=health_worker)`,
);
