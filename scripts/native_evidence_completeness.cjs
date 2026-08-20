'use strict';

const fs = require('node:fs');
const CANONICAL_REQUEST_TYPES = new Set(['movie', 'tv', 'anime']);

function fields(line) {
  const out = {};
  const re = /([A-Za-z0-9_]+)=([^\s]+)/g;
  let match;
  while ((match = re.exec(line)) !== null) out[match[1]] = match[2];
  return out;
}

function decode(value) {
  if (!value) return '';
  let text = String(value).replace(/-/g, '+').replace(/_/g, '/');
  while (text.length % 4) text += '=';
  try { return Buffer.from(text, 'base64').toString('utf8'); } catch { return ''; }
}

function providerName(f) {
  return (decode(f.provider64) || String(f.provider || '')).trim().toLowerCase();
}

function requestType(f) {
  return String(f.request_type || '').trim().toLowerCase();
}

function validRequestType(f) {
  return CANONICAL_REQUEST_TYPES.has(requestType(f));
}

function scopeKey(client, fixture) {
  return `${client}\u0000${fixture}`;
}

function routeKey(client, fixture, provider, requestedType) {
  return `${client}\u0000${fixture}\u0000${provider}\u0000${String(requestedType || 'unknown').toLowerCase()}`;
}

function playerKey(client, fixture, provider, requestedType, index) {
  return `${routeKey(client, fixture, provider, requestedType)}\u0000${Number(index || 0)}`;
}

function httpKey(client, provider, requestedType, method, endpoint) {
  return `${client}\u0000${provider}\u0000${String(requestedType || 'unknown').toLowerCase()}\u0000${String(method || 'GET').toUpperCase()}\u0000${String(endpoint || '')}`;
}

function repositoryHttpKey(client, kind, method, endpoint) {
  return `${client}\u0000${String(kind || 'repository').toLowerCase()}\u0000${String(method || 'GET').toUpperCase()}\u0000${String(endpoint || '')}`;
}

function ensureScope(scopes, client, fixture) {
  const key = scopeKey(client, fixture);
  if (!scopes.has(key)) {
    scopes.set(key, {
      client,
      fixture,
      expectedProviders: 0,
      ended: false,
      instrumented: false,
      traversed: new Set(),
      frontendPhases: new Set(),
      results: 0,
      httpRequests: 0,
      repositoryHttpRequests: 0,
      repositoryHttpTerminal: 0,
      repositoryCacheHits: 0,
      playerResults: 0,
      providerRoutesBegun: 0,
      repositoryLoadBegun: 0,
      repositoryLoadTerminal: 0,
      repositoryLoadFailed: false,
      repositoryLoadExpected: 0,
      providerLoadObserved: new Set(),
      providerLoadResults: 0,
      providerLoadErrors: 0,
      providerLoadSkipped: 0,
    });
  }
  return scopes.get(key);
}

function increment(map, key) {
  map.set(key, Number(map.get(key) || 0) + 1);
}

function assessNativeEvidence(logPaths) {
  const scopes = new Map();
  const routesBegun = new Map();
  const routesTerminal = new Map();
  const playersBegun = new Map();
  const playersTerminal = new Map();
  const httpRequests = new Map();
  const httpTerminal = new Map();
  const repositoryHttpRequests = new Map();
  const repositoryHttpTerminal = new Map();
  const problems = [];
  let readableLogs = 0;
  let frontendErrors = 0;

  const requireRoute = (kind, f, client, fixture, provider) => {
    if (validRequestType(f)) return;
    const raw = requestType(f) || '<missing>';
    problems.push(`invalid_request_type:${kind}:${client}:${fixture}:${provider || '<unknown>'}:${raw}`);
  };

  for (const file of logPaths) {
    if (!fs.existsSync(file)) {
      problems.push(`missing_log:${file}`);
      continue;
    }
    readableLogs += 1;
    const fileScopeKeys = new Set();
    const fileFrontend = new Set();
    const fileInstrumentedClients = new Set();
    const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/);

    for (const raw of lines) {
      const markerAt = raw.indexOf('FIELD_NATIVE_');
      if (markerAt < 0) continue;
      const line = raw.slice(markerAt).trim();
      const f = fields(line);
      const client = f.client || 'unknown';
      const fixture = f.fixture || 'unknown';

      if (line.startsWith('FIELD_NATIVE_CORPUS_BEGIN ')) {
        const scope = ensureScope(scopes, client, fixture);
        scope.expectedProviders = Number(f.providers || 0);
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_CORPUS_END ')) {
        const scope = ensureScope(scopes, client, fixture);
        scope.ended = true;
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_EVIDENCE_INSTRUMENTED ')) {
        fileInstrumentedClients.add(client);
      } else if (line.startsWith('FIELD_NATIVE_FRONTEND_CAPTURE ')) {
        if (f.phase) fileFrontend.add(f.phase);
      } else if (line.startsWith('FIELD_NATIVE_FRONTEND_ERROR ')) {
        frontendErrors += 1;
      } else if (line.startsWith('FIELD_NATIVE_REPOSITORY_LOAD_BEGIN ')) {
        const scope = ensureScope(scopes, client, fixture);
        scope.repositoryLoadBegun += 1;
        scope.repositoryLoadExpected = Math.max(scope.repositoryLoadExpected, Number(f.expected || 0));
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_REPOSITORY_CACHE_HIT ')) {
        const scope = ensureScope(scopes, client, fixture);
        scope.repositoryCacheHits += 1;
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_REPOSITORY_LOAD_RESULT ')) {
        const scope = ensureScope(scopes, client, fixture);
        scope.repositoryLoadTerminal += 1;
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_REPOSITORY_LOAD_ERROR ')) {
        const scope = ensureScope(scopes, client, fixture);
        scope.repositoryLoadTerminal += 1;
        scope.repositoryLoadFailed = true;
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_REPOSITORY_HTTP_REQUEST ')) {
        const key = repositoryHttpKey(client, f.kind, f.method, f.endpoint);
        increment(repositoryHttpRequests, key);
        for (const scopeId of fileScopeKeys) {
          const scope = scopes.get(scopeId);
          if (scope && scope.client === client) scope.repositoryHttpRequests += 1;
        }
      } else if (line.startsWith('FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE ') || line.startsWith('FIELD_NATIVE_REPOSITORY_HTTP_ERROR ')) {
        const key = repositoryHttpKey(client, f.kind, f.method, f.endpoint);
        increment(repositoryHttpTerminal, key);
        for (const scopeId of fileScopeKeys) {
          const scope = scopes.get(scopeId);
          if (scope && scope.client === client) scope.repositoryHttpTerminal += 1;
        }
      } else if (
        line.startsWith('FIELD_NATIVE_PROVIDER_LOAD_RESULT ') ||
        line.startsWith('FIELD_NATIVE_PROVIDER_LOAD_ERROR ') ||
        line.startsWith('FIELD_NATIVE_PROVIDER_LOAD_SKIPPED ')
      ) {
        const scope = ensureScope(scopes, client, fixture);
        const provider = providerName(f);
        if (provider) scope.providerLoadObserved.add(provider);
        if (line.startsWith('FIELD_NATIVE_PROVIDER_LOAD_RESULT ')) scope.providerLoadResults += 1;
        else if (line.startsWith('FIELD_NATIVE_PROVIDER_LOAD_ERROR ')) scope.providerLoadErrors += 1;
        else scope.providerLoadSkipped += 1;
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_PROVIDER_SKIPPED ')) {
        const provider = providerName(f);
        const scope = ensureScope(scopes, client, fixture);
        if (provider) scope.traversed.add(provider);
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_PROVIDER_BEGIN ')) {
        const provider = providerName(f);
        requireRoute('provider_begin', f, client, fixture, provider);
        const scope = ensureScope(scopes, client, fixture);
        scope.providerRoutesBegun += 1;
        const key = routeKey(client, fixture, provider, f.request_type);
        increment(routesBegun, key);
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_RESULT ')) {
        const provider = providerName(f);
        requireRoute('provider_result', f, client, fixture, provider);
        const scope = ensureScope(scopes, client, fixture);
        if (provider) scope.traversed.add(provider);
        scope.results += 1;
        increment(routesTerminal, routeKey(client, fixture, provider, f.request_type));
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
        const provider = providerName(f);
        requireRoute('provider_error', f, client, fixture, provider);
        const scope = ensureScope(scopes, client, fixture);
        if (provider) scope.traversed.add(provider);
        increment(routesTerminal, routeKey(client, fixture, provider, f.request_type));
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_PLAYER_BEGIN ')) {
        const provider = providerName(f);
        requireRoute('player_begin', f, client, fixture, provider);
        increment(playersBegun, playerKey(client, fixture, provider, f.request_type, f.index));
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_PLAYER ')) {
        const provider = providerName(f);
        requireRoute('player_result', f, client, fixture, provider);
        increment(playersTerminal, playerKey(client, fixture, provider, f.request_type, f.index));
        const scope = ensureScope(scopes, client, fixture);
        scope.playerResults += 1;
        fileScopeKeys.add(scopeKey(client, fixture));
      } else if (line.startsWith('FIELD_NATIVE_HTTP_REQUEST ')) {
        const provider = providerName(f);
        requireRoute('http_request', f, client, fixture, provider);
        increment(httpRequests, httpKey(client, provider, f.request_type, f.method, f.endpoint));
        for (const key of fileScopeKeys) {
          const scope = scopes.get(key);
          if (scope && scope.client === client) scope.httpRequests += 1;
        }
      } else if (line.startsWith('FIELD_NATIVE_HTTP_RESPONSE ') || line.startsWith('FIELD_NATIVE_HTTP_ERROR ')) {
        const provider = providerName(f);
        requireRoute('http_terminal', f, client, fixture, provider);
        increment(httpTerminal, httpKey(client, provider, f.request_type, f.method, f.endpoint));
      }
    }

    for (const key of fileScopeKeys) {
      const scope = scopes.get(key);
      if (!scope) continue;
      if (fileInstrumentedClients.has(scope.client)) scope.instrumented = true;
      for (const phase of fileFrontend) scope.frontendPhases.add(phase);
    }
  }

  if (readableLogs === 0) problems.push('no_readable_log');
  if (scopes.size === 0) problems.push('missing_corpus_scope');
  if (frontendErrors > 0) problems.push(`frontend_capture_errors:${frontendErrors}`);

  for (const scope of scopes.values()) {
    const label = `${scope.client}:${scope.fixture}`;
    if (scope.expectedProviders <= 0) problems.push(`invalid_expected_provider_count:${label}`);
    if (!scope.ended) problems.push(`missing_corpus_end:${label}`);
    if (!scope.instrumented) problems.push(`missing_runtime_instrumentation:${label}`);
    if (scope.expectedProviders > 0 && scope.traversed.size !== scope.expectedProviders) {
      problems.push(`provider_traversal:${label}:${scope.traversed.size}/${scope.expectedProviders}`);
    }
    const executionProofs = scope.providerRoutesBegun + scope.providerLoadErrors + (scope.repositoryLoadFailed ? 1 : 0);
    if (executionProofs <= 0) problems.push(`missing_provider_execution:${label}`);

    if (scope.repositoryLoadBegun === 0) problems.push(`missing_repository_load:${label}`);
    if (scope.repositoryLoadBegun !== scope.repositoryLoadTerminal) {
      problems.push(`repository_load_terminal:${label}:${scope.repositoryLoadTerminal}/${scope.repositoryLoadBegun}`);
    }
    const expectedLoad = scope.repositoryLoadExpected || scope.expectedProviders;
    if (expectedLoad > 0 && scope.providerLoadObserved.size !== expectedLoad) {
      problems.push(`provider_load_coverage:${label}:${scope.providerLoadObserved.size}/${expectedLoad}`);
    }

    // Cache hits legitimately produce no repository network traffic. A successful
    // fresh install must prove its manifest/provider HTTP chain. A terminal install
    // failure may occur before a request is constructed; that absence is itself
    // valid evidence when the structured load error and provider fallout are present.
    if (!scope.repositoryLoadFailed && scope.repositoryLoadBegun > 0 && scope.repositoryCacheHits === 0 && scope.repositoryHttpRequests === 0) {
      problems.push(`missing_repository_http:${label}`);
    }
    if (scope.repositoryHttpRequests !== scope.repositoryHttpTerminal) {
      problems.push(`repository_http_terminal:${label}:${scope.repositoryHttpTerminal}/${scope.repositoryHttpRequests}`);
    }

    const requiredFrontend = new Set(['ui-launched', 'corpus-begin', 'corpus-end']);
    if (scope.providerRoutesBegun > 0) requiredFrontend.add('provider-loading');
    if (scope.repositoryLoadBegun > 0) {
      requiredFrontend.add('repository-load');
      if (!scope.repositoryLoadFailed) requiredFrontend.add('repository-loaded');
      else requiredFrontend.add('repository-load-error');
    }
    if (scope.repositoryHttpRequests > 0) {
      requiredFrontend.add('repository-http-request');
      requiredFrontend.add('repository-http-terminal');
    }
    if (scope.providerLoadObserved.size > 0) requiredFrontend.add('provider-load-state');
    if (scope.results > 0) requiredFrontend.add('provider-result');
    if (scope.httpRequests > 0) {
      requiredFrontend.add('provider-http-request');
      requiredFrontend.add('provider-http-terminal');
    }
    if (scope.playerResults > 0) {
      requiredFrontend.add('player-start');
      requiredFrontend.add('player-result');
    }
    for (const phase of requiredFrontend) {
      const legacyPhase = phase === 'repository-http-terminal'
        ? 'repository-http-response'
        : phase === 'provider-http-terminal'
          ? 'provider-http-response'
          : null;
      const observed = scope.frontendPhases.has(phase) || (legacyPhase && scope.frontendPhases.has(legacyPhase));
      if (!observed) problems.push(`missing_frontend_phase:${label}:${phase}`);
    }
  }

  for (const [key, begun] of routesBegun) {
    const terminal = Number(routesTerminal.get(key) || 0);
    if (terminal !== begun) problems.push(`provider_route_terminal:${key.replace(/\u0000/g, ':')}:${terminal}/${begun}`);
  }
  for (const [key, terminal] of routesTerminal) {
    const begun = Number(routesBegun.get(key) || 0);
    if (terminal > begun) problems.push(`provider_route_missing_begin:${key.replace(/\u0000/g, ':')}:${terminal}/${begun}`);
  }
  for (const [key, begun] of playersBegun) {
    const terminal = Number(playersTerminal.get(key) || 0);
    if (terminal !== begun) problems.push(`player_terminal:${key.replace(/\u0000/g, ':')}:${terminal}/${begun}`);
  }
  for (const [key, terminal] of playersTerminal) {
    const begun = Number(playersBegun.get(key) || 0);
    if (terminal > begun) problems.push(`player_missing_begin:${key.replace(/\u0000/g, ':')}:${terminal}/${begun}`);
  }
  for (const [key, requested] of httpRequests) {
    const terminal = Number(httpTerminal.get(key) || 0);
    if (terminal !== requested) problems.push(`http_terminal:${key.replace(/\u0000/g, ':')}:${terminal}/${requested}`);
  }
  for (const [key, terminal] of httpTerminal) {
    const requested = Number(httpRequests.get(key) || 0);
    if (terminal > requested) problems.push(`http_missing_request:${key.replace(/\u0000/g, ':')}:${terminal}/${requested}`);
  }
  for (const [key, requested] of repositoryHttpRequests) {
    const terminal = Number(repositoryHttpTerminal.get(key) || 0);
    if (terminal !== requested) problems.push(`repository_http_pair:${key.replace(/\u0000/g, ':')}:${terminal}/${requested}`);
  }
  for (const [key, terminal] of repositoryHttpTerminal) {
    const requested = Number(repositoryHttpRequests.get(key) || 0);
    if (terminal > requested) problems.push(`repository_http_missing_request:${key.replace(/\u0000/g, ':')}:${terminal}/${requested}`);
  }

  const providerExecutions = [...routesTerminal.values()].reduce((a, b) => a + b, 0);
  const providerLoadErrors = [...scopes.values()].reduce((sum, scope) => sum + scope.providerLoadErrors, 0);
  const repositoryLoadFailures = [...scopes.values()].reduce((sum, scope) => sum + (scope.repositoryLoadFailed ? 1 : 0), 0);
  const executionProofs = providerExecutions + providerLoadErrors + repositoryLoadFailures;
  return {
    complete: problems.length === 0,
    problems,
    stats: {
      readableLogs,
      scopes: scopes.size,
      providerRoutes: routesBegun.size,
      providerExecutions,
      executionProofs,
      providerLoads: [...scopes.values()].reduce((sum, scope) => sum + scope.providerLoadObserved.size, 0),
      providerLoadErrors,
      repositoryLoadFailures,
      repositoryCacheHits: [...scopes.values()].reduce((sum, scope) => sum + scope.repositoryCacheHits, 0),
      repositoryHttpRequests: [...repositoryHttpRequests.values()].reduce((a, b) => a + b, 0),
      playerProbes: playersTerminal.size,
      httpRequests: [...httpRequests.values()].reduce((a, b) => a + b, 0),
      frontendErrors,
    },
  };
}

module.exports = { assessNativeEvidence };
