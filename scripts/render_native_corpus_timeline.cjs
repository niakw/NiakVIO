#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const args = process.argv.slice(2);
const dir = path.resolve(value('--dir') || '.');
const jsonOut = path.resolve(value('--json') || 'device-lab-timeline.json');
const htmlOut = path.resolve(value('--html') || 'device-lab-timeline.html');

const rows = [];
for (const file of walk(dir).filter((p) => p.endsWith('.log'))) {
  const text = fs.readFileSync(file, 'utf8');
  const fixtureFromFile = path.basename(file).replace(/^(?:desktop|mobile|tv)-native-corpus-/, '').replace(/\.log$/, '');
  const state = new Map();
  for (const raw of text.split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const line = raw.slice(marker).trim();
    const f = fields(line);
    const client = f.client || inferClient(file);
    const provider = decode(f.provider64);
    if (!provider) continue;
    const key = `${client}\u0000${provider}`;
    const item = state.get(key) || {
      client, provider, fixture: f.fixture || fixtureFromFile,
      stages: {
        invocation: { state: 'unknown' },
        providerResult: { state: 'unknown' },
        transport: { state: 'unknown' },
      },
    };
    if (line.startsWith('FIELD_NATIVE_RESULT ')) {
      item.stages.invocation = { state: 'ok', durationMs: Number(f.duration_ms || 0) };
      item.stages.providerResult = { state: Number(f.count || 0) > 0 ? 'streams' : 'empty', count: Number(f.count || 0), enabled: f.enabled === 'true' };
    } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
      item.firstStream = {
        host: decode(f.host64) || null,
        mediaHint: decode(f.media_hint64) || null,
        quality: decode(f.quality64) || null,
        language: decode(f.language64) || null,
        type: decode(f.type64) || null,
      };
    } else if (line.startsWith('FIELD_NATIVE_TRANSPORT ')) {
      item.stages.transport = {
        state: f.state || 'unknown', kind: f.kind || 'unknown', status: Number(f.status || 0),
        contentType: decode(f.content_type64) || null,
        durationSeconds: Number(f.duration_seconds || 0) || null,
        host: decode(f.host64) || null,
      };
    } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
      item.stages.invocation = { state: 'error', durationMs: Number(f.duration_ms || 0), error: safeText(decode(f.error64)) };
    }
    state.set(key, item);
  }
  rows.push(...state.values());
}

rows.sort((a, b) => `${a.fixture}:${a.client}:${a.provider}`.localeCompare(`${b.fixture}:${b.client}:${b.provider}`));
const payload = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  sublab: 'native-corpus-device-visual',
  rows,
  note: 'Timeline uses sanitized native-device logs only. Internal catalogue/detail/player hops remain unobserved unless the official runtime emits them; they are never fabricated.',
  privacy: 'No raw stream URL, token, query string or header value is persisted.',
};
fs.writeFileSync(jsonOut, JSON.stringify(payload, null, 2) + '\n');
fs.writeFileSync(htmlOut, renderHtml(payload));
console.log(`FIELD_DEVICE_VISUAL_TIMELINE rows=${rows.length}`);

function value(name) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; }
function walk(root) {
  if (!fs.existsSync(root)) return [];
  const out = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) out.push(...walk(full)); else out.push(full);
  }
  return out;
}
function inferClient(file) { const name = path.basename(file); return name.startsWith('tv-') ? 'tv' : name.startsWith('mobile-') ? 'mobile' : 'desktop'; }
function decode(value) {
  if (!value) return '';
  let text = String(value).replace(/-/g, '+').replace(/_/g, '/'); while (text.length % 4) text += '=';
  try { return Buffer.from(text, 'base64').toString('utf8'); } catch { return ''; }
}
function fields(line) { const out = {}; const re = /([A-Za-z0-9_]+)=([^\s]+)/g; let m; while ((m = re.exec(line))) out[m[1]] = m[2]; return out; }
function safeText(value) { return String(value || '').replace(/(?:https?|magnet|acestream|torrent):[^\s"']+/gi, '[endpoint]').slice(0, 300); }
function esc(value) { return String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function renderHtml(data) {
  const body = data.rows.map((row) => `<tr><td>${esc(row.fixture)}</td><td>${esc(row.client)}</td><td>${esc(row.provider)}</td><td>${esc(row.stages.invocation.state)}</td><td>${esc(row.stages.providerResult.state)}${row.stages.providerResult.count != null ? ` (${row.stages.providerResult.count})` : ''}</td><td>${esc(row.stages.transport.state)} / ${esc(row.stages.transport.kind)} / ${esc(row.stages.transport.status || '')}</td><td>${esc(row.firstStream?.host || row.stages.transport.host || '')}</td><td>${esc(row.firstStream?.mediaHint || '')}</td></tr>`).join('');
  return `<!doctype html><meta charset="utf-8"><title>NiakVIO Device Lab visual timeline</title><style>body{font-family:system-ui,sans-serif;margin:24px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #ddd;padding:6px;vertical-align:top}th{position:sticky;top:0;background:#fff}code{background:#f4f4f4;padding:2px 4px}</style><h1>NiakVIO Device Lab — visual sub-lab</h1><p>${esc(data.note)}</p><p><strong>Privacy:</strong> ${esc(data.privacy)}</p><table><thead><tr><th>Fixture</th><th>Client</th><th>Provider</th><th>Invocation</th><th>Provider result</th><th>Transport</th><th>Host</th><th>Media hint</th></tr></thead><tbody>${body}</tbody></table>`;
}
