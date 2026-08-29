'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
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
  console.log(`patched provider load smoke skipped (0 enabled referenced artifacts, disabled_skipped=${disabledCount})`);
  process.exit(0);
}

/*
 * This is deliberately a load/export smoke, not a network/provider-health probe.
 * Real getStreams execution belongs to provider_worker.cjs + Health/Quick/Deep
 * and native Labs, where the full Nuvio runtime context, guarded network and
 * bounded evidence policy are available. Calling provider business logic here
 * with a fake 404 fetch created false hangs for otherwise active providers.
 */
const childScript = String.raw`
'use strict';
const path = require('node:path');
const file = path.resolve(process.argv[1]);
const errors = [];
const originalError = console.error;
console.error = (...args) => errors.push(args.map(String).join(' '));

try {
  delete require.cache[file];
  const mod = require(file);
  const candidates = [mod, mod && mod.default, mod && mod.module];
  const getStreams = candidates
    .map((candidate) => candidate && candidate.getStreams)
    .find((value) => typeof value === 'function')
    || (typeof mod === 'function' ? mod : null);
  if (typeof getStreams !== 'function') throw new Error('getStreams missing');
  const fatal = errors.find((line) => /ReferenceError|SyntaxError|is not defined|Unexpected identifier/i.test(line));
  if (fatal) throw new Error('load smoke detected ' + fatal);
  process.exit(0);
} catch (error) {
  originalError(error && error.stack || error);
  process.exit(1);
}
`;

for (const relative of files) {
  const file = path.join(root, relative);
  const child = spawnSync(process.execPath, ['-e', childScript, file], {
    cwd: root,
    encoding: 'utf8',
    timeout: 5000,
    maxBuffer: 256 * 1024,
  });

  if (child.error && child.error.code === 'ETIMEDOUT') {
    throw new Error(`${relative}: isolated load smoke exceeded 5s`);
  }
  if (child.error) {
    throw new Error(`${relative}: isolated load smoke failed to start: ${child.error.message}`);
  }
  if (child.signal) {
    throw new Error(`${relative}: isolated load smoke terminated by ${child.signal}`);
  }
  if (child.status !== 0) {
    const detail = String(child.stderr || child.stdout || '').trim().slice(0, 2000);
    throw new Error(`${relative}: load smoke failed${detail ? `\n${detail}` : ''}`);
  }
}

console.log(
  `patched provider load smoke passed (${files.length} enabled referenced artifact(s), disabled_skipped=${disabledCount}, isolated=true, runtime_execution=health_worker)`,
);
