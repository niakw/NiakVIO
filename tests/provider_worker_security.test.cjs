#!/usr/bin/env node
'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nuvio-worker-security-'));
const fixture = JSON.stringify({tmdbId:'1',mediaType:'movie',title:'Test'});
const context = JSON.stringify({locale:'fr-FR',networkLimits:{maxFetches:1}});

function runProvider(source) {
  const provider = path.join(dir, `provider-${Math.random().toString(16).slice(2)}.cjs`);
  fs.writeFileSync(provider, source);
  return spawnSync(process.execPath,[path.join(root,'scripts/provider_worker.cjs'),provider,fixture,context],{cwd:root,encoding:'utf8'});
}

for (const request of ['node:child_process','node:fs','node:https','node:net','node:dns']) {
  const result = runProvider(`module.exports={getStreams(){require('${request}');return []}}`);
  assert.match(result.stdout, /provider module blocked/);
}

if (typeof process.getBuiltinModule === 'function') {
  const result = runProvider(`module.exports={getStreams(){process.getBuiltinModule('fs');return []}}`);
  assert.match(result.stdout, /provider module blocked(?: by source policy)?: fs/);
}

{
  const result = runProvider(`module.exports={async getStreams(){await import('node:http');return []}}`);
  assert.match(result.stdout, /provider module blocked by source policy: node:http/);
}

{
  const result = runProvider(`module.exports={getStreams(){process.binding('fs');return []}}`);
  assert.match(result.stdout, /provider process API blocked: binding/);
}

{
  const result = runProvider(`const cheerio=require('cheerio-without-node-native');module.exports={getStreams(){const $=cheerio.load('<div>ok</div>');if($('div').text()!=='ok')throw new Error('parser failed');return []}}`);
  assert.strictEqual(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /NUVIO_HEALTH_RESULT=/);
}

console.log('provider worker security tests passed');
