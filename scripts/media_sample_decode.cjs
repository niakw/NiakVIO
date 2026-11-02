'use strict';

const childProcess = require('node:child_process');

const MAX_SAMPLE_BYTES = 1024 * 1024;
const MAX_PROGRESS_BYTES = 4096;

/** Decode one frame from an in-memory prefix. FFmpeg cannot open network/files. */
async function decodeVideoSample(sample, { timeoutMs = 5000 } = {}) {
  if (!Buffer.isBuffer(sample) || sample.length === 0) {
    return { attempted: false, outcome: 'unsupported', framesDecoded: 0 };
  }
  const input = Buffer.from(sample.subarray(0, MAX_SAMPLE_BYTES));
  const timeout = Number.isFinite(timeoutMs) && timeoutMs > 0
    ? Math.min(5000, Math.max(1, Math.floor(timeoutMs))) : 5000;
  return new Promise(resolve => {
    let child, timer, finished = false, progress = Buffer.alloc(0);
    const result = (outcome, frames = 0, attempted = true) => ({
      attempted, outcome, framesDecoded: outcome === 'decoded' ? Math.min(1, frames) : 0,
    });
    const finish = value => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      resolve(value);
    };
    const stop = outcome => {
      if (finished) return;
      finish(result(outcome));
      try { child.kill('SIGKILL'); } catch (_) { /* no process errors in evidence */ }
      try { child.stdin.destroy(); } catch (_) { /* bounded shutdown */ }
      try { child.stdout.destroy(); } catch (_) { /* bounded shutdown */ }
      try { child.unref(); } catch (_) { /* do not wait on uncooperative children */ }
    };
    try {
      child = childProcess.spawn('ffmpeg', [
        '-hide_banner', '-loglevel', 'error', '-nostats', '-nostdin',
        '-protocol_whitelist', 'pipe', '-i', 'pipe:0',
        '-map', '0:v:0', '-frames:v', '1', '-progress', 'pipe:1', '-f', 'null', '-',
      ], {
        shell: false, windowsHide: true,
        stdio: ['pipe', 'pipe', 'ignore'],
        env: { PATH: process.env.PATH || '/usr/bin:/bin' },
      });
    } catch (_) {
      finish(result('unavailable', 0, false));
      return;
    }
    child.once('error', () => finish(result('unavailable', 0, false)));
    child.once('close', code => {
      if (finished) return;
      const frames = [...progress.toString('ascii').matchAll(/^frame=\s*(\d{1,9})\s*$/gm)]
        .some(match => Number(match[1]) >= 1) ? 1 : 0;
      finish(result(code === 0 && frames === 1 ? 'decoded' : 'failed', frames));
    });
    child.stdout.on('data', chunk => {
      if (finished) return;
      const data = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      if (progress.length + data.length > MAX_PROGRESS_BYTES) {
        stop('failed');
        return;
      }
      progress = Buffer.concat([progress, data]);
    });
    child.stdout.on('error', () => stop('failed'));
    // FFmpeg may stop after its first frame before all prefix bytes are sent.
    // EPIPE is expected there; only its exit/progress determine the result.
    child.stdin.on('error', () => {});
    timer = setTimeout(() => stop('timeout'), timeout);
    try { child.stdin.end(input); } catch (_) { stop('failed'); }
  });
}

module.exports = { decodeVideoSample };
