'use strict';

// Shared strict direct-media proof used by Mobile/Desktop platform probes.
// A top-level #EXTM3U is not playback proof: master variants, external audio
// renditions and the first media segments are traversed with bounded requests.

function clean(value) {
  return String(value == null ? '' : value).replace(/^\uFEFF/, '').replace(/^ï»¿/, '').trimStart();
}

function sanitize(value, limit = 80) {
  return String(value || '').replace(/(?:https?|magnet|acestream|torrent):[^\s"']+/gi, '[endpoint]').replace(/[\r\n\t]+/g, ' ').slice(0, limit);
}

function absolute(raw, base) {
  try { return new URL(String(raw || '').trim(), base).toString(); } catch { return null; }
}

async function readLimited(response, limit = 196608) {
  if (!response?.body) return Buffer.alloc(0);
  const reader = response.body.getReader();
  const chunks = [];
  let length = 0;
  try {
    while (length < limit) {
      const { done, value } = await reader.read();
      if (done) break;
      const remaining = limit - length;
      const slice = value.byteLength > remaining ? value.slice(0, remaining) : value;
      chunks.push(Buffer.from(slice));
      length += slice.byteLength;
      if (value.byteLength > remaining) break;
    }
  } finally {
    try { await reader.cancel(); } catch {}
  }
  return Buffer.concat(chunks);
}

function parseAttributes(line) {
  const out = {};
  for (const match of String(line || '').matchAll(/([A-Z0-9-]+)=("[^"]*"|[^,]*)/gi)) {
    out[String(match[1]).toUpperCase()] = String(match[2] || '').replace(/^"|"$/g, '');
  }
  return out;
}

function parseHls(text, baseUrl) {
  const value = clean(text);
  const lines = value.split(/\r?\n/).map((line) => line.trim());
  const header = lines.some((line) => line === '#EXTM3U');
  const variants = [];
  const audio = [];
  const segments = [];
  let mediaTags = 0;
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (/^#EXT-X-STREAM-INF\s*:/i.test(line)) {
      for (let next = index + 1; next < lines.length; next += 1) {
        if (!lines[next]) continue;
        if (lines[next].startsWith('#')) continue;
        const url = absolute(lines[next], baseUrl);
        if (url && !variants.includes(url)) variants.push(url);
        break;
      }
      continue;
    }
    if (/^#EXT-X-MEDIA\s*:/i.test(line)) {
      const attrs = parseAttributes(line.slice(line.indexOf(':') + 1));
      if (String(attrs.TYPE || '').toUpperCase() === 'AUDIO' && attrs.URI) {
        const url = absolute(attrs.URI, baseUrl);
        if (url && !audio.includes(url)) audio.push(url);
      }
      continue;
    }
    if (/^#EXTINF\s*:/i.test(line) || /^#EXT-X-(?:PART|MAP)\s*:/i.test(line)) mediaTags += 1;
    if (line && !line.startsWith('#') && index > 0 && /^#EXTINF\s*:/i.test(lines[index - 1])) {
      const url = absolute(line, baseUrl);
      if (url && !segments.includes(url)) segments.push(url);
    }
  }
  // LL-HLS PART/MAP URIs may be attributes instead of following lines.
  for (const line of lines) {
    if (!/^#EXT-X-(?:PART|MAP)\s*:/i.test(line)) continue;
    const attrs = parseAttributes(line.slice(line.indexOf(':') + 1));
    if (attrs.URI) {
      const url = absolute(attrs.URI, baseUrl);
      if (url && !segments.includes(url)) segments.push(url);
    }
  }
  return {
    valid: header && (variants.length > 0 || mediaTags > 0),
    master: variants.length > 0,
    variants,
    audio,
    segments,
  };
}

function binaryKind(buffer) {
  if (buffer.length >= 12 && buffer.subarray(4, 8).toString('ascii') === 'ftyp') return 'mp4';
  if (buffer.length >= 4 && buffer[0] === 0x1a && buffer[1] === 0x45 && buffer[2] === 0xdf && buffer[3] === 0xa3) return 'matroska_webm';
  if (buffer.length >= 376 && buffer[0] === 0x47 && buffer[188] === 0x47) return 'mpegts';
  return null;
}

function inconclusiveError(error) {
  const name = String(error?.name || '');
  const code = String(error?.code || '');
  return /Abort|Timeout|Network|Fetch/i.test(name) || /TIMEOUT|ECONN|ENOTFOUND|EAI_AGAIN|NETWORK/i.test(code);
}

async function boundedFetch(url, headers, options, limit) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeoutMs);
  try {
    const response = await options.guardedFetch(
      options.fetchImpl,
      url,
      { method: 'GET', headers, redirect: 'follow', signal: controller.signal },
      { maxRedirects: options.maxRedirects },
    );
    const body = await readLimited(response, limit);
    return { response, body, text: clean(body.toString('utf8')) };
  } finally {
    clearTimeout(timer);
  }
}

async function probeSegment(url, headers, options) {
  try {
    const { response, body, text } = await boundedFetch(url, headers, options, 65536);
    if (!(response.status === 200 || response.status === 206)) return { playable: false, inconclusive: false, reason: `http_${response.status}` };
    const type = String(response.headers.get('content-type') || '').toLowerCase();
    if (/text\/html|application\/(?:json|xhtml)|^text\/plain/.test(type) || /^<!doctype html|^<html/i.test(text)) {
      return { playable: false, inconclusive: false, reason: 'segment_non_media_document' };
    }
    return { playable: Boolean(binaryKind(body) || body.length > 0), inconclusive: false, reason: body.length ? null : 'empty_segment' };
  } catch (error) {
    return { playable: false, inconclusive: inconclusiveError(error), reason: sanitize(error?.name || error?.code || error?.message || 'segment_error') };
  }
}

async function probeHlsText(text, baseUrl, headers, options, depth = 0) {
  const parsed = parseHls(text, baseUrl);
  if (!parsed.valid) return { playable: false, inconclusive: false, kind: 'hls_invalid_structure', hls_master: parsed.master };
  if (depth > 2) return { playable: false, inconclusive: false, kind: 'hls_nested_too_deep', hls_master: parsed.master };

  let videoSegment = null;
  if (parsed.master) {
    const variantUrl = parsed.variants[0];
    try {
      const child = await boundedFetch(variantUrl, headers, options, 196608);
      if (!(child.response.status === 200 || child.response.status === 206)) {
        return { playable: false, inconclusive: false, kind: `hls_variant_http_${child.response.status}`, hls_master: true };
      }
      const childProbe = await probeHlsText(child.text, child.response.url || variantUrl, headers, options, depth + 1);
      if (!childProbe.playable) return { ...childProbe, hls_master: true, hls_variant_playable: false };
      videoSegment = true;
    } catch (error) {
      return { playable: false, inconclusive: inconclusiveError(error), kind: sanitize(error?.name || error?.code || 'hls_variant_error'), hls_master: true, hls_variant_playable: false };
    }
  } else if (parsed.segments.length) {
    const segment = await probeSegment(parsed.segments[0], headers, options);
    if (!segment.playable) return { playable: false, inconclusive: segment.inconclusive, kind: segment.reason || 'hls_segment_invalid', hls_master: false, hls_segment_playable: false };
    videoSegment = true;
  } else {
    return { playable: false, inconclusive: false, kind: 'hls_no_media_segment', hls_master: false };
  }

  if (parsed.audio.length) {
    const audioUrl = parsed.audio[0];
    try {
      const audio = await boundedFetch(audioUrl, headers, options, 196608);
      if (!(audio.response.status === 200 || audio.response.status === 206)) {
        return { playable: false, inconclusive: false, kind: `hls_audio_http_${audio.response.status}`, hls_master: parsed.master, hls_audio_playable: false };
      }
      const audioParsed = parseHls(audio.text, audio.response.url || audioUrl);
      if (!audioParsed.valid || audioParsed.master) {
        const audioProbe = await probeHlsText(audio.text, audio.response.url || audioUrl, headers, options, depth + 1);
        if (!audioProbe.playable) return { ...audioProbe, hls_master: parsed.master, hls_audio_playable: false };
      } else if (audioParsed.segments.length) {
        const segment = await probeSegment(audioParsed.segments[0], headers, options);
        if (!segment.playable) return { playable: false, inconclusive: segment.inconclusive, kind: segment.reason || 'hls_audio_segment_invalid', hls_master: parsed.master, hls_audio_playable: false };
      } else {
        return { playable: false, inconclusive: false, kind: 'hls_audio_no_segment', hls_master: parsed.master, hls_audio_playable: false };
      }
    } catch (error) {
      return { playable: false, inconclusive: inconclusiveError(error), kind: sanitize(error?.name || error?.code || 'hls_audio_error'), hls_master: parsed.master, hls_audio_playable: false };
    }
  }

  return {
    playable: true,
    inconclusive: false,
    kind: 'hls',
    hls_master: parsed.master,
    hls_variant_playable: parsed.master ? true : null,
    hls_segment_playable: videoSegment,
    hls_external_audio_count: parsed.audio.length,
    hls_audio_playable: parsed.audio.length ? true : null,
  };
}

async function probeDirectMedia(stream, supplied = {}) {
  const rawUrl = String(stream?.url || '').trim();
  if (!/^https?:\/\//i.test(rawUrl)) return { playable: false, inconclusive: false, kind: 'unsupported_url', host: null, status: null };
  let host;
  try { host = new URL(rawUrl).hostname.toLowerCase(); } catch { return { playable: false, inconclusive: false, kind: 'invalid_url', host: null, status: null }; }
  const options = {
    guardedFetch: supplied.guardedFetch,
    fetchImpl: supplied.fetchImpl || globalThis.fetch,
    timeoutMs: Math.max(3000, Math.min(Number(supplied.timeoutMs || 18000), 30000)),
    maxRedirects: Math.max(1, Math.min(Number(supplied.maxRedirects || 5), 8)),
  };
  if (typeof options.guardedFetch !== 'function' || typeof options.fetchImpl !== 'function') throw new TypeError('guardedFetch and fetchImpl are required');
  const headers = Object.fromEntries(Object.entries(stream?.headers || {}).map(([key, value]) => [String(key), String(value)]));
  const manifestLike = /\.(?:m3u8|mpd)(?:$|[?#])/i.test(rawUrl);
  if (!manifestLike && !Object.keys(headers).some((key) => key.toLowerCase() === 'range')) headers.Range = 'bytes=0-196607';
  try {
    const top = await boundedFetch(rawUrl, headers, options, 196608);
    const status = top.response.status;
    const type = String(top.response.headers.get('content-type') || '').toLowerCase();
    const finalUrl = top.response.url || rawUrl;
    if (!(status === 200 || status === 206)) return { playable: false, inconclusive: false, kind: `http_${status}`, host, status };
    if (top.text.startsWith('#EXTM3U') || /mpegurl/.test(type) || /\.m3u8(?:$|[?#])/i.test(finalUrl)) {
      return { ...(await probeHlsText(top.text, finalUrl, headers, options)), host, status };
    }
    if (/^<\?xml[\s\S]*?<MPD[\s>]|^<MPD[\s>]/i.test(top.text) || /application\/(?:dash\+xml|mpd)/.test(type)) {
      const valid = /<MPD[\s>]/i.test(top.text) && /<(?:Representation|AdaptationSet)\b/i.test(top.text);
      return { playable: valid, inconclusive: false, kind: valid ? 'dash' : 'dash_invalid_structure', host, status };
    }
    const binary = binaryKind(top.body);
    if (binary) return { playable: true, inconclusive: false, kind: binary, host, status };
    if (/text\/html|application\/(?:json|xhtml)|^text\/plain/.test(type) || /^<!doctype html|^<html/i.test(top.text)) {
      return { playable: false, inconclusive: false, kind: 'non_media_document', host, status };
    }
    if (/^video\//.test(type)) return { playable: true, inconclusive: false, kind: type.split(';')[0], host, status };
    return { playable: false, inconclusive: false, kind: 'unverified_payload', host, status };
  } catch (error) {
    return { playable: false, inconclusive: inconclusiveError(error), kind: sanitize(error?.name || error?.code || error?.message || 'probe_error'), host, status: null };
  }
}

module.exports = { parseHls, probeDirectMedia };
