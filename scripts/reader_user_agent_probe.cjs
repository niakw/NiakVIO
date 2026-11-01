'use strict';

const { observeHttpResponse, safeHttpFacts } = require('./http_response_observation.cjs');

const UNKNOWN_HTTP = () => safeHttpFacts({});

function safeReaderProbe(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const attempted = value.attempted === true;
  const outcome = attempted
    ? ['response', 'timeout', 'error'].includes(value.outcome) ? value.outcome : 'error'
    : 'missing_profile';
  return {
    attempted, profile_source: 'prior_successful_html', changed_header: 'user-agent',
    status: attempted && outcome === 'response' && Number.isInteger(value.status)
      && value.status >= 100 && value.status <= 599 ? value.status : null,
    outcome,
    http_observation: safeHttpFacts(value.http_observation) || UNKNOWN_HTTP(),
  };
}

function cancelBody(response) {
  try { if (response && response.body) Promise.resolve(response.body.cancel()).catch(() => {}); }
  catch (_) { /* Diagnostics never expose response or cancellation errors. */ }
}

function createReaderUserAgentProbe({ fetch: fetchResponse, timeoutMs = 2500 }) {
  const timeout = Number.isInteger(timeoutMs) && timeoutMs > 0 ? Math.min(2500, timeoutMs) : 2500;
  let profiles = [], queued = null, flushed = false, flushPromise = null;

  function record(response, requestUrl, init, observation) {
    if (flushed || !observation || typeof observation !== 'object') return;
    try {
      const settings = init && typeof init === 'object' ? init : {};
      const headers = new Headers(settings.headers || {});
      const userAgent = headers.get('user-agent') || '';
      const type = String(response.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase();
      if (response.status >= 200 && response.status <= 299
          && ['text/html', 'application/xhtml+xml'].includes(type)) {
        if (userAgent && userAgent.length <= 512 && !profiles.includes(userAgent) && profiles.length < 3) {
          profiles.push(userAgent);
        }
        return;
      }
      if (queued || response.status !== 403 || observation.status !== 403 || observation.stage !== 'player'
          || String(settings.method || 'GET').toUpperCase() !== 'GET') return;
      const alternate = profiles.find(profile => profile !== userAgent);
      if (!alternate) {
        observation.reader_user_agent_probe = safeReaderProbe({ attempted: false });
        return;
      }
      queued = { requestUrl, init: { ...settings, headers }, userAgent: alternate, observation };
    } catch (_) { /* Malformed diagnostic inputs must not change provider execution. */ }
  }

  function flush() {
    if (flushPromise) return flushPromise;
    flushed = true;
    const target = queued;
    queued = null;
    profiles = [];
    if (!target) {
      flushPromise = Promise.resolve(null);
      return flushPromise;
    }
    flushPromise = (async () => {
      const controller = new AbortController();
      const deadline = Date.now() + timeout;
      const cancelled = new WeakSet();
      let expired = false, activeResponse = null, timer;
      const cancelOnce = response => {
        if (response && typeof response === 'object' && !cancelled.has(response)) {
          cancelled.add(response); cancelBody(response);
        }
      };
      const execute = async () => {
        let response;
        try {
          const headers = new Headers(target.init.headers);
          headers.set('User-Agent', target.userAgent);
          response = await fetchResponse(target.requestUrl, { ...target.init, headers, signal: controller.signal });
          if (expired) { cancelOnce(response); return null; }
          activeResponse = response;
          const http = await observeHttpResponse(response, target.requestUrl, {
            timeoutMs: Math.max(1, Math.min(250, deadline - Date.now())),
          });
          return safeReaderProbe({ attempted: true, outcome: 'response', status: response.status,
            http_observation: http });
        } catch (_) {
          return safeReaderProbe({ attempted: true, outcome: 'error' });
        } finally {
          cancelOnce(response); activeResponse = null;
        }
      };
      try {
        const result = await Promise.race([
          execute(),
          new Promise(resolve => { timer = setTimeout(() => {
            expired = true;
            controller.abort();
            cancelOnce(activeResponse);
            resolve(safeReaderProbe({ attempted: true, outcome: 'timeout' }));
          }, timeout); }),
        ]);
        target.observation.reader_user_agent_probe = result;
        return result;
      } finally {
        clearTimeout(timer);
        profiles = []; queued = null;
      }
    })();
    return flushPromise;
  }

  return { record, flush };
}

module.exports = { createReaderUserAgentProbe, safeReaderProbe };
