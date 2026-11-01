'use strict';

// Error-page hints only. Never retain response values or change the original
// stream, headers, status, or playback verdict.
const MAX_BYTES = 8192;
const TIMEOUT_MS = 250;

function contentKind(response) {
  let type;
  try { type = String(response.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase(); }
  catch (_) { return 'unknown'; }
  if (type === 'text/html' || type === 'application/xhtml+xml') return 'html';
  if (/^(?:application|text)\/(?:[a-z0-9!#$&^_.+-]+\+)?json$/.test(type)) return 'json';
  if (/^(?:video|audio)\//.test(type) || /^(?:application\/(?:vnd\.apple\.mpegurl|x-mpegurl|dash\+xml)|text\/vtt)$/.test(type)) return 'media';
  if (/^text\/[a-z0-9!#$&^_.+-]+$/.test(type)) return 'text';
  return /^[a-z0-9!#$&^_.+-]+\/[a-z0-9!#$&^_.+-]+$/.test(type) ? 'binary' : 'unknown';
}

function urlRelation(response, requestUrl) {
  try {
    const request = new URL(requestUrl), effective = new URL(response.url);
    if (!/^https?:$/.test(request.protocol) || !/^https?:$/.test(effective.protocol)) return 'unknown';
    if (request.href === effective.href) return 'same_url';
    return request.origin === effective.origin ? 'same_origin' : 'cross_origin';
  } catch (_) { return 'unknown'; }
}

function pageSignal(prefix) {
  const text = prefix.toString('utf8');
  if (/\bcf-chl-|\bchallenge-platform\b/i.test(text)) return 'challenge_markup';
  if (/\b(?:g-recaptcha|h-captcha|cf-turnstile)\b/i.test(text)) return 'captcha_markup';
  if (/\btoo\s+many\s+requests\b/i.test(text)) return 'rate_limit_text';
  if (/\b(?:access\s+denied|forbidden)\b/i.test(text)) return 'access_denied_text';
  if (/\bnot\s+found\b/i.test(text)) return 'not_found_text';
  return 'none';
}

function boundedOption(value, fallback) {
  return Number.isInteger(value) && value > 0 ? Math.min(fallback, value) : fallback;
}

async function observeHttpResponse(response, requestUrl, options = {}) {
  const result = {
    content_kind: contentKind(response), url_relation: urlRelation(response, requestUrl),
    body_state: 'not_sampled', sampled_bytes: 0, page_signal: 'unknown',
  };
  if (response.ok || !Number.isInteger(response.status) || response.status < 400 || response.status > 599
      || !['html', 'json', 'text'].includes(result.content_kind)) return result;

  const settings = options && typeof options === 'object' ? options : {};
  const maxBytes = boundedOption(settings.maxBytes, MAX_BYTES);
  const timeoutMs = boundedOption(settings.timeoutMs, TIMEOUT_MS);
  const deadline = Date.now() + timeoutMs;
  let reader, prefix = Buffer.alloc(0), complete = false;
  try {
    let clone;
    try { clone = response.clone(); }
    catch (_) { result.body_state = 'unavailable'; return result; }
    if (clone.body === null) {
      result.body_state = 'empty'; result.page_signal = 'none'; return result;
    }
    try { reader = clone.body.getReader(); }
    catch (_) { result.body_state = 'unavailable'; return result; }
    while (prefix.length < maxBytes) {
      const remaining = deadline - Date.now();
      if (remaining <= 0) { result.body_state = 'timeout'; break; }
      let timer;
      const outcome = await Promise.race([
        Promise.resolve().then(() => reader.read()).then(value => ({ value }), () => ({ error: true })),
        new Promise(resolve => { timer = setTimeout(() => resolve({ timeout: true }), remaining); }),
      ]).finally(() => clearTimeout(timer));
      if (outcome.timeout) { result.body_state = 'timeout'; break; }
      if (outcome.error) { result.body_state = 'error'; break; }
      if (outcome.value.done) {
        complete = true; result.body_state = prefix.length ? 'complete' : 'empty'; break;
      }
      const value = outcome.value.value;
      if (!ArrayBuffer.isView(value)) { result.body_state = 'error'; break; }
      const bytes = Buffer.from(value.buffer, value.byteOffset, value.byteLength);
      prefix = Buffer.concat([prefix, bytes.subarray(0, maxBytes - prefix.length)]);
      result.body_state = 'sampled';
    }
    result.sampled_bytes = prefix.length;
    if (prefix.length || complete) result.page_signal = pageSignal(prefix);
    return result;
  } catch (_) {
    result.body_state = 'error'; result.sampled_bytes = prefix.length;
    if (prefix.length) result.page_signal = pageSignal(prefix);
    return result;
  } finally {
    if (reader) {
      // A cloned response is a tee: cancellation can wait for the original
      // consumer. Request it without making diagnostics wait on that consumer.
      if (!complete) {
        try { Promise.resolve(reader.cancel()).catch(() => {}); } catch (_) { /* no response data */ }
      }
      try { reader.releaseLock(); } catch (_) { /* pending cancellation */ }
    }
  }
}

module.exports = { observeHttpResponse };
