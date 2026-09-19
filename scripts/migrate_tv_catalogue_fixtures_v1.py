#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'scripts' / 'audit_catalogue_identity_media.py'
PACKAGE = ROOT / 'package.json'


def main() -> int:
    source = AUDIT.read_text(encoding='utf-8')

    old_doc = '''Coverage:
- every TV-capable provider: a South-Korean series fixture (Squid Game S01E01),
- every movie-capable provider: Interstellar plus an impossible TMDb identity sentinel,
- every anime-capable provider: Jujutsu Kaisen S01E01,
- VF membership is retained in the report for language-specific coverage metrics,
- named HLS regression providers receive the same compatible representative fixtures.
'''
    new_doc = '''Coverage:
- every TV-capable provider: a South-Korean series fixture (Squid Game S01E01),
- VF TV providers: Revenant S01E01 to catch title/year collision and wrong-episode regressions,
- every movie-capable provider: Interstellar plus an impossible TMDb identity sentinel,
- every anime-capable provider: Jujutsu Kaisen S01E01 plus Mushoku Tensei S01E01 for VF members,
- VF membership is retained in the report for language-specific coverage metrics,
- named HLS regression providers receive the same compatible representative fixtures.
'''
    if new_doc not in source:
        if old_doc not in source:
            raise SystemExit('audit coverage doc anchor not found')
        source = source.replace(old_doc, new_doc, 1)

    fixture_anchor = '''    "impossible_movie": {
'''
    fixture_block = '''    "vf_revenant_s01e01": {
        "label": "Revenant S01E01",
        "tmdbId": "126485",
        "mediaType": "tv",
        "season": 1,
        "episode": 1,
        "title": "Revenant",
        "year": 2023,
    },
    "vf_mushoku_s01e01": {
        "label": "Mushoku Tensei S01E01",
        "tmdbId": "94664",
        "mediaType": "anime",
        "season": 1,
        "episode": 1,
        "title": "Mushoku Tensei: Jobless Reincarnation",
        "year": 2021,
    },
'''
    if '"vf_revenant_s01e01"' not in source:
        if fixture_anchor not in source:
            raise SystemExit('audit fixture insertion anchor not found')
        source = source.replace(fixture_anchor, fixture_block + fixture_anchor, 1)

    old_vf_tv = '''        if is_vf and "tv" in types:
            fixture_names.append("vf_jjk_s01e01")
'''
    new_vf_tv = '''        if is_vf and "tv" in types:
            fixture_names.extend(["vf_jjk_s01e01", "vf_revenant_s01e01"])
        if is_vf and "anime" in types:
            fixture_names.append("vf_mushoku_s01e01")
'''
    if new_vf_tv not in source:
        if old_vf_tv not in source:
            raise SystemExit('audit VF TV fixture anchor not found')
        source = source.replace(old_vf_tv, new_vf_tv, 1)

    old_suspect = '''            if "tv" in types:
                fixture_names.append("kdrama_squid_game_s01e01")
            if "anime" in types:
                fixture_names.append("vf_jjk_s01e01")
'''
    new_suspect = '''            if "tv" in types:
                fixture_names.extend(["kdrama_squid_game_s01e01", "vf_revenant_s01e01"])
            if "anime" in types:
                fixture_names.extend(["vf_jjk_s01e01", "vf_mushoku_s01e01"])
'''
    if new_suspect not in source:
        if old_suspect not in source:
            raise SystemExit('audit suspect fixture anchor not found')
        source = source.replace(old_suspect, new_suspect, 1)

    AUDIT.write_text(source, encoding='utf-8')

    import json
    package = json.loads(PACKAGE.read_text(encoding='utf-8'))
    command = package['scripts']['test']
    test = 'python3 tests/tv_catalogue_fixture_coverage_test.py'
    if test not in command:
        command += ' && ' + test
    package['scripts']['test'] = command
    PACKAGE.write_text(json.dumps(package, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print('TV catalogue audit now permanently covers Revenant and Mushoku Tensei for VF/suspect providers')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
