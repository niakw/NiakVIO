#!/usr/bin/env node
'use strict';

const readline = require('node:readline');
const path = require('node:path');
const { runLab, markdown, sanitizeText } = require('./nuvio_client_lab.cjs');

const root = path.resolve(process.cwd());
const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

function reply(payload) {
  process.stdout.write('NUVIO_LAB_SESSION_RESULT=' + JSON.stringify(payload) + '\n');
}

process.stderr.write('FIELD_LEARNING_LAB_SESSION state=ready mode=warm-persistent\n');

rl.on('line', async (line) => {
  let request;
  try {
    request = JSON.parse(line);
  } catch (_) {
    reply({ ok: false, error: 'invalid_json' });
    return;
  }
  if (request?.action === 'close') {
    reply({ ok: true, closed: true });
    process.exit(0);
  }
  if (request?.action === 'ping') {
    reply({ ok: true, ready: true });
    return;
  }
  try {
    const config = request?.config || {};
    const report = await runLab(root, config, {});
    reply({ ok: true, report, markdown: markdown(report), mode: 'learning-quick' });
  } catch (error) {
    reply({ ok: false, error: sanitizeText(error?.stack || error?.message || error, 1600) });
  }
});
