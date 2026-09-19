"use strict";

/* NIAKVIO_PROVIDER_BASE_OWNED_V2 */
const NIAKVIO_PROVIDER_MODEL = Object.freeze({"authoring":"niakvio-owned-v2","displayName":"Mugiwara-no-Streaming","fixedApi":null,"knownSite":"https://www.mugiwara-no-streaming.com","observedUrls":["https://video/","https://${/","https://vidmoly.to/","https://${_}/","https://my.mail.ru/+/video/meta/${i}","https://my.mail.ru/","https://${v}${n}/","https://${v}/","https://${n}/","https://f/","https://vidzy.live/","https://${i}/pa","https://${i}/","https://www.myvi.ru/","https://www.myvi.ru/api/video/${a[1]}","https://younetu.org/","https://vidoza.net/","https://lecteurvideo.com/","https://wookafr.center/","https://${a}/","https://up4fun.top/","https://www.mugiwara-no-/","https://kit/","https://npm/","https://loda/","https://openj/","http://under/"],"officialApi":null,"officialHub":"https://streaminganime.fr/site/10/mugiwara-no-streaming","officialSite":"https://www.mugiwara-no-streaming.com","origins":["https://video.sibnet.ru","https://vidmoly.me","https://streamtape.com","https://sendvid.com","https://www.myvi.ru","https://younetu.org","https://vidoza.net","https://lecteurvideo.com","https://up4fun.top","https://www.mugiwara-no-streaming.com","https://kitsu.io","https://npms.io","https://lodash.com","https://openjsf.org","http://underscorejs.org","https://old.invalid","https://www.themoviedb.org","https://video","https://${","https://vidmoly.to","https://${_}","https://my.mail.ru","https://${v}${n}","https://${v}"],"providerId":"mugiwarastream","reconstructionState":"learning-clean-seed","routePlanVersion":1,"routes":["/","/+/video/meta/${i}","/pa","/api/video/${a[1]}"],"runtimeDiscovery":false,"runtimeRole":"reader","strategy":"mixed_embed_resolver","supportedTypes":["movie","tv"],"upstreamCodeEmbedded":false,"upstreamCodeExecuted":false});

function _uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}
function _origin(value) {
  try { return new URL(value).origin; } catch (_) { return ""; }
}
function _absolute(value, base) {
  try { return new URL(value, base).toString(); } catch (_) { return ""; }
}
function _text(value) {
  return String(value == null ? "" : value);
}
function _embeddedText(value) {
  return _text(value).replace(
    /\\u002[fF]|\\u003[aA]|\\u0026|\\u003[dD]|\\\/|\\"|&quot;|&#34;|&amp;/gi,
    token => {
      const normalized = token.toLowerCase();
      if (normalized === "\\u002f" || normalized === "\\/") return "/";
      if (normalized === "\\u003a") return ":";
      if (normalized === "\\u0026" || normalized === "&amp;") return "&";
      if (normalized === "\\u003d") return "=";
      if (normalized === '\\"' || normalized === "&quot;" || normalized === "&#34;") return '"';
      return token;
    }
  );
}
function _slug(value) {
  return _text(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
function _directMedia(url) {
  return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/(?:hls|dash|stream)(?:\/|[?#]|$)/i.test(_text(url));
}
function _extractUrls(text, base) {
  const out = [];
  const normalized = _embeddedText(text);
  const patterns = [
    /(?:src|href|file|url|pathname|permalink|embedUrl|embed_url|contentUrl)\s*["']?\s*[:=]\s*["']([^"'<>\s]+)["']/gi,
    /["'](\/(?:api|watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|manifest|action)(?:[^"'<>\\\s]{0,500}))["']/gi,
    /https?:\\?\/\\?\/[^"'<>\s]+/gi
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(normalized))) {
      const raw = match[1] || match[0] || "";
      const absolute = _absolute(raw, base);
      if (absolute && /^https?:/i.test(absolute)) out.push(absolute);
      if (out.length >= 240) break;
    }
  }
  return _uniq(out);
}
function _mediaNamespace(mediaType) {
  try {
    const ctx = typeof globalThis !== "undefined" ? globalThis.__nuvioMediaContext : null;
    if (ctx && (ctx.tmdbNamespace === "movie" || ctx.tmdbNamespace === "tv")) return ctx.tmdbNamespace;
  } catch (_) {}
  return mediaType === "movie" ? "movie" : "tv";
}
function _playerLike(url) {
  try {
    const parsed = new URL(url);
    return /\/(?:watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy)(?:[/?#.-]|$)/i.test(parsed.pathname + parsed.search);
  } catch (_) {
    return false;
  }
}
async function _crawlDirectMedia(seedUrls, referer, maxDepth) {
  const queue = _uniq(seedUrls).filter(_playerLike).slice(0, 3).map(url => ({ url, depth: 0, referer }));
  const seen = new Set();
  const streams = [];
  let requests = 0;
  while (queue.length && requests < 4 && streams.length < 12) {
    const row = queue.shift();
    if (!row || seen.has(row.url)) continue;
    seen.add(row.url);
    requests += 1;
    try {
      const response = await _fetch(row.url, {
        headers: row.referer ? { Referer: row.referer } : {}
      });
      const responseUrl = response.url || row.url;
      const contentType = _text(response.headers.get("content-type")).toLowerCase();
      if (_directMedia(responseUrl) || /(?:mpegurl|dash\+xml|video\/)/i.test(contentType)) {
        streams.push(..._streams([responseUrl], row.referer || referer || ""));
        continue;
      }
      let urls = [];
      if (contentType.includes("json")) {
        urls = _jsonUrls(await response.json());
      } else {
        urls = _extractUrls(await response.text(), responseUrl);
      }
      const direct = urls.filter(_directMedia);
      if (direct.length) {
        streams.push(..._streams(direct, responseUrl));
        continue;
      }
      if (row.depth < Math.max(0, Number(maxDepth) || 0)) {
        for (const next of urls.filter(_playerLike).slice(0, 2)) {
          if (!seen.has(next)) queue.push({ url: next, depth: row.depth + 1, referer: responseUrl });
        }
      }
    } catch (_) {}
  }
  return streams.slice(0, 40);
}
function _candidateScore(url, meta) {
  let parsed;
  try { parsed = new URL(url); } catch (_) { return -1; }
  const path = decodeURIComponent(parsed.pathname || "").toLowerCase();
  if (!path || path === "/" || /\/(?:_next|static|assets?|images?|icons?|fonts?)(?:\/|$)/i.test(path)) return -1;
  const slug = _slug(meta && meta.title);
  const tokens = slug.split("-").filter(token => token.length >= 3);
  let score = 0;
  if (slug && path.includes(slug)) score += 120;
  for (const token of tokens) if (path.includes(token)) score += 18;
  if (meta && meta.year && path.includes(String(meta.year))) score += 20;
  if (meta && meta.tmdbId && path.includes(String(meta.tmdbId))) score += 45;
  if (/\/(?:movie|movies|film|films|series|tv|show|watch|title|media)\//i.test(path)) score += 12;
  return score;
}
function _expandLearnedRoute(pattern, meta, mediaType, season, episode) {
  let route = _text(pattern);
  if (!route || /^https?:\/\//i.test(route) && !/\{[^}]+\}/.test(route)) {
    return /^https?:\/\//i.test(route) ? [route] : [];
  }
  const id = _text(meta && meta.tmdbId);
  const title = _text(meta && meta.title);
  const slug = _slug(title);
  const transport = mediaType === "movie" ? "movie" : "tv";
  route = route
    .replace(/\{(?:tmdb_?id|id)\}/gi, encodeURIComponent(id))
    .replace(/\{slug\}/gi, encodeURIComponent(slug))
    .replace(/\{(?:title|query|q)\}/gi, encodeURIComponent(title))
    .replace(/\{(?:media|media_?type|type)\}/gi, encodeURIComponent(transport))
    .replace(/\{season\}/gi, encodeURIComponent(season == null ? "" : season))
    .replace(/\{episode\}/gi, encodeURIComponent(episode == null ? "" : episode));
  if (/\{[^}]+\}/.test(route)) return [];
  const out = [];
  for (const base of _runtimeBases()) {
    const absolute = _absolute(route, base);
    if (absolute) out.push(absolute);
  }
  return _uniq(out);
}
function _routeKind(route) {
  const value = _text(route).toLowerCase();
  if (!value || /\/(?:track|report|warm|dead|working|ad-link|fp)(?:[/?#]|$)/i.test(value)) return "ignore";
  if (/\/(?:api)(?:[/?#]|$)/i.test(value)) return "api";
  if (/\/(?:player|embed|play)(?:[/?#]|$)/i.test(value)) return "player";
  if (/\/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword)=/i.test(value)) return "search";
  if (/\{(?:tmdb_?id|id|slug|title)\}/i.test(value) || /\/(?:title|movie|film|series|tv|show|watch|media)(?:[/?#]|$)/i.test(value)) return "detail";
  return "ignore";
}
function _learnedUrls(kind, meta, mediaType, season, episode) {
  const out = [];
  for (const route of NIAKVIO_PROVIDER_MODEL.routes || []) {
    if (_routeKind(route) !== kind) continue;
    out.push(..._expandLearnedRoute(route, meta, mediaType, season, episode));
  }
  return _uniq(out);
}
async function _fetch(url, options) {
  const response = await fetch(url, {
    redirect: "follow",
    headers: Object.assign({
      "Accept": "application/json,text/html,application/xhtml+xml,text/plain,*/*",
      "User-Agent": "Mozilla/5.0 NiakVIO/2"
    }, (options && options.headers) || {})
  });
  if (!response.ok) throw new Error("provider_http_" + response.status);
  return response;
}
async function _tmdb(tmdbId, mediaType) {
  if (!tmdbId) return null;
  const type = _mediaNamespace(mediaType);
  const identity = type + ":" + String(tmdbId || "");
  try {
    const cache = typeof globalThis !== "undefined" ? globalThis.__nuvioTmdbMetadataCacheV1 : null;
    const cached = cache && cache[identity];
    if (cached && typeof cached.then !== "function") {
      return {
        title: cached.title || cached.name || cached.original_title || cached.original_name || "",
        year: String(cached.release_date || cached.first_air_date || "").slice(0, 4),
        tmdbId: String(tmdbId || "")
      };
    }
  } catch (_) {}
  const key = typeof globalThis !== "undefined" ? globalThis.TMDB_API_KEY : null;
  if (!key) return null;
  try {
    const response = await _fetch(
      "https://api.themoviedb.org/3/" + type + "/" + encodeURIComponent(tmdbId) +
      "?api_key=" + encodeURIComponent(key) + "&language=en-US"
    );
    const row = await response.json();
    return {
      title: row.title || row.name || row.original_title || row.original_name || "",
      year: String(row.release_date || row.first_air_date || "").slice(0, 4),
      tmdbId: String(tmdbId || "")
    };
  } catch (_) {
    return null;
  }
}
function _runtimeBases() {
  return _uniq([
    NIAKVIO_PROVIDER_MODEL.officialSite,
    NIAKVIO_PROVIDER_MODEL.knownSite,
    ...(NIAKVIO_PROVIDER_MODEL.origins || [])
  ]).filter(value => /^https?:/i.test(value));
}
function _searchBases() {
  return _runtimeBases();
}
function _searchUrls(meta, mediaType, season, episode) {
  return _learnedUrls("search", meta, mediaType, season, episode);
}
function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.fixedApi || NIAKVIO_PROVIDER_MODEL.officialApi) return true;
  if ((NIAKVIO_PROVIDER_MODEL.observedUrls || []).some(value => /api|stream|source|embed|player/i.test(_text(value)))) return true;
  return (NIAKVIO_PROVIDER_MODEL.routes || []).some(route => ["search","detail","player","api"].includes(_routeKind(route)));
}
function _apiUrls(tmdbId, mediaType, season, episode) {
  const bases = _uniq([
    NIAKVIO_PROVIDER_MODEL.fixedApi,
    NIAKVIO_PROVIDER_MODEL.officialApi,
    ...(NIAKVIO_PROVIDER_MODEL.observedUrls || []).filter(value => /api|stream|source|embed|player/i.test(value))
  ]);
  const out = [];
  for (const base of bases) {
    if (!/^https?:/i.test(base)) continue;
    let url = base
      .replace(/\{(?:tmdb_?id|id)\}/gi, encodeURIComponent(tmdbId || ""))
      .replace(/\{(?:media_?type|type)\}/gi, encodeURIComponent(mediaType || "movie"))
      .replace(/\{season\}/gi, encodeURIComponent(season == null ? "" : season))
      .replace(/\{episode\}/gi, encodeURIComponent(episode == null ? "" : episode));
    out.push(url);
    try {
      const parsed = new URL(url);
      if (!parsed.searchParams.size) {
        parsed.searchParams.set("tmdbId", tmdbId || "");
        parsed.searchParams.set("type", mediaType || "movie");
        if (season != null) parsed.searchParams.set("season", String(season));
        if (episode != null) parsed.searchParams.set("episode", String(episode));
        out.push(parsed.toString());
      }
    } catch (_) {}
  }
  return _uniq(out);
}
function _directPlayerUrls(tmdbId, mediaType) {
  if (!tmdbId) return [];
  const hasPlayerRoute = (NIAKVIO_PROVIDER_MODEL.routes || []).some(route =>
    /^\/player(?:[?#]|$)/i.test(_text(route))
  );
  if (!hasPlayerRoute) return [];
  const transportType = _mediaNamespace(mediaType);
  const out = [];
  for (const base of _searchBases()) {
    try {
      const url = new URL("/player", base);
      url.searchParams.set("m", transportType);
      url.searchParams.set("id", _text(tmdbId));
      out.push(url.toString());
    } catch (_) {}
  }
  return _uniq(out);
}
function _runtimeApiUrls(playerUrl, mediaType, tmdbId, season, episode) {
  let player;
  try { player = new URL(playerUrl); } catch (_) { return []; }
  const out = [];
  // Transport-level player media values are commonly movie/tv even when
  // Nuvio's semantic type is anime. Preserve anime as a Nuvio type, but route
  // episodic/anime players through the site's TV transport convention.
  const desiredMedia = _mediaNamespace(mediaType);
  const observedMedia = _text(player.searchParams.get("m") || player.searchParams.get("media") || player.searchParams.get("type")).toLowerCase();
  for (const pattern of NIAKVIO_PROVIDER_MODEL.routes || []) {
    if (!/^\/api\/(?:streams?(?:\/|$)|source|sources|resolve|proxy)/i.test(_text(pattern))) continue;
    if (/\/(?:working|dead|warm)(?:[?#]|$)/i.test(_text(pattern))) continue;
    const parts = _text(pattern).split("?", 2);
    let path = parts[0].replace(/\{media\}/gi, encodeURIComponent(desiredMedia));
    if (observedMedia && /\/(?:movie|tv|anime)$/i.test(path)) {
      path = path.replace(/\/(?:movie|tv|anime)$/i, "/" + encodeURIComponent(desiredMedia));
    }
    const keys = (parts[1] || "").split("&").map(part => part.split("=", 1)[0]).filter(Boolean);
    if (!keys.length) continue;
    let target;
    try { target = new URL(path, player.origin); } catch (_) { continue; }
    let missing = false;
    for (const key of keys) {
      const lower = key.toLowerCase();
      let value = player.searchParams.get(key);
      if (value == null && lower === "id") value = _text(tmdbId);
      if (value == null && /^(?:m|media|type)$/.test(lower)) value = desiredMedia;
      if (value == null && /^(?:season|s)$/.test(lower) && season != null) value = _text(season);
      if (value == null && /^(?:episode|e)$/.test(lower) && episode != null) value = _text(episode);
      if (value == null || value === "") { missing = true; break; }
      target.searchParams.set(key, value);
    }
    if (!missing) out.push({ url: target.toString(), referer: player.toString() });
  }
  const seen = new Set();
  return out.filter(row => row.url && !seen.has(row.url) && seen.add(row.url));
}
function _jsonUrls(value, out) {
  out = out || [];
  if (typeof value === "string") {
    if (/^https?:/i.test(value)) out.push(value);
    return out;
  }
  if (Array.isArray(value)) {
    for (const child of value) _jsonUrls(child, out);
    return out;
  }
  if (value && typeof value === "object") {
    for (const child of Object.values(value)) _jsonUrls(child, out);
  }
  return out;
}
function _sourceUrls(value, base, out) {
  out = out || [];
  if (Array.isArray(value)) {
    for (const child of value) _sourceUrls(child, base, out);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  for (const [key, child] of Object.entries(value)) {
    if (typeof child === "string" && /^(?:src|url|file|stream|source)$/i.test(key)) {
      const absolute = _absolute(child, base);
      if (absolute && /^https?:/i.test(absolute) &&
          !/\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) {
        out.push(absolute);
      }
    }
    if (child && typeof child === "object") _sourceUrls(child, base, out);
  }
  return out;
}
function _streams(urls, referer) {
  return _uniq(urls).slice(0, 40).map((url, index) => ({
    name: NIAKVIO_PROVIDER_MODEL.displayName,
    title: NIAKVIO_PROVIDER_MODEL.displayName + (index ? " #" + (index + 1) : ""),
    url,
    headers: referer ? { Referer: referer } : undefined
  }));
}
async function _resolveApi(tmdbId, mediaType, season, episode) {
  const streams = [];
  for (const url of _apiUrls(tmdbId, mediaType, season, episode).slice(0, 4)) {
    try {
      const response = await _fetch(url);
      const type = _text(response.headers.get("content-type")).toLowerCase();
      if (type.includes("json")) {
        const value = await response.json();
        streams.push(..._jsonUrls(value).filter(_directMedia));
      } else {
        const text = await response.text();
        streams.push(..._extractUrls(text, response.url || url).filter(_directMedia));
      }
    } catch (_) {}
    if (streams.length) break;
  }
  return _streams(streams, _searchBases()[0] || "");
}
async function _resolveRuntimeApi(playerUrls, mediaType, tmdbId, season, episode) {
  const streams = [];
  for (const playerUrl of _uniq(playerUrls).slice(0, 3)) {
    for (const row of _runtimeApiUrls(playerUrl, mediaType, tmdbId, season, episode).slice(0, 4)) {
      try {
        const response = await _fetch(row.url, {
          headers: row.referer ? { Referer: row.referer } : {}
        });
        const type = _text(response.headers.get("content-type")).toLowerCase();
        if (type.includes("json")) {
          const value = await response.json();
          const sources = _sourceUrls(value, response.url || row.url);
          if (sources.length) streams.push(..._streams(sources, row.referer));
        } else {
          const text = await response.text();
          const urls = _extractUrls(text, response.url || row.url);
          const direct = urls.filter(_directMedia);
          if (direct.length) streams.push(..._streams(direct, row.referer));
        }
      } catch (_) {}
      if (streams.length) break;
    }
    if (streams.length) break;
  }
  return streams.slice(0, 40);
}
async function _resolveKnownPlayer(tmdbId, mediaType, season, episode) {
  const known = _directPlayerUrls(tmdbId, mediaType).slice(0, 2);
  for (const playerUrl of known) {
    try {
      const response = await _fetch(playerUrl);
      const responseUrl = response.url || playerUrl;
      let text = "";
      try { text = await response.text(); } catch (_) {}
      const candidates = _uniq([
        responseUrl,
        ..._extractUrls(text, responseUrl).filter(_playerLike)
      ]).slice(0, 3);
      const runtime = await _resolveRuntimeApi(candidates, mediaType, tmdbId, season, episode);
      if (runtime.length) return runtime;
      const direct = _extractUrls(text, responseUrl).filter(_directMedia);
      if (direct.length) return _streams(direct, responseUrl).slice(0, 12);
    } catch (_) {}
  }
  return [];
}
async function _resolveHtml(meta, mediaType, season, episode) {
  if (!meta || (!meta.title && !meta.tmdbId)) return [];
  const candidates = [];
  if (meta.title) {
    for (const searchUrl of _searchUrls(meta, mediaType, season, episode).slice(0, 2)) {
      try {
        const response = await _fetch(searchUrl);
        const html = await response.text();
        const urls = _extractUrls(html, response.url || searchUrl)
          .filter(value => {
            const host = _origin(value);
            return host && _searchBases().some(base => _origin(base) === host);
          })
          .map(value => ({ url: value, score: _candidateScore(value, meta) }))
          .filter(row => row.score >= 18)
          .sort((a, b) => b.score - a.score)
          .map(row => row.url);
        candidates.push(...urls);
      } catch (_) {}
      if (candidates.length) break;
    }
  }
  candidates.push(..._learnedUrls("detail", meta, mediaType, season, episode));
  const streams = [];
  for (const detailUrl of _uniq(candidates).slice(0, 6)) {
    try {
      const response = await _fetch(detailUrl);
      const html = await response.text();
      let urls = _extractUrls(html, response.url || detailUrl);
      if (mediaType !== "movie" && season != null && episode != null) {
        const token = new RegExp("(?:s(?:eason)?\\s*0*" + Number(season) + "[^\\n]{0,80}e(?:pisode)?\\s*0*" + Number(episode) + "|0*" + Number(season) + "x0*" + Number(episode) + ")", "i");
        const episodeLinks = urls.filter(value => token.test(value));
        if (episodeLinks.length) {
          for (const episodeUrl of episodeLinks.slice(0, 2)) {
            try {
              const episodeResponse = await _fetch(episodeUrl);
              const episodeHtml = await episodeResponse.text();
              urls = urls.concat(_extractUrls(episodeHtml, episodeResponse.url || episodeUrl));
            } catch (_) {}
          }
        }
      }
      const direct = urls.filter(_directMedia);
      if (direct.length) streams.push(..._streams(direct, response.url || detailUrl));
      if (!direct.length && /iframe|mixed_embed|html_scraper/i.test(NIAKVIO_PROVIDER_MODEL.strategy)) {
        const discoveredNested = _uniq(urls.filter(_playerLike));
        if (discoveredNested.length) {
          const runtimeCandidates = _uniq([
            ...discoveredNested,
            ..._directPlayerUrls(meta.tmdbId, mediaType)
          ]);
          // A signed player URL can carry short-lived keys required by a
          // learned runtime API. Consume that exact route before recursively
          // crawling third-party embeds, otherwise an unrelated player-like
          // URL can steal the bounded crawl budget and the signed key is lost.
          const runtime = await _resolveRuntimeApi(
            runtimeCandidates,
            mediaType,
            meta.tmdbId,
            season,
            episode
          );
          if (runtime.length) {
            streams.push(...runtime);
          } else {
            // Runtime-route enrichment remains fail-open: providers without a
            // usable learned API continue through the generic player crawl.
            const crawled = await _crawlDirectMedia(
              discoveredNested,
              response.url || detailUrl,
              1
            );
            if (crawled.length) streams.push(...crawled);
          }
        } else {
          const runtimeCandidates = _directPlayerUrls(meta.tmdbId, mediaType);
          if (runtimeCandidates.length) {
            const runtime = await _resolveRuntimeApi(
              runtimeCandidates,
              mediaType,
              meta.tmdbId,
              season,
              episode
            );
            if (runtime.length) streams.push(...runtime);
          }
        }
      }
    } catch (_) {}
    if (streams.length >= 12) break;
  }
  return streams.slice(0, 40);
}
async function getStreams(tmdbId, mediaType, season, episode) {
  const type = String(mediaType || "movie").toLowerCase();
  if (NIAKVIO_PROVIDER_MODEL.supportedTypes.length &&
      !NIAKVIO_PROVIDER_MODEL.supportedTypes.includes(type) &&
      !(type === "tv" && NIAKVIO_PROVIDER_MODEL.supportedTypes.includes("anime")) &&
      !(type === "movie" && NIAKVIO_PROVIDER_MODEL.supportedTypes.includes("anime"))) {
    return [];
  }
  if (!_runtimePlanAvailable()) return [];
  const strategy = NIAKVIO_PROVIDER_MODEL.strategy;

  // Reader fast path: consume already learned ID/API/player routes before any
  // title metadata lookup. Runtime executes a plan; it does not discover one.
  if (/api_stream_resolver|direct_media/i.test(strategy)) {
    const api = await _resolveApi(tmdbId, type, season, episode);
    if (api.length) return api;
  }
  const player = await _resolveKnownPlayer(tmdbId, type, season, episode);
  if (player.length) return player;

  const needsMetadata = (NIAKVIO_PROVIDER_MODEL.routes || []).some(route =>
    ["search","detail"].includes(_routeKind(route))
  );
  if (!needsMetadata) {
    if (!/api_stream_resolver|direct_media/i.test(strategy)) {
      return _resolveApi(tmdbId, type, season, episode);
    }
    return [];
  }

  const meta = await _tmdb(tmdbId, type) || {
    title: "",
    year: "",
    tmdbId: String(tmdbId || "")
  };
  const html = await _resolveHtml(meta, type, season, episode);
  if (html.length) return html;
  if (!/api_stream_resolver|direct_media/i.test(strategy)) {
    return _resolveApi(tmdbId, type, season, episode);
  }
  return [];
}
module.exports = { getStreams, __niakvioProviderBase: NIAKVIO_PROVIDER_MODEL };