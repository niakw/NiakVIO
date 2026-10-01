'use strict';

const NON_MEDIA_HOST = /(?:^|\.)(?:youtube\.com|youtu\.be|facebook\.com|instagram\.com|twitter\.com|x\.com|telegram\.me|t\.me)$/i;
const STATIC_PATH = /\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i;
const PLAYER_KEY = /(?:server(?:_link)?|player|embed|stream|source|video|file|link|download|mirror)/i;
const PLAYER_CONTEXT = /(?:lecteur|server|player|embed|stream|watch|download|mirror|source|video|direct|vf|vostfr|2160|1080|720|480|4k|uhd|m3u8|mp4)/i;
const PLAYER_PATH = /\/(?:e|embed|player|watch|play|video|stream|server|source|download|file|v)(?:[/?#.-]|$)/i;

function normalizeQuality(value) {
  const text = String(value || '').toLowerCase();
  if (/\b(?:2160p?|4k|uhd)\b/.test(text)) return 2160;
  const match = text.match(/\b(1440|1080|720|576|540|480|360)p?\b/);
  return match ? Number(match[1]) : 0;
}

function candidate(raw, base, trustedContext) {
  const value = String(raw || '').replace(/&amp;/gi, '&').replace(/\\\//g, '/').trim();
  if (!value || value.length > 1800) return null;
  if (!/^(?:https?:)?\/\//i.test(value) && !/[\/?#]/.test(value)) return null;
  let parsed;
  try { parsed = new URL(value, base || undefined); } catch { return null; }
  if (!/^https?:$/i.test(parsed.protocol)) return null;
  const host = String(parsed.hostname || '').toLowerCase();
  const path = String(parsed.pathname || '') + String(parsed.search || '');
  if (!host || NON_MEDIA_HOST.test(host) || STATIC_PATH.test(path)) return null;
  const direct = /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)/i.test(path);
  if (!trustedContext && !direct && !PLAYER_PATH.test(path)) return null;
  parsed.hash = '';
  return { key: parsed.toString(), host };
}

function indexedPlayerCandidateCount(text) {
  const indices = new Set();
  const tag = /<(?:button|a|li|div)\b[^>]{0,1800}>/gi;
  let match;
  while ((match = tag.exec(text)) !== null && indices.size < 128) {
    const rawTag = String(match[0] || '');
    const indexMatch = rawTag.match(/\bdata-(?:i|index|player-index|server-index)\s*=\s*(?:["']\s*)?(\d{1,4})/i);
    if (!indexMatch) continue;
    const roleMenuItem = /\brole\s*=\s*["']menuitem["']/i.test(rawTag);
    const around = text.slice(Math.max(0, match.index - 180), Math.min(text.length, tag.lastIndex + 360));
    if (!roleMenuItem && !PLAYER_CONTEXT.test(around)) continue;
    if (!PLAYER_CONTEXT.test(around)) continue;
    indices.add(Number(indexMatch[1]));
  }
  return indices.size;
}

function extractResponseVariantHints(value, options = {}) {
  const base = String(options.baseUrl || '');
  let text = '';
  if (typeof value === 'string') text = value;
  else {
    try { text = JSON.stringify(value); } catch { text = ''; }
  }
  if (!text) return {
    declared_player_candidate_count: 0,
    declared_player_hosts: [],
    declared_quality_heights: [],
  };
  text = text.slice(0, 1024 * 1024);
  const urls = new Map();
  const qualities = new Set();

  for (const token of text.match(/\b(?:2160p?|1440p?|1080p?|720p?|576p?|540p?|480p?|360p?|4k|uhd)\b/gi) || []) {
    const height = normalizeQuality(token);
    if (height) qualities.add(height);
  }

  const keyed = /["']?([A-Za-z0-9_.-]{1,64})["']?\s*[:=]\s*["'](https?:\\?\/\\?\/[^"'<>\s]{3,1600})["']/gi;
  let match;
  while ((match = keyed.exec(text)) !== null && urls.size < 64) {
    const row = candidate(match[2], base, PLAYER_KEY.test(match[1]));
    if (row) urls.set(row.key, row.host);
  }

  const attr = /\b(?:href|src|data-src|data-url|data-link|data-player|data-embed)\s*=\s*(["'])([^"']{1,1600})\1/gi;
  while ((match = attr.exec(text)) !== null && urls.size < 64) {
    const around = text.slice(Math.max(0, match.index - 180), Math.min(text.length, attr.lastIndex + 180));
    const row = candidate(match[2], base, PLAYER_CONTEXT.test(around));
    if (row) urls.set(row.key, row.host);
  }

  const absolute = /https?:\\?\/\\?\/[^\s"'<>\\]{4,1600}/gi;
  while ((match = absolute.exec(text)) !== null && urls.size < 64) {
    const around = text.slice(Math.max(0, match.index - 160), Math.min(text.length, absolute.lastIndex + 160));
    if (!PLAYER_CONTEXT.test(around)) continue;
    const row = candidate(match[0], base, true);
    if (row) urls.set(row.key, row.host);
  }

  return {
    declared_player_candidate_count: Math.max(urls.size, indexedPlayerCandidateCount(text)),
    declared_player_hosts: [...new Set(urls.values())].sort().slice(0, 32),
    declared_quality_heights: [...qualities].sort((a, b) => a - b).slice(0, 12),
  };
}

module.exports = { extractResponseVariantHints };
