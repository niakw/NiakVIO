#!/usr/bin/env python3
"""One-shot/idempotent source upgrade for the common ProviderBase v3 reader.

The upgrade deliberately changes only NiakVIO-owned source.  It does not import
or execute upstream code.  Once a successful reconstruction commits the changed
source files, subsequent runs are no-ops except for the pinned source assertion.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOWARU_REF = "c3ce6f43a1ba8ccf2f3838b5cd9db40745c33fa2"
MARKER = "NIAKVIO_PROVIDER_BASE_SOURCE_PLAN_V4"

SOURCE_PLAN_JS = r'''
/* NIAKVIO_PROVIDER_BASE_SOURCE_PLAN_V4 */
function _spv4Family() {
  return _text(NIAKVIO_PROVIDER_MODEL.sourceRuntimeFamily || "unknown").toLowerCase();
}
function _spv4Routes() {
  return Array.isArray(NIAKVIO_PROVIDER_MODEL.routes) ? NIAKVIO_PROVIDER_MODEL.routes.map(_text).filter(Boolean) : [];
}
function _spv4Titles(meta) {
  return _uniq([meta && meta.title, ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])])
    .map(_text).filter(Boolean).slice(0, 4);
}
function _spv4Base64(value) {
  const raw = _text(value).replace(/\s+/g, "");
  try { if (typeof atob === "function") return atob(raw); } catch (_) {}
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  let bits = 0, bitCount = 0, out = "";
  for (let i = 0; i < raw.length; i += 1) {
    if (raw[i] === "=") break;
    const n = alphabet.indexOf(raw[i]);
    if (n < 0) continue;
    bits = (bits << 6) | n;
    bitCount += 6;
    if (bitCount >= 8) {
      bitCount -= 8;
      out += String.fromCharCode((bits >> bitCount) & 255);
    }
  }
  return out;
}
function _spv4Expand(pattern, meta, vars, mediaType, season, episode) {
  let route = _text(pattern);
  if (!route) return [];
  vars = vars || {};
  const values = {
    query: vars.query != null ? vars.query : (meta && meta.title),
    title: vars.query != null ? vars.query : (meta && meta.title),
    slug: vars.slug != null ? vars.slug : _slug(meta && meta.title),
    id: vars.providerId != null ? vars.providerId : "",
    providerid: vars.providerId != null ? vars.providerId : "",
    tmdbid: meta && meta.tmdbId,
    tmdb_id: meta && meta.tmdbId,
    imdbid: meta && meta.imdbId,
    imdb_id: meta && meta.imdbId,
    media: mediaType === "movie" ? "movie" : "tv",
    type: mediaType === "movie" ? "movie" : "tv",
    season,
    episode
  };
  route = route.replace(/\{([^}]+)\}/g, function(match, key) {
    const value = values[_text(key).toLowerCase()];
    return value == null || value === "" ? "" : encodeURIComponent(_text(value));
  });
  if (/\{[^}]+\}/.test(route)) return [];
  if (/^https?:\/\//i.test(route)) return [route];
  const out = [];
  for (const base of _runtimeBases()) {
    const absolute = _absolute(route, base);
    if (absolute) out.push(absolute);
  }
  return _uniq(out);
}
function _spv4IsSearchRoute(route, family) {
  const value = _text(route).toLowerCase();
  if (/\{query\}|[?&](?:s|q|query|keyword|search|story)=/i.test(value)) return true;
  if (/\/api\/search(?:[/?#]|$)/i.test(value)) return true;
  return /form/.test(family) && /\/template-php\/[^?#]*fetch\.php(?:[?#]|$)/i.test(value);
}
function _spv4IsActionRoute(route) {
  return /full-story\.php|controller\.php\?mod=playepisode/i.test(_text(route));
}
function _spv4IsDetailRoute(route, family) {
  const value = _text(route).toLowerCase();
  if (!value || _spv4IsSearchRoute(value, family) || _spv4IsActionRoute(value)) return false;
  return /\{(?:slug|id|imdbid|imdb_id|tmdbid|tmdb_id|season|episode)\}/i.test(value) ||
    /\/(?:anime|animes|movie|movies|film|films|serie|series|voir-series|episode|saison|season|saga|catalogue|watch)(?:[/?#.-]|$)/i.test(value);
}
function _spv4SameProviderOrigin(url) {
  const candidate = _origin(url);
  return !!candidate && _runtimeBases().some(base => _origin(base) === candidate);
}
function _spv4AttrUrls(text, base) {
  const out = [];
  const value = _embeddedText(text);
  const re = /(?:src|href|data-embed|data-src|data-url|file)\s*=\s*["']([^"']+)["']/gi;
  let match;
  while ((match = re.exec(value)) !== null) {
    const absolute = _absolute(match[1], base);
    if (absolute && /^https?:/i.test(absolute)) out.push(absolute);
    if (out.length >= 160) break;
  }
  return _uniq(out.concat(_extractUrls(value, base)));
}
function _spv4UrlScore(url, meta) {
  let score = _candidateScore(url, meta);
  try {
    const path = decodeURIComponent(new URL(url).pathname || "").toLowerCase();
    const wanted = _spv4Titles(meta).map(_slug).filter(Boolean);
    for (const title of wanted) {
      if (title && path.includes(title)) score += 100;
      for (const token of title.split("-").filter(v => v.length >= 3)) if (path.includes(token)) score += 16;
    }
    if (/\/(?:anime|animes|movie|movies|film|films|serie|series|voir-series|watch|title)\//i.test(path)) score += 24;
  } catch (_) {}
  return score;
}
function _spv4HtmlDetails(html, base, meta) {
  return _spv4AttrUrls(html, base)
    .filter(_spv4SameProviderOrigin)
    .map(url => ({ url, score: _spv4UrlScore(url, meta) }))
    .filter(row => row.score >= 24)
    .sort((a, b) => b.score - a.score)
    .map(row => row.url)
    .slice(0, 8);
}
function _spv4JsonRows(value, out) {
  out = out || [];
  if (Array.isArray(value)) {
    for (const child of value) _spv4JsonRows(child, out);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  out.push(value);
  for (const child of Object.values(value)) {
    if (child && typeof child === "object") _spv4JsonRows(child, out);
    if (out.length >= 300) break;
  }
  return out;
}
function _spv4TitleScore(title, meta) {
  const actual = _slug(title);
  if (!actual) return 0;
  let best = 0;
  for (const expected of _spv4Titles(meta).map(_slug).filter(Boolean)) {
    if (actual === expected) best = Math.max(best, 240);
    else if (actual.includes(expected) || expected.includes(actual)) best = Math.max(best, 110);
    else {
      let score = 0;
      for (const token of expected.split("-").filter(v => v.length >= 3)) if (actual.includes(token)) score += 18;
      best = Math.max(best, score);
    }
  }
  return best;
}
function _spv4JsonDetails(value, base, meta, mediaType, season, episode, family) {
  const details = [];
  const detailRoutes = _spv4Routes().filter(route => _spv4IsDetailRoute(route, family));
  const rows = _spv4JsonRows(value, [])
    .map(row => ({
      row,
      score: _spv4TitleScore(row.title || row.name || row.original_title || row.post_title || "", meta)
    }))
    .filter(item => item.score >= 36)
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);
  for (const item of rows) {
    const row = item.row;
    const direct = _text(row.url || row.href || row.permalink || "");
    if (direct) {
      const absolute = _absolute(direct, base);
      if (absolute && _spv4SameProviderOrigin(absolute)) details.push(absolute);
    }
    const vars = {
      slug: _text(row.slug || row.permalink_slug || row.seo_slug || "") || _slug(row.title || row.name || meta.title),
      providerId: _text(row.id || row._id || row.media_id || row.post_id || "")
    };
    for (const route of detailRoutes) {
      details.push(..._spv4Expand(route, meta, vars, mediaType, season, episode));
    }
  }
  return _uniq(details).slice(0, 12);
}
async function _spv4SearchResponse(url, query, family) {
  const form = /form/.test(family) && /\/template-php\/[^?#]*fetch\.php(?:[?#]|$)/i.test(url);
  const options = form ? {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-Requested-With": "XMLHttpRequest",
      "Referer": _searchBases()[0] || ""
    },
    body: "query=" + encodeURIComponent(_text(query))
  } : {};
  const response = await _fetch(url, options);
  const contentType = _text(response.headers.get("content-type")).toLowerCase();
  if (contentType.includes("json")) return { json: await response.json(), text: "", base: response.url || url };
  const text = await response.text();
  try {
    if (/^\s*[\[{]/.test(text)) return { json: JSON.parse(text), text: "", base: response.url || url };
  } catch (_) {}
  return { json: null, text, base: response.url || url };
}
async function _spv4FindDetails(meta, mediaType, season, episode, family) {
  const out = [];
  const searchRoutes = _spv4Routes().filter(route => _spv4IsSearchRoute(route, family));
  for (const query of _spv4Titles(meta).slice(0, 3)) {
    for (const route of searchRoutes.slice(0, 3)) {
      const urls = _spv4Expand(route, Object.assign({}, meta, { title: query }), { query }, mediaType, season, episode);
      for (const url of urls.slice(0, 2)) {
        try {
          const payload = await _spv4SearchResponse(url, query, family);
          if (payload.json != null) out.push(..._spv4JsonDetails(payload.json, payload.base, meta, mediaType, season, episode, family));
          else out.push(..._spv4HtmlDetails(payload.text, payload.base, meta));
        } catch (_) {}
        if (out.length) break;
      }
      if (out.length) break;
    }
    if (out.length) break;
  }

  // Slug-driven catalogues (Sekai and similar) do not expose a search endpoint.
  // Generate only deterministic title slugs from Core metadata.
  const detailRoutes = _spv4Routes().filter(route => _spv4IsDetailRoute(route, family));
  for (const title of _spv4Titles(meta).slice(0, 3)) {
    const slug = _slug(title);
    if (!slug) continue;
    for (const route of detailRoutes) {
      if (!/\{slug\}/i.test(route) || /\{id\}/i.test(route)) continue;
      out.push(..._spv4Expand(route, Object.assign({}, meta, { title }), { slug }, mediaType, season, episode));
    }
  }
  return _uniq(out).slice(0, 16);
}
function _spv4DirectStreams(urls, referer) {
  const direct = _uniq(urls).filter(_directMedia);
  return direct.length ? _streams(direct, referer).slice(0, 12) : [];
}
async function _spv4NestedStreams(urls, referer) {
  const candidates = _uniq(urls).filter(url => _playerLike(url) || /(?:sibnet|vidmoly|streamtape|sendvid|vidoza|myvi)/i.test(url)).slice(0, 6);
  if (!candidates.length) return [];
  return (await _crawlDirectMedia(candidates, referer, 2)).slice(0, 12);
}
async function _spv4FullStory(detailUrl, meta, mediaType, season, episode) {
  const idMatch = _text(detailUrl).match(/\/(\d+)-/);
  if (!idMatch) return [];
  const route = _spv4Routes().find(value => /full-story\.php/i.test(value));
  if (!route) return [];
  const targets = _spv4Expand(route, meta, { providerId: idMatch[1] }, mediaType, season, episode);
  for (const target of targets.slice(0, 2)) {
    try {
      const response = await _fetch(target, { headers: { "X-Requested-With": "XMLHttpRequest", "Referer": detailUrl } });
      let html = "";
      const contentType = _text(response.headers.get("content-type")).toLowerCase();
      if (contentType.includes("json")) {
        const value = await response.json();
        html = _text(value && value.html);
      } else {
        const raw = await response.text();
        try { const value = JSON.parse(raw); html = _text(value && value.html); } catch (_) { html = raw; }
      }
      if (!html) continue;
      const wanted = Math.max(1, Number(episode) || 1);
      const epNumbers = [];
      const epRe = /data-number\s*=\s*["'](\d+)["']/gi;
      let epMatch;
      while ((epMatch = epRe.exec(html)) !== null) epNumbers.push(Number(epMatch[1]));
      const players = [];
      const cpRe = /id\s*=\s*["']content_player_(\d+)[a-z]*["'][^>]*>\s*(\d+)\s*</gi;
      let cp;
      while ((cp = cpRe.exec(html)) !== null) players.push(cp[2]);
      const index = epNumbers.indexOf(wanted);
      if (index >= 0 && index < players.length && /^\d+$/.test(players[index])) {
        return _streams(["https://video.sibnet.ru/shell.php?videoid=" + players[index]], detailUrl).slice(0, 4);
      }
      const urls = _spv4AttrUrls(html, target);
      const direct = _spv4DirectStreams(urls, target);
      if (direct.length) return direct;
      const nested = await _spv4NestedStreams(urls, target);
      if (nested.length) return nested;
    } catch (_) {}
  }
  return [];
}
async function _spv4PlayEpisode(detailUrl, html, meta, mediaType, season, episode) {
  let pageUrl = detailUrl;
  let pageHtml = html;
  if (mediaType !== "movie" && season != null && episode != null && /\.html(?:[?#]|$)/i.test(detailUrl)) {
    pageUrl = detailUrl.replace(/\.html(?:[?#].*)?$/i, "") + "/" + Number(season || 1) + "-saison/" + Number(episode || 1) + "-episode.html";
    try {
      const response = await _fetch(pageUrl);
      pageHtml = await response.text();
    } catch (_) { return []; }
  }
  const pairs = [];
  const pairRe = /playEpisode\([^,]+,\s*["'](\d+)["']\s*,\s*["']([^"']+)["']/gi;
  let match;
  while ((match = pairRe.exec(pageHtml)) !== null) {
    const key = match[1] + "\u0000" + match[2];
    if (!pairs.some(row => row.key === key)) pairs.push({ key, id: match[1], xfield: match[2] });
    if (pairs.length >= 6) break;
  }
  if (!pairs.length) return [];
  const actionRoute = _spv4Routes().find(value => /controller\.php\?mod=playepisode/i.test(value));
  if (!actionRoute) return [];
  const actionUrls = _spv4Expand(actionRoute, meta, {}, mediaType, season, episode);
  for (const actionUrl of actionUrls.slice(0, 2)) {
    for (const pair of pairs.slice(0, 4)) {
      try {
        const response = await _fetch(actionUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": pageUrl
          },
          body: "id=" + encodeURIComponent(pair.id) + "&xfield=" + encodeURIComponent(pair.xfield) + "&action=playEpisode"
        });
        const text = await response.text();
        const urls = _spv4AttrUrls(text, response.url || actionUrl);
        const direct = _spv4DirectStreams(urls, pageUrl);
        if (direct.length) return direct;
        const nested = await _spv4NestedStreams(urls, pageUrl);
        if (nested.length) return nested;
      } catch (_) {}
    }
  }
  return [];
}
function _spv4SagaTargets(episode) {
  const out = [];
  try {
    const ctx = typeof globalThis !== "undefined" ? globalThis.__nuvioMediaContext : null;
    for (const key of ["absoluteEpisode", "absoluteEpisodeNumber", "episodeAbsolute", "absolute_episode"]) {
      const n = Number(ctx && ctx[key]);
      if (Number.isFinite(n) && n > 0 && !out.includes(n)) out.push(n);
    }
  } catch (_) {}
  const ep = Number(episode);
  if (Number.isFinite(ep) && ep > 0 && !out.includes(ep)) out.push(ep);
  return out;
}
function _spv4ParseSagaMedia(html, targets) {
  const constants = Object.create(null);
  const constRe = /var\s+([A-Za-z0-9_]+)\s*=\s*atob\(["']([^"']+)["']\)/g;
  let cm;
  while ((cm = constRe.exec(html)) !== null) constants[cm[1]] = _spv4Base64(cm[2]);
  const found = [];
  const assignment = /(episodeHD|episodeLow|episode)\s*\[\s*(\d+)\s*\]\s*=\s*([A-Za-z0-9_]+)\s*\+\s*["']([^"']+\.(?:mp4|m3u8))["']/gi;
  let row;
  while ((row = assignment.exec(html)) !== null) {
    const number = Number(row[2]);
    if (!targets.includes(number)) continue;
    const url = _text(constants[row[3]]) + row[4];
    if (/^https?:\/\//i.test(url)) found.push(url);
  }
  return _uniq(found);
}
async function _spv4Saga(detailUrl, html, episode) {
  const targets = _spv4SagaTargets(episode);
  if (!targets.length) return [];
  let urls = _spv4ParseSagaMedia(html, targets);
  if (urls.length) return _streams(urls, detailUrl).slice(0, 6);
  const sagaUrls = _spv4AttrUrls(html, detailUrl).filter(url => /\/saga-\d+(?:[/?#]|$)/i.test(url)).slice(0, 6);
  for (const sagaUrl of sagaUrls) {
    try {
      const response = await _fetch(sagaUrl);
      const sagaHtml = await response.text();
      urls = _spv4ParseSagaMedia(sagaHtml, targets);
      if (urls.length) return _streams(urls, sagaUrl).slice(0, 6);
    } catch (_) {}
  }
  return [];
}
async function _spv4ResolveDetail(detailUrl, meta, mediaType, season, episode, family) {
  let response, html;
  try {
    response = await _fetch(detailUrl);
    html = await response.text();
  } catch (_) { return []; }
  const base = response.url || detailUrl;
  if (!_strictHtmlIdentityOk(html, meta)) return [];

  if (family === "dle-full-story") {
    const special = await _spv4FullStory(base, meta, mediaType, season, episode);
    if (special.length) return special;
  }
  if (family === "dle-playepisode-form") {
    const special = await _spv4PlayEpisode(base, html, meta, mediaType, season, episode);
    if (special.length) return special;
  }
  if (family === "slug-saga-inline-media") {
    const special = await _spv4Saga(base, html, episode);
    if (special.length) return special;
  }

  let urls = _spv4AttrUrls(html, base);
  if (mediaType !== "movie" && season != null && episode != null) {
    const s = Math.max(1, Number(season) || 1);
    const e = Math.max(1, Number(episode) || 1);
    const patterns = [
      new RegExp("/saison[-_/]?0*" + s + "[^?#]*episode[-_/]?0*" + e + "(?:[./?#]|$)", "i"),
      new RegExp("/0*" + s + "-saison/0*" + e + "-episode(?:[./?#]|$)", "i"),
      new RegExp("/episode[-_/]?0*" + e + "(?:[./?#]|$)", "i")
    ];
    const episodeLinks = urls.filter(url => patterns.some(pattern => pattern.test(url))).slice(0, 3);
    for (const episodeUrl of episodeLinks) {
      try {
        const epResponse = await _fetch(episodeUrl);
        const epHtml = await epResponse.text();
        urls = urls.concat(_spv4AttrUrls(epHtml, epResponse.url || episodeUrl));
      } catch (_) {}
    }
  }

  // DLE/legacy pages sometimes expose a numeric Sibnet id without a URL.
  const numeric = [];
  const sibRe = /(?:content_player_[^>]+>|videoid\s*[:=]\s*["']?)(\d{3,})/gi;
  let sm;
  while ((sm = sibRe.exec(html)) !== null) numeric.push("https://video.sibnet.ru/shell.php?videoid=" + sm[1]);
  urls = urls.concat(numeric);

  const direct = _spv4DirectStreams(urls, base);
  if (direct.length) return direct;
  return _spv4NestedStreams(urls, base);
}
async function _spv4GetStreams(tmdbId, mediaType, season, episode) {
  const primary = await getStreams(tmdbId, mediaType, season, episode);
  if (Array.isArray(primary) && primary.length) return primary;
  const family = _spv4Family();
  if (!family || family === "unknown") return [];
  const type = _text(mediaType || "movie").toLowerCase();
  const meta = await _tmdb(tmdbId, type);
  // Catalogue/source-plan families are forbidden from performing provider
  // network requests until Core has supplied TMDB metadata/cache.
  if (!meta || !meta.title) return [];
  const details = await _spv4FindDetails(meta, type, season, episode, family);
  for (const detail of details.slice(0, 8)) {
    const streams = await _spv4ResolveDetail(detail, meta, type, season, episode, family);
    if (streams.length) return streams;
  }
  return [];
}
'''


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one old source shape, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def patch_provider_base() -> bool:
    path = ROOT / "scripts/provider_base_store.py"
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    old = '''module.exports = {\n  getStreams,\n  get __niakvioProviderBase(){ return NIAKVIO_PROVIDER_MODEL; }\n};'''
    new = SOURCE_PLAN_JS.strip() + '''\nmodule.exports = {\n  getStreams: _spv4GetStreams,\n  get __niakvioProviderBase(){ return NIAKVIO_PROVIDER_MODEL; }\n};'''
    if text.count(old) != 1:
        raise AssertionError("ProviderBase export bridge source shape drifted")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def patch_strategy_contract() -> bool:
    path = ROOT / "tests/provider_v3_strategy_plan_contract_test.py"
    old = '''def route_kind(route: object) -> str:\n    value = str(route or "").strip().casefold()\n    if not value:\n        return "ignore"\n    if re.search(r"/api(?:[./?#]|$)", value):\n        return "api"\n    if re.search(r"/(?:player|embed|play)(?:[/?#.-]|$)", value):\n        return "player"\n    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword)=", value):\n        return "search"\n    if re.search(\n        r"\\{(?:id|tmdb|tmdb_id|tmdbid|title|slug)\\}|"\n        r"/(?:title|movie|movies|film|films|tv|series|show|watch|media)(?:[/?#]|$)",\n        value,\n    ):\n        return "detail"\n    return "other"\n'''
    new = '''def route_kind(route: object) -> str:\n    value = str(route or "").strip().casefold()\n    if not value:\n        return "ignore"\n    # Search semantics must win over a generic /api prefix (/api/search).\n    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword|search|story)=", value):\n        return "search"\n    if re.search(r"/template-php/[^?#]*fetch\\.php(?:[?#]|$)", value):\n        return "search"\n    if re.search(r"/api(?:[./?#]|$)", value):\n        return "api"\n    if re.search(r"/(?:player|embed|play)(?:[/?#.-]|$)", value):\n        return "player"\n    if re.search(\n        r"\\{(?:id|tmdb|tmdb_id|tmdbid|imdb|imdb_id|imdbid|title|query|slug|season|episode)\\}|"\n        r"/(?:title|movie|movies|film|films|tv|serie|series|show|watch|media|anime|animes|voir-series|episode|saison|season|saga|catalogue)(?:[/?#.-]|$)",\n        value,\n    ):\n        return "detail"\n    return "other"\n'''
    return replace_once(path, old, new, "strategy plan route classifier")


def patch_identity_classifier() -> bool:
    path = ROOT / "scripts/materialize_provider_v3_all.py"
    text = path.read_text(encoding="utf-8")
    changed = False
    old = 'r"|(?:[?&])(?:s|q|query|keyword|search)=",'
    new = 'r"|(?:[?&])(?:s|q|query|keyword|search|story)="\n            r"|/template-php/[^?#]*fetch\\.php(?:[?#]|$)",'
    if new not in text:
        if text.count(old) != 1:
            raise AssertionError("identity route classifier source shape drifted")
        text = text.replace(old, new, 1)
        changed = True
    path.write_text(text, encoding="utf-8")
    return changed


def patch_discovery_literals() -> bool:
    path = ROOT / "scripts/discover_candidates.py"
    text = path.read_text(encoding="utf-8")
    changed = False
    old = 'if key in {"q", "query", "search", "keyword", "s"}:'
    new = 'if key in {"q", "query", "search", "keyword", "story", "s"}:'
    if new not in text:
        if text.count(old) != 1:
            raise AssertionError("discovery query-placeholder source shape drifted")
        text = text.replace(old, new, 1)
        changed = True
    old2 = 'r"""(?:^|["\'])(/(?:api|search|recherche|watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|movie|movies|media|sheet|film|films|tv|series|show|episode|season|wp-json|wp-admin|index\\.php)[^"\'<>\\\\\\s]{0,500})""",'
    new2 = 'r"""(?:^|["\'])(/(?:api|search|recherche|watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|movie|movies|media|sheet|film|films|tv|series|show|anime|animes|catalogue|template-php|episode|episodes|season|saison|wp-json|wp-admin|index\\.php)[^"\'<>\\\\\\s]{0,500})""",'
    if new2 not in text and old2 in text:
        text = text.replace(old2, new2, 1)
        changed = True
    path.write_text(text, encoding="utf-8")
    return changed


def pin_gowaru_sources() -> bool:
    path = ROOT / "sources.json"
    text = path.read_text(encoding="utf-8")
    pinned = f"https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/{GOWARU_REF}/"
    main = "https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/refs/heads/main/"
    if main not in text:
        if pinned not in text:
            raise AssertionError("Gowaru source templates are neither main nor pinned")
        return False
    path.write_text(text.replace(main, pinned), encoding="utf-8")
    return True


def main() -> int:
    changes = {
        "provider_base": patch_provider_base(),
        "strategy_contract": patch_strategy_contract(),
        "identity_classifier": patch_identity_classifier(),
        "discovery_literals": patch_discovery_literals(),
        "gowaru_pin": pin_gowaru_sources(),
    }
    print(
        "PROVIDER_V3_SOURCE_PLAN_V4_UPGRADE_OK "
        + " ".join(f"{key}={str(value).lower()}" for key, value in changes.items())
        + f" gowaru_ref={GOWARU_REF}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
