// Diagnostic/engine mirror of CORE.STREAM_IDENTITY.V1 catalogue policy.
// Production provider bundles are authoritative through the Core Lego; engine_v2
// uses this helper so smoke probes cannot silently apply a provider-local policy.

export function scoreCatalogueIdentity({
  title,
  expectedTitles = [],
  actualMedia,
  expectedMedia,
  year,
  expectedYear,
  providerId,
  strictIdentity = false,
  requireProviderTypeEvidence = false,
} = {}) {
  const candidateTitle = normalizeTitle(title);
  const targets = unique(expectedTitles.map(normalizeTitle).filter(Boolean));
  const actual = providerMedia(actualMedia);
  const expected = providerMedia(expectedMedia);
  const movie = expected === "movie";
  const candidateYear = asYear(year);
  const targetYear = asYear(expectedYear);

  if (actual && expected && actual !== expected) return -1;
  if (requireProviderTypeEvidence && (!actual || !expected)) return -1;

  if (strictIdentity) {
    if (!cleanText(providerId) || !candidateTitle || !targets.length || !targets.includes(candidateTitle)) return -1;
    if (movie && targetYear) {
      if (!candidateYear || Math.abs(candidateYear - targetYear) > 1) return -1;
    }
    return 120 + (movie && candidateYear === targetYear ? 20 : 0);
  }

  if (movie && candidateYear && targetYear && candidateYear !== targetYear) return -1;
  let score = 0;
  const primary = targets[0] ?? "";
  if (candidateTitle && targets.includes(candidateTitle)) score += 200;
  else if (candidateTitle && primary && (candidateTitle.includes(primary) || primary.includes(candidateTitle))) score += 90;
  if (candidateTitle && primary) {
    for (const token of primary.split(" ").filter((value) => value.length >= 3)) {
      if (candidateTitle.includes(token)) score += 10;
    }
  }
  if (movie && candidateYear && targetYear && candidateYear === targetYear) score += 40;
  if (actual && expected && actual === expected) score += 60;
  if (cleanText(providerId)) score += 15;
  return score;
}

export function providerMedia(value) {
  const raw = cleanText(value)?.toLowerCase() ?? "";
  if (raw === "movie") return "movie";
  if (["tv", "series", "show", "anime"].includes(raw)) return "tv";
  return "";
}

export function normalizeTitle(value) {
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
