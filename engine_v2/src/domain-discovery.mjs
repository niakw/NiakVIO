import dns from "node:dns/promises";
import net from "node:net";

const INFRA_HOSTS = ["github.com", "githubusercontent.com", "google.com", "gstatic.com", "jsdelivr.net", "cloudflare.com", "postimg.cc"];

export function buildDomainCandidates(provider, legacyHub = null, legacyHistory = null) {
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
  if (legacyHub?.direct) add(legacyHub.direct, "legacy-direct", 80);
  for (const url of legacyHub?.direct_candidates ?? []) add(url, "legacy-direct-candidate", 75);
  for (const host of provider?.hosts ?? []) add(`https://${host}/`, "original-js-host", 60);

  const bestByHost = new Map();
  for (const candidate of rows) {
    const previous = bestByHost.get(candidate.host);
    if (!previous || candidate.trust > previous.trust) bestByHost.set(candidate.host, candidate);
  }
  return [...bestByHost.values()].sort((a, b) => b.trust - a.trust || a.host.localeCompare(b.host));
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
    if (!url.hostname) return null;
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
