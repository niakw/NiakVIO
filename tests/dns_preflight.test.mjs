#!/usr/bin/env node
import assert from 'node:assert/strict';
import {
  checkDomainAcrossResolvers,
  createGlobalpingDependencies,
  discoverMigrationCandidates,
  discoverPeerMigrationCandidates,
  extractCandidateDomains,
  providerDecision,
} from '../scripts/provider_dns_preflight.mjs';

const baseConfig = {
  primary_french_isp: 'sfr',
  fallback_french_isps: ['orange', 'free'],
  neutral_resolvers: ['cloudflare'],
  continue_on_inconclusive: true,
  continue_on_global_unreachable: false,
  skip_runtime_on_confirmed_french_block: true,
  migration_discovery: { minimum_confidence: 80 },
  resolvers: {
    sfr: { servers: ['109.0.66.10'] },
    orange: { servers: ['80.10.246.2'] },
    free: { servers: ['212.27.40.240'] },
    cloudflare: { servers: ['1.1.1.1'], neutral: true },
  },
};

function dnsResult(name, status, addresses = []) {
  return { resolver: name, status, addresses, errors: [] };
}

{
  const hints = extractCandidateDomains(
    {
      canonical_id: 'movix',
      metadata: {
        logo: 'https://i.postimg.cc/logo.png',
        description: 'Films sur movix.fun',
      },
    },
    'fetch("https://raw.githubusercontent.com/x/y"); fetch("https://api.themoviedb.org/3/movie"); fetch("https://api.movix.fun/api/fstream")',
    {
      provider_patches: {
        movix: {
          fixed_endpoint: { api: 'https://api.movix.fun' },
          runtime_domain_replacements: { 'api.movix.cash': 'api.movix.fun' },
        },
      },
    },
    4,
  );
  assert.equal(hints[0].host, 'api.movix.fun');
  assert.ok(hints.some((item) => item.host === 'movix.fun'));
  assert.equal(hints.some((item) => item.host === 'raw.githubusercontent.com'), false);
  assert.equal(hints.some((item) => item.host === 'api.themoviedb.org'), false);
}

{
  const result = await checkDomainAcrossResolvers('example.test', baseConfig, {
    resolveFn: async (_host, resolver) => {
      if (resolver.name === 'sfr') return dnsResult('sfr', 'negative');
      if (resolver.name === 'orange') return dnsResult('orange', 'resolved', [{ address: '93.184.216.34', family: 4 }]);
      throw new Error('neutral resolver should not be reached after Orange passes');
    },
    probeFn: async (_host, resolver) => ({
      status: resolver.name === 'orange' ? 'reachable' : 'unreachable',
      redirects: [],
      body_excerpt: '',
    }),
  });
  assert.equal(result.status, 'accessible_french_fallback');
  assert.equal(result.selected_resolver, 'orange');
  assert.equal(result.continue_runtime, true);
}

{
  const result = await checkDomainAcrossResolvers('example.test', baseConfig, {
    resolveFn: async (_host, resolver) => {
      if (resolver.name === 'cloudflare') return dnsResult('cloudflare', 'resolved', [{ address: '93.184.216.34', family: 4 }]);
      return dnsResult(resolver.name, 'unavailable');
    },
    probeFn: async (_host, resolver) => ({
      status: resolver.name === 'cloudflare' ? 'reachable' : 'unreachable',
      redirects: [],
      body_excerpt: '',
    }),
  });
  assert.equal(result.status, 'french_resolvers_inconclusive');
  assert.equal(result.continue_runtime, true);
}

{
  const result = await checkDomainAcrossResolvers('movix.show', baseConfig, {
    resolveFn: async (_host, resolver) => {
      if (resolver.name === 'cloudflare') return dnsResult('cloudflare', 'resolved', [{ address: '93.184.216.34', family: 4 }]);
      return dnsResult(resolver.name, 'negative');
    },
    probeFn: async (_host, resolver) => ({
      status: resolver.name === 'cloudflare' ? 'reachable' : 'unreachable',
      redirects: resolver.name === 'cloudflare' ? [{ from: 'movix.show', to: 'movix.fun', status: 302 }] : [],
      body_excerpt: '',
    }),
    domainHints: [{ host: 'movix.fun' }],
  });
  assert.equal(result.status, 'confirmed_french_dns_or_http_block');
  assert.equal(result.continue_runtime, false);
  assert.equal(result.migration_candidates[0].host, 'movix.fun');
  assert.ok(result.migration_candidates[0].confidence >= 80);
  const decision = providerDecision([result], baseConfig);
  assert.equal(decision.status, 'confirmed_french_block');
  assert.equal(decision.continue_runtime, false);
  assert.equal(decision.migration_candidate.host, 'movix.fun');
}

{
  const candidates = discoverMigrationCandidates('api.movix.cash', [
    { http: { redirects: [{ from: 'api.movix.cash', to: 'api.movix.fun', status: 301 }], body_excerpt: '' } },
  ]);
  assert.equal(candidates[0].host, 'api.movix.fun');
  assert.equal(candidates[0].same_brand, true);
  assert.ok(candidates[0].confidence >= 80);
}


{
  const decision = providerDecision([
    { status: 'all_custom_resolvers_unavailable', migration_candidates: [] },
  ], baseConfig);
  assert.equal(decision.status, 'inconclusive');
  assert.equal(decision.continue_runtime, true);
}


{
  const calls = [];
  const fakeRunMeasurement = async (body) => {
    calls.push(body);
    if (body.type === 'dns') {
      return {
        id: 'dns-measurement-sfr',
        payload: {
          status: 'finished',
          results: [{
            probe: { country: 'FR', city: 'Paris', network: 'SFR', asn: 15557, tags: ['eyeball'] },
            result: { statusCode: 'NOERROR', answers: [{ type: 'A', value: '93.184.216.34' }], rawOutput: 'status: NOERROR' },
          }],
        },
      };
    }
    return {
      id: 'http-measurement-sfr',
      payload: {
        status: 'finished',
        results: [{
          probe: { country: 'FR', city: 'Paris', network: 'SFR', asn: 15557, tags: ['eyeball'] },
          result: { statusCode: 200, headers: [], rawOutput: 'HTTP/2 200\ncontent-type: text/html' },
        }],
      },
    };
  };
  const config = {
    ...baseConfig,
    remote_probe: {
      enabled: true,
      location_magic: { sfr: ['France+SFR+eyeball'] },
    },
    resolvers: {
      ...baseConfig.resolvers,
      sfr: { kind: 'french_isp', servers: ['109.0.66.10'] },
    },
  };
  const dependencies = createGlobalpingDependencies(config, { runMeasurement: fakeRunMeasurement });
  const dns = await dependencies.resolveFn('example.com', { name: 'sfr', kind: 'french_isp', servers: ['109.0.66.10'] }, config);
  assert.equal(dns.status, 'resolved');
  assert.equal(dns.transport, 'globalping');
  assert.equal(dns.measurement_id, 'dns-measurement-sfr');
  assert.equal(dns.location_magic, 'France+SFR+eyeball');
  const http = await dependencies.probeFn('example.com', { name: 'sfr', kind: 'french_isp', servers: ['109.0.66.10'] }, config);
  assert.equal(http.status, 'reachable');
  assert.equal(http.transport, 'globalping');
  assert.equal(calls[0].locations[0].magic, 'France+SFR+eyeball');
  assert.equal(calls[0].measurementOptions.resolver, '109.0.66.10');
  assert.equal(calls[1].locations[0].magic, 'France+SFR+eyeball');
  assert.equal(calls[1].measurementOptions.method, 'GET');
  assert.equal(calls[1].measurementOptions.ipVersion, 4);
  assert.equal('request' in calls[1].measurementOptions, false);
}


{
  const domainResults = [
    { host: 'api.movix.cloud', status: 'globally_unreachable', migration_candidates: [] },
    { host: 'api.movix.fun', status: 'accessible_primary_french_isp', selected_resolver: 'sfr', migration_candidates: [] },
    { host: 'movix.fun', status: 'accessible_primary_french_isp', selected_resolver: 'sfr', migration_candidates: [] },
  ];
  const migrations = discoverPeerMigrationCandidates(domainResults, baseConfig);
  assert.equal(migrations.length, 1);
  assert.equal(migrations[0].original_host, 'api.movix.cloud');
  assert.equal(migrations[0].host, 'api.movix.fun');
  assert.ok(migrations[0].evidence.includes('provider_peer_reachable_same_role'));
  const decision = providerDecision(domainResults, baseConfig);
  assert.equal(decision.status, 'pass');
  assert.equal(decision.migration_candidate.original_host, 'api.movix.cloud');
  assert.equal(decision.migration_candidate.host, 'api.movix.fun');
}

console.log('French ISP DNS preflight tests passed');


// Minified JavaScript member accesses must never become DNS candidates.
{
  const candidate = { canonical_id: 'demo', metadata: {} };
  const hints = extractCandidateDomains(candidate, `
    s.includes(x); Array.isArray(v); Object.keys(v); g.fetch(url);
    const a = "api.movix.fun"; const b = "https://real-provider.example.com/path";
  `, {}, 12);
  const hosts = new Set(hints.map((item) => item.host));
  for (const fake of ['s.includes', 'array.isarray', 'object.keys', 'g.fetch']) {
    assert.equal(hosts.has(fake), false, `false JavaScript domain leaked: ${fake}`);
  }
  assert.equal(hosts.has('api.movix.fun'), true);
  assert.equal(hosts.has('real-provider.example.com'), true);
}


// Neutral resolvers also use Globalping when remote probing is enabled, avoiding
// blocked outbound UDP from GitHub-hosted runners.
{
  const calls = [];
  const fakeRunMeasurement = async (body) => {
    calls.push(body);
    return {
      id: 'dns-neutral',
      payload: { status: 'finished', results: [{ probe: { country: 'FR' }, result: { statusCode: 'NOERROR', answers: [{ value: '93.184.216.34' }] } }] },
    };
  };
  const config = {
    ...baseConfig,
    remote_probe: { enabled: true, neutral_location_magic: ['France+eyeball'] },
    resolvers: { cloudflare: { kind: 'neutral', servers: ['1.1.1.1'] } },
  };
  const dependencies = createGlobalpingDependencies(config, { runMeasurement: fakeRunMeasurement });
  const dns = await dependencies.resolveFn('example.com', { name: 'cloudflare', kind: 'neutral', servers: ['1.1.1.1'] }, config);
  assert.equal(dns.transport, 'globalping');
  assert.equal(calls[0].locations[0].magic, 'France+eyeball');
  assert.equal(calls[0].measurementOptions.resolver, '1.1.1.1');
}
