#!/usr/bin/env node
'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nuvio-worker-security-'));
const provider = path.join(dir, 'provider.cjs');
fs.writeFileSync(provider, `module.exports={getStreams(){require('node:child_process');return []}}`);
const fixture = JSON.stringify({tmdbId:'1',mediaType:'movie',title:'Test'});
const context = JSON.stringify({locale:'fr-FR',networkLimits:{maxFetches:1}});
const result = spawnSync(process.execPath,[path.join(root,'scripts/provider_worker.cjs'),provider,fixture,context],{cwd:root,encoding:'utf8'});
assert.match(result.stdout,/provider module blocked: node:child_process/);
console.log('provider worker security tests passed');
