#!/usr/bin/env node
import fs from "node:fs";
import { loadProviderCatalog } from "../src/provider-catalog.mjs";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const key = process.argv[i];
  if (!key.startsWith("--")) continue;
  const value = process.argv[i + 1] && !process.argv[i + 1].startsWith("--") ? process.argv[++i] : true;
  args.set(key, value);
}

const catalogPath = String(args.get("--catalog") || "provider_catalog.json");
const stagePath = String(args.get("--stage") || "staging/candidates.json");
const requirePublishedBaseline = args.get("--allow-missing-baseline") !== true;
const catalog = loadProviderCatalog(catalogPath);
const stage = JSON.parse(fs.readFileSync(stagePath, "utf8"));
const candidates = Array.isArray(stage.candidates) ? stage.candidates : [];
const byCanonical = new Map();
for (const candidate of candidates) {
  if (!candidate || typeof candidate !== "object") continue;
  const id = String(candidate.canonical_id || candidate.upstream_id || "").trim().toLowerCase();
  if (!id) continue;
  if (!byCanonical.has(id)) byCanonical.set(id, []);
  byCanonical.get(id).push(candidate);
}

const missing = [];
const missingBaseline = [];
for (const provider of catalog.providers) {
  const variants = byCanonical.get(provider.canonicalId) || [];
  if (!variants.length) {
    missing.push(provider.canonicalId);
    continue;
  }
  if (requirePublishedBaseline && !variants.some((row) => row.source === "published-baseline" || row.source === "local-lkg" || row.baseline === true)) {
    missingBaseline.push(provider.canonicalId);
  }
}

if (missing.length || missingBaseline.length) {
  const details = [];
  if (missing.length) details.push(`missing canonical providers: ${missing.join(", ")}`);
  if (missingBaseline.length) details.push(`missing LKG/published baseline: ${missingBaseline.join(", ")}`);
  throw new Error(`staging/catalog preservation gate failed\n- ${details.join("\n- ")}`);
}

const discoveredIds = [...byCanonical.keys()];
const catalogIds = new Set(catalog.providers.map((row) => row.canonicalId));
const newUpstreamProviders = discoveredIds.filter((id) => !catalogIds.has(id));
console.log(JSON.stringify({
  catalogProviders: catalog.providers.length,
  stagedCanonicalProviders: byCanonical.size,
  stagedVariants: candidates.length,
  preservedCatalogProviders: catalog.providers.length - missing.length,
  newUpstreamProviders,
}, null, 2));
