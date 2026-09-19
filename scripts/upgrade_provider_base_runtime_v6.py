#!/usr/bin/env python3
'''Apply cumulative ProviderBase runtime v6 fixes on top of the verified v5 reader.'''
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'provider_base_store.py'
V5_MARKER = '/* NIAKVIO_PROVIDER_BASE_RUNTIME_V5 */'
MARKER = '/* NIAKVIO_PROVIDER_BASE_RUNTIME_V6 */'


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f'{label}: expected one anchor, got {count}')
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding='utf-8')
    if MARKER in text:
        return False
    if V5_MARKER not in text:
        raise AssertionError('runtime v6 requires verified runtime v5 baseline')

    old_projection = '''    return {\n      title: aliases[0] || "",\n      aliases,\n      year: String(row.release_date || row.first_air_date || row.year || "").slice(0, 4),\n      tmdbId: String(tmdbId || "")\n    };'''
    new_projection = '''    const externalIds = row.external_ids && typeof row.external_ids === "object"\n      ? row.external_ids\n      : {};\n    const imdbId = _text(\n      row.imdb_id || row.imdbId || externalIds.imdb_id || ""\n    ).trim();\n    return {\n      title: aliases[0] || "",\n      aliases,\n      year: String(row.release_date || row.first_air_date || row.year || "").slice(0, 4),\n      tmdbId: String(tmdbId || ""),\n      imdbId,\n      externalIds\n    };'''
    text = once(text, old_projection, new_projection, 'tmdb-external-ids')

    crawl_anchor = 'async function _crawlDirectMedia(seedUrls, referer, maxDepth) {'
    eligible = r'''function _crawlEligible(url) {
  try {
    if (_directMedia(url) || _playerLike(url)) return true;
    const parsed = new URL(url);
    if (!/^https?:$/i.test(parsed.protocol)) return false;
    const host = _text(parsed.hostname).toLowerCase();
    const path = (parsed.pathname + parsed.search).toLowerCase();
    if (/(?:^|\.)(?:t\.me|telegram\.me|facebook\.com|instagram\.com|twitter\.com|x\.com|youtube\.com|youtu\.be)$/i.test(host)) return false;
    if (/\/(?:feed|comments?\/feed|wp-json\/oembed|assets?|static|images?|icons?|fonts?)(?:[/?#.-]|$)/i.test(path)) return false;
    if (/\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(path)) return false;
    return _crawlUrlScore(url) > 0;
  } catch (_) { return false; }
}
'''
    text = once(text, crawl_anchor, eligible + crawl_anchor, 'crawl-eligible-anchor')

    text = once(
        text,
        'const queue = _uniq(seedUrls).filter(_playerLike).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 6).map(url => ({ url, depth: 0, referer }));',
        'const queue = _uniq(seedUrls).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8).map(url => ({ url, depth: 0, referer }));',
        'crawl-seed-eligibility',
    )
    text = once(
        text,
        'for (const next of urls.filter(_playerLike).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 3)) {',
        'for (const next of urls.filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 4)) {',
        'crawl-child-eligibility',
    )
    text = once(
        text,
        'const discoveredNested = _uniq(urls.filter(_playerLike));',
        'const discoveredNested = _uniq(urls.filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a))).slice(0, 10);',
        'legacy-nested-eligibility',
    )
    text = once(
        text,
        'const candidates = _uniq(urls).filter(url => _playerLike(url) || /(?:sibnet|vidmoly|streamtape|sendvid|vidoza|myvi)/i.test(url)).slice(0, 6);',
        'const candidates = _uniq(urls).filter(url => _crawlEligible(url) || /(?:sibnet|vidmoly|streamtape|sendvid|vidoza|myvi)/i.test(url)).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8);',
        'source-plan-nested-eligibility',
    )

    text = once(text, V5_MARKER, V5_MARKER + '\n' + MARKER, 'runtime-v6-marker')
    TARGET.write_text(text, encoding='utf-8')
    return True


def validate() -> None:
    text = TARGET.read_text(encoding='utf-8')
    for needle in (
        MARKER,
        'function _crawlEligible(url)',
        'filter(_crawlEligible)',
        'imdbId,',
        'externalIds',
        'source-plan-nested-eligibility',
    ):
        if needle == 'source-plan-nested-eligibility':
            if 'filter(url => _crawlEligible(url)' not in text:
                raise AssertionError('missing runtime v6 source-plan nested eligibility')
            continue
        if needle not in text:
            raise AssertionError(f'missing runtime v6 marker: {needle}')
    subprocess.run([sys.executable, '-m', 'py_compile', str(TARGET)], check=True)


def main() -> int:
    changed = patch()
    validate()
    print(
        'PROVIDER_BASE_RUNTIME_V6_OK '
        f'changed={str(changed).lower()} external_ids=1 traversal_eligibility=1 nested_priority=1'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
