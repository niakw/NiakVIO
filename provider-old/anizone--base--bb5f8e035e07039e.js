"use strict";

/*
 * NiakVIO ProviderBase: AniZone
 * Reconstructed from observed routes and response shapes. External provider code is
 * never copied into ProviderBase; upstream repositories are knowledge sources only.
 */
const cheerio = require("cheerio-without-node-native");

const PROVIDER_ID = "anizone";
const BASE_URL = "https://anizone.to";
const MAPPING_URL = "https://id-mapping-api-malid.hf.space/api/resolve";
const JIKAN_URL = "https://api.jikan.moe/v4/anime";
const HEADERS = Object.freeze({
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
  "Referer": BASE_URL + "/"
});

function runtimeTmdbKey() {
  try {
    return String(globalThis.TMDB_API_KEY || "").trim();
  } catch (_error) {
    return "";
  }
}

function normalizeTitle(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function absoluteUrl(value, base = BASE_URL) {
  try {
    return new URL(String(value || ""), base).href;
  } catch (_error) {
    return "";
  }
}

async function fetchText(url, options = {}) {
  const target = absoluteUrl(url);
  if (!target) return "";
  try {
    const response = await fetch(target, {
      ...options,
      headers: {...HEADERS, ...(options.headers || {})}
    });
    return response && response.ok ? await response.text() : "";
  } catch (_error) {
    return "";
  }
}

async function fetchJson(url, options = {}) {
  const target = absoluteUrl(url, BASE_URL);
  if (!target) return null;
  try {
    const response = await fetch(target, options);
    return response && response.ok ? await response.json() : null;
  } catch (_error) {
    return null;
  }
}

async function tmdbJson(path) {
  const key = runtimeTmdbKey();
  if (!key) return null;
  const separator = path.includes("?") ? "&" : "?";
  return fetchJson(
    "https://api.themoviedb.org/3/" + path + separator + "api_key=" + encodeURIComponent(key),
    {headers: HEADERS}
  );
}

async function resolveAnimeIdentity(tmdbId, season, episode) {
  const episodic = Number(season) > 0 && Number(episode) > 0;
  if (!episodic) {
    const movie = await tmdbJson("movie/" + encodeURIComponent(tmdbId));
    if (!movie) return null;
    const title = movie.title || movie.original_title || "";
    return title ? {title, mappedEpisode: 1, season: 0} : null;
  }

  const external = await tmdbJson("tv/" + encodeURIComponent(tmdbId) + "/external_ids");
  const imdbId = external && String(external.imdb_id || "").trim();
  if (!imdbId) return null;

  const mapping = await fetchJson(
    MAPPING_URL +
      "?id=" + encodeURIComponent(imdbId) +
      "&s=" + encodeURIComponent(season) +
      "&e=" + encodeURIComponent(episode)
  );
  const malId = mapping && Number(mapping.mal_id);
  if (!malId) return null;

  const jikan = await fetchJson(JIKAN_URL + "/" + encodeURIComponent(malId));
  const title =
    (jikan && jikan.data && (jikan.data.title_english || jikan.data.title || jikan.data.title_japanese)) ||
    String(mapping.anime_title || "").trim();
  if (!title) return null;
  return {
    title,
    searchTitle: String(mapping.anime_title || title).split(":")[0].trim(),
    mappedEpisode: Number(mapping.mal_episode || episode) || Number(episode) || 1,
    season: Number(season) || 1
  };
}

function extractCards($) {
  const cards = [];
  $('a[href*="/anime/"]').each((_index, element) => {
    const link = $(element);
    const href = String(link.attr("href") || "").trim();
    const resolved = absoluteUrl(href);
    if (!resolved) return;
    let parsed;
    try {
      parsed = new URL(resolved);
    } catch (_error) {
      return;
    }
    if (parsed.hostname !== new URL(BASE_URL).hostname || !parsed.pathname.startsWith("/anime/")) return;
    const slug = parsed.pathname.split("/").filter(Boolean)[1] || "";
    if (!slug) return;
    const container = link.closest("article,li,div");
    const texts = [
      link.attr("title"),
      link.attr("aria-label"),
      link.text(),
      container.find("h1,h2,h3,h4,.title,[class*='title']").first().text(),
      container.text()
    ].map(value => String(value || "").trim()).filter(Boolean);
    cards.push({slug, titles: [...new Set(texts)]});
  });
  return cards;
}

function seasonMatches(text, season) {
  const normalized = normalizeTitle(text);
  if (!season || season <= 1) {
    return !/\b(?:season|saison)\s*(?:2|3|4|5|6|7|8|9)\b/i.test(text);
  }
  const number = String(season);
  return new RegExp("\\b(?:season|saison)\\s*" + number + "\\b", "i").test(text) ||
    new RegExp("\\bs" + number.padStart(2, "0") + "\\b", "i").test(normalized);
}

function chooseCard(cards, title, season) {
  const target = normalizeTitle(String(title || "").split(":")[0]);
  if (!target) return null;
  let best = null;
  let bestScore = -1;
  for (const card of cards) {
    for (const candidate of card.titles) {
      const normalized = normalizeTitle(candidate);
      if (!normalized) continue;
      let score = 0;
      if (normalized === target) score = 100;
      else if (normalized.includes(target) || target.includes(normalized)) score = 70;
      else {
        const wanted = new Set(target.split(" ").filter(Boolean));
        const have = new Set(normalized.split(" ").filter(Boolean));
        let overlap = 0;
        for (const token of wanted) if (have.has(token)) overlap += 1;
        score = wanted.size ? Math.round((overlap / wanted.size) * 50) : 0;
      }
      if (!seasonMatches(candidate, season)) score -= 40;
      if (score > bestScore) {
        bestScore = score;
        best = card;
      }
    }
  }
  return bestScore >= 35 ? best : null;
}

function extractMasterUrl($, html) {
  const direct = absoluteUrl($("media-player").first().attr("src"));
  if (direct && /\.m3u8(?:[?#]|$)/i.test(direct)) return direct;
  const matches = String(html || "").match(/https:\/\/[^"'<>\\\s]+\.m3u8(?:\?[^"'<>\\\s]*)?/i);
  return matches ? absoluteUrl(matches[0]) : "";
}

function extractSubtitles($) {
  const subtitles = [];
  $("track").each((_index, element) => {
    const row = $(element);
    const kind = String(row.attr("kind") || "").toLowerCase();
    const src = absoluteUrl(row.attr("src"));
    if (!src || !["subtitles", "captions"].includes(kind)) return;
    subtitles.push({
      url: src,
      name: String(row.attr("label") || "Subtitle").trim(),
      language: String(row.attr("srclang") || "").trim() || "und"
    });
  });
  return subtitles;
}

function audioLabel($) {
  const text = $("button").map((_index, element) => $(element).text()).get().join(" ");
  const japanese = /\bJapanese\b/i.test(text);
  const english = /\bEnglish\b/i.test(text);
  if (japanese && english) return "MULTI";
  if (english) return "EN";
  if (japanese) return "JA";
  return "VO";
}

async function getStreams(tmdbId, mediaType, season, episode) {
  try {
    if (!tmdbId || !["anime", "tv", "movie"].includes(String(mediaType || "").toLowerCase())) return [];
    const identity = await resolveAnimeIdentity(tmdbId, season, episode);
    if (!identity) return [];

    const query = identity.searchTitle || String(identity.title).split(":")[0].trim();
    const searchHtml = await fetchText("/anime?search=" + encodeURIComponent(query));
    if (!searchHtml) return [];
    const $search = cheerio.load(searchHtml);
    const card = chooseCard(extractCards($search), identity.title, identity.season);
    if (!card) return [];

    const episodeUrl = "/anime/" + encodeURIComponent(card.slug) + "/" + encodeURIComponent(identity.mappedEpisode);
    const episodeHtml = await fetchText(episodeUrl);
    if (!episodeHtml) return [];
    const $episode = cheerio.load(episodeHtml);
    const masterUrl = extractMasterUrl($episode, episodeHtml);
    if (!masterUrl) return [];

    return [{
      name: "AniZone",
      title: String(identity.title) + " - Episode " + String(identity.mappedEpisode),
      url: masterUrl,
      quality: "Unknown",
      language: audioLabel($episode),
      headers: HEADERS,
      subtitles: extractSubtitles($episode),
      format: "HLS"
    }];
  } catch (_error) {
    return [];
  }
}

module.exports = {
  getStreams,
  __niakvioProviderBase: Object.freeze({
    providerId: PROVIDER_ID,
    knownSite: BASE_URL,
    supportedTypes: Object.freeze(["anime"]),
    reconstructionState: "niakvio-clean"
  })
};
