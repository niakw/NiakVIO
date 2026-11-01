'use strict';
const assert = require('node:assert/strict');
const { observeHttpResponse } = require('../scripts/http_response_observation.cjs');

function atUrl(response, url) {
  Object.defineProperty(response, 'url', { value: url });
  return response;
}

function instrument(response) {
  const counts = { clones: 0, reads: 0, cancels: 0 };
  const originalClone = response.clone.bind(response);
  response.clone = () => {
    counts.clones++;
    const clone = originalClone();
    if (clone.body) {
      const getReader = clone.body.getReader.bind(clone.body);
      clone.body.getReader = () => {
        const reader = getReader();
        const read = reader.read.bind(reader), cancel = reader.cancel.bind(reader);
        reader.read = (...args) => { counts.reads++; return read(...args); };
        reader.cancel = (...args) => { counts.cancels++; return cancel(...args); };
        return reader;
      };
    }
    return clone;
  };
  return counts;
}

(async () => {
  const sensitive = 'PRIVATE_TOKEN_COOKIE_BODY';
  for (const [body, type, signal] of [
    ['<script src="/cdn-cgi/challenge-platform/h/g/orchestrate"></script>', 'text/html', 'challenge_markup'],
    ['<div id="cf-chl-widget">loading</div>', 'application/xhtml+xml', 'challenge_markup'],
    ['<div class="g-recaptcha"></div>', 'text/html', 'captcha_markup'],
    ['<div class="h-captcha"></div>', 'text/html', 'captcha_markup'],
    ['<div class="cf-turnstile"></div>', 'text/html', 'captcha_markup'],
    ['Access denied', 'text/plain; charset=utf-8', 'access_denied_text'],
    ['403 Forbidden', 'text/html', 'access_denied_text'],
    ['{"message":"Not found"}', 'application/problem+json', 'not_found_text'],
    ['Too many requests', 'text/plain', 'rate_limit_text'],
    ['<p>unrecognized error</p>', 'text/html', 'none'],
  ]) {
    const raw = body + ' ' + sensitive;
    const response = atUrl(new Response(raw, { status: 403, headers: {
      'content-type': type, 'set-cookie': sensitive, 'x-private-token': sensitive,
    } }), 'https://reader.test/error?token=' + sensitive);
    const headers = response.headers;
    const facts = await observeHttpResponse(response, 'https://reader.test/embed');
    assert.equal(facts.page_signal, signal);
    assert.equal(facts.body_state, 'complete');
    assert.equal(facts.sampled_bytes, Buffer.byteLength(raw));
    assert.equal(response.headers, headers);
    assert.equal(response.headers.get('set-cookie'), sensitive);
    assert.equal(response.bodyUsed, false);
    assert.equal(await response.text(), raw);
    assert.deepEqual(Object.keys(facts).sort(), ['body_state', 'content_kind', 'page_signal', 'sampled_bytes', 'url_relation']);
    assert.ok(!JSON.stringify(facts).includes(sensitive));
    assert.ok(!JSON.stringify(facts).includes('reader.test'));
  }

  let successPulls = 0;
  const success = atUrl(new Response(new ReadableStream({
    pull(controller) { successPulls++; controller.enqueue(new TextEncoder().encode('success')); controller.close(); },
  }, { highWaterMark: 0 }), { status: 200, headers: { 'content-type': 'text/html' } }), 'https://reader.test/embed');
  const successCounts = instrument(success);
  const successFacts = await observeHttpResponse(success, 'https://reader.test/embed');
  assert.deepEqual(successCounts, { clones: 0, reads: 0, cancels: 0 });
  assert.equal(successPulls, 0);
  assert.equal(successFacts.body_state, 'not_sampled');
  assert.equal(successFacts.url_relation, 'same_url');
  assert.equal(await success.text(), 'success');

  const redirect = new Response(sensitive, { status: 302, headers: { 'content-type': 'text/html' } });
  const redirectCounts = instrument(redirect);
  assert.equal((await observeHttpResponse(redirect, 'https://reader.test')).body_state, 'not_sampled');
  assert.deepEqual(redirectCounts, { clones: 0, reads: 0, cancels: 0 });
  assert.equal(await redirect.text(), sensitive);

  for (const [url, requested, relation] of [
    ['https://reader.test:443/embed', 'https://reader.test/embed', 'same_url'],
    ['https://reader.test/login', 'https://reader.test/embed', 'same_origin'],
    ['https://other.test/error', 'https://reader.test/embed', 'cross_origin'],
    ['', 'https://reader.test/embed', 'unknown'],
    ['https://reader.test/embed', 'not a url', 'unknown'],
    ['file:///tmp/private', 'https://reader.test/embed', 'unknown'],
  ]) {
    const response = atUrl(new Response(null), url);
    assert.equal((await observeHttpResponse(response, requested)).url_relation, relation);
  }

  for (const [type, kind] of [
    ['video/mp4', 'media'], ['audio/mpeg', 'media'], ['application/vnd.apple.mpegurl', 'media'],
    ['application/dash+xml', 'media'], ['application/octet-stream', 'binary'], ['image/png', 'binary'],
    ['', 'unknown'],
  ]) {
    const response = new Response(sensitive, { status: 403, headers: { 'content-type': type } });
    const counts = instrument(response);
    const facts = await observeHttpResponse(response, 'https://reader.test');
    assert.equal(facts.content_kind, kind);
    assert.equal(facts.body_state, 'not_sampled');
    assert.deepEqual(counts, { clones: 0, reads: 0, cancels: 0 });
    assert.equal(await response.text(), sensitive);
  }

  const largeBytes = Buffer.alloc(20000, 65);
  const large = new Response(new ReadableStream({ start(controller) { controller.enqueue(largeBytes); controller.close(); } }), {
    status: 500, headers: { 'content-type': 'text/html' },
  });
  const largeCounts = instrument(large);
  const largeFacts = await observeHttpResponse(large, 'https://reader.test', { maxBytes: 999999, timeoutMs: 999999 });
  assert.equal(largeFacts.sampled_bytes, 8192);
  assert.equal(largeFacts.body_state, 'sampled');
  assert.equal(largeCounts.cancels, 1);
  assert.deepEqual(Buffer.from(await large.arrayBuffer()), largeBytes);

  let stalledController;
  const stalled = new Response(new ReadableStream({ start(controller) {
    stalledController = controller;
    controller.enqueue(new TextEncoder().encode('Access denied'));
  } }), { status: 403, headers: { 'content-type': 'text/plain' } });
  const stalledCounts = instrument(stalled);
  const start = Date.now();
  const stalledFacts = await observeHttpResponse(stalled, 'https://reader.test', { timeoutMs: 30 });
  assert.ok(Date.now() - start < 500, 'cloned cancellation must not await original consumption');
  assert.equal(stalledFacts.body_state, 'timeout');
  assert.equal(stalledFacts.page_signal, 'access_denied_text');
  assert.equal(stalledFacts.sampled_bytes, 13);
  assert.equal(stalledCounts.cancels, 1);
  stalledController.close();
  assert.equal(await stalled.text(), 'Access denied');

  let cappedController;
  const capped = new Response(new ReadableStream({ start(controller) { cappedController = controller; } }), {
    status: 503, headers: { 'content-type': 'text/html' },
  });
  const cappedStart = Date.now();
  const cappedFacts = await observeHttpResponse(capped, 'https://reader.test', { timeoutMs: 999999 });
  assert.ok(Date.now() - cappedStart < 800, 'timeout option must remain capped at 250ms');
  assert.equal(cappedFacts.body_state, 'timeout');
  assert.equal(cappedFacts.sampled_bytes, 0);
  assert.equal(cappedFacts.page_signal, 'unknown');
  cappedController.close();
  assert.equal(await capped.text(), '');

  const errored = new Response(new ReadableStream({ start(controller) { controller.error(new Error(sensitive)); } }), {
    status: 502, headers: { 'content-type': 'text/html' },
  });
  const errorFacts = await observeHttpResponse(errored, 'https://reader.test');
  assert.equal(errorFacts.body_state, 'error');
  assert.equal(errorFacts.page_signal, 'unknown');
  assert.ok(!JSON.stringify(errorFacts).includes(sensitive));
  await assert.rejects(errored.text());

  const empty = new Response(null, { status: 404, headers: { 'content-type': 'text/html' } });
  assert.equal((await observeHttpResponse(empty, 'https://reader.test')).body_state, 'empty');
  const used = new Response('used', { status: 403, headers: { 'content-type': 'text/html' } });
  await used.text();
  assert.equal((await observeHttpResponse(used, 'https://reader.test')).body_state, 'unavailable');

  const limited = new Response('forbidden beyond bound', { status: 403, headers: { 'content-type': 'text/plain' } });
  const limitedFacts = await observeHttpResponse(limited, 'https://reader.test', { maxBytes: 3 });
  assert.equal(limitedFacts.sampled_bytes, 3);
  assert.equal(limitedFacts.page_signal, 'none');
  assert.equal(await limited.text(), 'forbidden beyond bound');
  console.log('HTTP response observation: bounded error-only clone, enum privacy, timeout/cancel and original-body preservation passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
