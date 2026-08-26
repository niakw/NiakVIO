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
    const append = kind === "movie" ? "release_dates,alternative_titles" : "content_ratings,alternative_titles";
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

  return {
    tmdbId: String(payload.id ?? request.tmdbId ?? "").trim() || null,
    title,
    originalTitle,
    aliases: unique([title, originalTitle, ...aliases, clean(request.title)].filter(Boolean)),
    year: yearFromDate(releaseDate) ?? positiveInt(request.year),
    releaseDate,
    runtime,
    durationMinutes: runtime,
    certification,
    ageRating: certification,
    source: "tmdb",
  };
}

function requestFallback(request = {}) {
  return {
    tmdbId: clean(request.tmdbId),
    title: clean(request.title),
    originalTitle: null,
    aliases: unique([clean(request.title)].filter(Boolean)),
    year: positiveInt(request.year),
    releaseDate: null,
    runtime: null,
    durationMinutes: null,
    certification: null,
    ageRating: null,
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
  return raw === "movie" ? "movie" : "tv";
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
