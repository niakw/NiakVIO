#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { analyzeProviderCode, mergeProviderKnowledge } from "../src/provider-analysis.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const inventoryPath = argValue("--inventory") ?? path.join(root, "reports", "provider-upstream-inventory.json");
const outputPath = argValue("--output") ?? path.join(root, "reports", "provider-knowledge-seed.json");
const concurrency = Math.max(1, Math.min(12, Number(argValue("--concurrency") ?? 8)));
const inventory = JSON.parse(await fs.readFile(inventoryPath, "utf8"));
const cache = new Map();
let analyzedVariantCount = 0;
let errorCount = 0;

const providers = await mapLimit(inventory.providers ?? [], concurrency, async (provider) => {
  const variants = await mapLimit(provider.variants ?? [], concurrency, async (variant) => {
    const source = variant.source ?? {};
    const key = [source.repository, source.ref, source.filename].join("::");
    try {
      let code = cache.get(key);
      if (code == null) {
        const response = await githubJson(`/repos/${source.repository}/contents/${encodePath(source.filename)}?ref=${encodeURIComponent(source.ref)}`);
        code = Buffer.from(response.content, "base64").toString("utf8");
        cache.set(key, code);
      }
      analyzedVariantCount += 1;
      return {
        source,
        version: variant.version,
        upstreamName: variant.name,
        analysis: analyzeProviderCode(code),
        error: null,
      };
    } catch (error) {
      errorCount += 1;
      return {
        source,
        version: variant.version,
        upstreamName: variant.name,
        analysis: analyzeProviderCode(""),
        error: String(error?.message ?? error),
      };
    }
  });
  return mergeProviderKnowledge(provider, variants);
});

const report = {
  schema_version: 1,
  generated_at: new Date().toISOString(),
  source_inventory_generated_at: inventory.generated_at ?? null,
  stats: {
    providers: providers.length,
    variants: providers.reduce((sum, provider) => sum + provider.variants.length, 0),
    analyzedVariants: analyzedVariantCount,
    errors: errorCount,
    providersWithPartialKnowledge: providers.filter((provider) => provider.state === "knowledge-partial").length,
    providersWithSettings: providers.filter((provider) => provider.requiresSettings).length,
    providersWithReferer: providers.filter((provider) => provider.observedHeaders.referer).length,
    providersWithOrigin: providers.filter((provider) => provider.observedHeaders.origin).length,
    providersWithCookies: providers.filter((provider) => provider.observedHeaders.cookie).length,
    providersWithEpisodeLogic: providers.filter((provider) => provider.observedStages.episode).length,
  },
  providers,
};

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report.stats, null, 2));

async function githubJson(apiPath) {
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": "NiakVIO-Provider-Engine-V2",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const response = await fetch(`https://api.github.com${apiPath}`, { headers });
  if (!response.ok) throw new Error(`GitHub ${response.status} for ${apiPath}: ${await response.text()}`);
  return response.json();
}

async function mapLimit(values, limit, mapper) {
  const results = new Array(values.length);
  let index = 0;
  async function worker() {
    while (true) {
      const current = index++;
      if (current >= values.length) return;
      results[current] = await mapper(values[current], current);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, values.length || 1) }, () => worker()));
  return results;
}

function encodePath(value) {
  return String(value).split("/").map(encodeURIComponent).join("/");
}

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}
