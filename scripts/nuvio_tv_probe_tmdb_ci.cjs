#!/usr/bin/env node
'use strict';

// CI-only bridge for the Node-compatible Nuvio probe. Provider/Core code reads
// TMDB credentials from the JS runtime global, while GitHub Actions exposes
// secrets through the process environment. Keep that transport concern out of
// provider business logic and never print either credential.
const key = String(process.env.TMDB_API_KEY || '').trim();
const token = String(process.env.TMDB_ACCESS_TOKEN || '').trim();
if (!key && !token) {
  console.error('FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=missing_tmdb_credential');
  process.exit(78);
}

function expose(name, value) {
  if (!value) return;
  try {
    Object.defineProperty(globalThis, name, {
      value,
      configurable: true,
      writable: false,
      enumerable: false,
    });
  } catch {
    globalThis[name] = value;
  }
}

expose('TMDB_API_KEY', key);
expose('TMDB_ACCESS_TOKEN', token);
console.error('FIELD_TMDB_PROBE_CONTEXT state=ready credential_present=true value_redacted=true');
require('./nuvio_tv_probe_v2.cjs');
