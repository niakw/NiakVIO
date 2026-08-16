#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { buildProviderInventory, inventoryStats } from "../src/provider-ingest.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const configPath = path.join(root, "config", "provider-upstreams.json");
const output = argValue("--output") ?? path.join(root, "reports", "provider-upstream-inventory.json");
const config = JSON.parse(await fs.readFile(configPath, "utf8"));
const manifests = [];

for (const upstream of config.upstreams) {
  const candidates = [upstream.repository, upstream.fallback_repository].filter(Boolean);
  let loaded = null;
  let lastError = null;
  for (const repository of candidates) {
    try {
      const head = await githubJson(`/repos/${repository}/commits/${encodeURIComponent(upstream.branch)}`);
      const content = await githubJson(`/repos/${repository}/contents/${encodePath(upstream.manifest)}?ref=${encodeURIComponent(head.sha)}`);
      const raw = Buffer.from(content.content, "base64").toString("utf8");
      loaded = {
        upstreamId: upstream.id,
        repository,
        ref: head.sha,
        manifestSha: content.sha,
        manifest: JSON.parse(raw),
      };
      break;
    } catch (error) {
      lastError = error;
    }
  }
  if (!loaded) throw new Error(`${upstream.id}: no manifest source available: ${lastError?.message ?? lastError}`);
  manifests.push(loaded);
}

const inventory = buildProviderInventory(manifests);
const report = {
  schema_version: 1,
  generated_at: new Date().toISOString(),
  sources: manifests.map(({ upstreamId, repository, ref, manifestSha, manifest }) => ({
    upstreamId,
    repository,
    ref,
    manifestSha,
    manifestName: manifest.name ?? null,
    manifestVersion: manifest.version ?? null,
    scraperCount: manifest.scrapers?.length ?? 0,
  })),
  stats: inventoryStats(inventory),
  ...inventory,
};

await fs.mkdir(path.dirname(output), { recursive: true });
await fs.writeFile(output, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ generated_at: report.generated_at, sources: report.sources, stats: report.stats }, null, 2));

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

function encodePath(value) {
  return String(value).split("/").map(encodeURIComponent).join("/");
}

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}
