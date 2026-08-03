#!/usr/bin/env node
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const WORKER = path.join(ROOT, 'scripts', 'provider_worker.cjs');
const fixture = { tmdbId: '157336', mediaType: 'movie', title: 'Interstellar', year: 2014, category: 'movie' };
const context = {
  locale: 'fr-FR', languages: ['fr-FR', 'fr'], platform: 'android', maxSettingsProfiles: 2,
  networkLimits: { maxFetches: 4, maxRedirects: 2, maxResponseBytes: 65536, maxTotalResponseBytes: 131072, maxDistinctHosts: 4 },
};

function execute(source) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nuvio-worker-invoke-'));
  const provider = path.join(dir, 'provider.js');
  fs.writeFileSync(provider, source);
  const run = spawnSync(process.execPath, [WORKER, provider, JSON.stringify(fixture), JSON.stringify(context)], {
    cwd: ROOT, encoding: 'utf8', timeout: 15000,
  });
  fs.rmSync(dir, { recursive: true, force: true });
  const markers = String(run.stdout || '').split(/\r?\n/).filter((line) => line.startsWith('NUVIO_HEALTH_RESULT='));
  assert.ok(markers.length, `missing worker result: ${run.stderr}`);
  return JSON.parse(markers.at(-1).slice('NUVIO_HEALTH_RESULT='.length));
}

const positional = execute(`module.exports={getStreams:async function(id,type){if(typeof id!=='string')throw new Error('bad positional id');return [];}};`);
assert.equal(positional.ok, true);
assert.equal(positional.invocation_diagnostics.length, 1);
assert.equal(positional.invocation_diagnostics[0].name, 'positional_with_settings');
assert.equal(positional.invocation_diagnostics[0].result, 'empty');
assert.ok(!JSON.stringify(positional).includes('[object Object]'));

const objectMode = execute(`module.exports={getStreams:async function({tmdbId,mediaType}){if(tmdbId!=='157336'||mediaType!=='movie')throw new Error('bad object input');return [];}};`);
assert.equal(objectMode.ok, true);
assert.equal(objectMode.invocation_diagnostics.length, 1);
assert.equal(objectMode.invocation_diagnostics[0].name, 'object');
assert.equal(objectMode.invocation_diagnostics[0].result, 'empty');

const broken = execute(`module.exports={getStreams:async function(id,type){const e=new Error('provider exploded');e.code='SAMPLE_RUNTIME';throw e;}};`);
assert.equal(broken.ok, false);
assert.equal(broken.error_details.name, 'ProviderRuntimeError');
assert.equal(broken.error_details.code, 'NUVIO_ALL_SETTINGS_PROFILES_FAILED');
assert.ok(Array.isArray(broken.settings_diagnostics));
assert.ok(broken.settings_diagnostics[0].error.message.includes('provider exploded'));

console.log('provider worker invocation tests passed');
