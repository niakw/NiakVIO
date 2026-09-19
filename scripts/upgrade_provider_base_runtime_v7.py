#!/usr/bin/env python3
'''Apply ProviderBase runtime v7 family-first routing and bounded catalogue/DLE recovery.'''
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'provider_base_store.py'
V6_MARKER = '/* NIAKVIO_PROVIDER_BASE_RUNTIME_V6 */'
MARKER = '/* NIAKVIO_PROVIDER_BASE_RUNTIME_V7 */'


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f'{label}: expected one anchor, got {count}')
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding='utf-8')
    if MARKER in text:
        return False
    if V6_MARKER not in text:
        raise AssertionError('runtime v7 requires verified runtime v6 baseline')

    old_same_origin = '''function _spv4SameProviderOrigin(url) {\nconst candidate = _origin(url);\nreturn !!candidate && _runtimeBases().some(base => _origin(base) === candidate);\n}'''
    new_same_origin = '''function _spv4SameProviderOrigin(url) {\nconst candidate = _origin(_substituteDomain(url));\nreturn !!candidate && _runtimeBases().some(base => _origin(_substituteDomain(base)) === candidate);\n}'''
    text = once(text, old_same_origin, new_same_origin, 'alias-aware-provider-origin')

    old_html_details = '''function _spv4HtmlDetails(html, base, meta) {\nreturn _spv4AttrUrls(html, base)\n.filter(_spv4SameProviderOrigin)\n.map(url => ({ url, score: _spv4UrlScore(url, meta) }))\n.filter(row => row.score >= 24)\n.sort((a, b) => b.score - a.score)\n.map(row => row.url)\n.slice(0, 8);\n}'''
    new_html_details = '''function _spv7DetailUrlEligible(url) {\ntry {\nconst parsed = new URL(url);\nconst path = _text(parsed.pathname).toLowerCase();\nconst hash = _text(parsed.hash).toLowerCase();\nif (/^#(?:comments?|respond|reply|share)/i.test(hash)) return false;\nif (/\\/(?:feed|wp-json|wp-admin|admin|login|register|privacy|terms)(?:[/?#.-]|$)/i.test(path)) return false;\nif (/\\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(path)) return false;\nreturn true;\n} catch (_) { return false; }\n}\nfunction _spv4HtmlDetails(html, base, meta) {\nreturn _spv4AttrUrls(html, base)\n.filter(_spv4SameProviderOrigin)\n.filter(_spv7DetailUrlEligible)\n.map(url => ({ url: _substituteDomain(url), score: _spv4UrlScore(url, meta) }))\n.filter(row => row.score >= 36)\n.sort((a, b) => b.score - a.score)\n.map(row => row.url)\n.slice(0, 8);\n}'''
    text = once(text, old_html_details, new_html_details, 'content-evidence-html-details')

    old_eligible = '''function _crawlEligible(url) {\n  try {\n    if (_directMedia(url) || _playerLike(url)) return true;\n    const parsed = new URL(url);\n    if (!/^https?:$/i.test(parsed.protocol)) return false;\n    const host = _text(parsed.hostname).toLowerCase();\n    const path = (parsed.pathname + parsed.search).toLowerCase();\n    if (/(?:^|\\.)(?:t\\.me|telegram\\.me|facebook\\.com|instagram\\.com|twitter\\.com|x\\.com|youtube\\.com|youtu\\.be)$/i.test(host)) return false;\n    if (/\\/(?:feed|comments?\\/feed|wp-json\\/oembed|assets?|static|images?|icons?|fonts?)(?:[/?#.-]|$)/i.test(path)) return false;\n    if (/\\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(path)) return false;\n    return _crawlUrlScore(url) > 0;\n  } catch (_) { return false; }\n}'''
    new_eligible = '''function _crawlCanonical(url) {\ntry {\nconst parsed = new URL(url);\nif (!/^https?:$/i.test(parsed.protocol)) return "";\nparsed.hash = "";\nreturn parsed.toString();\n} catch (_) { return ""; }\n}\nfunction _crawlEligible(url) {\n  try {\n    if (_directMedia(url)) return true;\n    const parsed = new URL(url);\n    if (!/^https?:$/i.test(parsed.protocol)) return false;\n    const host = _text(parsed.hostname).toLowerCase();\n    const path = (parsed.pathname + parsed.search).toLowerCase();\n    const hash = _text(parsed.hash).toLowerCase();\n    if (/^#(?:comments?|respond|reply|share)/i.test(hash)) return false;\n    if (/(?:^|\\.)(?:t\\.me|telegram\\.me|facebook\\.com|instagram\\.com|twitter\\.com|x\\.com|youtube\\.com|youtu\\.be)$/i.test(host)) return false;\n    if (/\\/(?:feed|comments?\\/feed|wp-json(?:\\/|$)|wp-admin|admin|login|register|assets?|static|images?|icons?|fonts?)(?:[/?#.-]|$)/i.test(path)) return false;\n    if (/\\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(path)) return false;\n    if (/(?:\\+t\\.uri|code%3a|message%3a|xhr%3a|\\{status:)/i.test(path)) return false;\n    return _playerLike(url) || _crawlUrlScore(url) > 0;\n  } catch (_) { return false; }\n}'''
    text = once(text, old_eligible, new_eligible, 'crawl-canonical-eligibility')

    text = once(
        text,
        'const queue = _uniq(seedUrls).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8).map(url => ({ url, depth: 0, referer }));',
        'const queue = _uniq(seedUrls.map(_crawlCanonical)).filter(Boolean).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8).map(url => ({ url, depth: 0, referer }));',
        'crawl-canonical-seeds',
    )
    text = once(
        text,
        'for (const next of urls.filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 4)) {',
        'for (const next of _uniq(urls.map(_crawlCanonical)).filter(Boolean).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 4)) {',
        'crawl-canonical-children',
    )
    text = once(
        text,
        'const candidates = _uniq(urls).filter(url => _crawlEligible(url) || /(?:sibnet|vidmoly|streamtape|sendvid|vidoza|myvi)/i.test(url)).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8);',
        'const candidates = _uniq(urls.map(_crawlCanonical)).filter(Boolean).filter(url => _crawlEligible(url) || /(?:sibnet|vidmoly|streamtape|sendvid|vidoza|myvi)/i.test(url)).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8);',
        'nested-canonical-candidates',
    )

    getstreams_anchor = 'async function _spv4GetStreams(tmdbId, mediaType, season, episode) {'
    helpers = r'''function _spv7ProviderSiteBases() {
  return _uniq([NIAKVIO_PROVIDER_MODEL.officialSite, NIAKVIO_PROVIDER_MODEL.knownSite])
    .map(_substituteDomain).filter(value => /^https?:/i.test(value));
}
function _spv7DleDetailLinks(html, base, meta) {
  const out = [];
  const text = _embeddedText(html);
  const re = /<a\b([^>]*)href=["']([^"']*(?:newsid=\d+|\/\d+[^"']*))['"]([^>]*)>([\s\S]*?)<\/a>/gi;
  let match;
  while ((match = re.exec(text)) !== null) {
    const label = _text(match[1]) + " " + _text(match[3]) + " " + _text(match[4]).replace(/<[^>]+>/g, " ");
    const score = _spv4TitleScore(label, meta);
    const url = _absolute(match[2], base);
    if (url && score >= 36 && _spv4SameProviderOrigin(url)) out.push({url:_substituteDomain(url), score});
    if (out.length >= 12) break;
  }
  return out.sort((a,b)=>b.score-a.score).map(row=>row.url).slice(0,6);
}
async function _spv7DleFindDetails(meta, mediaType, season, episode) {
  const out = [];
  for (const base of _spv7ProviderSiteBases().slice(0,2)) {
    try {
      const target = new URL("/engine/ajax/search.php", base).toString();
      const response = await _fetch(target, {
        method:"POST",
        headers:{"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","X-Requested-With":"XMLHttpRequest",Referer:base+"/"},
        body:"query="+encodeURIComponent(_text(meta && meta.title))+"&page=1"
      });
      out.push(..._spv7DleDetailLinks(await response.text(), response.url || target, meta));
    } catch (_) {}
    if (out.length) break;
  }
  if (out.length) return _uniq(out).slice(0,8);
  return _spv4FindDetails(meta, mediaType, season, episode, "dle-film-api");
}
async function _spv7DleTv(tmdbId, mediaType, season, episode) {
  if (mediaType === "movie" || tmdbId == null || episode == null) return [];
  const wantedSeason = Math.max(1, Number(season) || 1);
  const wantedEpisode = String(Math.max(1, Number(episode) || 1));
  for (const base of _spv7ProviderSiteBases().slice(0,2)) {
    try {
      const seasonsUrl = new URL("/engine/ajax/get_seasons.php?serie_tag=s-"+encodeURIComponent(_text(tmdbId))+"&news_id=0", base).toString();
      const response = await _fetch(seasonsUrl, {headers:{Accept:"application/json,text/plain,*/*",Referer:base+"/"}});
      const raw = await response.text();
      let seasons = null; try { seasons = JSON.parse(raw); } catch (_) {}
      if (!Array.isArray(seasons) || !seasons.length) continue;
      let chosen = seasons.find(row => {
        const match = _text(row && row.title).match(/saison\s*(\d+)/i);
        return match && Number(match[1]) === wantedSeason;
      }) || seasons[0];
      const seasonId = _text(chosen && chosen.id).trim();
      if (!seasonId) continue;
      const epsUrl = new URL("/data/eps_"+encodeURIComponent(seasonId)+".txt?v="+Math.floor(Date.now()/30000), base).toString();
      const epsResponse = await _fetch(epsUrl, {headers:{Accept:"application/json,text/plain,*/*",Referer:base+"/"}});
      const epsRaw = await epsResponse.text();
      let eps = null; try { eps = JSON.parse(epsRaw); } catch (_) {}
      if (!eps || typeof eps !== "object") continue;
      const rows = [];
      const seen = new Set();
      for (const lang of ["vf","vostfr","vo"]) {
        const bucket = eps[lang];
        const players = bucket && (bucket[wantedEpisode] || bucket[Number(wantedEpisode)]);
        if (!players || typeof players !== "object") continue;
        for (const [host, value] of Object.entries(players)) {
          const url = _text(value).trim();
          if (!/^https?:\/\//i.test(url) || seen.has(url)) continue;
          seen.add(url);
          rows.push({name:NIAKVIO_PROVIDER_MODEL.displayName,title:"["+lang.toUpperCase()+"] "+_text(host).toUpperCase(),url,language:lang,headers:{Referer:base+"/"}});
        }
      }
      if (rows.length) return rows.slice(0,24);
    } catch (_) {}
  }
  return [];
}
'''
    text = once(text, getstreams_anchor, helpers + getstreams_anchor, 'runtime-v7-family-helpers')

    old_getstreams = '''async function _spv4GetStreams(tmdbId, mediaType, season, episode) {\nconst runtimeFamily = _spv4Family();\nif (runtimeFamily === "stremio-json") {\nconst stremio = await _spv5Stremio(tmdbId, mediaType, season, episode);\nif (stremio.length) return stremio;\n}\nconst primary = await getStreams(tmdbId, mediaType, season, episode);\nif (Array.isArray(primary) && primary.length) return primary;\nconst family = _spv4Family();\nif (!family || family === "unknown") return [];\nconst type = _text(mediaType || "movie").toLowerCase();\nconst meta = await _tmdb(tmdbId, type);\n// Catalogue/source-plan families are forbidden from performing provider\n// network requests until Core has supplied TMDB metadata/cache.\nif (!meta || !meta.title) return [];\nconst details = await _spv4FindDetails(meta, type, season, episode, family);\nfor (const detail of details.slice(0, 8)) {\nconst streams = await _spv4ResolveDetail(detail, meta, type, season, episode, family);\nif (streams.length) return streams;\n}\nreturn [];\n}'''
    new_getstreams = '''async function _spv4GetStreams(tmdbId, mediaType, season, episode) {\nconst family = _spv4Family();\nconst type = _text(mediaType || "movie").toLowerCase();\nif (family === "stremio-json") {\nconst stremio = await _spv5Stremio(tmdbId, type, season, episode);\nif (stremio.length) return stremio;\n}\nif (family && family !== "unknown") {\nconst meta = await _tmdb(tmdbId, type);\n// Known source families execute their typed source plan before the generic\n// fallback. This prevents broad catalogue/API guesses from spending the\n// provider budget on category pages, dead aliases and placeholder routes.\nif (meta && meta.title) {\nif (family === "dle-film-api" && type !== "movie") {\nconst tv = await _spv7DleTv(tmdbId, type, season, episode);\nif (tv.length) return tv;\n}\nconst details = family === "dle-film-api"\n? await _spv7DleFindDetails(meta, type, season, episode)\n: await _spv4FindDetails(meta, type, season, episode, family);\nfor (const detail of details.slice(0, 8)) {\nconst streams = await _spv4ResolveDetail(detail, meta, type, season, episode, family);\nif (streams.length) return streams;\n}\n}\n}\nconst primary = await getStreams(tmdbId, type, season, episode);\nif (Array.isArray(primary) && primary.length) return primary;\nreturn [];\n}'''
    text = once(text, old_getstreams, new_getstreams, 'source-plan-first-runtime')

    text = once(text, V6_MARKER, V6_MARKER + '\n' + MARKER, 'runtime-v7-marker')
    TARGET.write_text(text, encoding='utf-8')
    return True


def validate() -> None:
    text = TARGET.read_text(encoding='utf-8')
    for needle in (
        MARKER,
        'function _crawlCanonical(url)',
        'function _spv7DleTv(',
        'function _spv7DleFindDetails(',
        'row.score >= 36',
        '_origin(_substituteDomain(url))',
        'Known source families execute their typed source plan before the generic',
    ):
        if needle not in text:
            raise AssertionError(f'missing runtime v7 contract: {needle}')
    subprocess.run([sys.executable, '-m', 'py_compile', str(TARGET)], check=True)


def main() -> int:
    changed = patch()
    validate()
    print(
        'PROVIDER_BASE_RUNTIME_V7_OK '
        f'changed={str(changed).lower()} source_plan_first=1 alias_origin=1 '
        'crawl_canonical=1 dle_tv=1 dle_search=1'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
