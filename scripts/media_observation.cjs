'use strict';

// Observe bytes already read by a terminal probe. No extra request or read,
// retained URL, response text, or change to the probe's returned bytes/verdict.
const PREFIX_LIMIT = 65536;

function prefixFacts(bytes) {
  let signature = 'unknown';
  if (bytes.length >= 8 && bytes.subarray(4, 8).toString('ascii') === 'ftyp') signature = 'mp4';
  else if (bytes.length >= 4 && bytes.readUInt32BE(0) === 0x1a45dfa3) signature = 'ebml';
  else if (bytes.length >= 376 && bytes[0] === 0x47 && bytes[188] === 0x47) signature = 'mpegts';
  else if (/^\s*#EXTM3U/.test(bytes.subarray(0, 100).toString('utf8'))) signature = 'hls';
  else if (/^\s*(?:<!doctype|<html|<body)/i.test(bytes.subarray(0, 100).toString('utf8'))) signature = 'html';
  let durationSeconds = null;
  if (signature === 'mp4') {
    for (let i = 4; i + 28 <= bytes.length; i++) {
      if (bytes.toString('ascii', i, i + 4) !== 'mvhd') continue;
      const start = i - 4, size = bytes.readUInt32BE(start), version = bytes[start + 8];
      if (size < 32) continue;
      let scale, duration;
      if (version === 0 && start + 28 <= bytes.length) {
        scale = bytes.readUInt32BE(start + 20); duration = bytes.readUInt32BE(start + 24);
      } else if (version === 1 && start + 40 <= bytes.length) {
        scale = bytes.readUInt32BE(start + 28);
        duration = Number(bytes.readBigUInt64BE(start + 32));
      }
      const seconds = scale && duration / scale;
      if (Number.isFinite(seconds) && seconds >= 1 && seconds <= 1209600) {
        durationSeconds = Math.round(seconds); break;
      }
    }
  }
  return { signature, durationSeconds };
}

function observeMediaResponse(response, observation) {
  let body, prefix = Buffer.alloc(0), facts;
  function state() {
    if (!facts) observation.media_observation = facts = {
      signature: 'unknown', durationSeconds: null, bytesSampled: 0,
      readState: 'not_read', cancelState: 'not_requested',
    };
    return facts;
  }
  function inspect(value) {
    const row = state();
    if (value && (ArrayBuffer.isView(value) || value instanceof ArrayBuffer)) {
      const bytes = ArrayBuffer.isView(value)
        ? Buffer.from(value.buffer, value.byteOffset, value.byteLength) : Buffer.from(value);
      const remaining = PREFIX_LIMIT - prefix.length;
      if (remaining > 0) prefix = Buffer.concat([prefix, bytes.subarray(0, remaining)]);
      Object.assign(row, prefixFacts(prefix), { bytesSampled: prefix.length, readState: bytes.length ? 'data' : 'empty' });
      if (['mp4', 'ebml', 'mpegts', 'hls'].includes(row.signature)) observation.stage = 'media';
    }
  }
  return new Proxy(response, {
    get(target, prop) {
      if (prop === 'body' && target.body) {
        if (!body) body = new Proxy(target.body, {
          get(stream, key) {
            if (key === 'getReader') return (...args) => {
              const reader = stream.getReader(...args);
              return new Proxy(reader, {
                get(current, name) {
                  if (name === 'read') return async (...values) => {
                    try {
                      const result = await current.read(...values);
                      if (result.done) state().readState = 'complete'; else inspect(result.value);
                      return result;
                    } catch (error) { state().readState = 'error'; throw error; }
                  };
                  if (name === 'cancel') return async (...values) => {
                    state().cancelState = 'requested';
                    try { const result = await current.cancel(...values); state().cancelState = 'complete'; return result; }
                    catch (error) { state().cancelState = 'error'; throw error; }
                  };
                  const value = Reflect.get(current, name, current);
                  return typeof value === 'function' ? value.bind(current) : value;
                },
              });
            };
            const value = Reflect.get(stream, key, stream);
            return typeof value === 'function' ? value.bind(stream) : value;
          },
        });
        return body;
      }
      if (prop === 'arrayBuffer') return async () => { const value = await target.arrayBuffer(); inspect(value); return value; };
      const value = Reflect.get(target, prop, target);
      return typeof value === 'function' ? value.bind(target) : value;
    },
  });
}

function safeMediaFacts(value) {
  if (!value || typeof value !== 'object') return null;
  const integer = (item, cap) => Number.isInteger(item) ? Math.max(0, Math.min(cap, item)) : 0;
  return {
    signature: ['unknown', 'mp4', 'ebml', 'mpegts', 'hls', 'html'].includes(value.signature) ? value.signature : 'unknown',
    durationSeconds: Number.isInteger(value.durationSeconds) ? integer(value.durationSeconds, 1209600) : null,
    bytesSampled: integer(value.bytesSampled, PREFIX_LIMIT),
    readState: ['not_read', 'data', 'empty', 'complete', 'error'].includes(value.readState) ? value.readState : 'not_read',
    cancelState: ['not_requested', 'requested', 'complete', 'error'].includes(value.cancelState) ? value.cancelState : 'not_requested',
  };
}

module.exports = { observeMediaResponse, prefixFacts, safeMediaFacts };
