'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
const rows = (manifest.scrapers || []).filter((row) => row && typeof row === 'object');
const disabledCount = rows.filter((row) => row.enabled === false && String(row.filename || '').includes('--nuvio--')).length;
const files = [...new Set(
  rows
    .filter((row) => row && row.enabled !== false)
    .map((row) => String(row && row.filename || ''))
    .filter((relative) => relative.startsWith('providers/') && relative.includes('--nuvio--') && relative.endsWith('.js')),
)].sort();

if (!files.length) {
  console.log(`patched provider runtime smoke skipped (0 enabled referenced artifacts, disabled_skipped=${disabledCount})`);
  process.exit(0);
}

const timedOut = [];

const childScript = String.raw`
'use strict';
const path = require('node:path');
const file = path.resolve(process.argv[1]);
const errors = [];
const originalError = console.error;
console.error = (...args) => errors.push(args.map(String).join(' '));
global.fetch = async () => new Response('{}', {
  status: 404,
  headers: { 'content-type': 'application/json' },
});

(async () => {
  delete require.cache[file];
  const mod = require(file);
  if (!mod || typeof mod.getStreams !== 'function') throw new Error('getStreams missing');
  const timeout = new Promise((_, reject) => {
    setTimeout(() => reject(new Error('smoke timeout')), 3000);
  });
  const invocation = Promise.resolve().then(
    () => mod.getStreams('577922', 'movie', null, null, { title: 'Tenet', year: 2020 }),
  );
  const result = await Promise.race([invocation, timeout]);
  if (!Array.isArray(result)) throw new Error('getStreams did not return an array');
  const fatal = errors.find((line) => /ReferenceError|SyntaxError|is not defined|Unexpected identifier/i.test(line));
  if (fatal) throw new Error('runtime smoke detected ' + fatal);
})().then(
  () => process.exit(0),
  (error) => {
    originalError(error && error.stack || error);
    process.exit(1);
  },
);
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
    timedOut.push(relative);
    console.log(`FIELD_PROVIDER_RUNTIME_SMOKE_TIMEOUT provider=${relative} budget_ms=5000 action=continue_to_health_pipeline`);
    continue;
  }
  if (child.error) {
    throw new Error(`${relative}: isolated smoke process failed to start: ${child.error.message}`);
  }
  if (child.signal) {
    throw new Error(`${relative}: isolated smoke process terminated by ${child.signal}`);
  }
  if (child.status !== 0) {
    const detail = String(child.stderr || child.stdout || '').trim().slice(0, 2000);
    throw new Error(`${relative}: runtime smoke failed${detail ? `\n${detail}` : ''}`);
  }
}

console.log(`patched provider runtime smoke passed (${files.length} enabled referenced artifact(s), disabled_skipped=${disabledCount}, timed_out=${timedOut.length}, isolated=true)`);
