'use strict';

const { safeAddressReference, safeAddressScope } = require('./address_reference.cjs');
const { observeMediaResponse, safeMediaFacts } = require('./media_observation.cjs');
const { observeHttpResponse, safeHttpFacts } = require('./http_response_observation.cjs');

const PREFIX_LIMIT = 32768;
const HEADER_NAMES = ['accept', 'accept-language', 'user-agent', 'referer', 'origin'];

function safeObservedMediaProbe(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || typeof value.attempted !== 'boolean') return null;
  const source = safeAddressReference(value.source_ref), template = safeAddressReference(value.template_ref);
  if (!source || !template || (!value.attempted && value.outcome !== 'budget_exhausted')) return null;
  const outcome = value.attempted
    ? ['response', 'timeout', 'error'].includes(value.outcome) ? value.outcome : 'error'
    : 'budget_exhausted';
  const media = safeMediaFacts(value.media_observation) || safeMediaFacts({});
  media.bytesSampled = Math.min(PREFIX_LIMIT, media.bytesSampled);
  return {
    attempted: value.attempted, source_ref: source, template_ref: template,
    status: value.attempted && outcome === 'response' && Number.isInteger(value.status)
      && value.status >= 100 && value.status <= 599 ? value.status : null,
    outcome, media_observation: media,
    http_observation: safeHttpFacts(value.http_observation) || safeHttpFacts({}),
  };
}

function httpUrl(value) {
  if (typeof value !== 'string' || value.length > 8192) return '';
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password ? url.href : '';
  } catch (_) { return ''; }
}

function cancelBody(response) {
  try { if (response && response.body) Promise.resolve(response.body.cancel()).catch(() => {}); }
  catch (_) { /* Diagnostics never expose body or cancellation errors. */ }
}

function createObservedMediaProbe({ fetch: fetchResponse, timeoutMs = 2500 }) {
  const timeout = Number.isInteger(timeoutMs) && timeoutMs > 0 ? Math.min(2500, timeoutMs) : 2500;
  let requests = [], candidates = [], requestsTruncated = false, flushed = false, flushPromise = null;

  function recordRequest(url, init, observation) {
    if (flushed || !observation || typeof observation !== 'object' || Array.isArray(observation)) return;
    try {
      const settings = init && typeof init === 'object' ? init : {};
      if (String(settings.method || observation.method || 'GET').toUpperCase() !== 'GET'
          || (observation.method && String(observation.method).toUpperCase() !== 'GET')) return;
      const scope = safeAddressScope(observation.address_scope), ref = safeAddressReference(observation.request_ref);
      if (!scope || !ref) return;
      if (requests.length >= 80) { requestsTruncated = true; return; }
      const request = { scope, ref, referer: safeAddressReference(observation.referer_ref), observation, headers: null };
      requests.push(request);
      const headers = new Headers(settings.headers || {});
      if (!httpUrl(url) || headers.has('cookie') || headers.has('authorization') || headers.has('proxy-authorization')) return;
      const selected = new Headers();
      for (const name of HEADER_NAMES) {
        const value = headers.get(name);
        if (value !== null) {
          if (value.length > 8192) return;
          selected.set(name, value);
        }
      }
      request.headers = selected;
    } catch (_) { /* Invalid templates still count as already requested refs. */ }
  }

  function recordCandidate(url, ref, documentRef, observation) {
    if (flushed || candidates.length >= 8 || !observation || typeof observation !== 'object' || Array.isArray(observation)) return;
    const scope = safeAddressScope(observation.address_scope), source = safeAddressReference(ref);
    const document = safeAddressReference(documentRef), address = httpUrl(url);
    if (!scope || !source || !document || !address || candidates.some(row => row.scope === scope && row.ref === source)) return;
    candidates.push({ url: address, scope, ref: source, document, observation });
  }

  function flush(options = {}) {
    if (flushPromise) return flushPromise;
    flushed = true;
    const observedRequests = requests, observedCandidates = candidates, truncated = requestsTruncated;
    requests = []; candidates = [];
    const settings = options && typeof options === 'object' ? options : {};
    let target = null;
    if (!truncated && settings.streamsReturned === 0 && Number.isFinite(settings.expectedDurationSeconds)
        && settings.expectedDurationSeconds >= 600) {
      for (const candidate of observedCandidates) {
        if (observedRequests.some(row => row.scope === candidate.scope && row.ref === candidate.ref)) continue;
        const template = observedRequests.find(row => {
          const media = safeMediaFacts(row.observation.media_observation);
          return row.scope === candidate.scope && row.referer === candidate.document && row.headers
            && media && media.signature === 'mp4' && media.durationSeconds >= 1 && media.durationSeconds <= 59
            && media.bytesSampled >= 40 && (media.cancelState === 'complete' || media.readState === 'complete');
        });
        if (template) { target = { candidate, template }; break; }
      }
    }
    if (!target) { flushPromise = Promise.resolve(null); return flushPromise; }
    const { candidate, template } = target;
    const safeResult = value => safeObservedMediaProbe({ source_ref: candidate.ref, template_ref: template.ref, ...value });
    const budget = Number.isFinite(settings.deadlineAtMs)
      ? Math.min(timeout, Math.floor(settings.deadlineAtMs - Date.now() - 500)) : timeout;
    if (budget <= 0) {
      const result = safeResult({ attempted: false, outcome: 'budget_exhausted' });
      candidate.observation.observed_media_probe = result;
      flushPromise = Promise.resolve(result);
      return flushPromise;
    }
    flushPromise = (async () => {
      const controller = new AbortController(), diagnostic = {};
      const deadline = Date.now() + budget;
      const cancelled = new WeakMap();
      let expired = false, activeReader = null, activeResponse = null, timer;
      const cancelReader = reader => {
        if (!reader) return Promise.resolve();
        if (cancelled.has(reader)) return cancelled.get(reader);
        let completion;
        try { completion = Promise.resolve(reader.cancel()).catch(() => {}); }
        catch (_) { completion = Promise.resolve(); }
        cancelled.set(reader, completion);
        return completion;
      };
      const cancelResponse = response => {
        if (!response || typeof response !== 'object' || cancelled.has(response)) return;
        cancelled.set(response, Promise.resolve()); cancelBody(response);
      };
      const facts = (outcome, status, http) => safeResult({ attempted: true, outcome, status,
        media_observation: diagnostic.media_observation, http_observation: http });
      const execute = async () => {
        try {
          const headers = new Headers(template.headers);
          headers.set('Range', 'bytes=0-32767');
          const response = await fetchResponse(candidate.url, {
            method: 'GET', headers, credentials: 'omit', signal: controller.signal,
          });
          if (expired) { cancelResponse(response); return null; }
          activeResponse = response;
          const http = await observeHttpResponse(response, candidate.url, {
            timeoutMs: Math.max(1, Math.min(250, deadline - Date.now())),
          });
          if (expired) return null;
          if (response.status < 200 || response.status >= 300) return facts('response', response.status, http);
          if (response.body) {
            const source = response.body.getReader();
            let remaining = PREFIX_LIMIT;
            // Trim before observeMediaResponse sees a chunk: its own prefix
            // limit is larger, and a reader may return a single huge chunk.
            const limited = { body: { getReader: () => ({
              async read() {
                const value = await source.read();
                if (value.done) return value;
                if (!ArrayBuffer.isView(value.value)) throw new Error('invalid media chunk');
                const bytes = new Uint8Array(value.value.buffer, value.value.byteOffset,
                  Math.min(remaining, value.value.byteLength));
                remaining -= bytes.byteLength;
                return { done: false, value: bytes };
              },
              cancel: () => source.cancel(), releaseLock: () => source.releaseLock(),
            }) } };
            activeReader = observeMediaResponse(limited, diagnostic).body.getReader();
            while (remaining > 0) {
              const value = await activeReader.read();
              if (expired) return null;
              if (value.done) break;
            }
            // A native stream may settle cancellation asynchronously. Wait a
            // small bounded interval before snapshotting its actual state.
            let cancellationTimer;
            try {
              await Promise.race([cancelReader(activeReader), new Promise(resolve => {
                cancellationTimer = setTimeout(resolve, Math.max(1, Math.min(100, deadline - Date.now())));
              })]);
            } finally { clearTimeout(cancellationTimer); }
            if (expired) return null;
          }
          return facts('response', response.status, http);
        } catch (_) {
          return facts('error');
        } finally {
          cancelReader(activeReader);
          try { if (activeReader) activeReader.releaseLock(); } catch (_) { /* pending read/cancel */ }
          cancelResponse(activeResponse);
          activeReader = null;
          activeResponse = null;
        }
      };
      try {
        const deadlineResult = new Promise(resolve => { timer = setTimeout(() => {
          expired = true; controller.abort(); cancelReader(activeReader);
          if (!activeReader) cancelResponse(activeResponse);
          resolve(facts('timeout'));
        }, budget); });
        const result = await Promise.race([execute(), deadlineResult]);
        candidate.observation.observed_media_probe = result;
        return result;
      } finally { clearTimeout(timer); }
    })();
    return flushPromise;
  }

  return { recordRequest, recordCandidate, flush };
}

module.exports = { createObservedMediaProbe, safeObservedMediaProbe };
