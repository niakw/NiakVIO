export const DEVICES = Object.freeze(["worker", "mobile", "desktop", "tv"]);
export const CANONICAL_MEDIA_TYPES = Object.freeze(["movie", "tv", "anime"]);

const SERIES_ALIASES = new Set(["series", "show", "other"]);

// External/client-facing requests remain tolerant because official Nuvio clients
// may surface aliases such as "series". NiakVIO normalizes those at the boundary.
export function normalizeMediaType(value) {
  const raw = String(value ?? "").trim().toLowerCase();
  if (!raw) throw new Error("mediaType is required");
  if (SERIES_ALIASES.has(raw)) return "tv";
  if (CANONICAL_MEDIA_TYPES.includes(raw)) return raw;
  throw new Error(`unsupported mediaType: ${raw}`);
}

// Provider manifests/specs are stricter than request inputs: one global vocabulary
// prevents divergent publication contracts and ambiguous lab coverage.
export function normalizeProviderMediaType(value) {
  const raw = String(value ?? "").trim().toLowerCase();
  if (!CANONICAL_MEDIA_TYPES.includes(raw)) {
    throw new Error(`provider media type must be canonical (${CANONICAL_MEDIA_TYPES.join("|")}): ${raw || "<empty>"}`);
  }
  return raw;
}

export function normalizeResolveRequest(input = {}) {
  const mediaType = normalizeMediaType(input.mediaType ?? input.type ?? input.category);
  const tmdbId = input.tmdbId == null ? null : String(input.tmdbId).trim();
  const title = input.title == null ? null : String(input.title).trim();
  const device = input.device == null ? "worker" : String(input.device).trim().toLowerCase();
  if (!DEVICES.includes(device)) throw new Error(`unsupported device: ${device}`);
  if (!tmdbId && !title) throw new Error("tmdbId or title is required");

  const season = toPositiveIntOrNull(input.season);
  const episode = toPositiveIntOrNull(input.episode);
  if ((mediaType === "tv" || mediaType === "anime") && (season == null || episode == null)) {
    throw new Error(`${mediaType} requests require season and episode`);
  }

  return {
    tmdbId,
    mediaType,
    title,
    year: toPositiveIntOrNull(input.year),
    season,
    episode,
    languages: normalizeStringList(input.languages ?? input.language),
    device,
    settings: isPlainObject(input.settings) ? structuredClone(input.settings) : {},
  };
}

export function adaptRequestForDevice(input, device) {
  const request = normalizeResolveRequest({ ...input, device });
  // The provider runtime receives NiakVIO's canonical vocabulary. Official Nuvio
  // aliases are accepted only before this boundary, never persisted in provider specs.
  return {
    device: request.device,
    call: "getStreams",
    args: [
      request.tmdbId ?? request.title,
      request.mediaType,
      request.season ?? undefined,
      request.episode ?? undefined,
    ],
    settings: request.settings,
    canonical: request,
  };
}

export function normalizeStreamCandidate(raw = {}, context = {}) {
  const nestedUrl = isPlainObject(raw.url) ? raw.url.url : null;
  const url = String(nestedUrl ?? raw.url ?? "").trim();
  if (!url) throw new Error("stream url is required");

  const headers = normalizeHeaders(raw.headers ?? raw.requestHeaders);
  const subtitles = Array.isArray(raw.subtitles)
    ? raw.subtitles.map(normalizeSubtitle).filter(Boolean)
    : [];

  return {
    title: textOrNull(raw.title) ?? textOrNull(raw.name) ?? context.providerName ?? "Unknown",
    name: textOrNull(raw.name),
    url,
    quality: textOrNull(raw.quality),
    size: textOrNull(raw.size),
    language: textOrNull(raw.language),
    provider: textOrNull(raw.provider) ?? context.providerId ?? null,
    type: textOrNull(raw.type),
    headers,
    subtitles,
    provenance: {
      providerId: context.providerId ?? null,
      source: context.source ?? null,
    },
  };
}

export function validateProviderSpec(spec = {}) {
  const errors = [];
  if (!textOrNull(spec.id)) errors.push("id is required");
  if (!textOrNull(spec.name)) errors.push("name is required");
  const types = normalizeStringList(spec.supportedTypes);
  if (!types.length) errors.push("supportedTypes is required");
  for (const type of types) {
    try { normalizeProviderMediaType(type); } catch { errors.push(`non-canonical provider type: ${type}`); }
  }
  if (!Array.isArray(spec.sources) || spec.sources.length === 0) errors.push("at least one provenance source is required");
  if (!isPlainObject(spec.strategies)) errors.push("strategies object is required");
  return { ok: errors.length === 0, errors };
}

export function normalizeProviderSpec(spec = {}) {
  const validation = validateProviderSpec(spec);
  if (!validation.ok) throw new Error(validation.errors.join("; "));
  return {
    id: String(spec.id).trim().toLowerCase(),
    name: String(spec.name).trim(),
    supportedTypes: [...new Set(spec.supportedTypes.map(normalizeProviderMediaType))],
    languages: normalizeStringList(spec.languages),
    sources: structuredClone(spec.sources),
    hubs: normalizeStringList(spec.hubs),
    domains: normalizeStringList(spec.domains),
    strategies: structuredClone(spec.strategies),
    session: isPlainObject(spec.session) ? structuredClone(spec.session) : {},
    quirks: normalizeStringList(spec.quirks),
    status: spec.status ?? "candidate",
  };
}

function normalizeSubtitle(value) {
  if (!isPlainObject(value)) return null;
  const url = textOrNull(value.url);
  if (!url) return null;
  return {
    url,
    language: textOrNull(value.language) ?? "Unknown",
    name: textOrNull(value.name),
    headers: normalizeHeaders(value.headers),
  };
}

function normalizeHeaders(value) {
  if (!isPlainObject(value)) return {};
  const out = {};
  for (const [key, raw] of Object.entries(value)) {
    if (raw == null) continue;
    const text = String(raw).trim();
    if (text) out[String(key)] = text;
  }
  return out;
}

function normalizeStringList(value) {
  const list = Array.isArray(value) ? value : value == null ? [] : [value];
  return [...new Set(list.map(textOrNull).filter(Boolean).map((v) => v.toLowerCase()))];
}

function toPositiveIntOrNull(value) {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) throw new Error(`expected positive integer, got ${value}`);
  return parsed;
}

function textOrNull(value) {
  if (value == null) return null;
  const text = String(value).trim();
  return text || null;
}

function isPlainObject(value) {
  return value != null && typeof value === "object" && !Array.isArray(value);
}
