#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_v3_routes_sequential import route_role  # noqa: E402

assert route_role('/api/resolve?id=tt123&s={season}&e={episode}') != 'search'
assert route_role('/api/resolve?id=tt123&s=1&e=2') != 'search'
assert route_role('/?s={query}') == 'search'
assert route_role('/?s=interstellar') == 'search'
assert route_role('/api/search?q={query}') == 'search'
assert route_role('/?story={query}') == 'search'

print('PROVIDER_V3_SEASON_QUERY_ROLE_TEST_OK s_plus_e=season_episode standalone_s=search')
