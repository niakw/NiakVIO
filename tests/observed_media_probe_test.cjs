'use strict';

const assert = require('node:assert/strict');
const { createObservedMediaProbe, safeObservedMediaProbe } = require('../scripts/observed_media_probe.cjs');

const SCOPE = 's0123456789abcdef', OTHER_SCOPE = 'sfedcba9876543210';
const PRIVATE = 'PRIVATE_URL_HEADER_BODY_TOKEN';
const SOURCE = 'https://media.test/video.mp4?signature=' + PRIVATE;
const OPTIONS = { streamsReturned: 0, expectedDurationSeconds: 1440 };
const short = () => ({ signature: 'mp4', durationSeconds: 5, bytesSampled: 80,
  readState: 'data', cancelState: 'complete' });

function movie(seconds, length = 80) {
  const bytes = Buffer.alloc(length);
  bytes.writeUInt32BE(16, 0); bytes.write('ftyp', 4);
  bytes.writeUInt32BE(48, 16); bytes.write('mvhd', 20);
  bytes.writeUInt32BE(1000, 36); bytes.writeUInt32BE(seconds * 1000, 40);
  return bytes;
}

function request(probe, overrides = {}) {
  const observation = { address_scope: SCOPE, request_ref: 'r55', referer_ref: 'r54', ...overrides };
  const init = { method: 'GET', headers: new Headers({ Accept: '*/*', 'Accept-Language': 'fr',
    'User-Agent': 'Observed Agent ' + PRIVATE, Referer: 'https://reader.test/' + PRIVATE,
    Origin: 'https://reader.test', 'X-Private': PRIVATE, Range: 'bytes=0-99999' }),
    signal: new AbortController().signal, cache: 'no-store' };
  probe.recordRequest('https://media.test/old.mp4?signature=' + PRIVATE, init, observation);
  // The worker records the GET before its caller reads and cancels the media.
  observation.media_observation = short();
  return { observation, init };
}

function candidate(probe, ref = 'r67', document = 'r54', scope = SCOPE) {
  const observation = { address_scope: scope, response_ref: document, status: 200 };
  probe.recordCandidate(SOURCE, ref, document, observation);
  return observation;
}

function privateFree(value) {
  const text = JSON.stringify(value);
  for (const raw of [PRIVATE, 'https:', 'media.test', 'reader.test', 'Observed Agent', 'Cookie', 'Authorization']) {
    assert.ok(!text.includes(raw), raw);
  }
}

(async () => {
  let calls = 0, originalResponse;
  const probe = createObservedMediaProbe({ fetch: async (url, init) => {
    calls++;
    assert.equal(url, SOURCE);
    assert.equal(init.method, 'GET'); assert.equal(init.credentials, 'omit');
    assert.notEqual(init.signal, prior.init.signal); assert.equal(init.signal.aborted, false);
    const expected = new Headers();
    for (const name of ['accept', 'accept-language', 'user-agent', 'referer', 'origin']) {
      expected.set(name, prior.init.headers.get(name));
    }
    expected.set('Range', 'bytes=0-32767');
    assert.deepEqual([...init.headers], [...expected]);
    assert.equal(init.headers.has('cookie'), false); assert.equal(init.headers.has('authorization'), false);
    assert.equal(init.headers.has('x-private'), false);
    originalResponse = new Response(movie(1440), { status: 206, headers: { 'content-type': 'video/mp4' } });
    return originalResponse;
  } });
  const prior = request(probe), originalHeaders = [...prior.init.headers];
  const priorMediaResponse = new Response(movie(5));
  const parentResponse = new Response('<video><source src="' + SOURCE + '"></video>');
  const alreadyRequested = candidate(probe, 'r55');
  const parent = candidate(probe), laterParent = candidate(probe, 'r68');
  assert.equal(calls, 0, 'recording never fetches');
  assert.equal(parent.observed_media_probe, undefined);
  assert.equal(parentResponse.bodyUsed, false);
  const [result, repeated] = await Promise.all([probe.flush(OPTIONS), probe.flush(OPTIONS)]);
  assert.equal(result, repeated); assert.equal(calls, 1);
  assert.equal(result.attempted, true); assert.equal(result.source_ref, 'r67'); assert.equal(result.template_ref, 'r55');
  assert.equal(result.outcome, 'response'); assert.equal(result.status, 206);
  assert.equal(result.media_observation.signature, 'mp4');
  assert.equal(result.media_observation.durationSeconds, 1440);
  assert.equal(result.media_observation.bytesSampled, 80);
  assert.equal(result.media_observation.readState, 'complete');
  assert.deepEqual(parent.observed_media_probe, result);
  assert.equal(alreadyRequested.observed_media_probe, undefined);
  assert.equal(laterParent.observed_media_probe, undefined);
  assert.equal(prior.observation.media_observation.durationSeconds, 5);
  assert.deepEqual([...prior.init.headers], originalHeaders);
  assert.equal(prior.init.signal.aborted, false);
  assert.equal(originalResponse.bodyUsed, true, 'the new control response is read and closed');
  assert.equal(priorMediaResponse.bodyUsed, false, 'the earlier provider media remains untouched');
  assert.deepEqual(Buffer.from(await priorMediaResponse.arrayBuffer()), movie(5));
  assert.ok((await parentResponse.text()).includes(SOURCE), 'the parent HTML remains unchanged');
  assert.deepEqual(safeObservedMediaProbe(result), result); privateFree(result);
  candidate(probe); request(probe); await probe.flush(OPTIONS);
  assert.equal(calls, 1, 'an instance performs at most one deferred control');

  for (const mode of ['healthy', 'short-fixture', 'unknown-fixture', 'long-media', 'zero-media', 'sixty-media',
    'tiny-prefix', 'uncancelled', 'wrong-signature', 'wrong-parent', 'wrong-scope', 'requested', 'post', 'invalid-scope']) {
    let fetched = 0;
    const skipped = createObservedMediaProbe({ fetch: () => { fetched++; throw new Error(PRIVATE); } });
    const prior = request(skipped, mode === 'post' ? { method: 'POST' } : {});
    const media = prior.observation.media_observation;
    if (mode === 'long-media') media.durationSeconds = 1440;
    if (mode === 'zero-media') media.durationSeconds = 0;
    if (mode === 'sixty-media') media.durationSeconds = 60;
    if (mode === 'tiny-prefix') media.bytesSampled = 39;
    if (mode === 'uncancelled') media.cancelState = 'requested';
    if (mode === 'wrong-signature') media.signature = 'html';
    const parent = candidate(skipped, mode === 'requested' ? 'r55' : 'r67',
      mode === 'wrong-parent' ? 'r53' : 'r54', mode === 'wrong-scope' ? OTHER_SCOPE : mode === 'invalid-scope' ? 'sBAD' : SCOPE);
    const options = { ...OPTIONS };
    if (mode === 'healthy') options.streamsReturned = 1;
    if (mode === 'short-fixture') options.expectedDurationSeconds = 599;
    if (mode === 'unknown-fixture') delete options.expectedDurationSeconds;
    assert.equal(await skipped.flush(options), null, mode);
    assert.equal(fetched, 0, mode); assert.equal(parent.observed_media_probe, undefined, mode);
  }

  for (const name of ['Cookie', 'cOoKiE', 'Authorization', 'Proxy-Authorization']) {
    let fetched = false;
    const blocked = createObservedMediaProbe({ fetch: () => { fetched = true; } });
    const observation = { address_scope: SCOPE, request_ref: 'r55', referer_ref: 'r54', media_observation: short() };
    blocked.recordRequest(SOURCE, { headers: { [name]: PRIVATE } }, observation);
    const parent = candidate(blocked);
    assert.equal(await blocked.flush(OPTIONS), null, name);
    assert.equal(fetched, false, name); assert.equal(parent.observed_media_probe, undefined);
  }

  let scopedCalls = 0;
  const scoped = createObservedMediaProbe({ fetch: async () => { scopedCalls++; return new Response(movie(5)); } });
  request(scoped);
  request(scoped, { address_scope: OTHER_SCOPE, request_ref: 'r67' });
  const scopedParent = candidate(scoped);
  const fiveSeconds = await scoped.flush(OPTIONS);
  assert.equal(scopedCalls, 1, 'the same ref in another scope is unrelated');
  assert.equal(fiveSeconds.media_observation.durationSeconds, 5);
  assert.equal(scopedParent.observed_media_probe.media_observation.durationSeconds, 5);
  assert.equal('playable' in fiveSeconds, false, 'a diagnostic duration is never a playback verdict');

  let cancelled = 0;
  const hugeBytes = movie(1440, 100000);
  const capped = createObservedMediaProbe({ fetch: async () => ({ status: 206, ok: true,
    headers: new Headers({ 'content-type': 'video/mp4' }), url: SOURCE,
    body: { getReader: () => ({ read: async () => ({ done: false, value: hugeBytes }),
      cancel: () => { cancelled++; return new Promise(() => {}); }, releaseLock() {} }) },
  }) });
  request(capped); candidate(capped);
  const cappedStart = Date.now(), cappedResult = await capped.flush(OPTIONS);
  assert.ok(Date.now() - cappedStart < 300, 'an unresolved cancellation must not hold flush open');
  assert.equal(cancelled, 1); assert.equal(cappedResult.media_observation.bytesSampled, 32768);
  assert.equal(cappedResult.media_observation.durationSeconds, 1440);
  assert.equal(cappedResult.media_observation.cancelState, 'requested'); privateFree(cappedResult);

  let upstreamCancelled = 0, upstreamReads = 0;
  const liveStream = createObservedMediaProbe({ fetch: async () => new Response(new ReadableStream({
    pull(controller) { upstreamReads++; controller.enqueue(hugeBytes); },
    cancel() { upstreamCancelled++; },
  }), { headers: { 'content-type': 'video/mp4' } }) });
  request(liveStream); candidate(liveStream);
  assert.equal((await liveStream.flush(OPTIONS)).media_observation.bytesSampled, 32768);
  assert.equal(upstreamCancelled, 1, 'capping the control must close its actual upstream body');
  assert.ok(upstreamReads <= 2, 'only the bounded stream prefetch may occur');

  const forbidden = createObservedMediaProbe({ fetch: async () => new Response('<html>Access denied ' + PRIVATE + '</html>', {
    status: 403, headers: { 'content-type': 'text/html' },
  }) });
  request(forbidden); candidate(forbidden);
  const forbiddenResult = await forbidden.flush(OPTIONS);
  assert.equal(forbiddenResult.status, 403); assert.equal(forbiddenResult.outcome, 'response');
  assert.equal(forbiddenResult.http_observation.page_signal, 'access_denied_text');
  assert.equal(forbiddenResult.media_observation.bytesSampled, 0);
  assert.equal(forbiddenResult.media_observation.readState, 'not_read'); privateFree(forbiddenResult);

  let errorPageCancelled = 0;
  const errorPage = Buffer.from('<html>Access denied ' + PRIVATE + ' '.repeat(10000));
  const streamingError = createObservedMediaProbe({ fetch: async () => new Response(new ReadableStream({
    pull(controller) { controller.enqueue(errorPage); }, cancel() { errorPageCancelled++; },
  }), { status: 403, headers: { 'content-type': 'text/html' } }) });
  request(streamingError); candidate(streamingError);
  const streamingErrorResult = await streamingError.flush(OPTIONS);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(errorPageCancelled, 1, 'both branches of an error-page sample must be closed');
  assert.equal(streamingErrorResult.http_observation.sampled_bytes, 8192); privateFree(streamingErrorResult);

  const brokenBody = createObservedMediaProbe({ fetch: async () => new Response(new ReadableStream({
    pull(controller) { controller.error(new Error(PRIVATE)); },
  })) });
  request(brokenBody); candidate(brokenBody);
  const brokenBodyResult = await brokenBody.flush(OPTIONS);
  assert.equal(brokenBodyResult.outcome, 'error'); assert.equal(brokenBodyResult.status, null);
  assert.equal(brokenBodyResult.media_observation.readState, 'error'); privateFree(brokenBodyResult);

  let lateResolve, lateCancelled = 0, timedSignal;
  const stalledFetch = createObservedMediaProbe({ timeoutMs: 25, fetch: (_url, init) => {
    timedSignal = init.signal; return new Promise(resolve => { lateResolve = resolve; });
  } });
  request(stalledFetch); const stalledParent = candidate(stalledFetch);
  const stalledStart = Date.now(), stalledResult = await stalledFetch.flush(OPTIONS);
  assert.ok(Date.now() - stalledStart < 300);
  assert.equal(stalledResult.outcome, 'timeout'); assert.equal(stalledResult.status, null);
  assert.equal(timedSignal.aborted, true);
  const late = new Response(movie(1440));
  late.body.cancel = () => { lateCancelled++; return new Promise(() => {}); };
  lateResolve(late); await new Promise(resolve => setImmediate(resolve));
  assert.equal(lateCancelled, 1); assert.equal(stalledParent.observed_media_probe, stalledResult);
  assert.equal(stalledParent.observed_media_probe.outcome, 'timeout'); privateFree(stalledResult);

  let bodyCancelled = 0, finishRead, bodySignal;
  const stalledBody = createObservedMediaProbe({ timeoutMs: 25, fetch: async (_url, init) => {
    bodySignal = init.signal;
    return { status: 200, ok: true, headers: new Headers(), body: {
      getReader: () => ({ read: () => new Promise(resolve => { finishRead = resolve; }),
        cancel: () => { bodyCancelled++; return new Promise(() => {}); }, releaseLock() {} }),
    } };
  } });
  request(stalledBody); const bodyParent = candidate(stalledBody);
  const bodyStart = Date.now(), bodyResult = await stalledBody.flush(OPTIONS);
  assert.ok(Date.now() - bodyStart < 300, 'the global timer must also bound body reads');
  assert.equal(bodyResult.outcome, 'timeout'); assert.equal(bodyCancelled, 1); assert.equal(bodySignal.aborted, true);
  const snapshot = JSON.stringify(bodyResult);
  finishRead({ done: false, value: movie(1440) }); await new Promise(resolve => setImmediate(resolve));
  assert.equal(JSON.stringify(bodyParent.observed_media_probe), snapshot, 'late reads cannot rewrite emitted facts');
  assert.equal(bodyCancelled, 1); privateFree(bodyResult);

  let budgetCalls = 0;
  const exhausted = createObservedMediaProbe({ fetch: () => { budgetCalls++; } });
  request(exhausted); const exhaustedParent = candidate(exhausted);
  const budget = await exhausted.flush({ ...OPTIONS, deadlineAtMs: Date.now() + 400 });
  assert.equal(budgetCalls, 0); assert.equal(budget.attempted, false); assert.equal(budget.outcome, 'budget_exhausted');
  assert.equal(budget.status, null); assert.equal(budget.source_ref, 'r67'); assert.equal(budget.template_ref, 'r55');
  assert.deepEqual(exhaustedParent.observed_media_probe, budget); privateFree(budget);

  let marginSignal;
  const margin = createObservedMediaProbe({ fetch: (_url, init) => { marginSignal = init.signal; return new Promise(() => {}); } });
  request(margin); candidate(margin);
  const deadline = Date.now() + 560, marginStart = Date.now();
  assert.equal((await margin.flush({ ...OPTIONS, deadlineAtMs: deadline })).outcome, 'timeout');
  assert.ok(Date.now() - marginStart < 250); assert.ok(deadline - Date.now() >= 450);
  assert.equal(marginSignal.aborted, true);

  let limitCalls = 0;
  const requestLimit = createObservedMediaProbe({ fetch: () => { limitCalls++; } });
  for (let index = 1; index <= 81; index++) request(requestLimit, { request_ref: 'r' + index });
  candidate(requestLimit, 'r100');
  assert.equal(await requestLimit.flush(OPTIONS), null); assert.equal(limitCalls, 0);
  const candidateLimit = createObservedMediaProbe({ fetch: () => { limitCalls++; } });
  request(candidateLimit);
  for (let index = 1; index <= 8; index++) candidate(candidateLimit, 'r' + (100 + index), 'r53');
  candidate(candidateLimit, 'r200');
  assert.equal(await candidateLimit.flush(OPTIONS), null); assert.equal(limitCalls, 0);

  let uniqueCalls = 0;
  const unique = createObservedMediaProbe({ fetch: async () => { uniqueCalls++; return new Response(movie(1440)); } });
  request(unique);
  for (let index = 0; index < 10; index++) candidate(unique, 'r55');
  candidate(unique);
  assert.equal((await unique.flush(OPTIONS)).source_ref, 'r67');
  assert.equal(uniqueCalls, 1, 'duplicate sources do not consume the eight-unique-source bound');

  let credentialedCalls = 0;
  const credentialedSeen = createObservedMediaProbe({ fetch: () => { credentialedCalls++; } });
  request(credentialedSeen);
  credentialedSeen.recordRequest(SOURCE, { headers: { Cookie: PRIVATE } }, {
    address_scope: SCOPE, request_ref: 'r67', referer_ref: 'r54', media_observation: short(),
  });
  candidate(credentialedSeen);
  assert.equal(await credentialedSeen.flush(OPTIONS), null);
  assert.equal(credentialedCalls, 0, 'a credentialed GET still establishes that a source was already requested');

  const timeoutCap = createObservedMediaProbe({ timeoutMs: 999999, fetch: () => new Promise(() => {}) });
  request(timeoutCap); candidate(timeoutCap);
  const timeoutStart = Date.now();
  assert.equal((await timeoutCap.flush(OPTIONS)).outcome, 'timeout');
  assert.ok(Date.now() - timeoutStart < 3000, 'the configured timeout must remain capped at 2500ms');

  const failed = createObservedMediaProbe({ fetch: async () => { throw new Error(PRIVATE); } });
  request(failed); candidate(failed);
  const failure = await failed.flush(OPTIONS);
  assert.equal(failure.outcome, 'error'); assert.equal(failure.status, null); privateFree(failure);

  const forged = safeObservedMediaProbe({ attempted: true, source_ref: 'r512', template_ref: 'r1', status: 200,
    outcome: 'response', url: SOURCE, headers: { Cookie: PRIVATE }, raw: PRIVATE,
    media_observation: { signature: 'mp4', durationSeconds: 9999999, bytesSampled: 999999,
      readState: 'data', cancelState: 'complete', body: PRIVATE },
    http_observation: { content_kind: 'html', url_relation: 'same_origin', body_state: 'complete',
      page_signal: 'access_denied_text', sampled_bytes: 999999, body: PRIVATE } });
  assert.equal(forged.media_observation.bytesSampled, 32768);
  assert.equal(forged.media_observation.durationSeconds, 1209600);
  assert.equal(forged.http_observation.sampled_bytes, 8192); privateFree(forged);
  assert.deepEqual(safeObservedMediaProbe(forged), forged);
  for (const key of ['source_ref', 'template_ref']) for (const invalid of ['r0', 'r01', 'r513', 'r1\n', PRIVATE, [], 1, true]) {
    assert.equal(safeObservedMediaProbe({ ...forged, [key]: invalid }), null);
  }
  for (const attempted of [1, 'true', null, [], {}]) assert.equal(safeObservedMediaProbe({ ...forged, attempted }), null);
  for (const status of [true, 200.5, 99, 600, PRIVATE]) {
    assert.equal(safeObservedMediaProbe({ ...forged, status }).status, null);
  }
  for (const outcome of ['timeout', 'error', PRIVATE, []]) {
    const clean = safeObservedMediaProbe({ ...forged, outcome });
    assert.equal(clean.status, null); assert.ok(['timeout', 'error'].includes(clean.outcome)); privateFree(clean);
  }
  assert.equal(safeObservedMediaProbe(null), null); assert.equal(safeObservedMediaProbe([]), null);
  assert.equal(safeObservedMediaProbe({ ...forged, attempted: false }), null);
  console.log('Observed media probe: scoped deferred control, 5s/1440s facts, one GET, caps, privacy, deadline and cancellation passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
