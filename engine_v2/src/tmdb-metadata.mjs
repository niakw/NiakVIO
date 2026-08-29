// Shared factual metadata resolver for Core presentation/catalogue matching.
// Credentials must be supplied by the caller or environment; never embed a
// third-party/public TMDB credential in repository source.
const TMDB_BASE = "https://api.themoviedb.org/3";

export function createTmdbMetadataResolver(options = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const accessToken = String(options.accessToken ?? process.env.TMDB_ACCESS_TOKEN ?? "").trim();
  const apiKey = String(options.apiKey ?? process.env.TMDB_API_KEY ?? "").trim();
  const language = String(options.language ?? "fr-FR").trim() || "fr-FR";
  const timeoutMs = Math.max(1000, Math.min(15000, Number(options.timeoutMs ?? 6000)));
  if (!accessToken && !apiKey) {
    throw new Error("TMDB credentials are required (TMDB_ACCESS_TOKEN or TMDB_API_KEY)");
  }

  return async function resolveTmdbMetadata(request = {}) {
    const tmdbId = String(request.tmdbId ?? "").trim();
    if (!/^\d+$/.test(tmdbId)) return requestFallback(request);
    const mediaType = normalizeMediaType(request.mediaType ?? request.type);
    const kind = mediaType === "movie" ? "movie" : "tv";
    const append = kind === "movie"
      ? "release_dates,alternative_titles,keywords"
      : "content_ratings,alternative_titles,keywords";
    const url = new URL(`${TMDB_BASE}/${kind}/${tmdbId}`);
    if (!accessToken) url.searchParams.set("api_key", apiKey);
    url.searchParams.set("language", language);
    url.searchParams.set("append_to_response", append);

    const headers = { Accept: "application/json" };
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
    const response = await fetchImpl(url, {
      headers,
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!response.ok) throw new Error(`TMDB HTTP ${response.status}`);
    const payload = await response.json();
    return normalizeTmdbPayload(payload, { mediaType, request });
  };
}

export function normalizeTmdbPayload(payload = {}, context = {}) {
  const mediaType = normalizeMediaType(context.mediaType ?? context.request?.mediaType);
  const movie = mediaType === "movie";
  const request = context.request ?? {};
  const releaseDate = clean(payload.release_date ?? payload.first_air_date);
  const runtime = movie
    ? positiveNumber(payload.runtime)
    : firstPositive(payload.episode_run_time) ?? positiveNumber(payload.runtime);
  const aliases = movie
    ? collectAlternativeTitles(payload.alternative_titles?.titles, "title")
    : collectAlternativeTitles(payload.alternative_titles?.results, "title");
  const title = clean(movie ? payload.title : payload.name) ?? clean(request.title);
  const originalTitle = clean(movie ? payload.original_title : payload.original_name);
  const certification = movie
    ? movieCertification(payload.release_dates?.results)
    : tvCertification(payload.content_ratings?.results);

  const resolvedMediaType = resolveCanonicalMediaType(mediaType, payload, request);

  return {
    tmdbId: String(payload.id ?? request.tmdbId ?? "").trim() || null,
    mediaType: resolvedMediaType,
    canonicalMediaType: resolvedMediaType,
    tmdbKind: movie ? "movie" : "tv",
    title,
    originalTitle,
    aliases: unique([title, originalTitle, ...aliases, clean(request.title)].filter(Boolean)),
    year: yearFromDate(releaseDate) ?? positiveInt(request.year),
    releaseDate,
    runtime,
    durationMinutes: runtime,
    certification,
    ageRating: certification,
    genres: Array.isArray(payload.genres)
      ? payload.genres.map((row) => ({ id: Number(row?.id) || null, name: clean(row?.name) })).filter((row) => row.id || row.name)
      : [],
    originalLanguage: clean(payload.original_language),
    originCountry: Array.isArray(payload.origin_country) ? payload.origin_country.map(clean).filter(Boolean) : [],
    animeEvidence: animeEvidence(payload),
    source: "tmdb",
  };
}

function keywordNames(payload = {}) {
  const raw = payload.keywords?.results ?? payload.keywords?.keywords ?? [];
  return Array.isArray(raw)
    ? raw.map((row) => clean(row?.name)?.toLowerCase()).filter(Boolean)
    : [];
}

export function animeEvidence(payload = {}) {
  const keywords = keywordNames(payload);
  const genres = Array.isArray(payload.genres) ? payload.genres : [];
  const animation = genres.some((row) => Number(row?.id) === 16 || clean(row?.name)?.toLowerCase() === "animation");
  const originalLanguage = clean(payload.original_language)?.toLowerCase();
  const originCountry = Array.isArray(payload.origin_country)
    ? payload.origin_country.map((value) => clean(value)?.toUpperCase()).filter(Boolean)
    : [];
  const productionCountries = Array.isArray(payload.production_countries)
    ? payload.production_countries.map((row) => clean(row?.iso_3166_1)?.toUpperCase()).filter(Boolean)
    : [];
  const keywordAnime = keywords.includes("anime");
  const japaneseOrigin = originalLanguage === "ja" || originCountry.includes("JP") || productionCountries.includes("JP");
  return {
    isAnime: keywordAnime || (animation && japaneseOrigin),
    keywordAnime,
    animation,
    japaneseOrigin,
  };
}

export function resolveCanonicalMediaType(inputType, payload = {}, request = {}) {
  const raw = String(inputType ?? request.mediaType ?? request.type ?? "movie").trim().toLowerCase();
  const category = String(request.category ?? "").trim().toLowerCase();
  if (category === "anime") return "anime";
  if (raw === "anime") return "anime";
  const aliased = ["series", "show", "other"].includes(raw) ? "tv" : raw;
  if (aliased === "tv" && animeEvidence(payload).isAnime) return "anime";
  return aliased === "movie" ? "movie" : "tv";
}

function requestFallback(request = {}) {
  const mediaType = resolveCanonicalMediaType(request.mediaType ?? request.type, {}, request);
  return {
    tmdbId: clean(request.tmdbId),
    mediaType,
    canonicalMediaType: mediaType,
    tmdbKind: mediaType === "movie" ? "movie" : "tv",
    title: clean(request.title),
    originalTitle: null,
    aliases: unique([clean(request.title)].filter(Boolean)),
    year: positiveInt(request.year),
    releaseDate: null,
    runtime: null,
    durationMinutes: null,
    certification: null,
    ageRating: null,
    genres: [],
    originalLanguage: null,
    originCountry: [],
    animeEvidence: { isAnime: mediaType === "anime", keywordAnime: false, animation: false, japaneseOrigin: false },
    source: "request",
  };
}

function movieCertification(results) {
  const rows = Array.isArray(results) ? results : [];
  const preferred = rows.find((row) => String(row?.iso_3166_1 ?? "").toUpperCase() === "FR")
    ?? rows.find((row) => String(row?.iso_3166_1 ?? "").toUpperCase() === "US")
    ?? rows[0];
  const dates = Array.isArray(preferred?.release_dates) ? preferred.release_dates : [];
  return clean(dates.map((row) => row?.certification).find((value) => clean(value)));
}

function tvCertification(results) {
  const rows = Array.isArray(results) ? results : [];
  const preferred = rows.find((row) => String(row?.iso_3166_1 ?? "").toUpperCase() === "FR")
    ?? rows.find((row) => String(row?.iso_3166_1 ?? "").toUpperCase() === "US")
    ?? rows[0];
  return clean(preferred?.rating);
}

function collectAlternativeTitles(rows, key) {
  if (!Array.isArray(rows)) return [];
  return rows.map((row) => clean(row?.[key])).filter(Boolean).slice(0, 20);
}

function normalizeMediaType(value) {
  const raw = String(value ?? "movie").trim().toLowerCase();
  if (raw === "movie") return "movie";
  if (raw === "anime") return "anime";
  if (["series", "show", "other", "tv"].includes(raw)) return "tv";
  return "tv";
}

function firstPositive(value) {
  if (!Array.isArray(value)) return null;
  for (const item of value) {
    const number = positiveNumber(item);
    if (number) return number;
  }
  return null;
}

function positiveNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? Math.round(number) : null;
}

function positiveInt(value) {
  const number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : null;
}

function yearFromDate(value) {
  const match = String(value ?? "").match(/(?:19|20)\d{2}/);
  return match ? Number(match[0]) : null;
}

function clean(value) {
  if (value == null) return null;
  const text = String(value).trim();
  return text || null;
}

function unique(values) {
  return [...new Set(values)];
}
