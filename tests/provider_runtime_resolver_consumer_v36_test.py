#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'scripts'/'provider_base_store.py').read_text(encoding='utf-8')

marker='NIAKVIO_PROVIDER_RUNTIME_RESOLVER_CONSUMER_V36'
assert marker in src
assert 'globalThis.__niakvioProviderRuntimeResolverV1' in src
assert 'owner !== expected' in src
assert '/^https?:\\/\\//i.test(_text(row.url))' in src

getstreams=src.index('async function getStreams(tmdbId, mediaType, season, episode)')
consumer=src.index('const providerOwned = await _providerRuntimeResolverV1', getstreams)
plan_gate=src.index('if (!_runtimePlanAvailable()) return [];', getstreams)
assert getstreams < consumer < plan_gate

print('Provider runtime resolver consumer V36 contract passed')
