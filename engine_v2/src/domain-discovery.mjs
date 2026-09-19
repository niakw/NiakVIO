import dns from "node:dns/promises";
import net from "node:net";

const INFRA_HOSTS = [
  "github.com", "githubusercontent.com", "google.com", "gstatic.com", "jsdelivr.net", "cloudflare.com", "postimg.cc",
  "themoviedb.org", "npms.io", "lodash.com", "openjsf.org", "underscorejs.org", "strem.io", "kitsu.io", "haglund.dev",
];

export function buildDomainCandidates(provider, legacyHub = null, legacyHistory = null, discoveredCandidates = []) {
  const rows = [];
  const add = (url, source, trust, role = "terminal") => {
    const normalized = normalizeHttpUrl(url);
    if (!normalized) return;
    const host = new URL(normalized).hostname.toLowerCase();
    if (isInfrastructureHost(host) && role !== "registry") return;
    rows.push({ url: normalized, host, source, trust, role });
  };

  if (legacyHub?.hub) add(legacyHub.hub, "legacy-official-hub", 100, "hub");
  for (const source of legacyHub?.sources ?? []) {
    if (source.type === "hub" && source.url) add(source.url, "legacy-official-hub", Number(source.priority ?? 95), "hub");
  }
  if (legacyHistory?.current?.url) add(legacyHistory.current.url, "lkg-history", 90, "terminal");
  for (const candidate of discoveredCandidates ?? []) add(candidate.url ?? candidate, candidate.source ?? "discovered", Number(candidate.trust ?? 85), candidate.role ?? "terminal");
  if (legacyHub?.direct) add(legacyHub.direct, "legacy-direct", 80, "terminal");
  for (const url of legacyHub?.direct_candidates ?? []) add(url, "legacy-direct-candidate", 75, "terminal");
  for (const host of provider?.providerCandidateHosts ?? provider?.hosts ?? []) add(`https://${host}/`, "original-js-host", 60, "terminal");

  const bestByRoleHost = new Map();
  for (const candidate of rows) {
    const key = `${candidate.role}:${candidate.host}`;
    const previous = bestByRoleHost.get(key);
    if (!previous || candidate.trust > previous.trust) bestByRoleHost.set(key, candidate);
  }
  return [...bestByRoleHost.values()].sort((a, b) => b.trust - a.trust || a.host.localeCompare(b.host));
}

export async function fetchHubOutboundCandidates(hubUrl, provider, legacyHub = {}, options = {}) {
  const normalized = normalizeHttpUrl(hubUrl);
  if (!normalized) return [];
  const timeoutMs = Math.max(1000, Math.min(10000, Number(options.timeoutMs ?? 5000)));
  try {
    const response = await fetch(normalized, {
      signal: AbortSignal.timeout(timeoutMs),
      redirect: "follow",
      headers: {
        "User-Agent": "Mozilla/5.0 (NiakVIO Provider Engine V2 hub discovery)",
        Accept: "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.2",
      },
    });
    const text = await response.text();
    if (text.length > 2_000_000) return [];
    const finalUrl = normalizeHttpUrl(response.url || normalized) ?? normalized;
    const hubHost = new URL(normalized).hostname.toLowerCase();
    const finalHost = new URL(finalUrl).hostname.toLowerCase();
    const found = [];
    if (finalHost !== hubHost && terminalHostAllowed(finalHost, provider, legacyHub)) {
      found.push({ url: finalUrl, trust: 97, source: "official-hub-redirect", role: "terminal" });
    }
    const hrefRe = /\bhref\s*=\s*["']([^"']+)["']/gi;
    let match;
    while ((match = hrefRe.exec(text))) {
      let resolved;
      try { resolved = new URL(match[1], finalUrl).href; } catch { continue; }
      const candidate = normalizeHttpUrl(resolved);
      if (!candidate) continue;
      const candidateHost = new URL(candidate).hostname.toLowerCase();
      if (candidateHost === hubHost || candidateHost === finalHost && finalHost === hubHost) continue;
      if (isInfrastructureHost(candidateHost)) continue;
      if (!terminalHostAllowed(candidateHost, provider, legacyHub)) continue;
      found.push({ url: candidate, trust: 96, source: "official-hub-outbound", role: "terminal" });
    }
    return dedupeByHost(found);
  } catch {
    return [];
  }
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
      if (relevant) candidates.push({
        url: normalized,
        trust: pathText && aliases.some((alias) => pathText.includes(alias)) ? 88 : 84,
        registryPath: path.join("."),
        source: "original-js-domain-registry",
        role: "terminal",
      });
      return;
    }
    if (Array.isArray(value)) return value.forEach((item, index) => visit(item, [...path, String(index)]));
    if (value && typeof value === "object") return Object.entries(value).forEach(([key, item]) => visit(item, [...path, key]));
  };
  visit(payload);
  return dedupeByHost(candidates.filter((candidate) => !isInfrastructureHost(new URL(candidate.url).hostname.toLowerCase())));
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
  const viable = probes.filter((probe) => probe.role !== "hub" && probe.dns?.ok && probe.reachable);
  viable.sort((a, b) => {
    const aUseful = usefulHttpRank(a.http?.status);
    const bUseful = usefulHttpRank(b.http?.status);
    return bUseful - aUseful || b.trust - a.trust;
  });
  return viable[0] ?? null;
}

function terminalHostAllowed(host, provider, legacyHub) {
  const exact = new Set((legacyHub.allowed_terminal_hosts ?? []).map((value) => String(value).toLowerCase().replace(/^www\./, "")));
  const normalizedHost = host.replace(/^www\./, "");
  if (exact.has(normalizedHost)) return true;
  for (const raw of legacyHub.allowed_terminal_host_patterns ?? []) {
    try { if (new RegExp(raw, "i").test(host)) return true; } catch {}
  }
  const aliases = providerAliases({ ...provider, names: [...(provider.names ?? []), ...(legacyHub.aliases ?? [])] });
  const compactHost = host.replace(/[^a-z0-9]/g, "");
  return aliases.some((alias) => compactHost.includes(alias) || alias.includes(compactHost));
}

function providerAliases(provider) {
  return [...new Set([provider.id, ...(provider.names ?? [])]
    .map((value) => String(value ?? "").toLowerCase().replace(/[^a-z0-9]/g, ""))
    .filter((value) => value.length >= 3))];
}

function dedupeByHost(candidates) {
  const map = new Map();
  for (const candidate of candidates) {
    const normalized = normalizeHttpUrl(candidate.url);
    if (!normalized) continue;
    const host = new URL(normalized).hostname.toLowerCase();
    const next = { ...candidate, url: normalized, host };
    const previous = map.get(host);
    if (!previous || Number(next.trust ?? 0) > Number(previous.trust ?? 0)) map.set(host, next);
  }
  return [...map.values()].sort((a, b) => Number(b.trust ?? 0) - Number(a.trust ?? 0));
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
