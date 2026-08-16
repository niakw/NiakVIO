const DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

export function createPurstreamAdapter(options = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const userAgent = options.userAgent ?? DEFAULT_UA;
  const terminal = normalizeTerminal(options.terminalUrl);
  const endpoint = derivePurstreamEndpoint(terminal);
  const metadataResolver = options.metadataResolver ?? null;

  return {
    id: "purstream",
    pipeline: ["homepage", "search", "identity", "detail", "episode", "media"],

    async discover() {
      return {
        ok: true,
        host: terminal.hostname,
        url: terminal.href,
        api: endpoint.api,
        source: options.domainSource ?? "v2-domain-observation",
      };
    },

    async homepage() {
      const response = await request(terminal.href, { accept: "text/html,*/*;q=0.5" });
      discard(response);
      return {
        ok: response.status > 0 && response.status < 500,
        reachable: response.status > 0,
        status: response.status,
      };
    },

    async search(ctx) {
      const metadata = await resolveMetadata(ctx.request, metadataResolver);
      ctx.state.metadata = metadata;
      const queries = unique([metadata.title, ...(metadata.aliases ?? [])].map(cleanText).filter(Boolean));
      const attempts = [];
      const matches = [];

      for (const query of queries.slice(0, 4)) {
        const url = `${endpoint.api}/search-bar/search/${encodeURIComponent(query)}`;
        const response = await request(url, { api: true });
        const payload = await readJson(response);
        const found = collectSearchItems(payload);
        attempts.push({ query, status: response.status, count: found.length, url });
        for (const item of found) matches.push({ ...item, __query: query });
        if (matches.some((item) => strictIdentityScore(item, metadata, providerMediaType(ctx.request.mediaType)) >= 100)) break;
      }

      ctx.state.searchAttempts = attempts;
      return {
        ok: attempts.some((attempt) => attempt.status >= 200 && attempt.status < 300),
        status: attempts.at(-1)?.status ?? null,
        matches: dedupeItems(matches),
        attempts,
      };
    },

    async identity(ctx) {
      const matches = ctx.state.search?.matches ?? [];
      const metadata = ctx.state.metadata ?? await resolveMetadata(ctx.request, metadataResolver);
      const targetType = providerMediaType(ctx.request.mediaType);
      const ranked = matches
        .map((item) => ({ item, score: strictIdentityScore(item, metadata, targetType) }))
        .sort((a, b) => b.score - a.score);
      const best = ranked[0] ?? null;
      const matched = Boolean(best && best.score >= 100 && providerId(best.item));
      if (matched) ctx.state.selected = best.item;
      return {
        ok: matched,
        matched,
        score: best?.score ?? 0,
        selectedId: matched ? providerId(best.item) : null,
        selectedTitle: matched ? itemTitle(best.item) : null,
        selectedType: matched ? itemType(best.item) : null,
        selectedYear: matched ? itemYear(best.item) : null,
        candidates: ranked.slice(0, 5).map(({ item, score }) => ({ id: providerId(item), title: itemTitle(item), type: itemType(item), year: itemYear(item), score })),
      };
    },

    async detail(ctx) {
      const selectedId = providerId(ctx.state.selected);
      if (!selectedId) return { ok: false, found: false, reason: "missing-provider-id" };
      if (ctx.request.mediaType !== "movie") {
        return { ok: true, found: true, deferredToEpisode: true };
      }
      const url = `${endpoint.api}/media/${encodeURIComponent(selectedId)}/sheet`;
      const response = await request(url, { api: true });
      const payload = await readJson(response);
      const sources = collectMovieSources(payload);
      ctx.state.movieSources = sources;
      return { ok: response.ok && sources.length > 0, found: sources.length > 0, status: response.status, sourceCount: sources.length, url };
    },

    async episode(ctx) {
      const selectedId = providerId(ctx.state.selected);
      if (!selectedId) return { ok: false, found: false, reason: "missing-provider-id" };
      const url = `${endpoint.api}/stream/${encodeURIComponent(selectedId)}/episode?season=${encodeURIComponent(ctx.request.season)}&episode=${encodeURIComponent(ctx.request.episode)}`;
      const response = await request(url, { api: true });
      const payload = await readJson(response);
      const sources = collectEpisodeSources(payload);
      ctx.state.episodeSources = sources;
      return {
        ok: response.ok && sources.length > 0,
        found: sources.length > 0,
        status: response.status,
        season: ctx.request.season,
        episode: ctx.request.episode,
        sourceCount: sources.length,
        url,
      };
    },

    async media(ctx) {
      const rawSources = ctx.request.mediaType === "movie"
        ? ctx.state.movieSources ?? []
        : ctx.state.episodeSources ?? [];
      const streams = rawSources
        .map((item) => normalizeSource(item, endpoint, userAgent, ctx.request))
        .filter(Boolean);
      return { ok: streams.length > 0, found: streams.length > 0, streams };
    },
  };

  async function request(url, { api = false, accept = "application/json,text/plain,*/*;q=0.5" } = {}) {
    const headers = {
      "User-Agent": userAgent,
      Accept: accept,
      Referer: endpoint.referer,
    };
    if (api) headers.Origin = endpoint.origin;
    return fetchImpl(url, { method: "GET", redirect: "follow", headers });
  }
}

export function derivePurstreamEndpoint(terminalUrl) {
  const terminal = terminalUrl instanceof URL ? terminalUrl : normalizeTerminal(terminalUrl);
  const host = terminal.hostname.toLowerCase().replace(/^www\./, "");
  if (host === "purstream.wiki" || host.endsWith(".purstream.wiki")) {
    throw new Error("Purstream hub is not a terminal provider domain");
  }
  const match = host.match(/^(?:api\.)?purstream\.(.+)$/i);
  if (!match) throw new Error(`unsupported Purstream terminal host: ${host}`);
  const suffix = match[1];
  return {
    suffix,
    site: `https://purstream.${suffix}/`,
    api: `https://api.purstream.${suffix}/api/v1`,
    referer: `https://purstream.${suffix}/`,
    origin: `https://purstream.${suffix}`,
  };
}

export function strictIdentityScore(item, metadata, targetType) {
  const candidateTitle = normalizeTitle(itemTitle(item));
  const targetTitles = unique([metadata.title, ...(metadata.aliases ?? [])].map(normalizeTitle).filter(Boolean));
  if (!candidateTitle || !targetTitles.includes(candidateTitle)) return 0;
  let score = 100;
  const type = itemType(item);
  if (type && targetType && type !== targetType) return 0;
  if (type === targetType) score += 20;
  const targetYear = asYear(metadata.year);
  const year = itemYear(item);
  if (targetYear && year) {
    const delta = Math.abs(targetYear - year);
    if (delta > 1) return 0;
    score += delta === 0 ? 20 : 10;
  }
  if (providerId(item)) score += 5;
  return score;
}

export function collectSearchItems(payload) {
  const items = payload?.data?.items ?? payload?.items ?? payload?.data ?? payload;
  const arrays = [];
  collectNamedArrays(items, arrays, new Set(), 0);
  return dedupeItems(arrays.flat());
}

export function collectMovieSources(payload) {
  const candidates = [
    payload?.data?.items?.urls,
    payload?.data?.urls,
    payload?.items?.urls,
    payload?.urls,
  ];
  return candidates.find(Array.isArray) ?? [];
}

export function collectEpisodeSources(payload) {
  const candidates = [
    payload?.data?.items?.sources,
    payload?.data?.sources,
    payload?.items?.sources,
    payload?.sources,
  ];
  return candidates.find(Array.isArray) ?? [];
}

function normalizeSource(item, endpoint, userAgent, request) {
  if (!item || typeof item !== "object") return null;
  const url = cleanText(item.stream_url ?? item.url ?? item.file ?? item.src);
  if (!url || !/^https?:\/\//i.test(url)) return null;
  const lower = url.split(/[?#]/)[0].toLowerCase();
  const explicitFormat = cleanText(item.format)?.toLowerCase();
  const direct = lower.endsWith(".m3u8") || lower.endsWith(".mp4") || explicitFormat === "m3u8" || explicitFormat === "mp4";
  if (!direct) return null;
  const label = cleanText(item.source_name ?? item.name ?? item.label) ?? "Purstream";
  const language = parseLanguage(label);
  const quality = parseQuality(label);
  return {
    title: `Purstream ${quality} | ${language}`,
    name: "Purstream",
    url,
    quality,
    language,
    format: lower.endsWith(".mp4") || explicitFormat === "mp4" ? "mp4" : "m3u8",
    headers: {
      "User-Agent": userAgent,
      Referer: endpoint.referer,
    },
    sourceLabel: label,
    season: request.season ?? null,
    episode: request.episode ?? null,
  };
}

function parseLanguage(value) {
  const text = String(value ?? "").toUpperCase();
  if (text.includes("VOSTFR")) return "VOSTFR";
  if (text.includes("VFQ")) return "VFQ";
  if (text.includes("VFF")) return "VFF";
  if (text.includes("VF")) return "VF";
  if (text.includes("MULTI") || text.includes("DUAL")) return "MULTI";
  return "MULTI";
}

function parseQuality(value) {
  const text = String(value ?? "").toUpperCase();
  if (text.includes("2160") || text.includes("4K")) return "4K";
  if (text.includes("1080")) return "1080p";
  if (text.includes("720")) return "720p";
  if (text.includes("480")) return "480p";
  return "HD";
}

async function resolveMetadata(request, resolver) {
  const base = {
    title: cleanText(request.title),
    aliases: [],
    year: asYear(request.year),
  };
  if (!resolver) {
    if (!base.title) throw new Error("Purstream search requires title or metadataResolver");
    return base;
  }
  const resolved = await resolver(request);
  return {
    title: cleanText(resolved?.title ?? resolved?.fr ?? base.title),
    aliases: unique([...(resolved?.aliases ?? []), resolved?.originalTitle, resolved?.orig, base.title].map(cleanText).filter(Boolean)),
    year: asYear(resolved?.year ?? base.year),
  };
}

function collectNamedArrays(value, out, seen, depth) {
  if (!value || depth > 5 || seen.has(value)) return;
  if (typeof value !== "object") return;
  seen.add(value);
  if (Array.isArray(value)) {
    if (value.some((item) => item && typeof item === "object" && (providerId(item) || itemTitle(item)))) out.push(value);
    for (const item of value) collectNamedArrays(item, out, seen, depth + 1);
    return;
  }
  for (const child of Object.values(value)) collectNamedArrays(child, out, seen, depth + 1);
}

function dedupeItems(items) {
  const map = new Map();
  for (const item of items) {
    if (!item || typeof item !== "object") continue;
    const key = providerId(item) ?? `${normalizeTitle(itemTitle(item))}:${itemType(item) ?? ""}:${itemYear(item) ?? ""}`;
    if (!key) continue;
    if (!map.has(key)) map.set(key, item);
  }
  return [...map.values()];
}

function providerId(item) {
  const value = item?.id ?? item?._id ?? item?.media_id ?? item?.mediaId;
  return value == null ? null : String(value).trim() || null;
}

function itemTitle(item) {
  return cleanText(item?.title ?? item?.name ?? item?.label ?? item?.original_title ?? item?.original_name);
}

function itemType(item) {
  const raw = cleanText(item?.type ?? item?.media_type ?? item?.mediaType)?.toLowerCase();
  if (!raw) return null;
  if (["series", "show", "anime"].includes(raw)) return "tv";
  return raw;
}

function itemYear(item) {
  const raw = item?.year ?? item?.release_year ?? item?.release_date ?? item?.first_air_date ?? item?.date;
  return asYear(raw);
}

function providerMediaType(mediaType) {
  return mediaType === "movie" ? "movie" : "tv";
}

function normalizeTerminal(value) {
  if (!value) throw new Error("Purstream terminalUrl is required");
  const url = new URL(String(value));
  if (!["http:", "https:"].includes(url.protocol)) throw new Error("Purstream terminalUrl must be HTTP(S)");
  derivePurstreamEndpointUnchecked(url);
  return url;
}

function derivePurstreamEndpointUnchecked(url) {
  const host = url.hostname.toLowerCase().replace(/^www\./, "");
  if (host === "purstream.wiki" || host.endsWith(".purstream.wiki")) throw new Error("Purstream hub is not a terminal provider domain");
  if (!/^(?:api\.)?purstream\.[a-z0-9.-]+$/i.test(host)) throw new Error(`unsupported Purstream terminal host: ${host}`);
}

function normalizeTitle(value) {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function asYear(value) {
  if (value == null || value === "") return null;
  const match = String(value).match(/(?:19|20)\d{2}/);
  return match ? Number(match[0]) : null;
}

function cleanText(value) {
  if (value == null) return null;
  const text = String(value).trim();
  return text || null;
}

function unique(values) {
  return [...new Set(values)];
}

async function readJson(response) {
  const text = await response.text();
  if (!response.ok) throw new Error(`Purstream HTTP ${response.status}`);
  try { return JSON.parse(text); }
  catch { throw new Error("Purstream returned non-JSON API response"); }
}

function discard(response) {
  try { response.body?.cancel?.(); } catch {}
}
