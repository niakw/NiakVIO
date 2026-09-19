"use strict";

/* NIAKVIO_PROVIDER_BASE_OWNED_V2 */
const NIAKVIO_PROVIDER_MODEL = Object.freeze({"authoring":"niakvio-owned-v2","displayName":"StreamZo","fixedApi":null,"knownSite":"https://streamzo.fr","observedUrls":["https://video/","https://${/","https://vidmoly.to/","https://${_}/","https://my.mail.ru/+/video/meta/${i}","https://my.mail.ru/","https://${a}${n}/","https://${a}/","https://${n}/","https://f/","https://vidzy.live/","https://${i}/pa","https://${i}/","https://www.myvi.ru/","https://www.myvi.ru/api/video/${a[1]}","https://younetu.org/","https://vidoza.net/","https://lecteurvideo.com/","https://wookafr.center/","https://up4fun.top/","https://kit/","https://npm/","https://loda/","https://openj/","http://under/"],"officialApi":null,"officialHub":null,"officialSite":"https://streamzo.fr","origins":["https://video.sibnet.ru","https://vidmoly.me","https://fsvid.lol","https://vidzy.live","https://streamtape.com","https://sendvid.com","https://www.myvi.ru","https://younetu.org","https://vidoza.net","https://lecteurvideo.com","https://up4fun.top","https://streamzo.fr","https://kitsu.io","https://npms.io","https://lodash.com","https://openjsf.org","http://underscorejs.org","https://old.invalid","https://www.themoviedb.org","https://video","https://${","https://vidmoly.to","https://${_}","https://my.mail.ru"],"providerId":"streamzo","reconstructionState":"learning-clean-seed","routePlanVersion":1,"routes":["/","/+/video/meta/${i}","/pa","/api/video/${a[1]}"],"runtimeDiscovery":false,"runtimeRole":"reader","strategy":"mixed_embed_resolver","supportedTypes":["movie","tv"],"upstreamCodeEmbedded":false,"upstreamCodeExecuted":false});

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
  return _text(value).split("\\/").join("/").replace(
    /\\u002[fF]|\\u003[aA]|\\u0026|\\u003[dD]|\\"|&quot;|&#34;|&amp;/gi,
    token => {
      const normalized = token.toLowerCase();
      if (normalized === "\\u002f") return "/";
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
    /https?:\/\/[^"'<>\s]+/gi
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

/* NUVIO_STREAMZO_PUBLIC_CATALOGUE_V3:df2630345897 */
;(function(g,c){"use strict";
var TMDB_KEY=(g&&g.TMDB_API_KEY)||"";
function s(v){return String(v==null?"":v).replace(/&amp;/gi,"&").split("\\/").join("/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return ""}}
function host(v){try{return new URL(v).hostname.toLowerCase()}catch(_){return ""}}
var SOCIAL=/(?:^|\.)(?:youtube\.com|youtu\.be|twitter\.com|x\.com|facebook\.com|instagram\.com)$/i;
function mediaCandidate(v,base,page){var u=abs(v,base),h=host(u);if(!u||!h||SOCIAL.test(h)||u===page)return "";return /(?:embed|player|watch|stream|video|\.m3u8|\.mpd|\.mp4|\.mkv|\.webm|\/e\/|\/v\/)/i.test(u)?u:""}
function unique(values){var out=[],seen={};(values||[]).forEach(function(v){v=s(v);var k=norm(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}});return out}
function args(a){var q=a[0]&&typeof a[0]==="object"?Object.assign({},a[0]):{tmdbId:a[0],mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};q.tmdbId=s(q.tmdbId||q.id);q.mediaType=s(q.mediaType||q.type||"movie").toLowerCase();return q}
async function request(url,kind,referer,extra){var headers=Object.assign({Accept:kind==="json"?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,application/json,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.5"},extra||{});if(referer){headers.Referer=referer;try{headers.Origin=new URL(referer).origin}catch(_){}}try{var r=await g.fetch(url,{headers:headers,redirect:"follow"});if(!r||!r.ok)return null;return {url:s(r.url||url),body:kind==="json"?await r.json():await r.text(),type:r.headers&&r.headers.get?r.headers.get("content-type"):""}}catch(_){return null}}
async function meta(q){var requested=s(q.title||q.name||q.label).replace(/\s*\(\d{4}\)\s*$/,"");var titles=unique([requested]),year=Number(q.year)||0;if(q.tmdbId&&TMDB_KEY){var type=q.mediaType==="tv"||q.mediaType==="anime"?"tv":"movie",r=await request("https://api.themoviedb.org/3/"+type+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR","json");if(r&&r.body){var d=r.body;titles=unique(titles.concat([d.title,d.name,d.original_title,d.original_name]));year=year||Number(s(d.release_date||d.first_air_date).slice(0,4))||0}}
return {title:titles[0]||"",titles:titles.slice(0,c.maxAliases),year:year}}
function scoreOne(text,title){var n=norm(text),t=norm(title),score=0;if(t&&n.indexOf(t)>=0)score+=100;t.split(" ").filter(function(x){return x.length>2}).forEach(function(x){if(n.indexOf(x)>=0)score+=8});return score}
function scoreText(text,m){var best=0;(m.titles||[m.title]).forEach(function(t){best=Math.max(best,scoreOne(text,t))});var n=norm(text);if(m.year&&n.indexOf(String(m.year))>=0)best+=20;return best}
function detailLinks(html,base,m){var rows=[],re=/<a\b([^>]*)href=["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,x;while((x=re.exec(s(html)))!==null){var attrs=s(x[1])+" "+s(x[3]),inner=s(x[4]).replace(/<[^>]+>/g," "),label=attrs+" "+inner,u=abs(x[2],base),score=scoreText(label,m);if(u&&score>20)rows.push({url:u,score:score})}return rows.sort(function(a,b){return b.score-a.score}).map(function(x){return x.url})}
function pageData(html,base){var text=s(html),id="",embed="",m;m=/\bdata-film-id=["'](\d+)["']/i.exec(text)||/["']film(?:_|-)?id["']\s*:\s*["']?(\d+)/i.exec(text)||/\/api\/mirrors\/film\/(\d+)/i.exec(text);if(m)id=m[1];m=/\bdata-embed=["']([^"']+)["']/i.exec(text);if(m)embed=mediaCandidate(m[1],base,base);var urls=[],seen={};function add(v){var u=mediaCandidate(v,base,base);if(!u||seen[u])return;seen[u]=1;urls.push(u)}if(embed)add(embed);var re=/(?:data-embed|data-src|data-url|src|href)=["']([^"']+)["']/gi;while((m=re.exec(text))!==null)add(m[1]);return {id:id,urls:urls}}
function mirrorUrls(value,base,out){out=out||[];if(value==null)return out;if(typeof value==="string"){var u=mediaCandidate(value,base,"");if(u)out.push(u);return out}if(Array.isArray(value)){value.forEach(function(v){mirrorUrls(v,base,out)});return out}if(typeof value==="object"){Object.keys(value).forEach(function(k){mirrorUrls(value[k],base,out)})}return out}
function uniqueUrls(values){var out=[],seen={};values.forEach(function(v){v=s(v);if(v&&!seen[v]){seen[v]=1;out.push(v)}});return out}
async function recover(q){if(["movie","tv","anime"].indexOf(q.mediaType)<0)return [];if((q.mediaType==="tv"||q.mediaType==="anime")&&Number(q.season)>0&&Number(q.episode)>0)return [];var m=await meta(q);if(!m.title)return [];var aliases=(m.titles||[m.title]).slice(0,c.maxAliases),candidates=[],searches=[];aliases.forEach(function(t){candidates.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t))});for(var i=0;i<searches.length;i++){var sr=await request(searches[i],"text",c.baseUrl+"/");if(sr)candidates=candidates.concat(detailLinks(sr.body,sr.url,m).slice(0,5))}candidates=uniqueUrls(candidates);var streams=[];for(var j=0;j<candidates.length&&streams.length<12;j++){var page=await request(candidates[j],"text",c.baseUrl+"/");if(!page)continue;var data=pageData(page.body,page.url);if(scoreText(page.body,m)<20&&!data.id&&!data.urls.length)continue;var urls=data.urls.slice();if(data.id){var mirrors=await request(c.baseUrl+"/api/mirrors/film/"+encodeURIComponent(data.id),"json",page.url);if(mirrors)urls=urls.concat(mirrorUrls(mirrors.body,c.baseUrl+"/",[]))}urls=uniqueUrls(urls);for(var k=0;k<urls.length;k++){var u=urls[k];streams.push({name:c.providerName+(streams.length?" #"+(streams.length+1):""),title:c.providerName+" - "+m.title,url:u,quality:"HD",language:"fr",isDirect:/\.(?:m3u8|mp4|mpd)(?:[?#]|$)/i.test(u),headers:{Referer:page.url,Origin:c.baseUrl}})}if(streams.length)break}return streams}
function direct(row){var u=s(row&&row.url),t=s(row&&(row.type||row.format)).toLowerCase();return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/hls2?\//i.test(u)||/(?:hls|mpegurl|dash|mp4|matroska|webm|video\/)/i.test(t)}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__streamzoPublicV3)return false;var old=o[k];var wrap=async function(){var native=[];try{native=await old.apply(this,arguments)}catch(_){}if(Array.isArray(native)&&native.some(direct))return native;var recovered=await recover(args(arguments));return recovered.length?recovered:(Array.isArray(native)?native:[])};wrap.__streamzoPublicV3=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://streamzo.fr","providerName":"StreamZo","maxAliases":4});
/* NUVIO_TV_TARGET_MEDIA_V3:1e7a3754eaa1 */
;(function(g,c){"use strict";
var ASSET=/\.(?:woff2?|ttf|otf|eot|css|js|mjs|map|png|jpe?g|gif|svg|ico|webmanifest|json|xml|vtt|srt)(?:[?#]|$)/i;
var SOCIAL=/(?:^|\.)(?:youtube\.com|youtu\.be|twitter\.com|x\.com|twimg\.com|facebook\.com|instagram\.com|google\.com|googleusercontent\.com|t\.me|telegram\.me|whatsapp\.com)$/i;
var DEMO=/(?:big[_-]?buck[_-]?bunny|sample[-_]?videos|test-videos|chrome\/static\/videos|sticky\/videos|static\/money|grok-|radar_promo)/i;
function s(v){return String(v==null?"":v).replace(/[\u200B-\u200D\uFEFF]/g,"").trim()}
function clean(v){return s(v).replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").split("\\/").join("/").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/").replace(/&amp;|&#038;/gi,"&").replace(/\\u0026/gi,"&")}
function abs(v,b){try{var raw=clean(v);if(/^\/\//.test(raw)){var scheme=/^https:/i.test(String(b||""))?"https:":"http:";return scheme+raw}return new URL(raw,b).toString()}catch(_){return ""}}
function hostname(u){try{return new URL(u).hostname.toLowerCase()}catch(_){return ""}}
function origin(u){try{return new URL(u).origin}catch(_){return ""}}
function rejected(u){var h=hostname(u);if(!h||ASSET.test(u)||SOCIAL.test(h)||DEMO.test(u)||/\/troll\/master\.m3u8(?:[?#]|$)/i.test(u)||/\/(?:static\/hero(?:[-_][^/?#]*)?\.(?:mp4|webm|avif)|cdn-cgi\/challenge-platform)(?:[?#]|$)/i.test(u)||/%7b|%7d|decodedlink|\$\{|encodeURIComponent\(|credentials:/i.test(u))return true;var blocked=["analytics.google.com","api.themoviedb.org","arm.haglund.dev","cloudflare.com","cloudflareinsights.com","connect.facebook.net","doubleclick.net","fstream.top","google-analytics.com","googlesyndication.com","googletagmanager.com","graphql.anilist.co","pagead2.googlesyndication.com","static.cloudflareinsights.com","v3-cinemeta.strem.io"];for(var bi=0;bi<blocked.length;bi++){var rule=blocked[bi];if(h===rule||h.endsWith('.'+rule))return true}return false}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
var NUVIO_PLAYBACK_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
function headerKey(obj,name){var keys=Object.keys(obj||{}),want=String(name||"").toLowerCase();for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===want)return keys[i];return""}
function setHeader(obj,name,value){if(!value)return;var old=headerKey(obj,name);if(old&&old!==name)delete obj[old];obj[name]=String(value)}
function defaultCookiePath(url){try{var p=new URL(url).pathname||"/",i=p.lastIndexOf("/");return i<=0?"/":p.slice(0,i+1)}catch(_){return"/"}}
function splitSetCookie(value){var raw=s(value);if(!raw)return[];return raw.split(/,(?=\s*[^;,=\s]+\s*=)/g).map(function(v){return v.trim()}).filter(Boolean)}
function rememberCookie(jar,setCookie,url){if(!jar||!setCookie)return;var u;try{u=new URL(url)}catch(_){return}splitSetCookie(setCookie).forEach(function(line){var parts=line.split(";"),first=s(parts.shift()),eq=first.indexOf("=");if(eq<=0)return;var item={name:s(first.slice(0,eq)),value:s(first.slice(eq+1)),domain:u.hostname.toLowerCase(),hostOnly:true,path:defaultCookiePath(url),secure:false,expired:false};if(!item.name)return;parts.forEach(function(part){var x=s(part),i=x.indexOf("="),k=(i>=0?x.slice(0,i):x).trim().toLowerCase(),v=i>=0?s(x.slice(i+1)):"";if(k==="domain"&&v){item.domain=v.replace(/^\./,"").toLowerCase();item.hostOnly=false}else if(k==="path"&&v.charAt(0)==="/")item.path=v;else if(k==="secure")item.secure=true;else if(k==="max-age"&&Number(v)<=0)item.expired=true;else if(k==="expires"){var ts=Date.parse(v);if(Number.isFinite(ts)&&ts<=Date.now())item.expired=true}});var id=item.name.toLowerCase()+"|"+item.domain+"|"+item.path;for(var j=jar.length-1;j>=0;j--){var old=jar[j],oldId=old.name.toLowerCase()+"|"+old.domain+"|"+old.path;if(oldId===id)jar.splice(j,1)}if(!item.expired&&item.value)jar.push(item)})}
function seedCookieHeader(jar,headers,url){if(!jar||!headers||typeof headers!=="object")return;var k=headerKey(headers,"cookie"),raw=k?s(headers[k]):"";if(!raw)return;var h=hostname(url);if(!h)return;raw.split(";").forEach(function(part){var x=s(part),i=x.indexOf("=");if(i<=0)return;jar.push({name:s(x.slice(0,i)),value:s(x.slice(i+1)),domain:h,hostOnly:true,path:"/",secure:false,expired:false})})}
function captureCookies(jar,response,url){try{if(!response||!response.headers||typeof response.headers.get!=="function")return;var v=response.headers.get("set-cookie")||response.headers.get("Set-Cookie");if(v)rememberCookie(jar,v,url)}catch(_){}}
function cookieHeader(jar,target){var u;try{u=new URL(target)}catch(_){return""}var h=u.hostname.toLowerCase(),p=u.pathname||"/",secure=u.protocol==="https:",out=[];(jar||[]).forEach(function(x){var domainOk=x.hostOnly?h===x.domain:(h===x.domain||h.endsWith("."+x.domain));if(!domainOk||x.secure&&!secure||p.indexOf(x.path)!==0)return;out.push(x.name+"="+x.value)});return out.join("; ")}
function outputHeaders(base,ref,target,jar){var out={};if(base&&typeof base==="object")Object.keys(base).forEach(function(k){var lower=String(k).toLowerCase();if(lower!=="range"&&lower!=="referer"&&lower!=="origin"&&lower!=="cookie")out[k]=s(base[k])});if(ref){setHeader(out,"Referer",ref);var o=origin(ref);if(o)setHeader(out,"Origin",o)}else{var bk=headerKey(base||{},"referer");if(bk)setHeader(out,"Referer",base[bk]);var bo=headerKey(base||{},"origin");if(bo)setHeader(out,"Origin",base[bo])}if(!headerKey(out,"user-agent"))setHeader(out,"User-Agent",NUVIO_PLAYBACK_UA);var cookie=cookieHeader(jar,target);if(cookie)setHeader(out,"Cookie",cookie);if(!headerKey(out,"accept"))out.Accept="*/*";return out}
function probeHeaders(base,ref,target,jar){var out=outputHeaders(base,ref,target,jar);if(!/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(target)&&!out.Range&&!out.range)out.Range="bytes=0-262143";return out}
function startsHls(text){return clean(text).trimStart().startsWith("#EXTM3U")}
function startsDash(text){return /<MPD[\s>]/i.test(clean(text).slice(0,4096))}
function bytesKind(bytes){if(!bytes||!bytes.length)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes.length>=4&&bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes.length>=188&&bytes[0]===71&&(bytes.length<376||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var out="";for(var i=0;i<Math.min(bytes.length,262144);i++)out+=String.fromCharCode(bytes[i]);return out}}
async function resource(u,base,ref,jar){try{var h=probeHeaders(base,ref,u,jar),r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var finalUrl=s(r.url||u);captureCookies(jar,r,finalUrl);var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",bytes=null,text="";if(typeof r.arrayBuffer==="function"){var buffer=await r.arrayBuffer();bytes=new Uint8Array(buffer);text=decode(bytes.slice(0,300000))}else if(typeof r.text==="function"){text=String(await r.text()||"").slice(0,300000)}return{ok:!!r.ok,status:r.status,url:finalUrl,type:type,bytes:bytes,text:text,headers:outputHeaders(base,ref,finalUrl,jar)}}catch(_){return null}}
function normalizedHlsProofText(text){return String(text==null?"":text).replace(/^(?:\uFEFF|ï»¿)/,"").trimStart()}
function hlsStructure(text){var value=normalizedHlsProofText(text);if(/^#EXTM3U(?:\s|$)/i.test(value))return true;return /(?:^|\n)#EXT-(?:X-[A-Z0-9-]+|INF)\s*:/i.test(value)}
function proof(r){if(!r)return null;if(hlsStructure(r.text))return"hls";if(startsDash(r.text)||/application\/dash\+xml/i.test(r.type))return"dash";var binary=bytesKind(r.bytes);if(binary)return binary;if(/^video\//i.test(r.type)&&r.bytes&&r.bytes.length>12)return"video";return null}
function unpackPackers(){return[]}
function decodeVidzy(text,base){var out=[];if(!/charCodeAt[\s\S]{0,420}(?:0x3d|61)[\s\S]{0,240}\*\s*89/i.test(text))return out;var host=hostname(base),H=0;for(var j=0;j<host.length;j++)H=(H+host.charCodeAt(j))&255;var hostKeyed=/\+\s*H\s*\)\s*&\s*255|\+\s*H\s*&\s*255/i.test(text),re=/["']([A-Za-z0-9+/=]{24,})["']/g,m;while((m=re.exec(text))!==null){try{var raw=typeof g.atob==="function"?g.atob(m[1]):"",rev=raw.split("").reverse().join(""),keys=hostKeyed?[H]:[0],value="";for(var k=0;k<keys.length;k++){value="";for(var i=0;i<rev.length;i++)value+=String.fromCharCode(rev.charCodeAt(i)^((0x3d+i*89+keys[k])&255));if(/^https?:\/\//i.test(value)&&!rejected(value)&&out.indexOf(value)<0){out.push(value);break}}}catch(_){}}return out}function decodeLecteurVideo(text,base){var out=[],seen={},re=/\bshowVideo\s*\(\s*["']([A-Za-z0-9+/=]{16,})["']/gi,m;while((m=re.exec(String(text||"")))!==null){try{var raw=typeof g.atob==="function"?g.atob(m[1]):"",u=abs(raw,base);if(u&&!rejected(u)&&!seen[u]){seen[u]=1;out.push(u)}}catch(_){}}return out}function genericUrls(text,base){var out=[],seen={};var PLAYER_HOST=/(?:^|\.)(?:vidzy\.(?:org|live|cc)|fsvid\.lol|uqload\.(?:is|co|cx)|lecteurvideo\.com|xtremestream\.xyz|megaup\.net|veev\.to|veevcdn\.co|waaw\.to|lulustream\.com|luluvdo\.com|vidmoly\.(?:me|biz)|emmmmbed\.com|ironwallnet\.net)$/i;var DIRECT=/(?:\.m3u8|\.mpd)(?:[?#]|$)|\/hls2?\//i;var MEDIA_FILE=/\.(?:mp4|mkv|webm)(?:[?#]|$)/i;var PLAYER_PATH=/(?:\/embed(?:[-./?]|$)|\/player(?:[-./?]|$)|\/e\/|\/f\/|\/video\.php(?:[?#]|$)|download\.megaup)/i;var MEDIAISH_HOST=/(?:^|\.)(?:cdn|media|video|stream|vod|edge|storage|files?|cloud)[-.]/i;function allowed(u){if(!u||rejected(u))return false;var h=hostname(u);if(DIRECT.test(u))return true;if(PLAYER_HOST.test(h))return true;if(PLAYER_PATH.test(u))return true;if(MEDIA_FILE.test(u)&&MEDIAISH_HOST.test(h))return true;return false}function add(v,front){var u=abs(v,base);if(!allowed(u)||seen[u])return;seen[u]=1;if(front)out.unshift(u);else out.push(u)}var normalized=clean(text),packed=unpackPackers(normalized);packed.forEach(function(body){decodeVidzy(body,base).forEach(function(u){add(u,true)});decodeLecteurVideo(body,base).forEach(function(u){add(u,true)});scan(body)});decodeVidzy(normalized,base).forEach(function(u){add(u,true)});decodeLecteurVideo(normalized,base).forEach(function(u){add(u,true)});scan(normalized);function scan(body){var patterns=[/(?:src|data-src|data-url|data-embed|data-player|data-link|data-file|href)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl|_fsvHls)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+)/gi],m;for(var i=0;i<patterns.length;i++){patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null)add(m[1])}}return out.slice(0,c.maxCandidates)}function normalizeRows(value){if(Array.isArray(value))return value;if(value&&typeof value==="object"){var keys=["streams","results","data"];for(var i=0;i<keys.length;i++)if(Array.isArray(value[keys[i]]))return value[keys[i]]}return[]}
function normalizeRow(row){if(!row||typeof row!=="object")return null;var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u))return null;return Object.assign({},row,{url:u,headers:row.headers&&typeof row.headers==="object"?row.headers:{}})}
function unique(rows){var out=[],seen={};rows.forEach(function(row){if(!row||!row.url||seen[row.url])return;seen[row.url]=1;out.push(row)});return out}
function compactRow(row,media){var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,260),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);var size=s(row.size||"");if(!size){var desc=s(row.description||""),lang=s(row.language||""),parts=[];if(desc&&!/^(?:unknown|inconnue?|n\/?a)$/i.test(desc))size=desc;else{if(lang)parts.push(lang);if(media.kind==="hls")parts.push("HLS");else if(media.kind)parts.push(media.kind.toUpperCase());size=parts.join(" • ")}}if(size)out.size=size;if(Array.isArray(row.subtitles)&&row.subtitles.length)out.subtitles=row.subtitles.slice(0,20);return out}
function serialNativeTargetRuntime(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");if(/NuvioTV|Android TV/i.test(ua))return true;if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}if(/followRedirects/.test(src))return false;var signalAware=/options\.signal|var\s+signal\s*=/.test(src);var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);return signalAware&&fourArgNative}catch(_e){return false}}
function targetRank(u,ref){u=s(u);if(/(?:\.m3u8|\.mpd)(?:[?#]|$)|\/hls2?\//i.test(u))return 0;var h=hostname(u),rh=hostname(ref);if(h&&rh&&h===rh)return 1;if(/(?:^|\.)(?:vidzy\.(?:org|live|cc)|fsvid\.lol|uqload\.(?:is|co|cx)|lecteurvideo\.com|xtremestream\.xyz|megaup\.net|veev\.to|veevcdn\.co|waaw\.to|lulustream\.com|luluvdo\.com|vidmoly\.(?:me|biz)|emmmmbed\.com|ironwallnet\.net)$/i.test(h))return 2;if(/(?:\/embed(?:[-./?]|$)|\/player(?:[-./?]|$)|\/e\/|\/f\/|\/video\.php(?:[?#]|$)|download\.megaup)/i.test(u))return 3;return 4}
function orderedTargets(values,ref){return (values||[]).map(function(v,i){return{v:v,i:i,r:targetRank(v,ref)}}).sort(function(a,b){return(a.r-b.r)||(a.i-b.i)}).map(function(x){return x.v})}
function orderedNativeRows(values){var out=[];(values||[]).slice(0,c.maxCandidates).forEach(function(raw,i){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);out.push({row:row,ref:ref,i:i,r:targetRank(row.url,ref)})});out.sort(function(a,b){return(a.r-b.r)||(a.i-b.i)});return out}
async function resolve(u,baseHeaders,referer,depth,seen,jar){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};jar=jar||[];if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer,jar);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||(!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body)))return[];var ref=r.url||u,next=orderedTargets(genericUrls(body,ref),ref),out=[];if(serialNativeTargetRuntime()){for(var i=0;i<next.length;i++){var found=await resolve(next[i],r.headers,ref,depth+1,seen,jar);if(found.length)return unique(found)}return[]}var groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,ref,depth+1,seen,jar)}));groups.forEach(function(group){out=out.concat(group)});return unique(out)}
async function invoke(old,self,args){var settings=g.SCRAPER_SETTINGS&&typeof g.SCRAPER_SETTINGS==="object"?g.SCRAPER_SETTINGS:{};var attempts=[function(){return old.call(self,args[0],args[1],args[2],args[3])},function(){return old.call(self,args[0],args[1],args[2],args[3],settings)},function(){return old.call(self,{tmdbId:args[0],mediaType:args[1],season:args[2],episode:args[3],settings:settings})}];for(var i=0;i<attempts.length;i++){try{var rows=normalizeRows(await attempts[i]());if(rows.length)return rows}catch(_){}}return[]}
async function tvRows(old,self,args){var native=await invoke(old,self,args),ordered=orderedNativeRows(native),out=[];if(serialNativeTargetRuntime()){for(var i=0;i<ordered.length;i++){var item=ordered[i],jar=[];seedCookieHeader(jar,item.row.headers,item.row.url);var found=await resolve(item.row.url,item.row.headers,item.ref,0,{},jar);if(found.length){found.forEach(function(media){out.push(compactRow(item.row,media))});return unique(out)}}return[]}var jobs=ordered.map(function(item){var jar=[];seedCookieHeader(jar,item.row.headers,item.row.url);return resolve(item.row.url,item.row.headers,item.ref,0,{},jar).then(function(found){return found.map(function(media){return compactRow(item.row,media)})})}),groups=await Promise.all(jobs);groups.forEach(function(group){out=out.concat(group)});return unique(out)}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioTargetMediaV3)return false;var old=obj[key],wrap=async function(tmdbId,mediaType,season,episode){return tvRows(old,this,arguments)};wrap.__nuvioTargetMediaV3=true;wrap.__nuvioOriginal=old;obj[key]=wrap;return true}
var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerName":"StreamZo","maxDepth":5,"maxCandidates":22,"timeoutMs":20000});
/* NUVIO_TV_TEXT_ONLY_FETCH_COMPAT_V1 */
/* NUVIO_TV_PROTOCOL_RELATIVE_URL_COMPAT_V1 */
/* NUVIO_EXPOSE_STRICT_WRAPPER_ORIGINAL_V1 */
/* NUVIO_TARGET_MEDIA_HOST_FILTER_V4:6504d6f57a5b */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function host(u){try{return new URL(s(u)).hostname.toLowerCase()}catch(_){return""}}
function matches(h,rule){return h===rule||h.endsWith("."+rule)}
function blocked(u){var h=host(u);if(!h)return true;for(var i=0;i<c.blockedHosts.length;i++)if(matches(h,c.blockedHosts[i]))return true;if(!c.allowedMediaHosts.length)return false;for(var j=0;j<c.allowedMediaHosts.length;j++)if(matches(h,c.allowedMediaHosts[j]))return false;return true}
function rows(value){if(Array.isArray(value))return value;if(value&&typeof value==="object"){for(var i=0;i<["streams","results","data"].length;i++){var key=["streams","results","data"][i];if(Array.isArray(value[key]))return value[key]}}return[]}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioTargetHostFilterV4)return false;var old=obj[key];var wrap=async function(){var value=await old.apply(this,arguments),out=rows(value).filter(function(row){return row&&row.url&&!blocked(row.url)});return out};wrap.__nuvioTargetHostFilterV4=true;wrap.__nuvioOriginal=old;obj[key]=wrap;return true}
var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"allowedMediaHosts":[],"blockedHosts":["analytics.google.com","api.themoviedb.org","arm.haglund.dev","cloudflare.com","cloudflareinsights.com","connect.facebook.net","doubleclick.net","fstream.top","google-analytics.com","googlesyndication.com","googletagmanager.com","graphql.anilist.co","pagead2.googlesyndication.com","static.cloudflareinsights.com","v3-cinemeta.strem.io"]});
/* NUVIO_TV_TARGET_MEDIA_V4 */
/* NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT */
/* NUVIO_TV_TARGET_MEDIA_HLS_PROOF_V6 */
/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:c7e771f2b347 */
;(function(g,config){
  "use strict";
  function hostOf(raw){try{return new URL(String(raw)).hostname.toLowerCase()}catch(_e){return ""}}
  function blocked(raw){
    var host=hostOf(raw);
    if(!host)return true;
    for(var i=0;i<config.blockedHosts.length;i++){
      var rule=config.blockedHosts[i];
      if(host===rule||host.endsWith("."+rule))return true;
    }
    try{
      var parsed=new URL(String(raw)),path=parsed.pathname.toLowerCase();
      for(var j=0;j<config.blockedPathPatterns.length;j++){
        if(path.indexOf(config.blockedPathPatterns[j])>=0)return true;
      }
      // NUVIO_EMBED_HTML_ALLOWLIST_V1
      // External-player pages often legitimately end in .html. Preserve them
      // only when their path has an explicit player/embed/watch role.
      var embedLike=/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path);
      if(/\.(?:js|mjs|css|json|xml|txt|map|woff2?|ttf|otf|ico|jpe?g|png|gif|webp|svg)(?:$|[?#])/i.test(path))return true;
      if(/\.html?(?:$|[?#])/i.test(path)&&!embedLike)return true;
    }catch(_e){}
    return false;
  }
  function urlOf(stream){return stream&&typeof stream.url==="string"?stream.url.trim():""}
  function directExtension(url){return /(?:\.m3u8?|\.mpd|\.mp4|\.m4v|\.mov|\.mkv|\.webm|\.mpeg|\.mpg|\.ogv)(?:[?#]|$)/i.test(String(url||""))}
  function isDirect(stream,url){
    var hint=String((stream&&(stream.type||stream.format||stream.mimeType||stream.contentType))||"").toLowerCase();
    return directExtension(url)||/(?:hls|mpegurl|dash|mp4|matroska|webm|video\/)/.test(hint);
  }
  function markDirect(stream,url){
    if(!stream||typeof stream!=="object")return;
    if(url&&!blocked(url))stream.url=String(url);
    stream.isDirect=true;
  }
  function rank(stream,url){
    if(isDirect(stream,url))return 0;
    try{
      var path=new URL(String(url)).pathname.toLowerCase();
      if(/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return 1;
    }catch(_e){}
    if(stream&&stream.headers&&typeof stream.headers==="object"&&Object.keys(stream.headers).length)return 2;
    return 3;
  }
  function hasHeader(headers,name){
    if(!headers||typeof headers!=="object")return false;
    var wanted=String(name||"").toLowerCase(),keys=[];
    try{keys=Object.keys(headers)}catch(_e){}
    for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===wanted)return true;
    return false;
  }
  function proxyRequestHeaders(stream){
    try{
      var hints=stream&&stream.behaviorHints;
      var proxy=hints&&hints.proxyHeaders;
      return proxy&&proxy.request&&typeof proxy.request==="object"?proxy.request:null;
    }catch(_e){return null}
  }
  function ensureProxyRequest(stream){
    if(!stream||typeof stream!=="object")return null;
    if(!stream.behaviorHints||typeof stream.behaviorHints!=="object")stream.behaviorHints={};
    if(!stream.behaviorHints.proxyHeaders||typeof stream.behaviorHints.proxyHeaders!=="object")stream.behaviorHints.proxyHeaders={};
    if(!stream.behaviorHints.proxyHeaders.request||typeof stream.behaviorHints.proxyHeaders.request!=="object")stream.behaviorHints.proxyHeaders.request={};
    stream.behaviorHints.notWebReady=true;
    return stream.behaviorHints.proxyHeaders.request;
  }
  function setHeaderIfMissing(headers,key,value){
    if(!headers||value==null||String(value).trim()===""||hasHeader(headers,key))return;
    headers[key]=String(value);
  }
  function syncPlaybackHeaders(stream){
    if(!stream||typeof stream!=="object")return;
    var legacy=stream.headers&&typeof stream.headers==="object"?stream.headers:null;
    if(!legacy)return;
    var request=ensureProxyRequest(stream);
    try{Object.keys(legacy).forEach(function(key){if(legacy[key]!=null)setHeaderIfMissing(request,key,legacy[key])})}catch(_e){}
  }
  function ensurePlaybackHeaders(stream,referer){
    if(!stream||typeof stream!=="object"||!referer)return;
    var request=ensureProxyRequest(stream);
    if(!stream.headers||typeof stream.headers!=="object")stream.headers={};
    setHeaderIfMissing(request,"Referer",referer);
    setHeaderIfMissing(stream.headers,"Referer",referer);
    try{
      var origin=new URL(String(referer)).origin;
      setHeaderIfMissing(request,"Origin",origin);
      setHeaderIfMissing(stream.headers,"Origin",origin);
    }catch(_e){}
  }
  function headersFor(stream,referer){
    var output={"Accept":"application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,*/*;q=0.8","Range":"bytes=0-32767","User-Agent":"Mozilla/5.0"};
    var legacy=stream&&stream.headers;
    if(legacy&&typeof legacy==="object"){
      try{Object.keys(legacy).forEach(function(key){if(legacy[key]!=null)output[key]=String(legacy[key])})}catch(_e){}
    }
    var proxy=proxyRequestHeaders(stream);
    if(proxy){try{Object.keys(proxy).forEach(function(key){if(proxy[key]!=null)output[key]=String(proxy[key])})}catch(_e){}}
    if(referer){
      setHeaderIfMissing(output,"Referer",referer);
      try{setHeaderIfMissing(output,"Origin",new URL(String(referer)).origin)}catch(_e){}
    }
    return output;
  }
  async function prefixBytes(response,controller){
    if(response.body&&typeof response.body.getReader==="function"){
      var reader=response.body.getReader(),chunks=[],total=0;
      try{
        while(total<32768){
          var chunk=await reader.read();
          if(!chunk||chunk.done)break;
          var value=chunk.value||new Uint8Array(0);
          if(!value.length)continue;
          if(total+value.length>32768)value=value.slice(0,32768-total);
          chunks.push(value);total+=value.length;
        }
        var output=new Uint8Array(total),offset=0;
        for(var i=0;i<chunks.length;i++){output.set(chunks[i],offset);offset+=chunks[i].length}
        return output;
      }finally{try{await reader.cancel()}catch(_e){};try{controller.abort()}catch(_e){}}
    }
    var buffer=await response.arrayBuffer();
    try{controller.abort()}catch(_e){}
    return new Uint8Array(buffer.slice(0,32768));
  }
  function ascii(bytes){
    var end=Math.min(bytes.length,32768),out="";
    for(var i=0;i<end;i++)out+=String.fromCharCode(bytes[i]);
    return out;
  }
  function absoluteMediaUri(raw,baseUrl){
    var value=String(raw||"").trim();
    if(!value||value.charAt(0)==="#")return value;
    if(/^(?:data:|blob:|skd:|urn:)/i.test(value))return value;
    try{return new URL(value,String(baseUrl||"")).toString()}catch(_e){return value}
  }
  function normalizeHlsText(text,baseUrl){
    var value=String(text||"").replace(/^(?:\uFEFF|\u00EF\u00BB\u00BF)/,"").trimStart();
    if(/^\s*(?:<!doctype|<html|<body|\{|\[)/i.test(value))return null;
    var hadHeader=value.indexOf("#EXTM3U")===0;
    if(!hadHeader){
      if(!/(?:^|\n)#EXT-(?:X-[A-Z0-9-]+|INF)\s*[:]/i.test(value))return null;
      value="#EXTM3U\n"+value;
    }
    if(!validHls(value))return null;
    var lines=value.split(/\r?\n/);
    for(var i=0;i<lines.length;i++){
      var line=String(lines[i]||"");
      if(line.charAt(0)==="#"){
        lines[i]=line.replace(/URI=(["'])([^"']+)\1/gi,function(_all,quote,uri){return "URI="+quote+absoluteMediaUri(uri,baseUrl)+quote});
      }else if(line.trim()){
        lines[i]=absoluteMediaUri(line.trim(),baseUrl);
      }
    }
    return {text:lines.join("\n"),repaired:!hadHeader};
  }
  function repairedHlsUrl(text){
    return "data:application/vnd.apple.mpegurl;charset=utf-8,"+encodeURIComponent(String(text||""));
  }
  function looksHtml(text,contentType){
    return /text\/html|application\/xhtml\+xml/i.test(String(contentType||""))||/^\s*(?:<!doctype|<html|<head|<body)/i.test(String(text||""));
  }
  function looksJson(text,contentType){
    return /application\/(?:json|[^;]+\+json)/i.test(String(contentType||""))||/^\s*[\[{]/.test(String(text||""));
  }
  function mediaCandidatesFromPayload(text,baseUrl){
    var value=String(text||"").split("\\/").join("/").replace(/&amp;/gi,"&").replace(/\\u0026/gi,"&"),rows=[],seen=Object.create(null);
    function push(raw,allowOpaque){
      var candidate=String(raw||"").trim().replace(/^['"]|['"]$/g,"");
      if(!candidate||candidate.length>4096)return;
      candidate=absoluteMediaUri(candidate,baseUrl);
      if(!candidate||candidate===baseUrl||blocked(candidate)||seen[candidate])return;
      var path="";try{path=new URL(candidate).pathname.toLowerCase()}catch(_e){}
      var embedLike=/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path);
      if(!allowOpaque&&!directExtension(candidate)&&!embedLike)return;
      seen[candidate]=1;rows.push({url:candidate,direct:isDirect(null,candidate)?0:1});
    }
    var match,re=/<(?:video|source|iframe)\b[^>]*?\b(?:src|data-src)\s*=\s*["']([^"']+)["']/gi;
    while((match=re.exec(value))!==null)push(match[1],true);
    re=/(?:["']?(?:file|src|source|url)["']?\s*[:=]\s*)["']([^"']+)["']/gi;
    while((match=re.exec(value))!==null)push(match[1],true);
    re=/https?:\/\/[^\s"'<>\\]+/gi;
    while((match=re.exec(value))!==null)push(match[0],false);
    rows.sort(function(a,b){return a.direct-b.direct});
    return rows.slice(0,2).map(function(row){return row.url});
  }
  function validHls(text){
    var value=String(text||"").replace(/^(?:\uFEFF|\u00EF\u00BB\u00BF)/,"").trimStart();
    if(value.indexOf("#EXTM3U")!==0)return false;
    var lines=value.split(/\r?\n/),hasVariantTag=false,hasVariantUri=false;
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i].trim()))continue;
      hasVariantTag=true;
      for(var j=i+1;j<lines.length;j++){
        var child=String(lines[j]||"").trim();
        if(!child)continue;
        if(child.charAt(0)==="#")continue;
        hasVariantUri=true;break;
      }
      if(hasVariantUri)break;
    }
    if(hasVariantTag&&!hasVariantUri)return false;
    var hasMedia=/#EXTINF\s*:/i.test(value)||/#EXT-X-PART\s*:/i.test(value)||/#EXT-X-MAP\s*:/i.test(value);
    if(!hasMedia&&!hasVariantUri)return false;
    var isVod=/#EXT-X-ENDLIST(?:\r?\n|$)/i.test(value);
    var durations=[],match,re=/#EXTINF:([0-9]+(?:\.[0-9]+)?)/gi;
    while((match=re.exec(value))!==null)durations.push(Number(match[1])||0);
    if(isVod&&durations.length&&config.minVodDurationSeconds>0){
      var total=durations.reduce(function(sum,item){return sum+item},0);
      if(total<config.minVodDurationSeconds)return false;
    }
    return true;
  }
  function validDash(text){
    var value=String(text||"").trimStart();
    return /<MPD[\s>]/i.test(value)&&/<(?:Representation|AdaptationSet)\b/i.test(value);
  }
  function dispositionMedia(value){
    return /filename\*?=(?:UTF-8''|["']?)[^;\r\n]*\.(?:m3u8?|mpd|mp4|m4v|mov|mkv|webm|mpeg|mpg|ogv)(?:["';\r\n]|$)/i.test(String(value||""));
  }
  function isEbml(bytes){return bytes.length>=4&&bytes[0]===0x1a&&bytes[1]===0x45&&bytes[2]===0xdf&&bytes[3]===0xa3}
  async function probeResolved(stream,url,depth,referer){
    if(typeof g.fetch!=="function")return true;
    var controller=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}};
    var timer=setTimeout(function(){try{controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",headers:headersFor(stream,referer),redirect:"follow",signal:controller.signal});
      var finalUrl=response&&response.url?String(response.url):url;
      if(!response||!response.ok||blocked(finalUrl))return false;
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      var disposition=String(response.headers&&response.headers.get?response.headers.get("content-disposition")||"":"");
      var bytes=await prefixBytes(response,controller),text=ascii(bytes);
      if(/(?:\.m3u8?)(?:[?#]|$)/i.test(url)||/(?:\.m3u8?)(?:[?#]|$)/i.test(finalUrl)||/(?:mpegurl|vnd\.apple)/.test(contentType)||/^\s*#EXT(?:M3U|-(?:X-[A-Z0-9-]+|INF)\s*:)/i.test(text)){
        var hls=normalizeHlsText(text,finalUrl);
        if(!hls)return false;
        if(hls.repaired){
          stream.url=repairedHlsUrl(hls.text);
          if(!stream.type)stream.type="hls";
          if(!stream.mimeType)stream.mimeType="application/vnd.apple.mpegurl";
          stream.isDirect=true;
        }else markDirect(stream,finalUrl);
        syncPlaybackHeaders(stream);
        return true;
      }
      if(looksHtml(text,contentType)||looksJson(text,contentType)){
        var candidates=mediaCandidatesFromPayload(text,finalUrl);
        if(depth<2&&candidates.length){
          ensurePlaybackHeaders(stream,finalUrl);
          for(var candidateIndex=0;candidateIndex<candidates.length;candidateIndex++){
            if(await probeResolved(stream,candidates[candidateIndex],depth+1,finalUrl))return true;
          }
        }
        return false;
      }
      if(/(?:\.mpd)(?:[?#]|$)/i.test(url)||/(?:\.mpd)(?:[?#]|$)/i.test(finalUrl)||/application\/dash\+xml/.test(contentType)||/^\s*(?:<\?xml[\s\S]{0,300})?<MPD[\s>]/i.test(text)){
        if(!validDash(text))return false;
        markDirect(stream,finalUrl);
        return true;
      }
      var hasFtyp=bytes.length>=8&&ascii(bytes.slice(4,8))==="ftyp";
      if(/(?:\.mp4|\.m4v|\.mov)(?:[?#]|$)/i.test(url)||/(?:\.mp4|\.m4v|\.mov)(?:[?#]|$)/i.test(finalUrl)||/video\/mp4/.test(contentType)||hasFtyp){
        if(!(/video\/mp4/.test(contentType)||hasFtyp||bytes.length>0))return false;
        markDirect(stream,finalUrl);
        return true;
      }
      if(/(?:video\/(?:webm|x-matroska|mpeg|ogg)|application\/(?:x-matroska|ogg))/.test(contentType)||isEbml(bytes)||dispositionMedia(disposition)){
        if(!bytes.length)return false;
        markDirect(stream,finalUrl);
        return true;
      }
      if(/^video\//.test(contentType)&&bytes.length){
        markDirect(stream,finalUrl);
        return true;
      }
      if(/^text\//i.test(contentType))return false;
      return bytes.length>0;
    }catch(_error){return false}
    finally{clearTimeout(timer);try{controller.abort()}catch(_e){}}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__nuvioSanitized)return false;
    var original=container[key];
    var wrapped=async function(){
      var result=await original.apply(this,arguments);
      if(!Array.isArray(result))return result;
      var seen=Object.create(null),candidates=[],probeCount=0;
      for(var i=0;i<result.length;i++){
        var stream=result[i];syncPlaybackHeaders(stream);var url=urlOf(stream);
        if(!url||blocked(url)||seen[url])continue;
        seen[url]=true;
        candidates.push({stream:stream,url:url,rank:rank(stream,url),index:i});
      }
      candidates.sort(function(a,b){return a.rank-b.rank||a.index-b.index});
      for(var c=0;c<candidates.length;c++){
        candidates[c].probe=(config.probeAllUrls||(config.probeDirectMedia&&isDirect(candidates[c].stream,candidates[c].url)))&&probeCount++<config.maxProbes;
      }
      var checked=await Promise.all(candidates.map(async function(item){
        if(!item.probe)return item.stream;
        return await probe(item.stream,item.url)?item.stream:null;
      }));
      return checked.filter(Boolean);
    };
    wrapped.__nuvioSanitized=true;
    wrapped.__nuvioOriginal=original;
    container[key]=wrapped;
    return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){
    if(installed&&typeof module!=="undefined"&&module.exports&&module.exports.getStreams)g.getStreams=module.exports.getStreams;
    else install(g,"getStreams");
  }}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"blockedHosts":["analytics.google.com","api.themoviedb.org","arm.haglund.dev","cloudflareinsights.com","connect.facebook.net","doubleclick.net","fstream.top","google-analytics.com","googlesyndication.com","googletagmanager.com","graphql.anilist.co","kitsu.io","lodash.com","npms.io","openjsf.org","pagead2.googlesyndication.com","static.cloudflareinsights.com","underscorejs.org","v3-cinemeta.strem.io"],"probeDirectMedia":false,"probeAllUrls":false,"maxProbes":0,"timeoutMs":4500,"minVodDurationSeconds":60,"blockedPathPatterns":["/analytics","/beacon.min.js","/cdn-cgi/rum","/collect","/gtag/js"],"implementationVersion":7});
/* NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5 */
/* NUVIO_STREAM_OUTPUT_HLS_HTML_REPAIR_V7 */
/* NUVIO_DESKTOP_RUNTIME_COMPAT_V1:09b86a7b40f8 */
;(function(g,config){
  "use strict";
  if(!g)return;

  // Runtime portability only. Never rewrite provider URLs/domains here.
  if(typeof g.setTimeout!=="function"){
    g.setTimeout=function(callback,delay){
      if((Number(delay)||0)<=0&&typeof callback==="function"&&typeof Promise!=="undefined"){
        Promise.resolve().then(callback).catch(function(){});
      }
      return 0;
    };
  }
  if(typeof g.clearTimeout!=="function")g.clearTimeout=function(){};
  if(typeof g.setInterval!=="function")g.setInterval=function(){return 0;};
  if(typeof g.clearInterval!=="function")g.clearInterval=function(){};

  function positive(value,fallback){
    var number=Number(value);
    return Number.isFinite(number)&&number>0?Math.floor(number):fallback;
  }
  function isSeries(type){
    var value=String(type||"").toLowerCase();
    return value==="tv"||value==="series"||value==="show";
  }
  function textOf(stream){
    if(!stream||typeof stream!=="object")return "";
    return [stream.name,stream.title,stream.description,stream.size,stream.url]
      .filter(function(value){return value!=null})
      .join(" ");
  }
  function episodeMatch(stream,season,episode){
    var text=textOf(stream);
    if(!text)return false;
    var s=String(season),e=String(episode);
    var patterns=[
      new RegExp("S0*"+s+"\\s*E0*"+e,"i"),
      new RegExp("\\b0*"+s+"x0*"+e+"\\b","i"),
      new RegExp("saison\\s*0*"+s+"[^0-9]{0,16}(?:episode|ep)\\s*0*"+e,"i"),
      new RegExp("season\\s*0*"+s+"[^0-9]{0,16}(?:episode|ep)\\s*0*"+e,"i")
    ];
    for(var i=0;i<patterns.length;i++)if(patterns[i].test(text))return true;
    return false;
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__nuvioDesktopCompat)return false;
    var original=container[key];
    var wrapped=async function(){
      var args=Array.prototype.slice.call(arguments);
      var series=isSeries(args[1]);
      if(series&&config.normalizeMissingEpisodes){
        args[2]=positive(args[2],config.fallbackSeason);
        args[3]=positive(args[3],config.fallbackEpisode);
      }
      var result=await original.apply(this,args);
      if(!series||!Array.isArray(result))return result;
      var output=result;
      if(config.filterEpisodeLabels){
        var exact=result.filter(function(stream){return episodeMatch(stream,args[2],args[3])});
        if(exact.length)output=exact;
      }
      if(config.maxSeriesStreams>0&&output.length>config.maxSeriesStreams){
        output=output.slice(0,config.maxSeriesStreams);
      }
      return output;
    };
    wrapped.__nuvioDesktopCompat=true;
    wrapped.__nuvioOriginal=original;
    container[key]=wrapped;
    return true;
  }

  var installed=false;
  try{
    if(typeof module!=="undefined"&&module.exports){
      installed=install(module.exports,"getStreams")||installed;
    }
  }catch(_error){}
  try{
    if(typeof g.getStreams==="function"){
      if(installed&&typeof module!=="undefined"&&module.exports&&module.exports.getStreams){
        g.getStreams=module.exports.getStreams;
      }else{
        install(g,"getStreams");
      }
    }
  }catch(_error){}
})(typeof globalThis!=="undefined"?globalThis:this,{"patchRevision":5,"normalizeMissingEpisodes":true,"fallbackSeason":1,"fallbackEpisode":1,"filterEpisodeLabels":false,"maxSeriesStreams":0});
/* NUVIO_STREAMZO_SOURCE_IDENTITY_V3:9bee7648f295 */
;(function(g,c){"use strict";
var TMDB_KEY=(g&&g.TMDB_API_KEY)||"";
function s(v){return String(v==null?"":v).trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,et:1,and:1,serie:1,series:1,tv:1,film:1,movie:1,streaming:1,watch:1,backtrack:1};return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!/^\d{4}$/.test(x)})}
function unique(v){var o=[],seen={};(v||[]).forEach(function(x){x=s(x).replace(/\s*\(\d{4}\)\s*$/,"");var k=norm(x);if(k&&!seen[k]){seen[k]=1;o.push(x)}});return o}
function req(a){var o=a[0]&&typeof a[0]==="object"?a[0]:{};return {id:s(o.tmdbId||o.id||a[0]),type:s(o.mediaType||o.type||a[1]||"movie").toLowerCase(),title:s(o.title||o.name||o.label),year:Number(o.year)||0}}
async function meta(q){var out={titles:unique([q.title]),year:q.year};if(!q.id||!TMDB_KEY)return out;var kind=q.type==="tv"||q.type==="series"||q.type==="anime"?"tv":"movie";try{var r=await g.fetch("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.id)+"?api_key="+TMDB_KEY+"&language=fr-FR",{headers:{Accept:"application/json"}});if(r&&r.ok){var d=await r.json();out.titles=unique(out.titles.concat([d.title,d.name,d.original_title,d.original_name]));var date=s(d.release_date||d.first_air_date);out.year=Number(date.slice(0,4))||out.year}}catch(_e){}return out}
function referer(row){try{return s(row&&row.headers&&row.headers.Referer||row&&row.headers&&row.headers.referer||row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request&&row.behaviorHints.proxyHeaders.request.Referer||row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request&&row.behaviorHints.proxyHeaders.request.referer)}catch(_e){return ""}}
function sourcePage(ref){try{var u=new URL(ref,c.baseUrl+"/");var b=new URL(c.baseUrl+"/");if(u.hostname!==b.hostname)return null;var p=s(u.pathname);if(!p||p==="/"||/^\/(?:embed|api|player|watch|search)(?:\/|$)/i.test(p))return null;return u}catch(_e){return null}}
function titleMatch(text,title){var want=tokens(title);if(!want.length)return false;var have=tokens(text);return want.every(function(x){return have.indexOf(x)>=0})}
function matches(u,m){if(!u)return true;var text=norm(decodeURIComponent(s(u.pathname))),aliases=m.titles||[];if(!aliases.some(function(t){return titleMatch(text,t)}))return false;if(m.year){var years=text.match(/\b(?:19|20)\d{2}\b/g)||[];if(years.length&&years.indexOf(String(m.year))<0)return false}return true}
function slot(v){if(Array.isArray(v))return {key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return {key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioStreamzoIdentityV3)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var m=await meta(q);if(!m.titles.length)return v;var kept=x.list.filter(function(row){return matches(sourcePage(referer(row)),m)});return rebuild(v,x,kept)};wrap.__nuvioStreamzoIdentityV3=true;wrap.__nuvioStreamzoIdentityOriginal=native;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://streamzo.fr","timeoutMs":6500});

/* NUVIO_TV_PLAYABLE_FIRST_V1 */
;(function(g){
 const MAX=8, TIMEOUT=6500;
 function isTv(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");if(/NuvioTV|Android TV/i.test(ua))return true;if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}if(/followRedirects/.test(src))return false;var signalAware=/options\.signal|var\s+signal\s*=/.test(src);var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);return signalAware&&fourArgNative;}catch(_e){return false}}
 function slot(v){if(Array.isArray(v))return {key:null,list:v};if(v&&typeof v==="object"){for(const k of ["streams","results","data"]){if(Array.isArray(v[k]))return {key:k,list:v[k]}}}return null}
 function rebuild(v,s,list){if(s.key===null)return list;return Object.assign({},v,{[s.key]:list})}
 function direct(u){return /^https?:\/\//i.test(u)&&!/\.(?:html?|php)(?:[?#]|$)/i.test(u)}
 function mergedHeaders(row){var h={};try{Object.assign(h,row&&row.headers||{},row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request||{})}catch(_e){}if(!h.Accept)h.Accept="*/*";if(!/\.m3u8(?:[?#]|$)/i.test(String(row&&row.url||""))&&!h.Range)h.Range="bytes=0-32767";return h}
 async function probe(row){
   const u=String(row&&row.url||"").trim();
   if(!direct(u))return {rank:1,dead:false};
   let timer;try{
     const c=typeof AbortController!=="undefined"?new AbortController():null;if(c)timer=setTimeout(()=>c.abort(),TIMEOUT);
     const r=await g.fetch(u,{headers:mergedHeaders(row),redirect:"follow",signal:c?c.signal:void 0});
     const st=Number(r&&r.status||0),ct=String(r&&r.headers&&r.headers.get?r.headers.get("content-type")||"":"").toLowerCase();
     if([401,403,404,410].includes(st)||st>=500)return {rank:3,dead:true,status:st};
     if(/^video\//.test(ct)&&(st===200||st===206))return {rank:0,dead:false,status:st};
     let text="";try{if(r&&typeof r.text==="function")text=String(await r.text()).replace(/^\uFEFF/,"").trimStart()}catch(_e){}
     if(text.startsWith("#EXTM3U"))return {rank:0,dead:false,status:st};
     if(/text\/html|application\/xhtml/.test(ct)||/^<!doctype html|^<html/i.test(text))return {rank:3,dead:true,status:st};
     return {rank:1,dead:false,status:st};
   }catch(_e){return {rank:2,dead:false};}finally{if(timer)clearTimeout(timer)}
 }
 function install(t){if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioTvPlayableFirstV1)return;const native=t.getStreams;
   const wrapped=async function(){const v=await native.apply(t,arguments);if(!isTv())return v;const s=slot(v);if(!s||s.list.length<1)return v;
     const head=s.list.slice(0,MAX),tail=s.list.slice(MAX),checks=await Promise.all(head.map(probe));
     const kept=head.map((row,i)=>({row,i,c:checks[i]})).filter(x=>!x.c.dead).sort((a,b)=>(a.c.rank-b.c.rank)||(a.i-b.i)).map(x=>x.row);
     return rebuild(v,s,kept.concat(tail));
   };wrapped.__nuvioTvPlayableFirstV1=true;wrapped.__nuvioTvPlayableFirstOriginal=native;t.getStreams=wrapped;
 }
 try{if(typeof module!=="undefined"&&module.exports)install(module.exports)}catch(_e){}
 try{if(g&&typeof g.getStreams==="function"){const o={getStreams:g.getStreams};install(o);g.getStreams=o.getStreams}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
/* NUVIO_NATIVE_SYNC_FETCH_TARGET_ORDER_V1 */
/* NUVIO_VF_CATALOGUE_RECOVERY_V1:7d831b28955e */
;(function(g,config){
  "use strict";
  var TMDB_KEY=(g&&g.TMDB_API_KEY)||"";
  function clean(v){return String(v==null?"":v).replace(/&amp;/gi,"&").trim()}
  function stripHtml(v){return clean(v).replace(/<[^>]+>/g," ").replace(/\s+/g," ").trim()}
  function normalize(v){try{return String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return String(v||"").toLowerCase()}}
  function slug(v){return normalize(v).replace(/\s+/g,"-").replace(/-+/g,"-").replace(/^-|-$/g,"")}
  function absolute(raw,base){try{return new URL(clean(raw),base).toString()}catch(_e){return ""}}
  function blocked(raw){
    try{
      var u=new URL(String(raw)); var h=u.hostname.toLowerCase(),p=u.pathname.toLowerCase();
      for(var i=0;i<config.blockedHosts.length;i++){var x=config.blockedHosts[i];if(h===x||h.endsWith("."+x))return true}
      for(var j=0;j<config.blockedPathPatterns.length;j++)if(p.indexOf(config.blockedPathPatterns[j])>=0)return true;
      if(/(?:youtube\.com|youtu\.be|googlevideo\.com)$/.test(h)||/(?:trailer|bande-annonce)/i.test(p))return true;
      return false;
    }catch(_e){return true}
  }
  function usable(raw){var u=clean(raw);return /^https?:\/\//i.test(u)&&!blocked(u)&&!/(?:\.jpg|\.jpeg|\.png|\.webp|\.gif|\.css|\.js|favicon)(?:[?#]|$)/i.test(u)}
  function headers(base){try{var u=new URL(base);return {Referer:u.origin+"/",Origin:u.origin,"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.6"}}catch(_e){return {"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.6"}}}
  async function request(url,asJson){
    var c=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}};
    var timer=setTimeout(function(){try{c.abort()}catch(_e){}},config.timeoutMs);
    try{
      var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:{"Accept":asJson?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,*/*;q=0.8","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.6"},signal:c.signal});
      if(!r||!r.ok)return null;
      return asJson?await r.json():await r.text();
    }catch(_e){return null}finally{clearTimeout(timer);try{c.abort()}catch(_e){}}
  }
  function argumentsOf(args){
    var first=args[0],out={};
    if(first&&typeof first==="object"&&!Array.isArray(first))out=Object.assign({},first);
    else{out.tmdbId=String(first||"");out.mediaType=String(args[1]||"movie");out.season=args[2];out.episode=args[3];out.settings=args[4]||{}}
    out.tmdbId=String(out.tmdbId||out.id||"");out.mediaType=String(out.mediaType||out.type||out.category||"movie").toLowerCase();
    try{
      var ctx=g&&g.__nuvioMediaContext;
      out.tmdbNamespace=String(out.tmdbNamespace||ctx&&ctx.tmdbNamespace||(out.mediaType==="movie"?"movie":"tv")).toLowerCase();
    }catch(_e){out.tmdbNamespace=out.mediaType==="movie"?"movie":"tv"}
    if(out.tmdbNamespace!=="movie")out.tmdbNamespace="tv";
    return out;
  }
  async function metadata(req){
    var title=clean(req.title||req.name||req.label||req.settings&&req.settings.title),year=Number(req.year||req.settings&&req.settings.year)||0,original="";
    if(title)title=title.replace(/\s*\(\d{4}\)\s*$/,"");
    var kind=req.tmdbNamespace==="movie"?"movie":"tv",data=null;
    try{
      var cache=g&&g.__nuvioTmdbMetadataCacheV1,identity=kind+":"+String(req.tmdbId||"");
      var cached=cache&&cache[identity];
      if(cached&&typeof cached.then!=="function")data=cached;
    }catch(_e){}
    if(!data&&req.tmdbId&&TMDB_KEY)data=await request("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(req.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR",true);
    if(data){title=clean(data.title||data.name)||title;original=clean(data.original_title||data.original_name);var date=clean(data.release_date||data.first_air_date);year=Number(date.slice(0,4))||year}
    return {title:title,original:original,year:year};
  }
  function significant(v){
    var noise={film:1,films:1,movie:1,movies:1,serie:1,series:1,streaming:1,watch:1,regarder:1,voir:1,vf:1,vff:1,vfq:1,vostfr:1,vo:1,hd:1,full:1,complet:1,complete:1,saison:1,season:1,episode:1,ep:1,french:1,francais:1};
    return normalize(v).split(" ").filter(function(x){return x.length>1&&!noise[x]});
  }
  function score(label,meta,url){
    var a=normalize(label),wanted=normalize(meta.title),original=normalize(meta.original),urlText=normalize(url);
    if(!a||(!wanted&&!original))return -100;
    if(meta.year){
      var years=String(label||"").match(/\b(?:19|20)\d{2}\b/g)||[];
      if(years.length&&years.indexOf(String(meta.year))<0)return -100;
    }
    function one(title){
      if(!title)return -100;
      if(a===title)return 120;
      var wantedWords=significant(title),labelWords=significant(a),hay=significant(a+" "+urlText);
      if(!wantedWords.length)return -100;
      var all=wantedWords.every(function(x){return hay.indexOf(x)>=0});
      if(!all)return -100;
      var extras=labelWords.filter(function(x){return wantedWords.indexOf(x)<0});
      if(extras.length>Math.max(4,wantedWords.length+2))return -100;
      return extras.length<=2?92:84;
    }
    var s=Math.max(one(wanted),one(original));
    if(s<0)return s;
    if(meta.year&&String(label+" "+url).indexOf(String(meta.year))>=0)s+=15;
    return s;
  }
  function links(html,base,meta){
    var rows=[],seen=Object.create(null),re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;
    while((m=re.exec(String(html||"")))!==null){var url=absolute(m[1],base),label=stripHtml(m[2]);if(!url||seen[url])continue;seen[url]=1;var s=score(label,meta,url);if(s>=80)rows.push({url:url,label:label,score:s})}
    return rows.sort(function(a,b){return b.score-a.score}).slice(0,8);
  }
  function players(html,base){
    var found=[],seen=Object.create(null),text=String(html||"").split("\\/").join("/");
    var patterns=[
      /(?:data-embed|data-src|data-player|data-url|data-video)=["']([^"']+)["']/gi,
      /<iframe\b[^>]*src=["']([^"']+)["']/gi,
      /<(?:source|video)\b[^>]*src=["']([^"']+)["']/gi,
      /(?:file|src|url)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi,
      /(https?:\/\/[^"'<>\s]+(?:\.m3u8|\/embed[-/]|\/e\/|\/player\/)[^"'<>\s]*)/gi
    ];
    for(var p=0;p<patterns.length;p++){var re=patterns[p],m;while((m=re.exec(text))!==null){var u=absolute(m[1],base);if(!usable(u)||seen[u])continue;seen[u]=1;found.push(u);if(found.length>=config.maxPlayers)return found}}
    return found;
  }
  function streamRows(urls,base,label){return urls.slice(0,config.maxPlayers).map(function(url,index){return {name:config.providerName+(urls.length>1?" #"+(index+1):""),title:config.providerName+" - "+label,url:url,quality:"HD",language:"fr",headers:headers(base),isDirect:/(?:\.m3u8|\.mp4|\.mpd)(?:[?#]|$)/i.test(url)}})}
  function episodePlayers(html,base,req){
    if(!req||req.mediaType!=="tv")return [];
    var season=Number(req.season)||1,episode=Number(req.episode)||1,text=String(html||"").split("\\/").join("/"),urls=[],seen=Object.create(null);
    var blocks=text.match(/<[^>]+(?:data-season|data-saison)=["'][^"']+["'][^>]*(?:data-episode|data-ep)=["'][^"']+["'][^>]*>/gi)||[];
    blocks.forEach(function(tag){
      var sm=tag.match(/(?:data-season|data-saison)=["'](\d+)["']/i),em=tag.match(/(?:data-episode|data-ep)=["'](\d+)["']/i);
      if(!sm||!em||Number(sm[1])!==season||Number(em[1])!==episode)return;
      var um=tag.match(/(?:data-embed|data-src|data-player|data-url|data-video|src)=["']([^"']+)["']/i),u=um&&absolute(um[1],base);
      if(usable(u)&&!seen[u]){seen[u]=1;urls.push(u)}
    });
    var jsonRe=/[{,]\s*["']?(?:season|saison)["']?\s*:\s*(\d+)[\s\S]{0,500}?["']?(?:episode|ep)["']?\s*:\s*(\d+)[\s\S]{0,700}?["']?(?:url|src|embedUrl|embed_url|player)["']?\s*:\s*["'](https?:\/\/[^"']+)["']/gi,m;
    while((m=jsonRe.exec(text))!==null){if(Number(m[1])!==season||Number(m[2])!==episode)continue;var u=absolute(m[3].split("\\/").join("/"),base);if(usable(u)&&!seen[u]){seen[u]=1;urls.push(u)}}
    return urls;
  }
  function episodeLinks(html,base,req){
    if(!req||req.mediaType!=="tv")return [];
    var season=Number(req.season)||1,episode=Number(req.episode)||1,out=[],seen=Object.create(null),re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;
    var patterns=[new RegExp("s(?:aison)?[ ._-]*0?"+season+"[ ._-]*e(?:p(?:isode)?)?[ ._-]*0?"+episode,"i"),new RegExp("saison[ ._-]*0?"+season+"[\\s\\S]{0,40}(?:episode|ep)[ ._-]*0?"+episode,"i")];
    while((m=re.exec(String(html||"")))!==null){var u=absolute(m[1],base),label=stripHtml(m[2])+" "+m[1];if(!u||seen[u]||!patterns.some(function(p){return p.test(label)}))continue;seen[u]=1;out.push(u)}
    return out.slice(0,8);
  }
  function materializeRoute(tpl,req){
    var type=req.tmdbNamespace==="movie"?"movie":"tv";
    return tpl.replace(/\{id\}/g,encodeURIComponent(req.tmdbId)).replace(/\{type\}/g,type)
      .replace(/\{season\}/g,String(Number(req.season)||1)).replace(/\{episode\}/g,String(Number(req.episode)||1));
  }
  function fixedApiRoutes(req){
    var type=req.tmdbNamespace==="movie"?"movie":"tv",out=[];
    for(var i=0;i<config.apiRoutes.length;i++){
      var route=clean(config.apiRoutes[i]),low=route.toLowerCase();
      if(!route)continue;
      if((low.indexOf("/movie/")>=0||low.indexOf("/movie{")>=0||low.endsWith("/movie"))&&type!=="movie")continue;
      if((low.indexOf("/tv/")>=0||low.indexOf("/tv{")>=0||low.endsWith("/tv"))&&type!=="tv")continue;
      out.push(route);
    }
    return Array.from(new Set(out)).slice(0,2);
  }
  function collectRows(rows,urls){if(Array.isArray(rows))rows.forEach(function(row){var u=clean(row&&row.url||row&&row.src||row&&row.embedUrl||row);if(usable(u))urls.push(u)})}
  function apiPlayers(data,req){
    var groups=data&&data.players||data&&data.links||{},urls=[];
    if(req&&req.tmdbNamespace==="tv"&&data&&data.episodes){
      var season=String(Number(req.season)||1),episode=String(Number(req.episode)||1),root=data.episodes;
      var selected=root[episode]||root[Number(episode)]||root[season]&&root[season][episode]||root[season]&&root[season][Number(episode)];
      if(selected){
        if(selected.languages&&typeof selected.languages==="object")Object.keys(selected.languages).forEach(function(k){collectRows(selected.languages[k],urls)});
        ["vf","vff","vfq","vostfr","vo","default","players","links"].forEach(function(k){collectRows(selected[k],urls)});
        if(Array.isArray(selected))collectRows(selected,urls);
      }
    }
    config.preferredPlayerGroups.forEach(function(group){collectRows(groups[group],urls)});
    if(!urls.length&&groups&&typeof groups==="object")Object.keys(groups).forEach(function(group){collectRows(groups[group],urls)});
    return Array.from(new Set(urls));
  }
  async function apiFixed(req,meta){
    var routes=fixedApiRoutes(req);if(!routes.length)return [];
    for(var i=0;i<routes.length;i++){
      var endpoint=absolute(materializeRoute(routes[i],req),config.apiUrl+"/"),data=await request(endpoint,true);
      if(!data||data.success===false)continue;
      var urls=apiPlayers(data,req);
      if(urls.length)return streamRows(urls,config.baseUrl||config.apiUrl,meta.title||(req.tmdbNamespace==="tv"?"Série":"Film"));
    }
    return [];
  }
  async function htmlRecovery(req,meta){
    var bases=[config.baseUrl],candidates=[];
    var slugs=[slug(meta.title),slug(meta.original)].filter(Boolean); if(meta.year)slugs=slugs.concat(slugs.map(function(s){return s+"-"+meta.year}));
    for(var i=0;i<config.directPaths.length;i++)for(var j=0;j<slugs.length;j++)candidates.push(absolute(config.directPaths[i].replace(/\{slug\}/g,slugs[j]).replace(/\{id\}/g,req.tmdbId).replace(/\{year\}/g,String(meta.year||"")),config.baseUrl+"/"));
    for(var k=0;k<config.searchPaths.length;k++){
      var search=absolute(config.searchPaths[k].replace(/\{query\}/g,encodeURIComponent(meta.title)).replace(/\{slug\}/g,slug(meta.title)).replace(/\{id\}/g,req.tmdbId),config.baseUrl+"/");
      var page=await request(search,false);if(!page)continue;
      var episodic=episodePlayers(page,search,req);if(episodic.length)return streamRows(episodic,search,meta.title);
      var direct=req.mediaType==="tv"?[]:players(page,search);if(direct.length)return streamRows(direct,search,meta.title);
      episodeLinks(page,search,req).forEach(function(url){candidates.push(url)});
      links(page,search,meta).forEach(function(row){candidates.push(row.url)});
    }
    var unique=Array.from(new Set(candidates.filter(Boolean))).slice(0,12);
    for(var n=0;n<unique.length;n++){var detail=await request(unique[n],false);if(!detail)continue;var urls=episodePlayers(detail,unique[n],req);if(!urls.length&&req.mediaType!=="tv")urls=players(detail,unique[n]);if(urls.length)return streamRows(urls,unique[n],meta.title)}
    return [];
  }
  async function recover(req){
    if(config.types.indexOf(req.mediaType)<0)return [];
    if(config.strategy==="api_fixed")return apiFixed(req,{title:""});
    var meta=await metadata(req);if(!meta.title)return [];
    return htmlRecovery(req,meta);
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__nuvioVfRecovery)return false;
    var original=container[key];
    var wrapped=async function(){var req=argumentsOf(arguments),fallback=[];if(config.recoveryFirst){fallback=await recover(req);if(fallback.length)return fallback;if(config.skipNativeWhenUnresolved&&config.strategy==="api_fixed")return []}var native=[],nativeError=null;try{native=filterNative(await original.apply(this,arguments))}catch(error){nativeError=error}if(Array.isArray(native)&&native.length)return native;if(!config.recoveryFirst){fallback=await recover(req);if(fallback.length)return fallback}if(nativeError)throw nativeError;return Array.isArray(native)?native:[]};
    wrapped.__nuvioVfRecovery=true;wrapped.__nuvioOriginal=original;container[key]=wrapped;return true;
  }
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"implementationVersion":3,"strategy":"streamzo","baseUrl":"https://streamzo.fr","apiUrl":"","types":["movie","tv","anime"],"searchPaths":["/?s={query}","/search?q={query}"],"directPaths":["/{slug}"],"apiRoutes":[],"blockedHosts":["fstream.top"],"blockedPathPatterns":[],"preferredPlayerGroups":["VFF","VFQ","VF","Default","VOSTFR"],"maxPlayers":6,"timeoutMs":7000,"providerName":"StreamZo","recoveryFirst":true,"skipNativeWhenUnresolved":false});
