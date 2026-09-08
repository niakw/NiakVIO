#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36';

function stripHtml(value) {
  return String(value || '')
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;|&#160;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&quot;|&#34;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function bounded(value, max = 320) {
  const text = String(value || '').replace(/[\r\n\t]+/g, ' ').replace(/\s+/g, ' ').trim();
  return text.length <= max ? text : text.slice(0, max) + '…';
}

async function getText(url, init = {}) {
  const options = {
    redirect: 'follow',
    signal: AbortSignal.timeout(20000),
    ...init,
    headers: {
      'User-Agent': UA,
      'Accept': 'text/html,application/xhtml+xml,application/json,text/plain,*/*',
      ...(init.headers || {}),
    },
  };
  const response = await fetch(url, options);
  const text = await response.text();
  console.log('V12_HTTP', response.status, response.url, response.headers.get('content-type') || '', 'bytes=' + text.length);
  return { response, text };
}

function anchors(html, base) {
  const out = [];
  const re = /<a\b([^>]*?)href\s*=\s*(["'])(.*?)\2([^>]*)>([\s\S]*?)<\/a>/gi;
  let match;
  while ((match = re.exec(html))) {
    let href = match[3] || '';
    try { href = new URL(href, base).toString(); } catch {}
    out.push({
      href,
      text: stripHtml(match[5]),
      attrs: bounded((match[1] || '') + ' ' + (match[4] || ''), 260),
    });
    if (out.length >= 2000) break;
  }
  return out;
}

async function diagnoseAnimeKai() {
  const url = 'https://www3.anikai.cc/browser?keyword=' + encodeURIComponent('Jujutsu Kaisen');
  const { response, text } = await getText(url);
  const rows = anchors(text, response.url || url)
    .filter(row => /jujutsu|culling|kaisen/i.test(row.href + ' ' + row.text))
    .slice(0, 40);
  console.log('V12_ANIMEKAI_COUNT', rows.length);
  for (const row of rows) {
    console.log('V12_ANIMEKAI_ANCHOR', JSON.stringify({ href: row.href, text: bounded(row.text, 220), attrs: row.attrs }));
  }
}

async function diagnoseMovies4u() {
  const url = 'https://new5.movies4u.clinic/interstellar-2014-imax-bluray-multi-audio-full-movie/';
  const { response, text } = await getText(url);
  const base = response.url || url;
  const rows = anchors(text, base)
    .filter(row => /m4uplay|hubcloud|modpro|\/(?:file|drive)\//i.test(row.href + ' ' + row.text + ' ' + row.attrs))
    .slice(0, 50);
  console.log('V12_MOVIES4U_ANCHOR_COUNT', rows.length);
  for (const row of rows) {
    console.log('V12_MOVIES4U_ANCHOR', JSON.stringify({ href: row.href, text: bounded(row.text, 220), attrs: row.attrs }));
  }

  const needle = /m4uplay|hubcloud|links\.modpro|\/file\/|\/drive\//ig;
  let match;
  let count = 0;
  while ((match = needle.exec(text)) && count < 30) {
    const start = Math.max(0, match.index - 220);
    const end = Math.min(text.length, match.index + 320);
    const context = text.slice(start, end);
    console.log('V12_MOVIES4U_CONTEXT', bounded(context, 520));
    count += 1;
  }
  console.log('V12_MOVIES4U_CONTEXT_COUNT', count);
}

function extractFunction(source, name) {
  const at = source.indexOf(`async function ${name}`);
  if (at < 0) return '';
  const brace = source.indexOf('{', at);
  if (brace < 0) return '';
  let depth = 0;
  let quote = '';
  let escaped = false;
  for (let i = brace; i < source.length; i += 1) {
    const ch = source[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === '\\') escaped = true;
      else if (ch === quote) quote = '';
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') { quote = ch; continue; }
    if (ch === '{') depth += 1;
    else if (ch === '}') {
      depth -= 1;
      if (depth === 0) return source.slice(at, i + 1);
    }
  }
  return source.slice(at, Math.min(source.length, at + 8000));
}

function diagnoseDleSource() {
  const file = path.join(process.cwd(), 'scripts/provider_base_store.py');
  const source = fs.readFileSync(file, 'utf8');
  const fn = extractFunction(source, '_spv7DleFindDetails');
  console.log('V12_DLE_SOURCE_BEGIN');
  console.log(fn.slice(0, 8000));
  console.log('V12_DLE_SOURCE_END');
}

async function main() {
  await diagnoseAnimeKai();
  await diagnoseMovies4u();
  diagnoseDleSource();
}

main().catch(error => {
  console.error('V12_DIAG_ERROR', error && error.stack ? error.stack : String(error));
  process.exitCode = 1;
});
