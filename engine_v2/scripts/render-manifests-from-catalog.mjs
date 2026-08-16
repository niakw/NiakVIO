#!/usr/bin/env node
import { loadProviderCatalog, manifestsFromCatalog, writeJson } from "../src/provider-catalog.mjs";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const key = process.argv[i];
  if (!key.startsWith("--")) continue;
  const value = process.argv[i + 1] && !process.argv[i + 1].startsWith("--") ? process.argv[++i] : true;
  args.set(key, value);
}

const catalogPath = String(args.get("--catalog") || "provider_catalog.json");
const generalPath = String(args.get("--general") || "manifest.json");
const vfPath = String(args.get("--vf") || "vf/manifest.json");
const catalog = loadProviderCatalog(catalogPath);
const manifests = manifestsFromCatalog(catalog);
writeJson(generalPath, manifests.general);
writeJson(vfPath, manifests.vf);
console.log(`rendered manifests from ${catalogPath}: general=${manifests.general.scrapers.length} vf=${manifests.vf.scrapers.length}`);
