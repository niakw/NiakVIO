#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from provider_base_store import build_clean_provider_seed

seed=build_clean_provider_seed('synthetic')
text=seed.decode('utf-8')

marker='NIAKVIO_PROVIDER_ABSOLUTE_ROUTE_DOMAIN_SUBSTITUTION_V35'
assert marker in text
assert 'const absolute = _substituteDomain(route);' in text
assert 'return absolute ? [absolute] : [];' in text

# Absolute learned routes must no longer bypass the same domainSubstitutions
# authority already used by _absolute() and runtime bases.
old='return /^https?:\\/\\//i.test(route) ? [route] : [];'
assert old not in text

print('ProviderBase absolute-route Domain Refresh substitution contract passed')
