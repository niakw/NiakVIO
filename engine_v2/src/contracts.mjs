export const DEVICES = Object.freeze(["worker", "mobile", "desktop", "tv"]);
export const CANONICAL_MEDIA_TYPES = Object.freeze(["movie", "tv", "anime"]);

const SERIES_ALIASES = new Set(["series", "show", "other"]);

export function normalizeMediaType(value) {
  const raw = String(value ?? "").trim().toLowerCase();
  if (!raw) throw new Error("mediaType is required");
  if (SERIES_ALIASES.has(raw)) return "tv";
  if (CANONICAL_MEDIA_TYPES.includes(raw)) return raw;
  throw new Error(`unsupported mediaType: ${raw}`);
}

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
  return {
    device: request.device,
    call: "getStreams",
    args: [request.tmdbId ?? request.title, request.mediaType, request.season ?? undefined, request.episode ?? undefined],
    settings: request.settings,
    canonical: request,
  };
}

export function normalizeStreamCandidate(raw = {}, context = {}) {
  const nested = isPlainObject(raw.url) ? raw.url : null;
  const nestedUrl = nested?.url ?? null;
  const url = String(nestedUrl ?? raw.url ?? "").trim();
  if (!url) throw new Error("stream url is required");

  const headers = mergeHeaders(
    nested?.behaviorHints?.proxyHeaders?.request,
    raw.behaviorHints?.proxyHeaders?.request,
    nested?.requestHeaders,
    nested?.headers,
    raw.requestHeaders,
    raw.headers,
  );
  const subtitles = Array.isArray(raw.subtitles)
    ? raw.subtitles.map(normalizeSubtitle).filter(Boolean)
    : [];
  const behaviorHints = mergePlainObjects(nested?.behaviorHints, raw.behaviorHints);

  return {
    title: textOrNull(raw.title) ?? textOrNull(raw.name) ?? context.providerName ?? "Unknown",
    name: textOrNull(raw.name),
    description: textOrNull(raw.description),
    url,
    quality: normalizeQualityLabel(raw.quality ?? raw.resolution),
    size: scalarOrNull(raw.size),
    language: textOrNull(raw.language ?? raw.lang ?? raw.audioLanguage ?? raw.audio_language),
    codec: textOrNull(raw.codec ?? raw.videoCodec ?? raw.video_codec),
    audio: textOrNull(raw.audio ?? raw.audioCodec ?? raw.audio_codec),
    duration: normalizeDurationMinutes(raw.duration ?? raw.durationMinutes ?? raw.duration_minutes ?? raw.runtime ?? raw.runtimeMinutes ?? raw.runtime_minutes),
    sourceType: textOrNull(raw.sourceType ?? raw.source_type),
    releaseType: textOrNull(raw.releaseType ?? raw.release_type),
    format: textOrNull(raw.format ?? raw.container ?? raw.mimeType ?? raw.contentType),
    ageRating: textOrNull(raw.ageRating ?? raw.age_rating ?? raw.certification ?? raw.contentRating),
    sourceLabel: textOrNull(raw.sourceLabel ?? raw.source_label ?? raw.label ?? raw.server),
    filename: textOrNull(raw.filename ?? raw.fileName ?? raw.file_name),
    behaviorHints: Object.keys(behaviorHints).length ? behaviorHints : null,
    videoTech: cloneStringOrArray(raw.videoTech ?? raw.video_tech ?? raw.visualTags ?? raw.hdr),
    hdr: textOrNull(raw.hdr ?? raw.hdrFormat ?? raw.hdr_format),
    bitDepth: textOrNull(raw.bitDepth ?? raw.bit_depth),
    badgeIds: normalizeDisplayList(raw.badgeIds),
    displayBadges: normalizeDisplayList(raw.displayBadges),
    presentationFacts: isPlainObject(raw.presentationFacts) ? structuredClone(raw.presentationFacts) : null,
    edition: textOrNull(raw.edition ?? raw.editions),
    releaseGroup: textOrNull(raw.releaseGroup ?? raw.release_group ?? raw.group),
    bitrate: scalarOrNull(raw.bitrate ?? raw.bitRate ?? raw.bit_rate),
    container: textOrNull(raw.container ?? raw.format),
    encode: textOrNull(raw.encode ?? raw.encoder),
    indexer: textOrNull(raw.indexer),
    network: textOrNull(raw.network),
    folderSize: scalarOrNull(raw.folderSize ?? raw.folder_size),
    seeders: numberOrNull(raw.seeders ?? raw.seeds),
    provider: textOrNull(raw.provider) ?? context.providerId ?? null,
    type: textOrNull(raw.type),
    headers,
    subtitles,
    provenance: { providerId: context.providerId ?? null, source: context.source ?? null },
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
  const nested = isPlainObject(value.url) ? value.url : null;
  const url = textOrNull(nested?.url ?? value.url);
  if (!url) return null;
  return {
    url,
    language: textOrNull(value.language) ?? "Unknown",
    name: textOrNull(value.name),
    headers: mergeHeaders(
      nested?.behaviorHints?.proxyHeaders?.request,
      value.behaviorHints?.proxyHeaders?.request,
      nested?.requestHeaders,
      nested?.headers,
      value.requestHeaders,
      value.headers,
    ),
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

function mergeHeaders(...sources) {
  const out = {};
  const keys = new Map();
  for (const source of sources) {
    for (const [key, value] of Object.entries(normalizeHeaders(source))) {
      const lower = key.toLowerCase();
      const previous = keys.get(lower);
      if (previous && previous !== key) delete out[previous];
      out[key] = value;
      keys.set(lower, key);
    }
  }
  return out;
}

function mergePlainObjects(...sources) {
  const out = {};
  for (const source of sources) {
    if (!isPlainObject(source)) continue;
    for (const [key, value] of Object.entries(source)) {
      if (isPlainObject(value) && isPlainObject(out[key])) out[key] = mergePlainObjects(out[key], value);
      else out[key] = structuredClone(value);
    }
  }
  return out;
}

function cloneStringOrArray(value) {
  if (Array.isArray(value)) return value.map(textOrNull).filter(Boolean);
  return textOrNull(value);
}

function normalizeDisplayList(value) {
  if (!Array.isArray(value)) return [];
  return value.map(textOrNull).filter(Boolean);
}

function scalarOrNull(value) {
  if (value == null || value === "") return null;
  if (typeof value === "number" || typeof value === "boolean") return value;
  return textOrNull(value);
}

function numberOrNull(value) {
  if (value == null || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function normalizeQualityLabel(value) {
  const text = textOrNull(value);
  if (!text) return null;
  if (/^(?:4k|uhd|2160p?)$/i.test(text)) return "2160p";
  const resolution = text.match(/(?:^|\b)(2160|1440|1080|720|576|480)p?(?:\b|$)/i);
  if (resolution) return `${resolution[1]}p`;
  return text;
}

function normalizeDurationMinutes(value) {
  if (value == null || value === "") return null;
  if (typeof value === "number" && Number.isFinite(value) && value > 0) {
    return value > 600 ? Math.round(value / 60) : Math.round(value);
  }
  const text = textOrNull(value);
  if (!text) return null;
  const hm = text.match(/(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:in(?:utes?)?)?)?/i);
  if (hm && (hm[1] || hm[2])) {
    const minutes = Number(hm[1] || 0) * 60 + Number(hm[2] || 0);
    return minutes > 0 ? minutes : null;
  }
  const parsed = Number(text);
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  return parsed > 600 ? Math.round(parsed / 60) : Math.round(parsed);
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
