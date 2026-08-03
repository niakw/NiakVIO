#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'health-config.json').read_text())
assert config['modes']['deep'].get('fixture_limit_per_category') is True
health=(ROOT/'scripts/health_check.mjs').read_text()
assert 'profile.requiredCategories' in health
assert "groups[category]" in health
worker=(ROOT/'scripts/provider_worker.cjs').read_text()
assert 'An array, including an empty one, is a valid provider contract result.' in worker
assert 'content_lookup_completed_no_streams' in health
sync=(ROOT/'scripts/discover_candidates.py').read_text()
assert 'published-baseline' in sync
assert 'provider_lkg_registry' in sync
assert 'Last published local artifact' in sync

# Explicit catalogue types must survive future upstream promotions. Anime-film
# providers use Nuvio's movie request shape even when their upstream manifest
# only advertises anime.
promote=(ROOT/'scripts/promote_candidates.py').read_text()
assert 'capability.get("catalogue_types")' in promote
assert 'policy_types or list(dict.fromkeys(curated_types + explicit_types))' in promote
overrides=json.loads((ROOT/'provider-overrides.json').read_text())
for provider_id in ['anime-sama','animesama-co','french-manga','voiranime-rip','vostfree','animoflix','voiranime']:
    assert set(overrides['provider_capabilities'][provider_id].get('catalogue_types', [])) >= {'movie','anime'}, provider_id
for manifest_path in [ROOT/'manifest.json', ROOT/'vf/manifest.json']:
    manifest=json.loads(manifest_path.read_text())
    by_id={str(row.get('id','')).casefold(): row for row in manifest.get('scrapers', [])}
    for provider_id in ['anime-sama','animesama-co','french-manga','voiranime-rip','vostfree','animoflix','voiranime']:
        if provider_id in by_id:
            assert {'movie','anime'} <= set(by_id[provider_id].get('supportedTypes', [])), (manifest_path, provider_id)

print('category regression and baseline policy tests passed')
