/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
/* NIAKVIO_PROVIDER_BASE_AUTHORING:niakvio-owned-v3 */
"use strict";

function _uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}
function _origin(value) {
  try { return new URL(value).origin; } catch (_) { return ""; }
}
function _substituteDomain(raw) {
  const value = _text(raw).trim();
  if (!value) return value;
  try {
    const parsed = new URL(value);
    const mapping = NIAKVIO_PROVIDER_MODEL.domainSubstitutions &&
      typeof NIAKVIO_PROVIDER_MODEL.domainSubstitutions === "object"
      ? NIAKVIO_PROVIDER_MODEL.domainSubstitutions
      : {};
    const host = _text(parsed.hostname).toLowerCase();
    const target = _text(mapping[host]).toLowerCase();
    if (target) parsed.hostname = target;
    return parsed.toString();
  } catch (_) {
    return value;
  }
}
function _absolute(value, base) {
  try { return _substituteDomain(new URL(value, base).toString()); } catch (_) { return ""; }
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
    const host = _text(parsed.hostname).toLowerCase();
    // Shared download/intermediate hosts used by multiple catalogue providers.
    // They are resolver pages, not playable output, so the bounded crawler may
    // traverse them but _directMedia() must still prove the final stream.
    if (/(?:^|\.)(?:abhilinks\.(?:site|life)|vcloud\.zip|hubcloud\.[a-z0-9.-]+|driveseed\.[a-z0-9.-]+|hubdrive\.[a-z0-9.-]+|gdflix\.[a-z0-9.-]+)$/i.test(host)) {
      return true;
    }
    return /\/(?:watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|drive|download)(?:[/?#.-]|$)/i.test(parsed.pathname + parsed.search);
  } catch (_) {
    return false;
  }
}
async function _crawlDirectMedia(seedUrls, referer, maxDepth) {
  const queue = _uniq(seedUrls).filter(_playerLike).slice(0, 4).map(url => ({ url, depth: 0, referer }));
  const seen = new Set();
  const streams = [];
  let requests = 0;
  while (queue.length && requests < 7 && streams.length < 12) {
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
function _identityMode() {
  const raw = NIAKVIO_PROVIDER_MODEL && NIAKVIO_PROVIDER_MODEL.identityInput;
  return _text(raw && raw.mode || "tmdb_direct").toLowerCase();
}
function _identityUsesTmdbId() {
  return _identityMode() === "tmdb_direct";
}
function _expandLearnedRoute(pattern, meta, mediaType, season, episode, bases) {
  let route = _text(pattern);
  if (/\$\{|encodeURIComponent\s*\(/i.test(route)) return [];
  if (!route || /^https?:\/\//i.test(route) && !/\{[^}]+\}/.test(route)) {
    return /^https?:\/\//i.test(route) ? [route] : [];
  }
  const id = _text(meta && meta.tmdbId);
  const title = _text(meta && meta.title);
  const slug = _slug(title);
  const transport = mediaType === "movie" ? "movie" : "tv";
  route = route.replace(/\{tmdb_?id\}/gi, encodeURIComponent(id));
  // {id} has no universal meaning across providers. It can be a provider
  // catalogue/session/file/MAL id. Only the explicit tmdb_direct identity
  // contract permits using the incoming TMDB id as its implicit value.
  if (/\{id\}/i.test(route)) {
    if (!_identityUsesTmdbId()) return [];
    route = route.replace(/\{id\}/gi, encodeURIComponent(id));
  }
  route = route
    .replace(/\{slug\}/gi, encodeURIComponent(slug))
    .replace(/\{(?:title|query|q)\}/gi, encodeURIComponent(title))
    .replace(/\{(?:media|media_?type|type)\}/gi, encodeURIComponent(transport))
    .replace(/\{season\}/gi, encodeURIComponent(season == null ? "" : season))
    .replace(/\{episode\}/gi, encodeURIComponent(episode == null ? "" : episode));
  if (/\{[^}]+\}/.test(route)) return [];
  const out = [];
  for (const base of (bases || _runtimeBases())) {
    const absolute = _absolute(route, base);
    if (absolute) out.push(absolute);
  }
  return _uniq(out);
}
function _routeKind(route) {
  const value = _text(route).toLowerCase();
  if (!value || /\/(?:track|report|warm|dead|working|ad-link|fp)(?:[/?#]|$)/i.test(value)) return "ignore";
  // Search semantics are more specific than a generic /api prefix. A route
  // such as /api?m=search&q={query} must carry Core title metadata instead of
  // falling into _apiUrls(), where title is intentionally empty for ID routes.
  if (/\/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword)=/i.test(value)) return "search";
  if (/\/(?:api)(?:[./?#]|$)/i.test(value)) return "api";
  if (/\/(?:player|embed|play)(?:[/?#]|$)/i.test(value)) return "player";
  if (/\{(?:tmdb_?id|id|slug|title)\}/i.test(value) || /\/(?:title|movie|film|series|tv|show|watch|media)(?:[/?#]|$)/i.test(value)) return "detail";
  return "ignore";
}
function _learnedUrls(kind, meta, mediaType, season, episode) {
  const out = [];
  const bases = kind === "api" ? _apiBases() : _searchBases();
  for (const route of NIAKVIO_PROVIDER_MODEL.routes || []) {
    if (_routeKind(route) !== kind) continue;
    out.push(..._expandLearnedRoute(route, meta, mediaType, season, episode, bases));
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
    const alternativeRows = row.alternative_titles && (
      row.alternative_titles.titles || row.alternative_titles.results || row.alternative_titles
    );
    const aliases = _uniq([
      row.title,
      row.name,
      row.original_title,
      row.original_name,
      ...(Array.isArray(alternativeRows) ? alternativeRows.map(item => item && (item.title || item.name)) : [])
    ].map(_text).filter(Boolean));
    return {
      title: aliases[0] || "",
      aliases,
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
function _searchBases() {
  return _uniq([
    NIAKVIO_PROVIDER_MODEL.officialSite,
    NIAKVIO_PROVIDER_MODEL.knownSite,
    NIAKVIO_PROVIDER_MODEL.officialHub
  ].map(_substituteDomain)).filter(value => /^https?:/i.test(value));
}
function _apiBases() {
  return _uniq([
    NIAKVIO_PROVIDER_MODEL.fixedApi,
    NIAKVIO_PROVIDER_MODEL.officialApi,
    NIAKVIO_PROVIDER_MODEL.officialSite,
    NIAKVIO_PROVIDER_MODEL.knownSite
  ].map(_substituteDomain)).filter(value => /^https?:/i.test(value));
}
function _runtimeBases() {
  return _uniq([..._searchBases(), ..._apiBases()]);
}
function _searchUrls(meta, mediaType, season, episode) {
  return _learnedUrls("search", meta, mediaType, season, episode);
}
function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
  return (NIAKVIO_PROVIDER_MODEL.routes || []).some(route => ["search","detail","player","api"].includes(_routeKind(route)));
}
function _apiUrls(tmdbId, mediaType, season, episode) {
  const bases = _apiBases();
  const out = [];
  // Route DATA is executable knowledge. API-family providers commonly persist
  // only a relative route plus one trusted origin; consume that plan directly
  // instead of requiring an observed full endpoint URL.
  out.push(..._learnedUrls(
    "api",
    { tmdbId: _text(tmdbId), title: "" },
    mediaType,
    season,
    episode
  ));
  // A bare API origin is not an executable request plan. The legacy fallback
  // that appended ?tmdbId=... is valid only for providers explicitly classified
  // tmdb_direct; catalogue providers must execute an observed route/search chain.
  if (!_identityUsesTmdbId()) return _uniq(out);
  for (const base of bases) {
    if (!/^https?:/i.test(base)) continue;
    let url = base
      .replace(/\{tmdb_?id\}/gi, encodeURIComponent(tmdbId || ""))
      .replace(/\{id\}/gi, encodeURIComponent(tmdbId || ""))
      .replace(/\{(?:media_?type|type)\}/gi, encodeURIComponent(mediaType || "movie"))
      .replace(/\{season\}/gi, encodeURIComponent(season == null ? "" : season))
      .replace(/\{episode\}/gi, encodeURIComponent(episode == null ? "" : episode));
    out.push(url);
    try {
      const parsed = new URL(url);
      if (!parsed.search) {
        const params = [
          ["tmdbId", tmdbId || ""],
          ["type", mediaType || "movie"]
        ];
        if (season != null) params.push(["season", String(season)]);
        if (episode != null) params.push(["episode", String(episode)]);
        out.push(parsed.origin + parsed.pathname + "?" + params
          .map(pair => encodeURIComponent(pair[0]) + "=" + encodeURIComponent(pair[1]))
          .join("&") + (parsed.hash || ""));
      }
    } catch (_) {}
  }
  return _uniq(out);
}
function _directPlayerUrls(tmdbId, mediaType) {
  if (!tmdbId || !_identityUsesTmdbId()) return [];
  const hasPlayerRoute = (NIAKVIO_PROVIDER_MODEL.routes || []).some(route =>
    /^\/player(?:[?#]|$)/i.test(_text(route))
  );
  if (!hasPlayerRoute) return [];
  const transportType = _mediaNamespace(mediaType);
  const out = [];
  for (const base of _searchBases()) {
    try {
      const parsed = new URL("/player", base);
      out.push(
        parsed.origin + parsed.pathname
        + "?m=" + encodeURIComponent(transportType)
        + "&id=" + encodeURIComponent(_text(tmdbId))
      );
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
    const query = [];
    for (const key of keys) {
      const lower = key.toLowerCase();
      let value = player.searchParams.get(key);
      if (value == null && lower === "id" && _identityUsesTmdbId()) value = _text(tmdbId);
      if (value == null && /^(?:m|media|type)$/.test(lower)) value = desiredMedia;
      if (value == null && /^(?:season|s)$/.test(lower) && season != null) value = _text(season);
      if (value == null && /^(?:episode|e)$/.test(lower) && episode != null) value = _text(episode);
      if (value == null || value === "") { missing = true; break; }
      query.push(encodeURIComponent(key) + "=" + encodeURIComponent(_text(value)));
    }
    if (!missing) {
      const targetUrl = target.origin + target.pathname + (query.length ? "?" + query.join("&") : "");
      out.push({ url: targetUrl, referer: player.toString() });
    }
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
function _rewriteOutputUrl(raw) {
  const value = _substituteDomain(_text(raw).trim());
  if (!/^https?:\/\//i.test(value)) return value;
  try {
    const parsed = new URL(value);
    const host = _text(parsed.hostname).toLowerCase();
    for (const rule of NIAKVIO_PROVIDER_MODEL.outputUrlHostRewrites || []) {
      const fromHost = _text(rule && rule.fromHost).toLowerCase();
      const toHost = _text(rule && rule.toHost).toLowerCase();
      if (!fromHost || !toHost || host !== fromHost) continue;
      parsed.hostname = toHost;
      return parsed.toString();
    }
  } catch (_) {}
  return value;
}
function _outputLanguage(url) {
  try {
    const host = new URL(_text(url)).hostname.toLowerCase();
    for (const rule of NIAKVIO_PROVIDER_MODEL.outputLanguageRules || []) {
      const prefix = _text(rule && rule.hostPrefix).toLowerCase();
      const language = _text(rule && rule.language).toLowerCase();
      if (prefix && language && host.startsWith(prefix)) return language;
    }
  } catch (_) {}
  return "";
}
function _streams(urls, referer, extraHeaders) {
  const headers = Object.assign({}, extraHeaders || {});
  if (referer) headers.Referer = referer;
  const hasHeaders = Object.keys(headers).length > 0;
  return _uniq(urls)
    .map(_rewriteOutputUrl)
    .filter(Boolean)
    .filter((url, index, list) => list.indexOf(url) === index)
    .slice(0, 40)
    .map((url, index) => {
      const language = _outputLanguage(url);
      return {
        name: NIAKVIO_PROVIDER_MODEL.displayName,
        title: NIAKVIO_PROVIDER_MODEL.displayName + (index ? " #" + (index + 1) : ""),
        url,
        language: language || undefined,
        headers: hasHeaders ? Object.assign({}, headers) : undefined
      };
    });
}
function _recipeValue(row, fields) {
  if (!row || typeof row !== "object") return "";
  for (const field of fields || []) {
    const value = row[field];
    if (value != null && value !== "") return _text(value);
  }
  return "";
}
function _collectionMediaType(key) {
  const value = _text(key).toLowerCase().replace(/[^a-z0-9]+/g, "");
  if (["movie","movies","film","films"].includes(value)) return "movie";
  if (["tv","tvs","series","show","shows","anime","animes","episode","episodes"].includes(value)) return "tv";
  return "";
}
function _recipeObjects(value, out, inheritedMedia) {
  out = out || [];
  inheritedMedia = inheritedMedia || "";
  if (Array.isArray(value)) {
    for (const child of value) _recipeObjects(child, out, inheritedMedia);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  if (inheritedMedia && !value.__nuvioCollectionMediaType) {
    out.push(Object.assign({ __nuvioCollectionMediaType: inheritedMedia }, value));
  } else {
    out.push(value);
  }
  for (const [key, child] of Object.entries(value)) {
    if (child && typeof child === "object") {
      _recipeObjects(child, out, _collectionMediaType(key) || inheritedMedia);
    }
    if (out.length >= 400) break;
  }
  return out;
}
function _recipeMediaType(row, recipe) {
  const raw = _recipeValue(row, recipe.typeFields || ["type","media_type","mediaType","kind","category"]).toLowerCase();
  if (raw) {
    if (["tv","series","show","anime","episode"].includes(raw)) return "tv";
    if (["movie","film"].includes(raw)) return "movie";
  }
  const inherited = _text(row && row.__nuvioCollectionMediaType).toLowerCase();
  return inherited === "movie" || inherited === "tv" ? inherited : "";
}
function _recipeScore(row, meta, recipe, expectedMedia) {
  const title = _slug(_recipeValue(row, recipe.titleFields || ["title","name","post_title","original_title"]));
  const expectedTitles = _uniq([meta && meta.title, ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])])
    .map(_slug).filter(Boolean);
  const expected = expectedTitles[0] || "";
  const actualMedia = _recipeMediaType(row, recipe);
  const year = _recipeValue(row, recipe.yearFields || ["year","release_date","first_air_date"]).slice(0, 4);
  const expectedYear = _text(meta && meta.year).slice(0, 4);
  const providerId = _recipeValue(row, recipe.idFields || ["id","_id","media_id","post_id"]);

  if (recipe.strictIdentity) {
    if (!providerId || !title || !expectedTitles.length || !expectedTitles.includes(title)) return -1;
    if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
    if (recipe.requireProviderTypeEvidence === true && (!actualMedia || !expectedMedia)) return -1;
    if (expectedYear) {
      if (!year || !/^\d{4}$/.test(year)) return -1;
      if (Math.abs(Number(year) - Number(expectedYear)) > 1) return -1;
    }
    return 100 + (year === expectedYear ? 20 : 10) + 20;
  }

  if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
  if (year && expectedYear && year !== expectedYear) return -1;
  let score = 0;
  if (title && expected && title === expected) score += 200;
  else if (title && expected && (title.includes(expected) || expected.includes(title))) score += 90;
  if (title && expected) {
    for (const token of expected.split("-").filter(value => value.length >= 3)) {
      if (title.includes(token)) score += 10;
    }
  }
  if (year && expectedYear && year === expectedYear) score += 40;
  if (actualMedia && expectedMedia && actualMedia === expectedMedia) score += 60;
  if (providerId) score += 15;
  return score;
}
function _recipeSourceUrls(value, base, recipe) {
  const urls = _sourceUrls(value, base);
  if (!recipe || !recipe.directSourcesOnly) return urls;
  return urls.filter(_directMedia);
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
  try {
    if (/^https?:\/\//i.test(route)) {
      url = new URL(route).toString();
    } else {
      const parsedBase = new URL(_text(base).trim());
      const basePath = _text(parsedBase.pathname || "").replace(/\/+$/, "");
      const prefix = parsedBase.origin + (basePath && basePath !== "/" ? basePath : "");
      url = prefix + "/" + route.replace(/^\/+/, "");
    }
  } catch (_) { return ""; }
  // NuvioTV's QuickJS URL polyfill does not synchronize URL.href after
  // searchParams mutations. Rebuild the query explicitly instead of relying
  // on mutating searchParams before toString().
  try {
    const parsed = new URL(url);
    const remove = new Set(
      ["season","episode","source"].filter(key => values[key] == null || values[key] === "")
    );
    if (!remove.size) return parsed.toString();
    const query = _text(parsed.search || "").replace(/^\?/, "");
    const kept = query ? query.split("&").filter(part => {
      const rawKey = part.split("=", 1)[0] || "";
      let key = rawKey;
      try { key = decodeURIComponent(rawKey); } catch (_) {}
      return !remove.has(_text(key).toLowerCase());
    }) : [];
    return parsed.origin + parsed.pathname + (kept.length ? "?" + kept.join("&") : "") + _text(parsed.hash || "");
  } catch (_) {
    return url;
  }
}
async function _recipePayload(url, recipe, body) {
  const headers = Object.assign({}, recipe.requestHeaders || {});
  if (recipe.referer) headers.Referer = recipe.referer;
  if (recipe.origin) headers.Origin = recipe.origin;
  const options = { headers };
  const requestTimeoutMs = Math.max(0, Number(recipe.requestTimeoutMs || 0) || 0);
  if (requestTimeoutMs > 0) {
    try {
      let timeoutMs = requestTimeoutMs;
      const deadline = Number(globalThis && globalThis.__nuvioProviderDeadlineMs);
      if (Number.isFinite(deadline) && deadline > 0) timeoutMs = Math.max(1, Math.min(timeoutMs, deadline - Date.now()));
      if (typeof AbortSignal !== "undefined" && AbortSignal.timeout) options.signal = AbortSignal.timeout(timeoutMs);
    } catch (_) {}
  }
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
function _recipeField(value,path){var cur=value;for(const part of _text(path).split(".").filter(Boolean)){if(!cur||typeof cur!=="object")return"";cur=cur[part]}return _text(cur)}
function _recipeStatusBase(domain,recipe){
  let raw=_text(domain).replace(/^https?:\/\//i,"").replace(/\/+$/,"");
  if(!raw)return"";
  let host=raw.split("/")[0];
  const prefix=_text(recipe.statusApiPrefix);
  if(prefix&&host.toLowerCase().indexOf(prefix.toLowerCase())!==0)host=prefix+host;
  const suffix=_text(recipe.statusApiSuffix);
  return "https://"+host+(suffix?(suffix.charAt(0)==="/"?suffix:"/"+suffix):"");
}
function _recipeStaticBases(recipe){
  const explicitFallbackBases=Array.isArray(recipe.fallbackBases)?recipe.fallbackBases:[];
  const modelFallbackBases=recipe.allowModelBases===true
    ? [NIAKVIO_PROVIDER_MODEL.fixedApi,NIAKVIO_PROVIDER_MODEL.officialApi,..._runtimeBases()]
    : [];
  return _uniq([
    recipe.base,
    ...explicitFallbackBases,
    ...modelFallbackBases
  ]).filter(value=>/^https?:/i.test(_text(value)));
}
async function _recipeStatusDynamicBase(recipe){
  if(!/^https?:\/\//i.test(_text(recipe.statusUrl))||!recipe.statusDomainField)return"";
  try{
    const statusOptions={headers:{Accept:"application/json,text/plain,*/*"}};
    try{
      const requestTimeoutMs=Math.max(0,Number(recipe.requestTimeoutMs||0)||0);
      if(requestTimeoutMs>0&&typeof AbortSignal!=="undefined"&&AbortSignal.timeout)statusOptions.signal=AbortSignal.timeout(requestTimeoutMs);
    }catch(_){}
    const response=await _fetch(_text(recipe.statusUrl),statusOptions);
    let value=null;
    const type=_text(response.headers&&response.headers.get?response.headers.get("content-type"):"").toLowerCase();
    if(type.includes("json"))value=await response.json();
    else{
      const body=await response.text();
      try{value=JSON.parse(body)}catch(_){value=null}
    }
    return _recipeStatusBase(_recipeField(value,recipe.statusDomainField),recipe);
  }catch(_){return""}
}
async function _recipeBases(recipe){
  return _recipeStaticBases(recipe);
}
async function _resolveApiRecipe(meta, mediaType, season, episode) {
  const recipe = NIAKVIO_PROVIDER_MODEL.apiRecipe;
  if (!recipe || typeof recipe !== "object") return [];
  const media = _mediaNamespace(mediaType);
  const bases = await _recipeBases(recipe);
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
    const sources = Array.isArray(recipe.sources) && recipe.sources.length ? recipe.sources.slice(0, 12) : [null];
    const batchSize = Math.max(1, Math.min(Number(recipe.sourceBatchSize || 4) || 4, 6));
    const minStreamsBeforeStop = Math.max(1, Math.min(Number(recipe.minStreamsBeforeStop || 1) || 1, 20));
    for (const base of bases.slice(0, 2)) {
      for (let offset = 0; offset < sources.length; offset += batchSize) {
        const batch = sources.slice(offset, offset + batchSize);
        const batchRows = await Promise.all(batch.map(async source => {
          const localValues = Object.assign({}, values, { source });
          const url = _recipeUrl(recipe.directRoute, localValues, base);
          if (!url) return [];
          try {
            const payload = await _recipePayload(url, recipe, null);
            if (typeof payload.value === "string") {
              return _streams(
                _extractUrls(payload.value, payload.base).filter(_directMedia),
                recipe.referer || base,
                Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
              );
            }
            return _streams(
              _recipeSourceUrls(payload.value, payload.base, recipe),
              recipe.referer || base,
              Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
            );
          } catch (_) {
            return [];
          }
        }));
        for (const rows of batchRows) streams.push(...rows);
        if (streams.length >= minStreamsBeforeStop) break;
      }
      if (streams.length) break;
    }
    return streams.slice(0, 40);
  }

  if (!recipe.searchRoute) return [];
  const searchQueries = _uniq([
    meta && meta.title,
    ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])
  ].map(_text).filter(Boolean)).slice(0, 3);

  let statusFallbackBlocked = false;
  async function findProvider(baseList) {
    const blockedBases = new Set();
    const skipStatuses = new Set(
      (Array.isArray(recipe.skipStatusOnHttpStatuses) ? recipe.skipStatusOnHttpStatuses : [])
        .map(value => Number(value))
        .filter(value => Number.isFinite(value))
    );
    const candidates = baseList.slice(0, 3);
    for (const query of searchQueries) {
      values.query = query;
      for (const base of candidates) {
        if (blockedBases.has(base)) continue;
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
          const id = _recipeValue(rows[0].row, recipe.idFields || ["id","_id","media_id","post_id"]);
          if (id) return { id, base };
        } catch (error) {
          const match = _text(error && error.message).match(/provider_http_(\d+)/i);
          const status = match ? Number(match[1]) : 0;
          if (status && skipStatuses.has(status)) blockedBases.add(base);
        }
      }
    }
    if (candidates.length && candidates.every(base => blockedBases.has(base))) statusFallbackBlocked = true;
    return null;
  }

  let providerMatch = await findProvider(bases);
  let dynamicStatusBase = "";
  if (!providerMatch && !statusFallbackBlocked) {
    dynamicStatusBase = await _recipeStatusDynamicBase(recipe);
    if (dynamicStatusBase && !bases.includes(dynamicStatusBase)) {
      providerMatch = await findProvider([dynamicStatusBase]);
    }
  }
  if (!providerMatch) return [];

  values.providerId = providerMatch.id;
  const route = media === "movie" ? recipe.movieRoute : (recipe.episodeRoute || recipe.movieRoute);
  if (!route) return [];

  async function resolveRoute(baseList) {
    for (const base of baseList.slice(0, 3)) {
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
          const urls = _recipeSourceUrls(payload.value, payload.base, recipe);
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

  const routeBases = _uniq([providerMatch.base, ...bases]);
  let resolved = await resolveRoute(routeBases);
  if (resolved.length) return resolved;

  if (!dynamicStatusBase) dynamicStatusBase = await _recipeStatusDynamicBase(recipe);
  if (dynamicStatusBase && !routeBases.includes(dynamicStatusBase)) {
    resolved = await resolveRoute([dynamicStatusBase]);
    if (resolved.length) return resolved;
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
function _htmlVisibleText(value) {
  const source = _text(value);
  const lower = source.toLowerCase();
  let out = "";
  let cursor = 0;
  let hidden = "";
  while (cursor < source.length) {
    if (hidden) {
      const closeAt = lower.indexOf("</" + hidden, cursor);
      if (closeAt < 0) break;
      cursor = closeAt;
      hidden = "";
      continue;
    }
    if (source.charAt(cursor) !== "<") {
      out += source.charAt(cursor);
      cursor += 1;
      continue;
    }
    const end = source.indexOf(">", cursor + 1);
    if (end < 0) {
      out += source.slice(cursor);
      break;
    }
    let raw = source.slice(cursor + 1, end).trim();
    let closing = raw.charAt(0) === "/";
    if (closing) raw = raw.slice(1).trim();
    let name = "";
    for (let i = 0; i < raw.length; i += 1) {
      const code = raw.charCodeAt(i);
      const alpha = (code >= 65 && code <= 90) || (code >= 97 && code <= 122);
      if (!alpha) break;
      name += raw.charAt(i).toLowerCase();
    }
    if (!closing && (name === "script" || name === "style")) hidden = name;
    out += " ";
    cursor = end + 1;
  }
  return out;
}
function _strictHtmlIdentityOk(html, meta) {
  if (!NIAKVIO_PROVIDER_MODEL.strictHtmlIdentity) return true;
  if (!meta || !meta.title) return false;
  const visible = _htmlVisibleText(html);
  const normalized = _slug(visible);
  const titles = _uniq([meta.title, ...((Array.isArray(meta.aliases) ? meta.aliases : []))])
    .map(_slug)
    .filter(Boolean);
  if (!titles.length || !titles.some(title => normalized.includes(title))) return false;
  const year = _text(meta.year).slice(0, 4);
  if (year && /^\d{4}$/.test(year)) {
    const years = _text(html).match(/\b(?:19|20)\d{2}\b/g) || [];
    if (years.length && !years.includes(year)) return false;
  }
  return true;
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
      if (!_strictHtmlIdentityOk(html, meta)) continue;
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
      if (!direct.length && /iframe|mixed_embed|html_scraper|direct_media/i.test(NIAKVIO_PROVIDER_MODEL.strategy)) {
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
              2
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
      !(type === "tv" && NIAKVIO_PROVIDER_MODEL.supportedTypes.includes("anime"))) {
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
    if (NIAKVIO_PROVIDER_MODEL.apiRecipe.allowGenericFallback !== true) return [];
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
module.exports = {
  getStreams,
  get __niakvioProviderBase(){ return NIAKVIO_PROVIDER_MODEL; }
};
