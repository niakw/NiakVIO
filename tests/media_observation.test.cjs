'use strict';
const assert = require('node:assert/strict');
const { observeMediaResponse, prefixFacts } = require('../scripts/media_observation.cjs');

function movie(seconds, version = 0) {
  const bytes = Buffer.alloc(80);
  bytes.writeUInt32BE(16, 0); bytes.write('ftyp', 4);
  bytes.writeUInt32BE(48, 16); bytes.write('mvhd', 20); bytes[24] = version;
  bytes.writeUInt32BE(1000, 16 + (version ? 28 : 20));
  if (version) bytes.writeBigUInt64BE(BigInt(seconds * 1000), 48);
  else bytes.writeUInt32BE(seconds * 1000, 40);
  return bytes;
}

(async () => {
  for (const seconds of [35, 1440]) for (const version of [0, 1]) {
    assert.deepEqual(prefixFacts(movie(seconds, version)), { signature: 'mp4', durationSeconds: seconds });
  }
  const bytes = movie(35), observation = {};
  let readCount = 0, cancelCount = 0;
  const original = new Response(new ReadableStream({
    pull(controller) { readCount++; controller.enqueue(bytes); },
    cancel() { cancelCount++; },
  }), { status: 206, headers: { 'content-type': 'video/mp4', 'x-private-token': 'PRIVATE' } });
  const wrapped = observeMediaResponse(original, observation);
  assert.equal(wrapped.status, 206);
  assert.equal(wrapped.headers, original.headers);
  assert.equal(wrapped.body, wrapped.body);
  assert.deepEqual(observation, {}); // Observation causes no read.
  const reader = wrapped.body.getReader();
  const value = await reader.read();
  assert.equal(value.value, bytes); // Preserve the exact caller-visible object.
  assert.equal(observation.media_observation.durationSeconds, 35);
  assert.equal(observation.stage, 'media');
  assert.equal(observation.media_observation.readState, 'data');
  await reader.cancel();
  assert.equal(cancelCount, 1);
  assert.equal(observation.media_observation.cancelState, 'complete');
  assert.ok(readCount <= 2); // Only the stream's normal bounded prefetch.
  assert.ok(!JSON.stringify(observation).includes('PRIVATE'));
  const large = {}, largeBytes = new Uint8Array(100000);
  const largeResponse = observeMediaResponse(new Response(largeBytes), large);
  assert.equal((await largeResponse.arrayBuffer()).byteLength, 100000);
  assert.equal(large.media_observation.bytesSampled, 65536);
  const error = new Error('PRIVATE'), failed = {};
  const broken = observeMediaResponse(new Response(new ReadableStream({
    pull(controller) { controller.error(error); },
  })), failed);
  await assert.rejects(broken.body.getReader().read(), value => value === error);
  assert.equal(failed.media_observation.readState, 'error');
  assert.ok(!JSON.stringify(failed).includes('PRIVATE'));
  console.log('Media observation: unchanged reads, bounded signature/duration, cancellation and error privacy passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
