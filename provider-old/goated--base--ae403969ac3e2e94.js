"use strict";
/* NUVIO_PROVIDER_SECURITY_HARDENING_V1:77e110a2a7b7 */
var __nuvioProviderSilentLog=function(){};


/* NIAKVIO_PROVIDER_BASE_OWNED_V2 */
const NIAKVIO_PROVIDER_MODEL = Object.freeze({"apiRecipe":null,"authoring":"niakvio-owned-v3","displayName":"🐐 Goated","fixedApi":null,"knownSite":"https://goated.cx","modelSchemaVersion":3,"observedUrls":["https://api.reallyfast.xyz/","https://goated.cx/"],"officialApi":null,"officialHub":null,"officialSite":"https://goated.cx","origins":["https://goated.cx","https://api.reallyfast.xyz"],"providerId":"goated","reconstructionState":"learning-clean-seed","routePlanVersion":2,"routes":["/api/challenge","/season/","/episode/","/api/resolve","/api/subtitles"],"runtimeDiscovery":false,"runtimeRole":"reader","strategy":"api_stream_resolver","supportedTypes":["movie","tv"],"upstreamCodeEmbedded":false,"upstreamCodeExecuted":false});

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
function _providerDeadlineExceeded() {
  try {
    const deadline = Number(globalThis && globalThis.__nuvioProviderDeadlineMs);
    return Number.isFinite(deadline) && deadline > 0 && Date.now() >= deadline;
  } catch (_) {
    return false;
  }
}
function _providerTimeoutError() {
  const error = new Error("nuvio_provider_timeout");
  error.name = "TimeoutError";
  error.code = "NUVIO_PROVIDER_TIMEOUT";
  error.__nuvioProviderTimeout = true;
  return error;
}
async function _fetch(url, options) {
  if (_providerDeadlineExceeded()) throw _providerTimeoutError();
  const requestOptions = options && typeof options === "object" ? Object.assign({}, options) : {};
  requestOptions.redirect = requestOptions.redirect || "follow";
  requestOptions.headers = Object.assign({
    "Accept": "application/json,text/html,application/xhtml+xml,text/plain,*/*",
    "User-Agent": "Mozilla/5.0 NiakVIO/3"
  }, requestOptions.headers || {});
  const response = await fetch(url, requestOptions);
  if (_providerDeadlineExceeded()) throw _providerTimeoutError();
  if (!response.ok) throw new Error("provider_http_" + response.status);
  return response;
}
async function _tmdb(tmdbId, mediaType) {
  if (!tmdbId) return null;
  const type = _mediaNamespace(mediaType);
  const identity = type + ":" + String(tmdbId || "");
  function project(row) {
    if (!row || typeof row !== "object") return null;
    return {
      title: row.title || row.name || row.original_title || row.original_name || "",
      year: String(row.release_date || row.first_air_date || row.year || "").slice(0, 4),
      tmdbId: String(tmdbId || "")
    };
  }
  try {
    const ctx = typeof globalThis !== "undefined" ? globalThis.__nuvioMediaContext : null;
    const ctxId = String(ctx && ctx.tmdbId || "");
    const ctxNamespace = String(ctx && ctx.tmdbNamespace || "");
    if (ctx && (!ctxId || ctxId === String(tmdbId)) && (!ctxNamespace || ctxNamespace === type)) {
      const projected = project(ctx.tmdbMetadata);
      if (projected) return projected;
    }
  } catch (_) {}
  try {
    const cache = typeof globalThis !== "undefined" ? globalThis.__nuvioTmdbMetadataCacheV1 : null;
    const cached = cache && cache[identity];
    if (cached && typeof cached.then !== "function") {
      const row = cached.metadata && typeof cached.metadata === "object" ? cached.metadata : cached;
      const projected = project(row);
      if (projected) return projected;
    }
  } catch (_) {}
  return null;
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
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
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
    if (typeof child === "string" && /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl)$/i.test(key)) {
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
function _streams(urls, referer, extraHeaders) {
  const headers = Object.assign({}, extraHeaders || {});
  if (referer) headers.Referer = referer;
  const hasHeaders = Object.keys(headers).length > 0;
  return _uniq(urls).slice(0, 40).map((url, index) => ({
    name: NIAKVIO_PROVIDER_MODEL.displayName,
    title: NIAKVIO_PROVIDER_MODEL.displayName + (index ? " #" + (index + 1) : ""),
    url,
    headers: hasHeaders ? Object.assign({}, headers) : undefined
  }));
}
function _recipeValue(row, fields) {
  if (!row || typeof row !== "object") return "";
  for (const field of fields || []) {
    const value = row[field];
    if (value != null && value !== "") return _text(value);
  }
  return "";
}
function _recipeObjects(value, out) {
  out = out || [];
  if (Array.isArray(value)) {
    for (const child of value) _recipeObjects(child, out);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  out.push(value);
  for (const child of Object.values(value)) {
    if (child && typeof child === "object") _recipeObjects(child, out);
    if (out.length >= 400) break;
  }
  return out;
}
function _recipeMediaType(row, recipe) {
  const raw = _recipeValue(row, recipe.typeFields || ["type","media_type","mediaType","kind","category"]).toLowerCase();
  if (!raw) return "";
  if (["tv","series","show","anime","episode"].includes(raw)) return "tv";
  if (["movie","film"].includes(raw)) return "movie";
  return "";
}
function _recipeScore(row, meta, recipe, expectedMedia) {
  const title = _slug(_recipeValue(row, recipe.titleFields || ["title","name","post_title","original_title"]));
  const expected = _slug(meta && meta.title);
  const actualMedia = _recipeMediaType(row, recipe);
  if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
  const year = _recipeValue(row, recipe.yearFields || ["year","release_date","first_air_date"]).slice(0, 4);
  if (year && meta && meta.year && year !== _text(meta.year)) return -1;
  let score = 0;
  if (title && expected && title === expected) score += 200;
  else if (title && expected && (title.includes(expected) || expected.includes(title))) score += 90;
  if (title && expected) {
    for (const token of expected.split("-").filter(value => value.length >= 3)) {
      if (title.includes(token)) score += 10;
    }
  }
  if (year && meta && meta.year && year === _text(meta.year)) score += 40;
  if (actualMedia && expectedMedia && actualMedia === expectedMedia) score += 60;
  if (_recipeValue(row, recipe.idFields || ["id","_id","media_id","post_id"])) score += 15;
  return score;
}
function _recipeUrl(pattern, values, base) {
  let route = _text(pattern);
  if (!route) return "";
  const replacements = {
    query: values.query,
    title: values.query,
    id: values.providerId,
    providerId: values.providerId,
    tmdbId: values.tmdbId,
    tmdb_id: values.tmdbId,
    media: values.media,
    type: values.media,
    season: values.season,
    episode: values.episode,
    source: values.source
  };
  route = route.replace(/\{([^}]+)\}/g, (match, key) => {
    const value = replacements[key];
    return value == null ? "" : encodeURIComponent(_text(value));
  });
  let url;
  try { url = new URL(route, base).toString(); } catch (_) { return ""; }
  try {
    const parsed = new URL(url);
    for (const key of ["season","episode","source"]) {
      if (values[key] == null || values[key] === "") {
        for (const param of [...parsed.searchParams.keys()]) {
          if (param.toLowerCase() === key) parsed.searchParams.delete(param);
        }
      }
    }
    return parsed.toString();
  } catch (_) {
    return url;
  }
}
async function _recipePayload(url, recipe, body) {
  const headers = Object.assign({}, recipe.requestHeaders || {});
  if (recipe.referer) headers.Referer = recipe.referer;
  if (recipe.origin) headers.Origin = recipe.origin;
  const options = { headers };
  if (body != null) {
    options.method = "POST";
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await _fetch(url, options);
  const type = _text(response.headers.get("content-type")).toLowerCase();
  if (type.includes("json")) return { value: await response.json(), base: response.url || url };
  const text = await response.text();
  try { return { value: JSON.parse(text), base: response.url || url }; }
  catch (_) { return { value: text, base: response.url || url }; }
}
async function _resolveApiRecipe(meta, mediaType, season, episode) {
  const recipe = NIAKVIO_PROVIDER_MODEL.apiRecipe;
  if (!recipe || typeof recipe !== "object") return [];
  const media = _mediaNamespace(mediaType);
  const bases = _uniq([
    recipe.base,
    NIAKVIO_PROVIDER_MODEL.fixedApi,
    NIAKVIO_PROVIDER_MODEL.officialApi,
    ..._runtimeBases()
  ]).filter(value => /^https?:/i.test(_text(value)));
  if (!bases.length) return [];
  const values = {
    query: _text(meta && meta.title),
    providerId: _text(meta && meta.tmdbId),
    tmdbId: _text(meta && meta.tmdbId),
    media,
    season,
    episode,
    source: null
  };

  if (recipe.directRoute) {
    const streams = [];
    const sources = Array.isArray(recipe.sources) && recipe.sources.length ? recipe.sources : [null];
    for (const base of bases.slice(0, 2)) {
      for (const source of sources.slice(0, 12)) {
        values.source = source;
        const url = _recipeUrl(recipe.directRoute, values, base);
        if (!url) continue;
        try {
          const payload = await _recipePayload(url, recipe, null);
          if (typeof payload.value === "string") {
            streams.push(..._streams(
              _extractUrls(payload.value, payload.base).filter(_directMedia),
              recipe.referer || base,
              Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
            ));
          } else {
            streams.push(..._streams(
              _sourceUrls(payload.value, payload.base),
              recipe.referer || base,
              Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
            ));
          }
        } catch (_) {}
        if (streams.length >= 20) break;
      }
      if (streams.length) break;
    }
    return streams.slice(0, 40);
  }

  if (!recipe.searchRoute) return [];
  let providerId = "";
  for (const base of bases.slice(0, 3)) {
    const url = _recipeUrl(recipe.searchRoute, values, base);
    if (!url) continue;
    try {
      const payload = await _recipePayload(url, recipe, null);
      if (!payload.value || typeof payload.value === "string") continue;
      const rows = _recipeObjects(payload.value, [])
        .map(row => ({ row, score: _recipeScore(row, meta, recipe, media) }))
        .filter(item => item.score > 0)
        .sort((a, b) => b.score - a.score);
      if (!rows.length) continue;
      providerId = _recipeValue(rows[0].row, recipe.idFields || ["id","_id","media_id","post_id"]);
      if (providerId) break;
    } catch (_) {}
  }
  if (!providerId) return [];
  values.providerId = providerId;
  const route = media === "movie" ? recipe.movieRoute : (recipe.episodeRoute || recipe.movieRoute);
  if (!route) return [];
  for (const base of bases.slice(0, 3)) {
    const url = _recipeUrl(route, values, base);
    if (!url) continue;
    try {
      const payload = await _recipePayload(url, recipe, null);
      if (typeof payload.value === "string") {
        const urls = _extractUrls(payload.value, payload.base).filter(_directMedia);
        if (urls.length) return _streams(
          urls,
          recipe.referer || base,
          Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
        );
      } else {
        const urls = _sourceUrls(payload.value, payload.base);
        if (urls.length) return _streams(
          urls,
          recipe.referer || base,
          Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
        );
      }
    } catch (_) {}
  }
  return [];
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

  // Declarative ProviderBase recipe: a clean reconstruction may need a bounded
  // search -> provider-id -> source chain. This remains data-driven and executes
  // no upstream JavaScript.
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) {
    const recipeMeta = await _tmdb(tmdbId, type) || {
      title: "",
      year: "",
      tmdbId: String(tmdbId || "")
    };
    const recipe = await _resolveApiRecipe(recipeMeta, type, season, episode);
    if (recipe.length) return recipe;
  }

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
/* NUVIO_TV_DIRECT_MEDIA_V2:be5c459312ae */
;(function(g,c){"use strict";
var ASSET=/\.(?:woff2?|ttf|otf|eot|css|js|mjs|map|png|jpe?g|gif|svg|ico|webmanifest|json|xml|vtt|srt)(?:[?#]|$)/i;
var DEMO=/(?:chrome\/static\/videos|sticky\/videos|static\/money|grok-|radar_promo|big[_-]?buck[_-]?bunny|sample[-_]?videos|test-videos)/i;
var SOCIAL=/(?:^|\.)(?:twitter\.com|x\.com|twimg\.com|google\.com|googleusercontent\.com|gitlab\.com|github\.com|facebook\.com|instagram\.com)$/i;
function s(v){return String(v==null?"":v).replace(/[\u200B-\u200D\uFEFF]/g,"").trim()}
function clean(v){return s(v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").replace(/\\u0026/gi,"&").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/")}
function abs(v,b){try{return new URL(clean(v),b).toString()}catch(_){return ""}}
function hostname(u){try{return new URL(u).hostname.toLowerCase()}catch(_){return ""}}
function origin(u){try{return new URL(u).origin}catch(_){return ""}}
function rejected(u){var h=hostname(u);if(!h||ASSET.test(u)||DEMO.test(u)||SOCIAL.test(h))return true;for(var i=0;i<c.blockedHosts.length;i++)if(h===c.blockedHosts[i]||h.endsWith("."+c.blockedHosts[i]))return true;return false}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function headers(base,ref,target){var out={};if(base&&typeof base==="object")Object.keys(base).forEach(function(k){out[k]=s(base[k])});if(ref&&!out.Referer&&!out.referer)out.Referer=ref;var o=origin(ref||target);if(o&&!out.Origin&&!out.origin)out.Origin=o;if(!out.Accept)out.Accept="*/*";return out}
function startsHls(text){return clean(text).trimStart().startsWith("#EXTM3U")}
function startsDash(text){return /<MPD[\s>]/i.test(clean(text).slice(0,4096))}
function bytesKind(bytes){if(!bytes||!bytes.length)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes.length>=4&&bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes.length>=188&&bytes[0]===71&&(bytes.length<376||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var out="";for(var i=0;i<Math.min(bytes.length,262144);i++)out+=String.fromCharCode(bytes[i]);return out}}
async function resource(u,h){try{var r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",buffer=await r.arrayBuffer(),bytes=new Uint8Array(buffer),text=decode(bytes.slice(0,262144));return{ok:!!r.ok,status:r.status,url:s(r.url||u),type:type,bytes:bytes,text:text}}catch(_){return null}}
function proof(r){if(!r)return null;if(startsHls(r.text))return"hls";if(startsDash(r.text)||/application\/dash\+xml/i.test(r.type))return"dash";var binary=bytesKind(r.bytes);if(binary)return binary;if(/^video\//i.test(r.type)&&!/^video\/(?:svg|x-font)/i.test(r.type))return"video";return null}
function unescapeJs(v){var raw=s(v),out="";for(var i=0;i<raw.length;i++){var ch=raw.charAt(i);if(ch!=="\\"||i+1>=raw.length){out+=ch;continue}var next=raw.charAt(++i),hex;if(next==="u"&&(hex=raw.slice(i+1,i+5)).length===4&&/^[0-9a-fA-F]{4}$/.test(hex)){out+=String.fromCharCode(parseInt(hex,16));i+=4;continue}if(next==="x"&&(hex=raw.slice(i+1,i+3)).length===2&&/^[0-9a-fA-F]{2}$/.test(hex)){out+=String.fromCharCode(parseInt(hex,16));i+=2;continue}if(/[0-7]/.test(next)){var oct=next;while(oct.length<3&&i+1<raw.length&&/[0-7]/.test(raw.charAt(i+1)))oct+=raw.charAt(++i);out+=String.fromCharCode(parseInt(oct,8));continue}if(next==="n"){out+="\n";continue}if(next==="r"){out+="\r";continue}if(next==="t"){out+="\t";continue}if(next==="b"){out+="\b";continue}if(next==="f"){out+="\f";continue}if(next==="v"){out+="\v";continue}out+=next}return out}
function unpack(source){var out=[],re=/eval\(function\(p,a,c,k,e,[rd]\)\{[\s\S]*?\}\(\s*['"]((?:\\.|[^'"\\])*)['"]\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*['"]((?:\\.|[^'"\\])*)['"]\.split\(['"]\|['"]\)/g,m;while((m=re.exec(s(source)))!==null){try{var payload=unescapeJs(m[1]),radix=parseInt(m[2],10),count=parseInt(m[3],10),words=unescapeJs(m[4]).split("|");function key(n){return n.toString(radix)}for(var i=count-1;i>=0;i--){if(!words[i])continue;var rx=new RegExp("\\b"+key(i)+"\\b","g");payload=payload.replace(rx,words[i])}out.push(payload)}catch(_){}}return out}
function base64(source){var out=[],re=/(?:atob|base64_decode)\(\s*['"]([A-Za-z0-9+/=]{16,})['"]\s*\)/gi,m;while((m=re.exec(s(source)))!==null){try{var value=typeof g.atob==="function"?g.atob(m[1]):"";if(value)out.push(value)}catch(_){}}return out}
function candidates(text,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;var low=u.toLowerCase();if(!/(?:\.m3u8|\.mp4|\.mkv|\.webm|\.mpd|\/hls\/|\/hls2\/|master\.m3u8|embed|player|watch|stream|video|\/e\/|\/v\/)/i.test(low))return;seen[u]=1;out.push(u)}function scan(body){body=clean(body);var patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-link|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mp4|mkv|webm|mpd|embed|player|watch|stream|\/e\/|\/v\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++)while((m=patterns[i].exec(body))!==null)add(m[1])}scan(text);unpack(text).forEach(scan);base64(text).forEach(scan);return out.slice(0,c.maxCandidates)}
function normalizeRows(value){if(Array.isArray(value))return value;if(value&&typeof value==="object"){var keys=["streams","results","data"];for(var i=0;i<keys.length;i++)if(Array.isArray(value[keys[i]]))return value[keys[i]]}return[]}
function normalizeRow(row){if(!row||typeof row!=="object")return null;var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u))return null;return Object.assign({},row,{url:u,headers:row.headers&&typeof row.headers==="object"?row.headers:{}})}
function compactRow(row,media){var subs=Array.isArray(row.subtitles)?row.subtitles.filter(function(x){return x&&x.url&&!rejected(x.url)}).slice(0,20):undefined;var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,240),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||row.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);if(row.size)out.size=s(row.size);if(subs&&subs.length)out.subtitles=subs;return out}
function unique(rows){var out=[],seen={};rows.forEach(function(row){if(!row||!row.url||seen[row.url])return;seen[row.url]=1;out.push(row)});return out}
async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var h=headers(baseHeaders,referer,u),r=await resource(u,h);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:h}];var type=s(r.type).toLowerCase();if(/text\/html|application\/xhtml|javascript|json|text\//i.test(type)||/[<>{}\[\]"']/.test(r.text)){var next=candidates(r.text,r.url||u),jobs=next.slice(0,c.maxCandidates).map(function(v){return resolve(v,h,r.url||u,depth+1,seen)}),groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}return[]}
async function invoke(old,self,args){var settings=g.SCRAPER_SETTINGS&&typeof g.SCRAPER_SETTINGS==="object"?g.SCRAPER_SETTINGS:{};var attempts=[function(){return old.call(self,args[0],args[1],args[2],args[3])},function(){return old.call(self,args[0],args[1],args[2],args[3],settings)},function(){return old.call(self,{tmdbId:args[0],mediaType:args[1],season:args[2],episode:args[3],settings:settings})}];for(var i=0;i<attempts.length;i++){try{var rows=normalizeRows(await attempts[i]());if(rows.length)return rows}catch(_){}}return[]}
async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);jobs.push(resolve(row.url,row.headers,ref,0,{}).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioTvDirectV2)return false;var old=obj[key],wrap=async function(tmdbId,mediaType,season,episode){return tvRows(old,this,arguments)};wrap.__nuvioTvDirectV2=true;obj[key]=wrap;return true}
var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerName":"Goated","maxDepth":4,"maxCandidates":10,"timeoutMs":12000,"blockedHosts":[]});