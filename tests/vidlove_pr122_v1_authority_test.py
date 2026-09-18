#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'provider-overrides.json').read_text(encoding='utf-8'))
row=data['provider_patches']['vidlove']
v1='scripts/provider_patches/vidlove_current_api_v1.py'
v2='scripts/provider_patches/vidlove_current_api_v2.py'
assert row.get('provider_lego_scripts') == [v1], row.get('provider_lego_scripts')
assert v2 not in (row.get('provider_lego_scripts') or [])
recipe=row.get('api_recipe') or {}
assert recipe.get('base') == 'https://api.vidlove.cc', recipe
assert recipe.get('directRoute') == '/{media}?id={tmdbId}&mode=json&season={season}&episode={episode}', recipe
assert (recipe.get('directRequest') or {}).get('headers',{}).get('Referer') == 'https://player.vidlove.cc/'
print('VidLove PR122 V1 execution authority contract passed')
