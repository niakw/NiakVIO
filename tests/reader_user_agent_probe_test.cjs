'use strict';
const assert = require('node:assert/strict');
const { createReaderUserAgentProbe, safeReaderProbe } = require('../scripts/reader_user_agent_probe.cjs');

const PRIVATE = 'PRIVATE_TOKEN_COOKIE_BODY';
const URL = 'https://reader.test/embed?id=' + PRIVATE;
const request = ua => ({ method: 'GET', redirect: 'follow', credentials: 'include', cache: 'no-store',
  headers: new Headers({ 'User-Agent': ua, Referer: 'https://provider.test/' + PRIVATE,
    Cookie: 'session=' + PRIVATE, Accept: 'text/html', 'X-Test': PRIVATE }),
});
const html = (status = 200, body = '<p>content</p>') => new Response(body, {
  status, headers: { 'content-type': 'text/html; charset=utf-8', 'set-cookie': PRIVATE },
});
function prior(probe, ua = 'Observed HTML Agent') {
  const response = html();
  probe.record(response, 'https://provider.test/home', request(ua), { stage: 'episode', status: 200 });
  return response;
}
function blocked(probe, init = request('Different Reader Agent'), stage = 'player') {
  const response = html(403, 'Access denied ' + PRIVATE);
  const observation = { stage, status: 403 };
  probe.record(response, URL, init, observation);
  return { response, observation };
}
function privateFree(value) {
  const encoded = JSON.stringify(value);
  for (const forbidden of [PRIVATE, 'reader.test', 'provider.test', 'Observed HTML Agent', 'Different Reader Agent']) {
    assert.ok(!encoded.includes(forbidden), forbidden);
  }
}

(async () => {
  let calls = 0, diagnosticCancelled = 0;
  const originalSignal = new AbortController().signal;
  const init = { ...request('Different Reader Agent'), signal: originalSignal };
  const snapshot = [...init.headers];
  const probe = createReaderUserAgentProbe({ fetch: async (url, options) => {
    calls++;
    assert.equal(url, URL);
    for (const key of ['method', 'redirect', 'credentials', 'cache']) assert.equal(options[key], init[key]);
    assert.notEqual(options.signal, originalSignal);
    assert.equal(options.signal.aborted, false);
    const expected = new Headers(init.headers); expected.set('User-Agent', 'Observed HTML Agent');
    assert.deepEqual([...options.headers], [...expected]);
    const response = html(200);
    response.body.cancel = () => { diagnosticCancelled++; return new Promise(() => {}); };
    return response;
  } });
  const priorResponse = prior(probe);
  const failure = blocked(probe, init);
  assert.equal(calls, 0, 'record must never fetch');
  assert.equal(failure.observation.reader_user_agent_probe, undefined);
  assert.equal(failure.response.bodyUsed, false);
  const result = await probe.flush();
  assert.equal(calls, 1);
  assert.equal(diagnosticCancelled, 1, 'body cancellation must not block flush');
  assert.equal(result.outcome, 'response');
  assert.equal(result.status, 200);
  assert.equal(result.http_observation.content_kind, 'html');
  assert.equal(result.http_observation.body_state, 'not_sampled');
  assert.deepEqual(failure.observation.reader_user_agent_probe, result);
  assert.equal(failure.observation.status, 403);
  assert.equal(failure.response.status, 403);
  assert.deepEqual([...init.headers], snapshot);
  assert.equal(failure.response.headers.get('set-cookie'), PRIVATE);
  assert.equal(await failure.response.text(), 'Access denied ' + PRIVATE);
  assert.equal(await priorResponse.text(), '<p>content</p>');
  privateFree(result);
  await probe.flush();
  blocked(probe);
  await probe.flush();
  assert.equal(calls, 1, 'one instance cannot perform a second probe');

  const unavailable = createReaderUserAgentProbe({ fetch: () => { throw new Error('unexpected'); } });
  const noProfile = blocked(unavailable);
  assert.deepEqual(noProfile.observation.reader_user_agent_probe, safeReaderProbe({ attempted: false }));
  assert.equal(await unavailable.flush(), null);
  assert.equal(await noProfile.response.text(), 'Access denied ' + PRIVATE);

  for (const mode of ['post', 'nonplayer', 'success', 'same-agent', 'long-agent', 'nonhtml-profile']) {
    let fetched = false;
    const skipped = createReaderUserAgentProbe({ fetch: () => { fetched = true; } });
    if (mode === 'long-agent') prior(skipped, 'a'.repeat(513));
    else if (mode === 'nonhtml-profile') skipped.record(new Response('data', { headers: { 'content-type': 'application/json' } }),
      URL, request('Observed HTML Agent'), { stage: 'episode', status: 200 });
    else prior(skipped, mode === 'same-agent' ? 'Different Reader Agent' : 'Observed HTML Agent');
    if (mode === 'success') skipped.record(html(), URL, request('Different Reader Agent'), { stage: 'player', status: 200 });
    else blocked(skipped, { ...request('Different Reader Agent'), method: mode === 'post' ? 'POST' : 'GET' },
      mode === 'nonplayer' ? 'episode' : 'player');
    await skipped.flush();
    assert.equal(fetched, false, mode);
  }

  let inheritedPostFetched = false;
  const inheritedPost = createReaderUserAgentProbe({ fetch: () => { inheritedPostFetched = true; } });
  prior(inheritedPost);
  const inheritedRequest = new Request(URL, { method: 'POST', body: PRIVATE });
  const inheritedResponse = html(403);
  const inheritedObservation = { status: 403, stage: 'player', method: inheritedRequest.method };
  inheritedPost.record(inheritedResponse, inheritedRequest.url, {}, inheritedObservation);
  assert.equal(await inheritedPost.flush(), null);
  assert.equal(inheritedPostFetched, false, 'effective Request POST must not become a GET probe');
  assert.equal(inheritedObservation.reader_user_agent_probe, undefined);
  assert.equal(await inheritedRequest.text(), PRIVATE);
  assert.equal(await inheritedResponse.text(), '<p>content</p>');

  let exhaustedFetched = false;
  const exhausted = createReaderUserAgentProbe({ fetch: () => { exhaustedFetched = true; } });
  prior(exhausted); const exhaustedFailure = blocked(exhausted);
  const exhaustedResult = await exhausted.flush({ deadlineAtMs: Date.now() + 400 });
  assert.equal(exhaustedFetched, false);
  assert.equal(exhaustedResult.attempted, false);
  assert.equal(exhaustedResult.outcome, 'budget_exhausted');
  assert.equal(exhaustedResult.status, null);
  assert.equal(exhaustedFailure.observation.status, 403);
  assert.equal(exhaustedFailure.response.status, 403);
  assert.equal(exhaustedFailure.response.headers.get('set-cookie'), PRIVATE);
  assert.equal(await exhaustedFailure.response.text(), 'Access denied ' + PRIVATE);
  assert.deepEqual(safeReaderProbe(exhaustedResult), exhaustedResult);
  privateFree(exhaustedResult);

  let budgetSignal;
  const budgeted = createReaderUserAgentProbe({ fetch: (_url, options) => {
    budgetSignal = options.signal; return new Promise(() => {});
  } });
  prior(budgeted); const budgetedFailure = blocked(budgeted);
  const parentDeadline = Date.now() + 650;
  const budgetStart = Date.now();
  const budgetedResult = await budgeted.flush({ deadlineAtMs: parentDeadline });
  assert.equal(budgetedResult.outcome, 'timeout');
  assert.equal(budgetSignal.aborted, true);
  assert.ok(Date.now() - budgetStart < 300, 'parent deadline must shorten the configured timeout');
  assert.ok(parentDeadline - Date.now() >= 450, 'reserve 500ms for emission and close (allow scheduler jitter)');
  assert.equal(await budgetedFailure.response.text(), 'Access denied ' + PRIVATE);
  privateFree(budgetedResult);

  let repeatedCalls = 0;
  const repeated = createReaderUserAgentProbe({ fetch: async () => { repeatedCalls++; return html(404, 'Not found'); } });
  prior(repeated);
  const failures = Array.from({ length: 10 }, () => blocked(repeated));
  const [first, second] = await Promise.all([repeated.flush(), repeated.flush()]);
  assert.equal(repeatedCalls, 1);
  assert.equal(first, second);
  assert.equal(first.http_observation.page_signal, 'not_found_text');
  assert.equal(failures.filter(value => value.observation.reader_user_agent_probe?.attempted).length, 1);
  privateFree(first);

  let lateResolve, lateCancelled = 0, timedSignal;
  const timed = createReaderUserAgentProbe({ timeoutMs: 25, fetch: (_url, options) => {
    timedSignal = options.signal;
    return new Promise(resolve => { lateResolve = resolve; });
  } });
  prior(timed); const timedFailure = blocked(timed);
  const start = Date.now(), timedResult = await timed.flush();
  assert.ok(Date.now() - start < 500, 'fetch ignoring AbortSignal must still time out');
  assert.equal(timedResult.outcome, 'timeout');
  assert.equal(timedSignal.aborted, true);
  assert.equal(timedResult.status, null);
  privateFree(timedResult);
  const late = html(); late.body.cancel = () => { lateCancelled++; return Promise.resolve(); };
  lateResolve(late);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(lateCancelled, 1, 'late responses must be cancelled');
  assert.equal(timedFailure.observation.reader_user_agent_probe.outcome, 'timeout');

  let cappedSignal;
  const capped = createReaderUserAgentProbe({ timeoutMs: 999999, fetch: (_url, options) => {
    cappedSignal = options.signal; return new Promise(() => {});
  } });
  prior(capped); const cappedFailure = blocked(capped);
  const cappedStart = Date.now();
  assert.equal((await capped.flush()).outcome, 'timeout');
  assert.ok(Date.now() - cappedStart < 3000, 'without parent deadline timeout must still be capped at 2500ms');
  assert.equal(cappedSignal.aborted, true);
  assert.equal(await cappedFailure.response.text(), 'Access denied ' + PRIVATE);

  const broken = createReaderUserAgentProbe({ fetch: async () => { throw new Error(PRIVATE); } });
  prior(broken); blocked(broken);
  const error = await broken.flush();
  assert.equal(error.outcome, 'error'); assert.equal(error.status, null); privateFree(error);

  const forged = safeReaderProbe({ attempted: true, profile_source: PRIVATE, changed_header: PRIVATE,
    status: 200, outcome: 'response', url: URL, headers: { Cookie: PRIVATE }, error: PRIVATE,
    http_observation: { content_kind: 'html', url_relation: 'same_origin', body_state: 'complete',
      page_signal: 'access_denied_text', sampled_bytes: 99999, raw: PRIVATE } });
  assert.equal(forged.profile_source, 'prior_successful_html');
  assert.equal(forged.changed_header, 'user-agent');
  assert.equal(forged.http_observation.sampled_bytes, 8192); privateFree(forged);
  const invalid = safeReaderProbe({ attempted: 'true', status: 777, outcome: PRIVATE, http_observation: { raw: PRIVATE } });
  assert.equal(invalid.attempted, false); assert.equal(invalid.outcome, 'missing_profile');
  assert.equal(invalid.status, null); privateFree(invalid);
  assert.equal(safeReaderProbe(null), null); assert.equal(safeReaderProbe([]), null);
  console.log('Reader UA probe: deferred single GET, parent deadline margin, preserved inputs, timeout/cancel and public projection passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
