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
const syntax = spawnSync(process.execPath, ['--check', file], { encoding: 'utf8' });
if (syntax.status !== 0) {
  process.stderr.write(syntax.stderr || syntax.stdout || 'syntax validation failed\n');
  process.exit(1);
}
try {
  delete require.cache[file];
  const mod = require(file);
  const getStreams = mod && typeof mod.getStreams === 'function' ? mod.getStreams : globalThis.getStreams;
  if (typeof getStreams !== 'function') throw new Error('getStreams export missing');
} catch (error) {
  console.error(error && error.stack || error);
  process.exit(1);
}
console.log('provider artifact validation passed:', path.basename(file));
