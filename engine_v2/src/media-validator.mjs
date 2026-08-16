export async function validateMediaCandidate(candidate, options = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const timeoutMs = clamp(Number(options.timeoutMs ?? 7000), 1000, 15000);
  const maxBodyBytes = clamp(Number(options.maxBodyBytes ?? 262144), 4096, 1048576);
  const headers = { ...(candidate.headers ?? {}) };
  if (!hasHeader(headers, "Range")) headers.Range = "bytes=0-262143";

  const result = {
    url: candidate.url,
    playable: false,
    status: null,
    finalUrl: null,
    contentType: null,
    format: inferFormat(candidate.url, candidate.format),
    reason: null,
    child: null,
  };
  try {
    const response = await fetchImpl(candidate.url, {
      method: "GET",
      redirect: "follow",
      signal: AbortSignal.timeout(timeoutMs),
      headers,
    });
    result.status = response.status;
    result.finalUrl = response.url || candidate.url;
    result.contentType = response.headers?.get?.("content-type") ?? null;
    if (!(response.status >= 200 && response.status < 300) && response.status !== 206) {
      result.reason = `http-${response.status}`;
      try { await response.body?.cancel?.(); } catch {}
      return result;
    }

    if (result.format === "hls") {
      const text = await readLimitedText(response, maxBodyBytes);
      if (!/^\s*#EXTM3U/m.test(text) || looksLikeHtml(text)) {
        result.reason = "invalid-hls-body";
        return result;
      }
      const childUrl = firstHlsChild(text, result.finalUrl);
      if (childUrl && options.probeHlsChild !== false) {
        result.child = await validateHlsChild(childUrl, headers, { fetchImpl, timeoutMs, maxBodyBytes });
        result.playable = result.child.playable;
        result.reason = result.playable ? null : `hls-child-${result.child.reason ?? "invalid"}`;
        return result;
      }
      result.playable = true;
      return result;
    }

    const contentType = String(result.contentType ?? "").toLowerCase();
    if (contentType.includes("text/html")) {
      result.reason = "html-instead-of-media";
      try { await response.body?.cancel?.(); } catch {}
      return result;
    }
    if (result.format === "mp4" || result.format === "mkv" || contentType.startsWith("video/") || contentType.includes("octet-stream")) {
      const sample = await readLimitedBytes(response, Math.min(maxBodyBytes, 32768));
      if (looksLikeHtmlBytes(sample)) {
        result.reason = "html-instead-of-media";
        return result;
      }
      result.playable = sample.length > 0 || Number(response.headers?.get?.("content-length") ?? 0) > 0;
      result.reason = result.playable ? null : "empty-media-body";
      return result;
    }

    const sample = await readLimitedBytes(response, Math.min(maxBodyBytes, 32768));
    if (looksLikeHtmlBytes(sample)) {
      result.reason = "html-instead-of-media";
      return result;
    }
    result.playable = sample.length > 0;
    result.reason = result.playable ? null : "unknown-empty-media";
    return result;
  } catch (error) {
    result.reason = String(error?.cause?.code ?? error?.name ?? error?.message ?? error);
    return result;
  }
}

export async function validateMediaCandidates(candidates = [], options = {}) {
  const maxCandidates = clamp(Number(options.maxCandidates ?? 3), 1, 6);
  const results = [];
  for (const candidate of candidates.slice(0, maxCandidates)) {
    const validation = await validateMediaCandidate(candidate, options);
    results.push({ candidate, validation });
  }
  return {
    playable: results.some((row) => row.validation.playable),
    playableCount: results.filter((row) => row.validation.playable).length,
    results,
  };
}

function inferFormat(url, explicit) {
  const hint = String(explicit ?? "").toLowerCase();
  if (hint.includes("m3u8") || hint === "hls") return "hls";
  if (hint.includes("mp4")) return "mp4";
  if (hint.includes("mkv")) return "mkv";
  const clean = String(url ?? "").split(/[?#]/)[0].toLowerCase();
  if (clean.endsWith(".m3u8")) return "hls";
  if (clean.endsWith(".mp4")) return "mp4";
  if (clean.endsWith(".mkv")) return "mkv";
  return "unknown";
}

async function validateHlsChild(url, headers, options) {
  try {
    const response = await options.fetchImpl(url, {
      method: "GET",
      redirect: "follow",
      signal: AbortSignal.timeout(options.timeoutMs),
      headers,
    });
    const out = { url, status: response.status, finalUrl: response.url || url, playable: false, reason: null };
    if (!(response.status >= 200 && response.status < 300) && response.status !== 206) {
      out.reason = `http-${response.status}`;
      try { await response.body?.cancel?.(); } catch {}
      return out;
    }
    const text = await readLimitedText(response, options.maxBodyBytes);
    if (/^\s*#EXTM3U/m.test(text) && !looksLikeHtml(text)) out.playable = true;
    else out.reason = "invalid-hls-child";
    return out;
  } catch (error) {
    return { url, playable: false, reason: String(error?.cause?.code ?? error?.name ?? error?.message ?? error) };
  }
}

function firstHlsChild(text, baseUrl) {
  const lines = text.split(/\r?\n/).map((line) => line.trim());
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line || line.startsWith("#")) continue;
    try { return new URL(line, baseUrl).href; } catch {}
  }
  return null;
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

function hasHeader(headers, name) {
  const lower = name.toLowerCase();
  return Object.keys(headers).some((key) => key.toLowerCase() === lower);
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value)));
}
