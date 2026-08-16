#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import {
  buildDomainCandidates,
  chooseBestObservedDomain,
  fetchDomainRegistryCandidates,
  fetchHubOutboundCandidates,
  probeDomainCandidate,
} from "../src/domain-discovery.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const repoRoot = path.resolve(root, "..");
const knowledgePath = argValue("--knowledge") ?? path.join(root, "reports", "provider-knowledge-seed.json");
const outputPath = argValue("--output") ?? path.join(root, "reports", "provider-domain-observations.json");
const maxCandidates = Math.max(1, Math.min(6, Number(argValue("--max-candidates") ?? 4)));
const concurrency = Math.max(1, Math.min(16, Number(argValue("--concurrency") ?? 10)));
const timeoutMs = Math.max(1000, Math.min(10000, Number(argValue("--timeout-ms") ?? 5000)));

const [knowledge, hubs, history] = await Promise.all([
  readJson(knowledgePath, { providers: [] }),
  readJson(path.join(repoRoot, "provider-hubs.json"), { providers: {} }),
  readJson(path.join(repoRoot, "provider-domain-history.json"), { providers: {} }),
]);

const providers = await mapLimit(knowledge.providers ?? [], concurrency, async (provider) => {
  const hubCfg = hubs.providers?.[provider.id] ?? null;
  const discoveredCandidates = [];
  const registryCandidates = [];
  const hubCandidates = [];

  for (const registryUrl of provider.domainRegistries ?? []) {
    const found = await fetchDomainRegistryCandidates(registryUrl, provider, { timeoutMs });
    registryCandidates.push(...found.map((candidate) => ({ ...candidate, registryUrl })));
  }
  discoveredCandidates.push(...registryCandidates);

  const hubUrls = new Set([
    hubCfg?.hub,
    ...(hubCfg?.sources ?? []).filter((source) => source.type === "hub").map((source) => source.url),
  ].filter(Boolean));
  for (const hubUrl of hubUrls) {
    const found = await fetchHubOutboundCandidates(hubUrl, provider, hubCfg ?? {}, { timeoutMs });
    hubCandidates.push(...found.map((candidate) => ({ ...candidate, hubUrl })));
  }
  discoveredCandidates.push(...hubCandidates);

  const candidates = buildDomainCandidates(
    provider,
    hubCfg,
    history.providers?.[provider.id],
    discoveredCandidates,
  ).slice(0, maxCandidates);
  const probes = [];
  for (const candidate of candidates) probes.push(await probeDomainCandidate(candidate, { timeoutMs }));
  const selected = chooseBestObservedDomain(probes);
  return {
    id: provider.id,
    registries: provider.domainRegistries ?? [],
    hubUrls: [...hubUrls],
    registryCandidateCount: registryCandidates.length,
    hubTerminalCandidateCount: hubCandidates.length,
    candidateCount: candidates.length,
    selected: selected ? {
      url: selected.http.finalUrl ?? selected.url,
      host: selected.http.finalHost ?? selected.host,
      status: selected.http.status,
      source: selected.source,
      trust: selected.trust,
    } : null,
    probes,
  };
});

const report = {
  schema_version: 3,
  generated_at: new Date().toISOString(),
  policy: "report-only; hubs are discovery sources and are never selected as terminal provider domains",
  stats: {
    providers: providers.length,
    withDomainRegistries: providers.filter((p) => p.registries.length > 0).length,
    registryCandidatesFound: providers.reduce((sum, p) => sum + p.registryCandidateCount, 0),
    withOfficialHubs: providers.filter((p) => p.hubUrls.length > 0).length,
    hubTerminalCandidatesFound: providers.reduce((sum, p) => sum + p.hubTerminalCandidateCount, 0),
    withCandidates: providers.filter((p) => p.candidateCount > 0).length,
    withReachableDomain: providers.filter((p) => p.selected).length,
    withoutCandidates: providers.filter((p) => p.candidateCount === 0).length,
    unresolved: providers.filter((p) => p.candidateCount > 0 && !p.selected).length,
  },
  providers,
};
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report.stats, null, 2));

async function readJson(file, fallback) {
  try { return JSON.parse(await fs.readFile(file, "utf8")); } catch { return fallback; }
}

async function mapLimit(values, limit, mapper) {
  const results = new Array(values.length);
  let cursor = 0;
  async function worker() {
    while (true) {
      const index = cursor++;
      if (index >= values.length) return;
      results[index] = await mapper(values[index], index);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, values.length || 1) }, () => worker()));
  return results;
}

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}
