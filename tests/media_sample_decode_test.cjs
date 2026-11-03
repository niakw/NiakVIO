'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const { EventEmitter } = require('node:events');
const { PassThrough } = require('node:stream');
const { decodeVideoSample } = require('../scripts/media_sample_decode.cjs');

const PRIVATE = 'PRIVATE_FRAME_COOKIE_URL_BODY';

function synthetic(format) {
  const output = format === 'mpegts'
    ? ['-c:v', 'mpeg2video', '-f', 'mpegts', 'pipe:1']
    : ['-c:v', 'mpeg4', '-movflags', 'frag_keyframe+empty_moov', '-f', 'mp4', 'pipe:1'];
  const generated = childProcess.spawnSync('ffmpeg', [
    '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
    '-i', 'color=c=red:s=64x64:d=2:r=25', '-an', ...output,
  ], { maxBuffer: 1024 * 1024, timeout: 5000, stdio: ['ignore', 'pipe', 'ignore'] });
  assert.equal(generated.status, 0, 'generate real synthetic video');
  assert.ok(generated.stdout.length > 188);
  return generated.stdout;
}

async function withFake(run, test) {
  const original = childProcess.spawn;
  const observed = { killed: 0, bytes: 0 };
  childProcess.spawn = (binary, args, options) => {
    observed.binary = binary; observed.args = args; observed.options = options;
    const child = new EventEmitter();
    child.stdin = new PassThrough(); child.stdout = new PassThrough();
    child.stdin.on('data', chunk => { observed.bytes += chunk.length; });
    child.kill = signal => { observed.killed++; observed.signal = signal; };
    child.unref = () => {};
    setImmediate(() => run(child));
    return child;
  };
  try { await test(observed); } finally { childProcess.spawn = original; }
}

(async () => {
  const available = childProcess.spawnSync('ffmpeg', ['-version'], { stdio: 'ignore', timeout: 5000 });
  if (available.status === 0) {
    for (const format of ['mpegts', 'mp4']) {
      const media = synthetic(format);
      assert.deepEqual(await decodeVideoSample(media), { attempted: true, outcome: 'decoded', framesDecoded: 1 });
      const truncated = await decodeVideoSample(media.subarray(0, 24));
      assert.equal(truncated.attempted, true);
      assert.equal(truncated.outcome, 'failed');
      assert.equal(truncated.framesDecoded, 0);
    }
    const garbage = await decodeVideoSample(Buffer.from(PRIVATE));
    assert.equal(garbage.outcome, 'failed');
    assert.equal(garbage.framesDecoded, 0);
    assert.ok(!JSON.stringify(garbage).includes(PRIVATE));
  } else {
    console.log('SKIP real FFmpeg samples: system FFmpeg unavailable');
  }

  for (const sample of [null, undefined, PRIVATE, new Uint8Array([1]), Buffer.alloc(0)]) {
    assert.deepEqual(await decodeVideoSample(sample), { attempted: false, outcome: 'unsupported', framesDecoded: 0 });
  }

  await withFake(child => { child.stdout.write('frame=1\nprogress=end\n'); child.emit('close', 0); }, async observed => {
    const originalTimer = global.setTimeout;
    const deadlines = [];
    global.setTimeout = (callback, ms, ...args) => {
      deadlines.push(ms);
      return originalTimer(callback, ms, ...args);
    };
    let pending;
    try { pending = decodeVideoSample(Buffer.alloc(2 * 1024 * 1024), { timeoutMs: 90000 }); }
    finally { global.setTimeout = originalTimer; }
    const decoded = await pending;
    assert.equal(decoded.outcome, 'decoded');
    assert.deepEqual(deadlines, [5000], 'caller cannot extend decoding beyond five seconds');
    assert.equal(observed.bytes, 1024 * 1024, 'never feed more than a 1 MiB prefix');
    assert.equal(observed.binary, 'ffmpeg');
    assert.equal(observed.args[observed.args.indexOf('-protocol_whitelist') + 1], 'pipe');
    assert.equal(observed.args[observed.args.indexOf('-i') + 1], 'pipe:0');
    assert.equal(observed.args[observed.args.indexOf('-frames:v') + 1], '1');
    assert.equal(observed.args[observed.args.indexOf('-map') + 1], '0:v:0');
    assert.deepEqual(observed.options.stdio, ['pipe', 'pipe', 'ignore']);
    assert.deepEqual(Object.keys(observed.options.env), ['PATH']);
    assert.equal(observed.options.shell, false);
    assert.ok(!JSON.stringify(observed.args).includes(PRIVATE));
  });

  await withFake(child => { child.stdout.write('frame=1\n'); child.emit('close', 1); }, async () => {
    assert.deepEqual(await decodeVideoSample(Buffer.from(PRIVATE)), { attempted: true, outcome: 'failed', framesDecoded: 0 });
  });
  await withFake(child => { child.stdout.write('frame=0\n'); child.emit('close', 0); }, async () => {
    assert.equal((await decodeVideoSample(Buffer.from(PRIVATE))).outcome, 'failed');
  });
  await withFake(child => { child.emit('error', Object.assign(new Error(PRIVATE), { code: 'ENOENT' })); }, async () => {
    assert.deepEqual(await decodeVideoSample(Buffer.from(PRIVATE)), { attempted: false, outcome: 'unavailable', framesDecoded: 0 });
  });
  await withFake(child => { child.stdout.write('frame=1\n' + 'x'.repeat(4096)); }, async observed => {
    const result = await decodeVideoSample(Buffer.from(PRIVATE));
    assert.equal(result.outcome, 'failed');
    assert.equal(observed.killed, 1, 'stop excessive progress output');
    assert.equal(observed.signal, 'SIGKILL');
  });
  await withFake(() => {}, async observed => {
    const start = Date.now();
    const result = await decodeVideoSample(Buffer.from(PRIVATE), { timeoutMs: 20 });
    assert.equal(result.outcome, 'timeout');
    assert.ok(Date.now() - start < 500);
    assert.equal(observed.killed, 1);
    assert.equal(observed.signal, 'SIGKILL');
  });

  console.log('Media prefix decode: real TS/MP4 frames, truncation, process bounds, pipe-only protocols and privacy passed');
})().catch(error => { console.error(error); process.exit(1); });
