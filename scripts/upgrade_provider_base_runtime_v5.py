#!/usr/bin/env python3
'''Upgrade the common ProviderBase reader with systemic runtime v5 fixes.'''
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'provider_base_store.py'
MARKER = '/* NIAKVIO_PROVIDER_BASE_RUNTIME_V5 */'


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f'{label}: expected one anchor, got {count}')
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding='utf-8')
    if MARKER in text:
        return False

    old = '''def _provider_data_route_is_executable(value: object) -> bool:\n    text = str(value or "").strip()\n    if not text or "${" in text or "encodeURIComponent(" in text:\n        return False\n    lowered = text.casefold()\n    return "q=ponyfill" not in lowered and lowered.rstrip("/") != "/license"\n'''
    new = '''def _provider_data_route_is_executable(value: object) -> bool:\n    text = str(value or "").strip()\n    if not text or "${" in text or "encodeURIComponent(" in text or "decodeURIComponent(" in text:\n        return False\n    lowered = text.casefold()\n    if "q=ponyfill" in lowered or lowered.rstrip("/") == "/license":\n        return False\n    if text.count("{") != text.count("}") or text.count("[") != text.count("]") or text.count("(") != text.count(")"):\n        return False\n    if re.search(r"(?:\\(\\?:|\\(\\?=|\\(\\?!|\\\\[dDsSwW][+*?]?|\\[[^\\]]*$|(?:^|[/_-])i\\[$)", text, re.I):\n        return False\n    if re.search(r"\\.(?:css|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)", text, re.I):\n        return False\n    if re.search(r"/(?:refs/heads/[^/]+/)?domains?\\.json(?:[?#]|$)", text, re.I):\n        return False\n    return True\n'''
    text = once(text, old, new, 'route-filter')

    anchor = 'async function _crawlDirectMedia(seedUrls, referer, maxDepth) {'
    scorer = r'''function _crawlUrlScore(url) {
  try {
    if (_directMedia(url)) return 5000;
    const parsed = new URL(url);
    const host = _text(parsed.hostname).toLowerCase();
    const path = (parsed.pathname + parsed.search).toLowerCase();
    let score = 0;
    if (/(?:^|\.)(?:vcloud|hubcloud|driveseed|hubdrive|gdflix|gofile|pixeldrain|streamtape|vidmoly|filelions|filemoon|streamwish|wishfast|dood|doodstream|mixdrop|voe|lulustream|savefiles)\./i.test(host)) score += 900;
    if (/(?:^|\.)(?:abhilinks\.(?:site|life))$/i.test(host)) score += 500;
    if (/\/(?:watch|embed|player|play|video|stream|source|server|resolve|proxy|drive|download|dl|links?|redirect)(?:[/?#.-]|$)/i.test(path)) score += 420;
    if (/\/archives?\/\d+/i.test(path)) score += 180;
    if (/(?:^|\.)(?:t\.me|telegram\.me|facebook\.com|instagram\.com|twitter\.com|x\.com|youtube\.com|youtu\.be)$/i.test(host)) score -= 1600;
    if (/\/(?:feed|comments?\/feed|wp-json\/oembed|assets?|static|images?|icons?|fonts?)(?:[/?#.-]|$)/i.test(path)) score -= 1200;
    if (/\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(path)) score -= 1600;
    return score;
  } catch (_) { return -5000; }
}
'''
    text = once(text, anchor, scorer + anchor, 'crawl-score-anchor')
    text = once(text, 'const queue = _uniq(seedUrls).filter(_playerLike).slice(0, 4).map(url => ({ url, depth: 0, referer }));', 'const queue = _uniq(seedUrls).filter(_playerLike).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 6).map(url => ({ url, depth: 0, referer }));', 'crawl-seed-priority')
    text = once(text, 'while (queue.length && requests < 7 && streams.length < 12) {', 'while (queue.length && requests < 10 && streams.length < 12) {\n    queue.sort((a,b)=>_crawlUrlScore(b.url)-_crawlUrlScore(a.url));', 'crawl-budget')
    text = once(text, 'for (const next of urls.filter(_playerLike).slice(0, 2)) {', 'for (const next of urls.filter(_playerLike).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 3)) {', 'crawl-child-priority')

    text = once(text, 'const re = /(?:src|href|data-embed|data-src|data-url|file)\\s*=\\s*["\']([^"\']+)["\']/gi;', 'const re = /(?:src|href|file|url|data-[a-z0-9_:-]+)\\s*=\\s*["\']([^"\']+)["\']/gi;', 'data-attrs')

    json_anchor = 'function _spv4JsonDetails(value, base, meta, mediaType, season, episode, family) {'
    scalar = r'''function _spv4Scalar(value) {
  if (value == null) return "";
  if (typeof value === "string" || typeof value === "number") return _text(value);
  if (typeof value !== "object") return "";
  for (const key of ["rendered","raw","value","text","title","name","slug","href","url","link","path"]) {
    const child = value[key];
    if (typeof child === "string" || typeof child === "number") return _text(child);
  }
  return "";
}
'''
    text = once(text, json_anchor, scalar + json_anchor, 'json-scalar')
    text = once(text, 'score: _spv4TitleScore(row.title || row.name || row.original_title || row.post_title || "", meta)', 'score: _spv4TitleScore(_spv4Scalar(row.title) || _spv4Scalar(row.name) || _spv4Scalar(row.original_title) || _spv4Scalar(row.post_title) || _spv4Scalar(row.label) || "", meta)', 'json-title')
    text = once(text, 'const direct = _text(row.url || row.href || row.permalink || "");', 'const direct = _spv4Scalar(row.url) || _spv4Scalar(row.href) || _spv4Scalar(row.permalink) || _spv4Scalar(row.link) || _spv4Scalar(row.path) || _spv4Scalar(row.guid) || "";', 'json-link')
    text = once(text, 'slug: _text(row.slug || row.permalink_slug || row.seo_slug || "") || _slug(row.title || row.name || meta.title),\n      providerId: _text(row.id || row._id || row.media_id || row.post_id || "")', 'slug: _spv4Scalar(row.slug) || _spv4Scalar(row.permalink_slug) || _spv4Scalar(row.seo_slug) || _slug(_spv4Scalar(row.title) || _spv4Scalar(row.name) || meta.title),\n      providerId: _spv4Scalar(row.id) || _spv4Scalar(row.ID) || _spv4Scalar(row._id) || _spv4Scalar(row.media_id) || _spv4Scalar(row.post_id)', 'json-vars')

    expand_anchor = 'route = route.replace(/\\{([^}]+)\\}/g, function(match, key) {'
    expand_prefix = r'''const encodedQuery = values.query == null ? "" : encodeURIComponent(_text(values.query));
  if (encodedQuery) route = route.replace(/([?&](?:s|q|query|keyword|search|story)=)(?:\.{3})?(?=&|#|$)/gi, function(_, prefix) { return prefix + encodedQuery; });
  '''
    text = once(text, expand_anchor, expand_prefix + expand_anchor, 'expand-empty-query')
    text = once(text, 'if (/\\{[^}]+\\}/.test(route)) return [];', 'if (/[{}]/.test(route)) return [];', 'expand-brace-guard')

    specials = r'''function _spv5SafeHttpStreamUrl(value) {
  const url = _text(value).trim();
  if (!/^https?:\/\//i.test(url)) return "";
  if (/\.torrent(?:[?#]|$)|[?&](?:magnet|infohash|btih)=/i.test(url)) return "";
  return url;
}
async function _spv5Stremio(tmdbId, mediaType, season, episode) {
  const type = mediaType === "movie" ? "movie" : "tv";
  const routes = _spv4Routes().filter(route => {
    const low = _text(route).toLowerCase();
    return /\/stream\//.test(low) && (type === "movie" ? /\/stream\/movie\//.test(low) : /\/stream\/(?:series|tv)\//.test(low));
  });
  for (const route of routes.slice(0, 4)) {
    for (const target of _spv4Expand(route, {tmdbId:_text(tmdbId),title:""}, {providerId:_text(tmdbId)}, type, season, episode).slice(0,3)) {
      try {
        const response = await _fetch(target, {headers:{Accept:"application/json"}});
        let value = null;
        const ct = _text(response.headers.get("content-type")).toLowerCase();
        if (ct.includes("json")) value = await response.json(); else { const raw=await response.text(); try{value=JSON.parse(raw)}catch(_){} }
        const urls=[];
        for (const row of (value && Array.isArray(value.streams) ? value.streams : []).slice(0,40)) {
          if (!row || typeof row !== "object" || row.infoHash || row.infohash || row.magnet || row.torrent) continue;
          const url=_spv5SafeHttpStreamUrl(row.url || row.streamUrl || row.stream_url || "");
          if (url) urls.push(url);
        }
        if (urls.length) return _streams(urls, response.url || target).slice(0,20);
      } catch (_) {}
    }
  }
  return [];
}
async function _spv5DleFilmApi(detailUrl, html, meta, mediaType, season, episode) {
  if (mediaType !== "movie") return [];
  const route = _spv4Routes().find(value => /\/engine\/ajax\/film_api\.php/i.test(_text(value)));
  if (!route) return [];
  const idMatch = _text(detailUrl).match(/\/(\d{2,})-[^/?#]+/) || _text(html).match(/(?:news[_-]?id|data-id|post[_-]?id)\s*[:=]\s*["']?(\d{2,})/i);
  if (!idMatch) return [];
  let targets = _spv4Expand(route, meta, {providerId:idMatch[1]}, mediaType, season, episode);
  targets = targets.map(value => /[?&]id=\d+/i.test(value) ? value : value + (value.includes("?") ? "&" : "?") + "id=" + encodeURIComponent(idMatch[1]));
  for (const target of targets.slice(0,3)) {
    try {
      const response = await _fetch(target,{headers:{"X-Requested-With":"XMLHttpRequest",Referer:detailUrl}});
      const ct=_text(response.headers.get("content-type")).toLowerCase();
      let urls=[];
      if (ct.includes("json")) { const value=await response.json(); urls=_uniq(_sourceUrls(value,response.url||target).concat(_jsonUrls(value))); }
      else { const raw=await response.text(); try{const value=JSON.parse(raw);urls=_uniq(_sourceUrls(value,response.url||target).concat(_jsonUrls(value)))}catch(_){urls=_spv4AttrUrls(raw,response.url||target)} }
      const direct=_spv4DirectStreams(urls,detailUrl); if (direct.length) return direct;
      const nested=await _spv4NestedStreams(urls,detailUrl); if (nested.length) return nested;
    } catch (_) {}
  }
  return [];
}
'''
    resolve_anchor = 'async function _spv4ResolveDetail(detailUrl, meta, mediaType, season, episode, family) {'
    text = once(text, resolve_anchor, specials + resolve_anchor, 'specials')
    dle_anchor = '''  if (family === "slug-saga-inline-media") {\n    const special = await _spv4Saga(base, html, episode);\n    if (special.length) return special;\n  }\n'''
    text = once(text, dle_anchor, dle_anchor + '''  if (family === "dle-film-api") {\n    const special = await _spv5DleFilmApi(base, html, meta, mediaType, season, episode);\n    if (special.length) return special;\n  }\n''', 'dle-call')

    get_anchor = 'async function _spv4GetStreams(tmdbId, mediaType, season, episode) {\n'
    text = once(text, get_anchor, get_anchor + '''  const runtimeFamily = _spv4Family();\n  if (runtimeFamily === "stremio-json") {\n    const stremio = await _spv5Stremio(tmdbId, mediaType, season, episode);\n    if (stremio.length) return stremio;\n  }\n''', 'stremio-call')

    text = once(text, '/* NIAKVIO_PROVIDER_BASE_SOURCE_PLAN_V4 */', '/* NIAKVIO_PROVIDER_BASE_SOURCE_PLAN_V4 */\n' + MARKER, 'marker')
    TARGET.write_text(text, encoding='utf-8')
    return True


def validate() -> None:
    text = TARGET.read_text(encoding='utf-8')
    for needle in (MARKER, 'function _crawlUrlScore(url)', 'async function _spv5Stremio(', 'async function _spv5DleFilmApi(', '_spv4Scalar(row.title)', 'family === "dle-film-api"'):
        if needle not in text:
            raise AssertionError(f'missing runtime v5 marker: {needle}')
    subprocess.run([sys.executable, '-m', 'py_compile', str(TARGET)], check=True)


def main() -> int:
    changed = patch()
    validate()
    print(f'PROVIDER_BASE_RUNTIME_V5_OK changed={str(changed).lower()} crawler_priority=1 stremio=1 wordpress_json=1 dle_film_api=1')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
