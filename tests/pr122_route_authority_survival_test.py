#!/usr/bin/env python3
"""Legacy filename; contract corrected 2026-09-18.

PR #127 is the route/recipe fence whenever it superseded PR #122. Later provider
Lego may supersede #127, but PR122-only generic routes must never be silently
reintroduced into structured authority without fresh terminal proof.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'provider-overrides.json').read_text(encoding='utf-8'))
p=data['provider_patches']

forbidden_routes={
    'allanime': ['/?s={title}','/{slug}/','/{slug}-episode-{episode}/'],
    'allwish': ['/filter?keyword={title}','/ajax/episode/list/{id}','/ajax/server/list?servers={serverKey}','/ajax/server?get={serverId}'],
    'flemmix': ['/search?q={title}','/embed/video/{id}?expires={expires}&signature={signature}'],
    'moviebox': ['https://vidsrcme.ru/vs_src.php?type=movie&id={tmdbId}','https://vidsrcme.ru/vs_src.php?type=tv&id={tmdbId}&season={season}&episode={episode}'],
    'vidfast': ['/movie/{tmdbId}','/tv/{tmdbId}/{season}/{episode}'],
    'wookafr': ['/?s={title}','/streaming/{category}/{slug}/','/streaming/episodes/{slug}-saison-{season}-episode-{episode}/','https://lecteurvideo.com/embed.php?id={id}&tp={type}&url={source}'],
}
for provider,routes in forbidden_routes.items():
    learned=set(p[provider].get('learned_routes') or [])
    candidates=set(p[provider].get('candidate_learned_routes') or [])
    leaked=[r for r in routes if r in learned or r in candidates]
    assert not leaked, f'{provider}: PR122-only route leaked past PR127 fence: {leaked}'

# YFlix #127 deliberately carried movie authority only in the structured recipe.
for key in ('api_recipe','candidate_api_recipe'):
    y=p['yflix'].get(key) or {}
    assert y.get('movieRoute')=='https://enc-dec.app/db/flix/find?tmdb_id={tmdbId}&type=movie', (key,y)
    assert y.get('directRoute')=='/db/flix/find?tmdb_id={tmdbId}&type=movie', (key,y)
    assert 'tvRoute' not in y, (key,y)

# VidLove #122 api.vidlove.cc recipe was removed by #127. Newer V2 Lego/candidate
# knowledge may exist, but old api_recipe cannot be restored as authoritative DATA.
assert p['vidlove'].get('api_recipe') is None, p['vidlove'].get('api_recipe')

# Explicit post-#127 supersessions stay allowed/required; fence applies to DATA,
# not to newer independently versioned provider Lego.
scripts={
    'allwish':'scripts/provider_patches/allwish_current_runtime_v2.py',
    'vidfast':'scripts/provider_patches/vidfast_current_runtime_v2.py',
    'vidlove':'scripts/provider_patches/vidlove_current_api_v2.py',
}
for provider,script in scripts.items():
    assert script in (p[provider].get('provider_lego_scripts') or []), (provider,p[provider].get('provider_lego_scripts'))

print('PR127 route authority fence contract passed')
