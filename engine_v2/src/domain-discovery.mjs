import dns from "node:dns/promises";
import net from "node:net";

const INFRA_HOSTS = [
  "github.com", "githubusercontent.com", "google.com", "gstatic.com", "jsdelivr.net", "cloudflare.com", "postimg.cc",
  "themoviedb.org", "npms.io", "lodash.com", "openjsf.org", "underscorejs.org", "strem.io", "kitsu.io", "haglund.dev",
];

export function buildDomainCandidates(provider, legacyHub = null, legacyHistory = null, registryCandidates = []) {
  const rows = [];
  const add = (url, source, trust) => {
    const normalized = normalizeHttpUrl(url);
    if (!normalized) return;
    const host = new URL(normalized).hostname.toLowerCase();
    if (isInfrastructureHost(host)) return;
    rows.push({ url: normalized, host, source, trust });
  };

  if (legacyHub?.hub) add(legacyHub.hub, "legacy-official-hub", 100);
  for (const source of legacyHub?.sources ?? []) {
    if (source.type === "hub" && source.url) add(source.url, "legacy-official-hub", Number(source.priority ?? 95));
  }
  if (legacyHistory?.current?.url) add(legacyHistory.current.url, "lkg-history", 90);
  for (const candidate of registryCandidates ?? []) add(candidate.url ?? candidate, "original-js-domain-registry", Number(candidate.trust ?? 85));
  if (legacyHub?.direct) add(legacyHub.direct, "legacy-direct", 80);
  for (const url of legacyHub?.direct_candidates ?? []) add(url, "legacy-direct-candidate", 75);
  for (const host of provider?.providerCandidateHosts ?? provider?.hosts ?? []) add(`https://${host}/`, "original-js-host", 60);

  const bestByHost = new Map();
  for (const candidate of rows) {
    const previous = bestByHost.get(candidate.host);
    if (!previous || candidate.trust > previous.trust) bestByHost.set(candidate.host, candidate);
  }
  return [...bestByHost.values()].sort((a, b) => b.trust - a.trust || a.host.localeCompare(b.host));
}

export async function fetchDomainRegistryCandidates(registryUrl, provider, options = {}) {
  const normalized = normalizeHttpUrl(registryUrl);
  if (!normalized) return [];
  const host = new URL(normalized).hostname.toLowerCase();
  if (!isInfrastructureHost(host) && options.allowNonInfrastructureRegistry !== true) return [];
  const timeoutMs = Math.max(1000, Math.min(10000, Number(options.timeoutMs ?? 5000)));
  try {
    const response = await fetch(normalized, {
      signal: AbortSignal.timeout(timeoutMs),
      redirect: "follow",
      headers: { "User-Agent": "NiakVIO-Provider-Engine-V2", Accept: "application/json,text/plain;q=0.9,*/*;q=0.2" },
    });
    if (!response.ok) return [];
    const text = await response.text();
    if (text.length > 2_000_000) return [];
    let payload;
    try { payload = JSON.parse(text); } catch { return []; }
    return extractDomainCandidatesFromRegistry(payload, provider);
  } catch { return []; }
}

export function extractDomainCandidatesFromRegistry(payload, provider = {}) {
  const aliases = providerAliases(provider);
  const candidates = [];
  const visit = (value, path = []) => {
    if (typeof value === "string") {
      const normalized = normalizeDomainishString(value);
      if (!normalized) return;
      const pathText = path.join(" ").toLowerCase();
      const host = new URL(normalized).hostname.toLowerCase();
      const hostText = host.replace(/[^a-z0-9]/g, "");
      const relevant = aliases.length === 0 || aliases.some((alias) => pathText.includes(alias) || hostText.includes(alias));
      if (relevant) candidates.push({ url: normalized, trust: pathText && aliases.some((alias) => pathText.includes(alias)) ? 88 : 84, registryPath: path.join(".") });
      return;
    }
    if (Array.isArray(value)) return value.forEach((item, index) => visit(item, [...path, String(index)]));
    if (value && typeof value === "object") return Object.entries(value).forEach(([key, item]) => visit(item, [...path, key]));
  };
  visit(payload);
  const byHost = new Map();
  for (const candidate of candidates) {
    const host = new URL(candidate.url).hostname.toLowerCase();
    if (isInfrastructureHost(host)) continue;
    const previous = byHost.get(host);
    if (!previous || candidate.trust > previous.trust) byHost.set(host, candidate);
  }
  return [...byHost.values()].sort((a, b) => b.trust - a.trust);
}

export async function probeDomainCandidate(candidate, options = {}) {
  const timeoutMs = Math.max(1000, Math.min(10000, Number(options.timeoutMs ?? 5000)));
  const result = {
    ...candidate,
    dns: { ok: false, addresses: [], error: null },
    http: { attempted: false, status: null, finalUrl: null, contentType: null, error: null },
    reachable: false,
  };
  try {
    const addresses = await dns.lookup(candidate.host, { all: true, verbatim: true });
    const publicAddresses = addresses.map((row) => row.address).filter(isPublicIp);
    result.dns = { ok: publicAddresses.length > 0, addresses: publicAddresses, error: null };
    if (!result.dns.ok) return result;
  } catch (error) {
    result.dns.error = String(error?.code ?? error?.message ?? error);
    return result;
  }

  result.http.attempted = true;
  try {
    const response = await fetch(candidate.url, {
      method: "GET",
      redirect: "follow",
      signal: AbortSignal.timeout(timeoutMs),
      headers: {
        "User-Agent": "Mozilla/5.0 (NiakVIO Provider Engine V2 domain probe)",
        Accept: "text/html,application/json,text/plain,*/*;q=0.5",
      },
    });
    const finalUrl = response.url || candidate.url;
    const finalHost = new URL(finalUrl).hostname.toLowerCase();
    result.http.status = response.status;
    result.http.finalUrl = finalUrl;
    result.http.contentType = response.headers.get("content-type");
    result.http.finalHost = finalHost;
    result.http.redirected = finalHost !== candidate.host;
    result.reachable = response.status > 0;
    try { await response.body?.cancel(); } catch {}
  } catch (error) {
    result.http.error = String(error?.cause?.code ?? error?.name ?? error?.message ?? error);
  }
  return result;
}

export function chooseBestObservedDomain(probes = []) {
  const viable = probes.filter((probe) => probe.dns?.ok && probe.reachable);
  viable.sort((a, b) => {
    const aUseful = usefulHttpRank(a.http?.status);
    const bUseful = usefulHttpRank(b.http?.status);
    return bUseful - aUseful || b.trust - a.trust;
  });
  return viable[0] ?? null;
}

function providerAliases(provider) {
  return [...new Set([provider.id, ...(provider.names ?? [])]
    .map((value) => String(value ?? "").toLowerCase().replace(/[^a-z0-9]/g, ""))
    .filter((value) => value.length >= 3))];
}

function normalizeDomainishString(value) {
  const raw = String(value).trim();
  if (!raw || raw.includes("${")) return null;
  if (/^https?:\/\//i.test(raw)) return normalizeHttpUrl(raw);
  if (/^(?:[a-z0-9-]+\.)+[a-z]{2,20}(?:\/.*)?$/i.test(raw)) return normalizeHttpUrl(`https://${raw}`);
  return null;
}

function usefulHttpRank(status) {
  const code = Number(status);
  if (code >= 200 && code < 400) return 4;
  if ([401, 403, 429, 451].includes(code)) return 3;
  if (code >= 400 && code < 500) return 2;
  if (code >= 500) return 1;
  return 0;
}

function normalizeHttpUrl(value) {
  try {
    const url = new URL(String(value));
    if (!["http:", "https:"].includes(url.protocol)) return null;
    if (!url.hostname || url.hostname.includes("$") || !url.hostname.includes(".")) return null;
    return url.href;
  } catch { return null; }
}

function isInfrastructureHost(host) {
  return INFRA_HOSTS.some((suffix) => host === suffix || host.endsWith(`.${suffix}`));
}

function isPublicIp(value) {
  if (!net.isIP(value)) return false;
  if (value.includes(":")) {
    const low = value.toLowerCase();
    return !(low === "::1" || low.startsWith("fe80:") || low.startsWith("fc") || low.startsWith("fd"));
  }
  const [a, b] = value.split(".").map(Number);
  if (a === 10 || a === 127 || a === 0) return false;
  if (a === 169 && b === 254) return false;
  if (a === 172 && b >= 16 && b <= 31) return false;
  if (a === 192 && b === 168) return false;
  if (a >= 224) return false;
  return true;
}
