#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'provider-overrides.json').read_text(encoding='utf-8'))
p=data['provider_patches']

expected_routes={
    'allanime': ['/?s={title}','/{slug}/','/{slug}-episode-{episode}/'],
    'allwish': ['/filter?keyword={title}','/ajax/episode/list/{id}','/ajax/server/list?servers={serverKey}','/ajax/server?get={serverId}'],
    'flemmix': ['/search?q={title}','/embed/video/{id}?expires={expires}&signature={signature}'],
    'moviebox': ['https://vidsrcme.ru/vs_src.php?type=movie&id={tmdbId}','https://vidsrcme.ru/vs_src.php?type=tv&id={tmdbId}&season={season}&episode={episode}'],
    'vidfast': ['/movie/{tmdbId}','/tv/{tmdbId}/{season}/{episode}'],
    'wookafr': ['/?s={title}','/streaming/{category}/{slug}/','/streaming/episodes/{slug}-saison-{season}-episode-{episode}/','https://lecteurvideo.com/embed.php?id={id}&tp={type}&url={source}'],
}
for provider,routes in expected_routes.items():
    learned=set(p[provider].get('learned_routes') or [])
    missing=[r for r in routes if r not in learned]
    assert not missing, f'{provider}: lost PR122 routes again: {missing}'

vidlove=p['vidlove'].get('api_recipe') or {}
assert vidlove.get('base')=='https://api.vidlove.cc', vidlove
assert vidlove.get('directRoute')=='/{media}?id={tmdbId}&mode=json&season={season}&episode={episode}', vidlove

for key in ('api_recipe','candidate_api_recipe'):
    y=p['yflix'].get(key) or {}
    assert y.get('movieRoute')=='/db/flix/find?tmdb_id={tmdbId}&type=movie', (key,y)
    assert y.get('tvRoute')=='/db/flix/find?tmdb_id={tmdbId}&type=tv', (key,y)

print('PR122 route authority survival contract passed')
