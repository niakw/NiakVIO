#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from provider_base_store import build_clean_provider_seed

text=build_clean_provider_seed('synthetic').decode('utf-8')
marker='NIAKVIO_PROVIDER_RUNTIME_RESOLVER_CONSUMER_V36'
assert marker in text
assert 'async function _providerRuntimeResolverV1' in text
assert 'globalThis.__niakvioProviderRuntimeResolverV1' in text
assert 'owner !== expected' in text
assert 'resolver.resolve([tmdbId, mediaType, season, episode])' in text

hook=text.index('const providerOwned = await _providerRuntimeResolverV1')
gate=text.index('if (!_runtimePlanAvailable()) return [];')
assert hook < gate, 'provider-owned resolver must run before generic-plan availability gate'

print('ProviderBase runtime resolver consumer V36 contract passed')
