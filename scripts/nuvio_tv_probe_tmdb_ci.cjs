#!/usr/bin/env node
'use strict';

// CI-only bridge for the Node-compatible Nuvio probe. The clean Provider v3
// runtime consumes TMDB metadata through __nuvioMediaContext / the shared cache,
// not directly from a credential global. GitHub Actions exposes the credential
// through process.env, so hydrate the exact metadata contract before loading the
// ordinary probe. Never print either credential or the full authenticated URL.
const key = String(process.env.TMDB_API_KEY || '').trim();
const token = String(process.env.TMDB_ACCESS_TOKEN || '').trim();
if (!key && !token) {
  console.error('FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=missing_tmdb_credential');
  process.exit(78);
}

function expose(name, value, writable = false) {
  if (value == null || value === '') return;
  try {
    Object.defineProperty(globalThis, name, {
      value,
      configurable: true,
      writable,
      enumerable: false,
    });
  } catch {
    globalThis[name] = value;
  }
}

function mediaNamespace(value) {
  return String(value || '').toLowerCase() === 'movie' ? 'movie' : 'tv';
}

async function hydrateTmdbContext() {
  let fixture = {};
  try {
    fixture = JSON.parse(process.argv[3] || '{}');
  } catch {
    fixture = {};
  }
  const tmdbId = String(fixture.tmdbId || fixture.id || '').trim();
  const type = mediaNamespace(fixture.mediaType || fixture.type || 'movie');
  if (!tmdbId) {
    console.error('FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=missing_tmdb_id');
    process.exit(78);
  }

  const endpoint = new URL(`https://api.themoviedb.org/3/${type}/${encodeURIComponent(tmdbId)}`);
  endpoint.searchParams.set('append_to_response', 'alternative_titles');
  const headers = { Accept: 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  else endpoint.searchParams.set('api_key', key);

  let response;
  try {
    response = await fetch(endpoint, {
      headers,
      redirect: 'follow',
      signal: AbortSignal.timeout(12000),
    });
  } catch (error) {
    console.error(`FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=tmdb_fetch_failed error=${error?.name || 'Error'}`);
    process.exit(78);
  }
  if (!response.ok) {
    console.error(`FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=tmdb_http status=${response.status}`);
    process.exit(78);
  }

  const metadata = await response.json();
  const identity = `${type}:${tmdbId}`;
  const cache = Object.create(null);
  cache[identity] = { metadata };

  expose('TMDB_API_KEY', key);
  expose('TMDB_ACCESS_TOKEN', token);
  expose('__nuvioTmdbMetadataCacheV1', cache, true);
  expose('__nuvioMediaContext', {
    tmdbId,
    tmdbNamespace: type,
    tmdbMetadata: metadata,
  }, true);
  console.error('FIELD_TMDB_PROBE_CONTEXT state=ready credential_present=true metadata_hydrated=true value_redacted=true');
}

(async () => {
  await hydrateTmdbContext();
  require('./nuvio_tv_probe_v2.cjs');
})().catch((error) => {
  console.error(`FIELD_TMDB_PROBE_CONTEXT state=infra_error reason=bridge_failure error=${error?.name || 'Error'}`);
  process.exit(78);
});
