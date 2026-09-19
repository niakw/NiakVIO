#!/usr/bin/env node
'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nuvio-signature-fallback-'));
const provider = path.join(dir, 'provider.cjs');
fs.writeFileSync(provider, `
module.exports={
  async getStreams(first){
    if(first && typeof first==='object') return [{name:'object-signature',url:'https://media.example.test/video.m3u8',quality:'720p'}];
    return [];
  }
};
`);
const fixture = JSON.stringify({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014,category:'movie'});
const context = JSON.stringify({locale:'fr-FR',networkLimits:{maxFetches:2}});
const result = spawnSync(process.execPath,[path.join(root,'scripts/provider_worker.cjs'),provider,fixture,context],{cwd:root,encoding:'utf8'});
assert.strictEqual(result.status,0,result.stderr || result.stdout);
const line=result.stdout.trim().split(/\n/).find((value)=>value.startsWith('NUVIO_HEALTH_RESULT='));
assert.ok(line,result.stdout);
const payload=JSON.parse(line.slice('NUVIO_HEALTH_RESULT='.length));
assert.strictEqual(payload.stream_count,1,payload);
assert.strictEqual(payload.streams[0].name,'object-signature');
console.log('provider signature fallback tests passed');
