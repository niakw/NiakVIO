"use strict";

/* NIAKVIO_PROVIDER_BASE_OWNED_V2 */
const NIAKVIO_PROVIDER_MODEL = Object.freeze({"authoring":"niakvio-owned-v2","displayName":"Kehflix","fixedApi":null,"knownSite":"https://kehflix.com/","observedUrls":["https://kehflix.com/"],"officialApi":null,"officialHub":"https://kehflix.wiki/","officialSite":"https://kehflix.com/","origins":["https://kehflix.com","https://kehflix.wiki"],"providerId":"kehflix","reconstructionState":"learning-clean-seed","routes":[],"strategy":"html_scraper","supportedTypes":["movie","tv","anime"],"upstreamCodeEmbedded":false,"upstreamCodeExecuted":false});

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
function _directMedia(url) {
  return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/(?:hls|dash|stream)(?:\/|[?#]|$)/i.test(_text(url));
}
function _extractUrls(text, base) {
  const out = [];
  const patterns = [
    /(?:src|href|file|url)\s*[:=]\s*["']([^"'<>\s]+)["']/gi,
    /https?:\\?\/\\?\/[^"'<>\s]+/gi
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(text || ""))) {
      const raw = (match[1] || match[0] || "").replace(/\\\//g, "/").replace(/&amp;/g, "&");
      const absolute = _absolute(raw, base);
      if (absolute && /^https?:/i.test(absolute)) out.push(absolute);
      if (out.length >= 160) break;
    }
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
  const key = typeof globalThis !== "undefined" ? globalThis.TMDB_API_KEY : null;
  if (!key || !tmdbId) return null;
  const type = String(mediaType || "movie").toLowerCase() === "movie" ? "movie" : "tv";
  try {
    const response = await _fetch(
      "https://api.themoviedb.org/3/" + type + "/" + encodeURIComponent(tmdbId) +
      "?api_key=" + encodeURIComponent(key) + "&language=en-US"
    );
    const row = await response.json();
    return {
      title: row.title || row.name || row.original_title || row.original_name || "",
      year: String(row.release_date || row.first_air_date || "").slice(0, 4)
    };
  } catch (_) {
    return null;
  }
}
function _searchBases() {
  return _uniq([
    NIAKVIO_PROVIDER_MODEL.officialSite,
    NIAKVIO_PROVIDER_MODEL.knownSite,
    NIAKVIO_PROVIDER_MODEL.officialHub,
    ...(NIAKVIO_PROVIDER_MODEL.origins || [])
  ]).filter(value => /^https?:/i.test(value));
}
function _searchUrls(title) {
  const query = encodeURIComponent(title || "");
  const out = [];
  for (const base of _searchBases()) {
    out.push(_absolute("/?s=" + query, base));
    out.push(_absolute("/search?q=" + query, base));
    out.push(_absolute("/search/" + query, base));
  }
  return _uniq(out);
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
  for (const url of _apiUrls(tmdbId, mediaType, season, episode).slice(0, 12)) {
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
async function _resolveHtml(meta, mediaType, season, episode) {
  if (!meta || !meta.title) return [];
  const candidates = [];
  for (const searchUrl of _searchUrls(meta.title).slice(0, 9)) {
    try {
      const response = await _fetch(searchUrl);
      const html = await response.text();
      const urls = _extractUrls(html, response.url || searchUrl);
      candidates.push(...urls.filter(value => {
        const host = _origin(value);
        return host && _searchBases().some(base => _origin(base) === host);
      }));
    } catch (_) {}
    if (candidates.length) break;
  }
  const streams = [];
  for (const detailUrl of _uniq(candidates).slice(0, 8)) {
    try {
      const response = await _fetch(detailUrl);
      const html = await response.text();
      let urls = _extractUrls(html, response.url || detailUrl);
      if (mediaType !== "movie" && season != null && episode != null) {
        const token = new RegExp("(?:s(?:eason)?\\s*0*" + Number(season) + "[^\\n]{0,80}e(?:pisode)?\\s*0*" + Number(episode) + "|0*" + Number(season) + "x0*" + Number(episode) + ")", "i");
        const episodeLinks = urls.filter(value => token.test(value));
        if (episodeLinks.length) {
          for (const episodeUrl of episodeLinks.slice(0, 4)) {
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
        const embeds = urls.filter(value => /embed|player|watch|iframe/i.test(value));
        streams.push(..._streams(embeds, response.url || detailUrl));
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
  const strategy = NIAKVIO_PROVIDER_MODEL.strategy;
  if (/api_stream_resolver|direct_media/i.test(strategy)) {
    const api = await _resolveApi(tmdbId, type, season, episode);
    if (api.length) return api;
  }
  const meta = await _tmdb(tmdbId, type);
  const html = await _resolveHtml(meta, type, season, episode);
  if (html.length) return html;
  if (!/api_stream_resolver|direct_media/i.test(strategy)) {
    return _resolveApi(tmdbId, type, season, episode);
  }
  return [];
}
module.exports = { getStreams, __niakvioProviderBase: NIAKVIO_PROVIDER_MODEL };