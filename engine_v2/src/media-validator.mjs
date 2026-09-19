export async function validateMediaCandidate(candidate, options = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const timeoutMs = clamp(Number(options.timeoutMs ?? 7000), 1000, 15000);
  const maxBodyBytes = clamp(Number(options.maxBodyBytes ?? 262144), 4096, 1048576);
  const maxHlsVariants = clamp(Number(options.maxHlsVariants ?? 4), 1, 8);
  const maxHlsRenditions = clamp(Number(options.maxHlsRenditions ?? 3), 1, 6);
  const maxHlsDepth = clamp(Number(options.maxHlsDepth ?? 2), 1, 4);
  const baseHeaders = cloneHeaders(candidate.headers ?? {});
  const inferred = inferFormat(candidate.url, candidate.format ?? candidate.type);

  const result = {
    url: candidate.url,
    playable: false,
    status: null,
    finalUrl: null,
    contentType: null,
    format: inferred,
    reason: null,
    child: null,
    chain: null,
    effectiveHeight: inferHeight(candidate),
    codecs: textOrNull(candidate.codecs ?? candidate.codec),
    fallbackCount: 0,
    warnings: [],
  };

  try {
    const firstHeaders = headersForResource(baseHeaders, inferred === "mp4" || inferred === "mkv" || inferred === "webm");
    const response = await fetchImpl(candidate.url, {
      method: "GET",
      redirect: "follow",
      signal: timeoutSignal(timeoutMs),
      headers: firstHeaders.headers,
    });
    result.status = response.status;
    result.finalUrl = response.url || candidate.url;
    result.contentType = response.headers?.get?.("content-type") ?? null;
    if (!okStatus(response.status)) {
      result.reason = `http-${response.status}`;
      try { await response.body?.cancel?.(); } catch {}
      return result;
    }

    const contentType = String(result.contentType ?? "").toLowerCase();
    const contentSaysHls = contentType.includes("mpegurl") || contentType.includes("vnd.apple.mpegurl");
    if (inferred === "hls" || contentSaysHls) {
      result.format = "hls";
      const text = await readLimitedText(response, maxBodyBytes);
      const chain = await validateHlsDocument({
        url: candidate.url,
        finalUrl: result.finalUrl,
        text,
        headers: baseHeaders,
        fetchImpl,
        timeoutMs,
        maxBodyBytes,
        maxHlsVariants,
        maxHlsRenditions,
        maxHlsDepth,
        depth: 0,
      });
      applyHlsChain(result, chain);
      return result;
    }

    if (contentType.includes("text/html")) {
      result.reason = "html-instead-of-media";
      try { await response.body?.cancel?.(); } catch {}
      return result;
    }
    if (contentType.includes("application/json")) {
      result.reason = "json-instead-of-media";
      try { await response.body?.cancel?.(); } catch {}
      return result;
    }

    const sample = await readLimitedBytes(response, Math.min(maxBodyBytes, 32768));
    const sampleText = new TextDecoder("utf-8", { fatal: false }).decode(sample.slice(0, 4096));
    if (/^\s*#EXTM3U/m.test(sampleText) && !looksLikeHtml(sampleText)) {
      result.format = "hls";
      const chain = await validateHlsDocument({
        url: candidate.url,
        finalUrl: result.finalUrl,
        text: new TextDecoder("utf-8", { fatal: false }).decode(sample),
        headers: baseHeaders,
        fetchImpl,
        timeoutMs,
        maxBodyBytes,
        maxHlsVariants,
        maxHlsRenditions,
        maxHlsDepth,
        depth: 0,
      });
      applyHlsChain(result, chain);
      return result;
    }
    if (looksLikeHtmlBytes(sample)) {
      result.reason = "html-instead-of-media";
      return result;
    }
    if (looksLikeJsonBytes(sample)) {
      result.reason = "json-instead-of-media";
      return result;
    }

    result.playable = sample.length > 0 || Number(response.headers?.get?.("content-length") ?? 0) > 0;
    result.reason = result.playable ? null : (inferred === "unknown" ? "unknown-empty-media" : "empty-media-body");
    return result;
  } catch (error) {
    result.reason = errorReason(error);
    return result;
  }
}

export async function validateMediaCandidates(candidates = [], options = {}) {
  const maxCandidates = clamp(Number(options.maxCandidates ?? 3), 1, 8);
  const results = [];
  for (const candidate of candidates.slice(0, maxCandidates)) {
    const validation = await validateMediaCandidate(candidate, options);
    results.push({ candidate, validation, rankScore: scoreMediaCandidate(candidate, validation) });
  }
  const rankedResults = results
    .map((row, index) => ({ ...row, originalIndex: index }))
    .sort((a, b) => b.rankScore - a.rankScore || a.originalIndex - b.originalIndex)
    .map(({ originalIndex: _originalIndex, ...row }) => row);
  return {
    playable: results.some((row) => row.validation.playable),
    playableCount: results.filter((row) => row.validation.playable).length,
    results,
    rankedResults,
    best: rankedResults[0] ?? null,
  };
}

function applyHlsChain(result, chain) {
  result.chain = chain;
  result.child = chain.child ?? null;
  result.playable = chain.playable === true;
  result.reason = result.playable ? null : `hls-${chain.reason ?? "invalid"}`;
  result.effectiveHeight = chain.effectiveHeight ?? result.effectiveHeight;
  result.codecs = chain.codecs ?? result.codecs;
  result.fallbackCount = Number(chain.fallbackCount ?? 0);
  result.warnings = Array.isArray(chain.warnings) ? chain.warnings : [];
}

async function validateHlsDocument(ctx) {
  const parsed = parseHlsPlaylist(ctx.text, ctx.finalUrl);
  if (!parsed.valid) return hlsFailure(parsed.reason ?? "invalid-body");

  if (parsed.kind === "media") {
    const media = await validateHlsMediaResources(parsed, ctx);
    return {
      ...media,
      kind: "media",
      url: ctx.url,
      finalUrl: ctx.finalUrl,
      effectiveHeight: null,
      codecs: null,
      fallbackCount: 0,
      warnings: media.warnings ?? [],
    };
  }

  if (parsed.kind !== "master") return hlsFailure("playlist-without-media");
  if (ctx.depth >= ctx.maxHlsDepth) return hlsFailure("depth-limit");

  const variants = [...parsed.variants]
    .sort((a, b) => (b.height ?? 0) - (a.height ?? 0) || (b.bandwidth ?? 0) - (a.bandwidth ?? 0))
    .slice(0, ctx.maxHlsVariants);
  if (!variants.length) return hlsFailure("master-without-variant");

  const attempts = [];
  let selected = null;
  let selectedChild = null;
  for (const variant of variants) {
    const fetched = await fetchHlsPlaylist(variant.url, ctx);
    if (!fetched.ok) {
      attempts.push({ url: variant.url, playable: false, reason: fetched.reason, status: fetched.status ?? null });
      continue;
    }
    const child = await validateHlsDocument({
      ...ctx,
      url: variant.url,
      finalUrl: fetched.finalUrl,
      text: fetched.text,
      depth: ctx.depth + 1,
    });
    attempts.push({ url: variant.url, playable: child.playable, reason: child.reason, status: fetched.status, height: variant.height });
    if (child.playable) {
      selected = variant;
      selectedChild = { ...child, status: fetched.status, finalUrl: fetched.finalUrl };
      break;
    }
  }

  if (!selected || !selectedChild) {
    const reason = attempts.find((row) => row.reason)?.reason ?? "no-playable-variant";
    return {
      ...hlsFailure(`variant-${reason}`),
      kind: "master",
      variants: attempts,
      fallbackCount: attempts.length,
    };
  }

  const warnings = [...(selectedChild.warnings ?? [])];
  const audio = await validateRequiredRendition("AUDIO", selected.audioGroup, parsed.renditions, ctx);
  if (audio.required && !audio.playable) {
    return {
      ...hlsFailure(`audio-${audio.reason ?? "unplayable"}`),
      kind: "master",
      variants: attempts,
      child: selectedChild,
      audio,
      effectiveHeight: selected.height ?? selectedChild.effectiveHeight ?? null,
      codecs: selected.codecs ?? selectedChild.codecs ?? null,
      fallbackCount: Math.max(0, attempts.length - 1) + Number(selectedChild.fallbackCount ?? 0),
      warnings,
    };
  }

  const subtitles = await validateOptionalRendition("SUBTITLES", selected.subtitleGroup, parsed.renditions, ctx);
  if (subtitles.required && !subtitles.playable) warnings.push(`subtitle-${subtitles.reason ?? "unplayable"}`);

  return {
    playable: true,
    reason: null,
    kind: "master",
    url: ctx.url,
    finalUrl: ctx.finalUrl,
    variants: attempts,
    selectedVariant: selected,
    child: selectedChild,
    audio,
    subtitles,
    effectiveHeight: selected.height ?? selectedChild.effectiveHeight ?? null,
    codecs: selected.codecs ?? selectedChild.codecs ?? null,
    fallbackCount: Math.max(0, attempts.length - 1) + Number(selectedChild.fallbackCount ?? 0),
    warnings,
  };
}

async function validateHlsMediaResources(parsed, ctx) {
  const warnings = [];
  if (parsed.key) {
    const key = await probeBinaryResource(parsed.key.url, ctx, "key", false);
    if (!key.playable) return { ...hlsFailure(`key-${key.reason}`), key, warnings };
  }
  let map = null;
  if (parsed.map) {
    map = await probeBinaryResource(parsed.map.url, ctx, "map", true);
    if (!map.playable) return { ...hlsFailure(`map-${map.reason}`), map, warnings };
  }
  const segmentUrl = parsed.segments[0] ?? parsed.parts[0] ?? null;
  if (!segmentUrl) return { ...hlsFailure("media-without-segment"), map, warnings };
  const segment = await probeBinaryResource(segmentUrl, ctx, "segment", true);
  if (!segment.playable) return { ...hlsFailure(`segment-${segment.reason}`), map, segment, warnings };
  return {
    playable: true,
    reason: null,
    key: parsed.key ? { url: parsed.key.url, playable: true } : null,
    map,
    segment,
    warnings,
  };
}

async function validateRequiredRendition(type, groupId, renditions, ctx) {
  if (!groupId) return { required: false, playable: true, reason: null, attempts: [] };
  const matching = renditions.filter((row) => row.type === type && row.groupId === groupId);
  const external = matching.filter((row) => row.url);
  if (!external.length) return { required: false, playable: true, reason: null, attempts: [] };
  const attempts = [];
  for (const rendition of external.slice(0, ctx.maxHlsRenditions)) {
    const probe = await probeHlsRendition(rendition.url, ctx);
    attempts.push(probe);
    if (probe.playable) return { required: true, playable: true, reason: null, selected: rendition, attempts };
  }
  return { required: true, playable: false, reason: attempts.find((row) => row.reason)?.reason ?? "no-playable-rendition", attempts };
}

async function validateOptionalRendition(type, groupId, renditions, ctx) {
  return validateRequiredRendition(type, groupId, renditions, ctx);
}

async function probeHlsRendition(url, ctx) {
  const fetched = await fetchHlsPlaylist(url, ctx);
  if (!fetched.ok) return { url, playable: false, status: fetched.status ?? null, reason: fetched.reason };
  const parsed = parseHlsPlaylist(fetched.text, fetched.finalUrl);
  if (!parsed.valid) return { url, playable: false, status: fetched.status, reason: parsed.reason };
  if (parsed.kind === "master") {
    const nested = await validateHlsDocument({ ...ctx, url, finalUrl: fetched.finalUrl, text: fetched.text, depth: ctx.depth + 1 });
    return { url, playable: nested.playable, status: fetched.status, reason: nested.reason, child: nested };
  }
  if (parsed.kind !== "media") return { url, playable: false, status: fetched.status, reason: "playlist-without-media" };
  const media = await validateHlsMediaResources(parsed, { ...ctx, url, finalUrl: fetched.finalUrl });
  return { url, playable: media.playable, status: fetched.status, reason: media.reason, media };
}

async function fetchHlsPlaylist(url, ctx) {
  try {
    const response = await ctx.fetchImpl(url, {
      method: "GET",
      redirect: "follow",
      signal: timeoutSignal(ctx.timeoutMs),
      headers: headersForResource(ctx.headers, false).headers,
    });
    const out = { ok: false, url, finalUrl: response.url || url, status: response.status, reason: null, text: "" };
    if (!okStatus(response.status)) {
      out.reason = `http-${response.status}`;
      try { await response.body?.cancel?.(); } catch {}
      return out;
    }
    out.text = await readLimitedText(response, ctx.maxBodyBytes);
    if (!/^\s*#EXTM3U/m.test(out.text) || looksLikeHtml(out.text)) {
      out.reason = "invalid-playlist";
      return out;
    }
    out.ok = true;
    return out;
  } catch (error) {
    return { ok: false, url, status: null, finalUrl: url, reason: errorReason(error), text: "" };
  }
}

async function probeBinaryResource(url, ctx, kind, allowSyntheticRange) {
  const request = headersForResource(ctx.headers, allowSyntheticRange);
  let response;
  try {
    response = await ctx.fetchImpl(url, {
      method: "GET",
      redirect: "follow",
      signal: timeoutSignal(ctx.timeoutMs),
      headers: request.headers,
    });
    if (response.status === 416 && request.syntheticRange) {
      try { await response.body?.cancel?.(); } catch {}
      response = await ctx.fetchImpl(url, {
        method: "GET",
        redirect: "follow",
        signal: timeoutSignal(ctx.timeoutMs),
        headers: headersForResource(ctx.headers, false).headers,
      });
    }
  } catch (error) {
    return { url, kind, playable: false, status: null, reason: errorReason(error) };
  }
  const out = {
    url,
    kind,
    finalUrl: response.url || url,
    playable: false,
    status: response.status,
    contentType: response.headers?.get?.("content-type") ?? null,
    reason: null,
  };
  if (!okStatus(response.status)) {
    out.reason = `http-${response.status}`;
    try { await response.body?.cancel?.(); } catch {}
    return out;
  }
  const sample = await readLimitedBytes(response, Math.min(ctx.maxBodyBytes, kind === "key" ? 4096 : 32768));
  if (!sample.length && Number(response.headers?.get?.("content-length") ?? 0) <= 0) {
    out.reason = "empty-body";
    return out;
  }
  if (looksLikeHtmlBytes(sample)) {
    out.reason = "html-body";
    return out;
  }
  if (looksLikeJsonBytes(sample)) {
    out.reason = "json-body";
    return out;
  }
  out.playable = true;
  return out;
}

function parseHlsPlaylist(text, baseUrl) {
  const body = String(text ?? "").replace(/^\uFEFF/, "").trim();
  if (!/^#EXTM3U(?:\s|$)/i.test(body) || looksLikeHtml(body)) return { valid: false, reason: "invalid-body" };
  const lines = body.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const variants = [];
  const renditions = [];
  const segments = [];
  const parts = [];
  let key = null;
  let map = null;
  let pendingVariant = null;
  let hasMediaTag = false;

  for (const line of lines) {
    if (/^#EXT-X-STREAM-INF\s*:/i.test(line)) {
      pendingVariant = parseAttributeList(line.slice(line.indexOf(":") + 1));
      continue;
    }
    if (/^#EXT-X-MEDIA\s*:/i.test(line)) {
      const attrs = parseAttributeList(line.slice(line.indexOf(":") + 1));
      renditions.push({
        type: String(attrs.TYPE ?? "").toUpperCase(),
        groupId: attrs["GROUP-ID"] ?? null,
        name: attrs.NAME ?? null,
        language: attrs.LANGUAGE ?? null,
        default: String(attrs.DEFAULT ?? "").toUpperCase() === "YES",
        url: attrs.URI ? resolveHlsUri(attrs.URI, baseUrl) : null,
      });
      continue;
    }
    if (/^#EXT-X-KEY\s*:/i.test(line)) {
      const attrs = parseAttributeList(line.slice(line.indexOf(":") + 1));
      if (String(attrs.METHOD ?? "").toUpperCase() !== "NONE" && attrs.URI) {
        key = { method: attrs.METHOD ?? null, url: resolveHlsUri(attrs.URI, baseUrl) };
      }
      continue;
    }
    if (/^#EXT-X-MAP\s*:/i.test(line)) {
      const attrs = parseAttributeList(line.slice(line.indexOf(":") + 1));
      if (attrs.URI) map = { url: resolveHlsUri(attrs.URI, baseUrl) };
      hasMediaTag = true;
      continue;
    }
    if (/^#EXT-X-PART\s*:/i.test(line)) {
      const attrs = parseAttributeList(line.slice(line.indexOf(":") + 1));
      if (attrs.URI) parts.push(resolveHlsUri(attrs.URI, baseUrl));
      hasMediaTag = true;
      continue;
    }
    if (/^#EXTINF\s*:/i.test(line)) {
      hasMediaTag = true;
      continue;
    }
    if (line.startsWith("#")) continue;

    const url = resolveHlsUri(line, baseUrl);
    if (pendingVariant) {
      const resolution = String(pendingVariant.RESOLUTION ?? "").match(/^(\d+)x(\d+)$/i);
      variants.push({
        url,
        width: resolution ? Number(resolution[1]) : null,
        height: resolution ? Number(resolution[2]) : null,
        bandwidth: Number(pendingVariant.BANDWIDTH ?? pendingVariant["AVERAGE-BANDWIDTH"] ?? 0) || null,
        codecs: pendingVariant.CODECS ?? null,
        audioGroup: pendingVariant.AUDIO ?? null,
        subtitleGroup: pendingVariant.SUBTITLES ?? null,
      });
      pendingVariant = null;
    } else {
      segments.push(url);
    }
  }

  if (variants.length) return { valid: true, kind: "master", variants, renditions, segments: [], parts: [], key: null, map: null };
  if (hasMediaTag && (segments.length || parts.length || map)) return { valid: true, kind: "media", variants: [], renditions, segments, parts, key, map };
  return { valid: true, kind: "unknown", variants: [], renditions, segments, parts, key, map };
}

function parseAttributeList(text) {
  const out = {};
  const re = /([A-Z0-9-]+)=("(?:[^"\\]|\\.)*"|[^,]*)/gi;
  let match;
  while ((match = re.exec(String(text ?? ""))) !== null) {
    const key = match[1].toUpperCase();
    let value = match[2].trim();
    if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1);
    out[key] = value;
  }
  return out;
}

function resolveHlsUri(raw, baseUrl) {
  const value = String(raw ?? "").trim();
  if (!value) return "";
  // Absolute signed HLS child URLs are opaque credentials. Preserve their exact
  // query spelling/order instead of round-tripping them through URL serialization.
  if (/^https?:\/\//i.test(value)) return value;
  try { return new URL(value, baseUrl).href; } catch { return value; }
}

function scoreMediaCandidate(candidate, validation) {
  if (!validation?.playable) return -100000;
  const height = Number(validation.effectiveHeight ?? inferHeight(candidate) ?? 0);
  const fallbackCount = Math.max(0, Number(validation.fallbackCount ?? 0));
  const codecText = [validation.codecs, candidate.codecs, candidate.codec, candidate.quality, candidate.name, candidate.title]
    .filter(Boolean).join(" ").toLowerCase();
  const broadCodecBonus = /\b(?:avc1|avc|h\.264|h264)\b/i.test(codecText) ? 300 : 0;
  const stability = Number(candidate.stabilityScore);
  const stabilityBonus = Number.isFinite(stability) ? clamp(stability, 0, 1) * 800 : 0;
  // A failed higher variant is a real stability signal. This deliberately allows a
  // clean AVC 1080p path to outrank a flaky 2160p/HEVC path, while a healthy 2160p
  // stream still wins on quality.
  return 10000 + Math.min(height, 2160) + broadCodecBonus + stabilityBonus - fallbackCount * 1800;
}

function inferHeight(candidate = {}) {
  const text = [candidate.quality, candidate.resolution, candidate.name, candidate.title]
    .filter(Boolean).join(" ");
  if (/\b(?:4k|uhd)\b/i.test(text)) return 2160;
  const match = text.match(/\b(2160|1440|1080|720|576|480)p?\b/i);
  return match ? Number(match[1]) : null;
}

function inferFormat(url, explicit) {
  const hint = String(explicit ?? "").toLowerCase();
  if (hint.includes("m3u8") || hint === "hls" || hint.includes("mpegurl")) return "hls";
  if (hint.includes("mp4")) return "mp4";
  if (hint.includes("mkv") || hint.includes("matroska")) return "mkv";
  if (hint.includes("webm")) return "webm";
  const clean = String(url ?? "").split(/[?#]/)[0].toLowerCase();
  if (clean.endsWith(".m3u8")) return "hls";
  if (clean.endsWith(".mp4")) return "mp4";
  if (clean.endsWith(".mkv")) return "mkv";
  if (clean.endsWith(".webm")) return "webm";
  return "unknown";
}

function headersForResource(baseHeaders, addRange) {
  const headers = cloneHeaders(baseHeaders);
  if (!addRange || hasHeader(headers, "Range")) return { headers, syntheticRange: false };
  headers.Range = "bytes=0-32767";
  return { headers, syntheticRange: true };
}

function cloneHeaders(value) {
  const out = {};
  if (!value || typeof value !== "object" || Array.isArray(value)) return out;
  for (const [key, raw] of Object.entries(value)) {
    if (raw == null) continue;
    const text = String(raw).trim();
    if (text) out[String(key)] = text;
  }
  return out;
}

async function readLimitedText(response, limit) {
  const bytes = await readLimitedBytes(response, limit);
  return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
}

async function readLimitedBytes(response, limit) {
  if (!response.body?.getReader) {
    const buffer = new Uint8Array(await response.arrayBuffer());
    return buffer.slice(0, limit);
  }
  const reader = response.body.getReader();
  const chunks = [];
  let total = 0;
  try {
    while (total < limit) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = value.slice(0, Math.max(0, limit - total));
      chunks.push(chunk);
      total += chunk.length;
      if (chunk.length < value.length) break;
    }
  } finally {
    try { await reader.cancel(); } catch {}
  }
  const out = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { out.set(chunk, offset); offset += chunk.length; }
  return out;
}

function looksLikeHtml(text) {
  return /<\s*(?:!doctype\s+html|html|body|head)\b/i.test(String(text).slice(0, 4096));
}

function looksLikeHtmlBytes(bytes) {
  return looksLikeHtml(new TextDecoder("utf-8", { fatal: false }).decode(bytes.slice(0, 4096)));
}

function looksLikeJsonBytes(bytes) {
  const text = new TextDecoder("utf-8", { fatal: false }).decode(bytes.slice(0, 4096)).trim();
  return /^(?:\{|\[)/.test(text) && /[}\]]/.test(text);
}

function hasHeader(headers, name) {
  const lower = name.toLowerCase();
  return Object.keys(headers).some((key) => key.toLowerCase() === lower);
}

function hlsFailure(reason) {
  return { playable: false, reason, warnings: [] };
}

function okStatus(status) {
  return (status >= 200 && status < 300) || status === 206;
}

function timeoutSignal(timeoutMs) {
  try { return AbortSignal.timeout(timeoutMs); } catch { return undefined; }
}

function errorReason(error) {
  return String(error?.cause?.code ?? error?.name ?? error?.message ?? error);
}

function textOrNull(value) {
  if (value == null) return null;
  const text = String(value).trim();
  return text || null;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value)));
}
