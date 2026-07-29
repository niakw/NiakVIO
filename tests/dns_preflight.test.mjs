#!/usr/bin/env node
import assert from 'node:assert/strict';
import {
  checkDomainAcrossResolvers,
  discoverMigrationCandidates,
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
  assert.ok(!hints.some((item) => item.host.includes('githubusercontent.com')));
  assert.ok(!hints.some((item) => item.host.includes('themoviedb.org')));
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

console.log('French ISP DNS preflight tests passed');
