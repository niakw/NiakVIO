#!/usr/bin/env node
import fs from "node:fs";
import { applyCommittedProviderLogos, buildCatalogFromPublished, writeJson } from "../src/provider-catalog.mjs";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const key = process.argv[i];
  if (!key.startsWith("--")) continue;
  const value = process.argv[i + 1] && !process.argv[i + 1].startsWith("--") ? process.argv[++i] : true;
  args.set(key, value);
}

const generalPath = String(args.get("--general") || "manifest.json");
const vfPath = String(args.get("--vf") || "vf/manifest.json");
const outputPath = String(args.get("--output") || "provider_catalog.json");
const logoIndexPath = String(args.get("--logo-index") || "assets/providers/index.json");

const generalManifest = JSON.parse(fs.readFileSync(generalPath, "utf8"));
const vfManifest = JSON.parse(fs.readFileSync(vfPath, "utf8"));
let catalog = buildCatalogFromPublished({ generalManifest, vfManifest });
let logoCount = 0;
if (fs.existsSync(logoIndexPath)) {
  const logoIndex = JSON.parse(fs.readFileSync(logoIndexPath, "utf8"));
  catalog = applyCommittedProviderLogos(catalog, logoIndex);
  logoCount = Number(catalog.policy?.committedProviderLogoCount || 0);
}
writeJson(outputPath, catalog);

const vfCount = catalog.providers.filter((row) => row.projections.vf).length;
console.log(
  `provider catalog bootstrapped: providers=${catalog.providers.length} vf=${vfCount} ` +
  `committed_logos=${logoCount} output=${outputPath}`
);