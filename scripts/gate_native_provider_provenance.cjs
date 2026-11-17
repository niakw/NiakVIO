#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const args = process.argv.slice(2);
let client = 'unknown';
const logs = [];
for (let i = 0; i < args.length; i += 1) {
  if (args[i] === '--client') {
    client = String(args[++i] || '').trim() || 'unknown';
    continue;
  }
  logs.push(path.resolve(args[i]));
}
if (!logs.length) {
  console.error('Usage: gate_native_provider_provenance.cjs --client <label> <native-log> [...]');
  process.exit(2);
}

function decode(value) {
  if (!value) return '';
  let text = String(value).replace(/-/g, '+').replace(/_/g, '/');
  while (text.length % 4) text += '=';
  try { return Buffer.from(text, 'base64').toString('utf8'); } catch { return ''; }
}

function fields(line) {
  const out = {};
  const re = /([A-Za-z0-9_]+)=([^\s]+)/g;
  let match;
  while ((match = re.exec(line)) !== null) out[match[1]] = match[2];
  return out;
}

function canonicalProvider(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/_/g, '-')
    .replace(/\s+/g, '-');
}

function externalVisibleSource(title, name) {
  for (const raw of [title, name]) {
    const value = String(raw || '').trim();
    const at = value.indexOf(' · ');
    if (at <= 0) continue;
    const suffix = value.slice(at + 3).trim();
    if (suffix) return suffix;
  }
  return '';
}

const rows = [];
for (const file of logs) {
  if (!fs.existsSync(file) || fs.statSync(file).size <= 0) {
    console.error('FIELD_NATIVE_PROVIDER_PROVENANCE status=fail client=' + client + ' reason=missing_log file=' + file);
    process.exit(2);
  }
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const genericAt = raw.indexOf('FIELD_NATIVE_ROW ');
    if (genericAt >= 0) {
      const f = fields(raw.slice(genericAt).trim());
      rows.push({
        fixture: String(f.fixture || ''),
        expected: decode(f.provider64) || String(f.provider || ''),
        logical: decode(f.logical_provider64),
        title: decode(f.title64),
        name: decode(f.name64),
      });
      continue;
    }
    const iosAt = raw.indexOf('FIELD_NATIVE_IOS_ROW ');
    if (iosAt >= 0) {
      const payload = raw.slice(iosAt + 'FIELD_NATIVE_IOS_ROW '.length).trim();
      try {
        const row = JSON.parse(payload);
        if (row && typeof row === 'object') {
          rows.push({
            fixture: String(row.fixture || ''),
            expected: String(row.provider || ''),
            logical: String(row.logicalProvider || ''),
            title: String(row.title || ''),
            name: String(row.name || ''),
          });
        }
      } catch {}
    }
  }
}

if (!rows.length) {
  console.error('FIELD_NATIVE_PROVIDER_PROVENANCE status=unproven client=' + client + ' rows=0 reason=no_stream_rows');
  process.exit(3);
}

const mismatches = [];
let externalWitnesses = 0;
const sources = new Set();
for (const row of rows) {
  const expected = canonicalProvider(row.expected);
  const logical = canonicalProvider(row.logical);
  if (!expected || !logical || expected !== logical) {
    mismatches.push(
      (row.fixture || 'unknown') + ':expected=' + (expected || 'missing') + ':logical=' + (logical || 'missing')
    );
    continue;
  }
  const source = externalVisibleSource(row.title, row.name);
  if (source) {
    externalWitnesses += 1;
    sources.add(source);
  }
}

if (mismatches.length) {
  console.error(
    'FIELD_NATIVE_PROVIDER_PROVENANCE status=fail client=' + client +
    ' rows=' + rows.length +
    ' ownership_mismatches=' + mismatches.length +
    ' details=' + mismatches.slice(0, 16).join(';')
  );
  process.exit(4);
}

if (externalWitnesses < 1) {
  console.error(
    'FIELD_NATIVE_PROVIDER_PROVENANCE status=unproven client=' + client +
    ' rows=' + rows.length +
    ' ownership_mismatches=0 external_witnesses=0 reason=no_visible_external_provenance_witness'
  );
  process.exit(3);
}

console.log(
  'FIELD_NATIVE_PROVIDER_PROVENANCE status=verified client=' + client +
  ' rows=' + rows.length +
  ' ownership_mismatches=0 external_witnesses=' + externalWitnesses +
  ' distinct_sources=' + sources.size
);
