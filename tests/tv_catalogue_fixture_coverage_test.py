#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'scripts' / 'audit_catalogue_identity_media.py').read_text(encoding='utf-8')

assert '"vf_revenant_s01e01"' in source
assert '"tmdbId": "126485"' in source
assert '"title": "Revenant"' in source
assert '"year": 2023' in source
assert '"vf_mushoku_s01e01"' in source
assert '"tmdbId": "94664"' in source
assert '"title": "Mushoku Tensei: Jobless Reincarnation"' in source
assert 'fixture_names.extend(["vf_jjk_s01e01", "vf_revenant_s01e01"])' in source
assert 'if is_vf and "anime" in types:' in source
assert 'fixture_names.append("vf_mushoku_s01e01")' in source

assert '"animated_movie_ninja_3"' in source
assert '"tmdbId": "1215638"' in source
assert '"title": "Mon ninja et moi 3"' in source
assert 'fixture_names.append("animated_movie_ninja_3")' in source

print('TV catalogue Revenant/Mushoku/animated-movie fixture coverage tests passed')
