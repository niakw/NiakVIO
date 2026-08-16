#!/usr/bin/env node
import fs from "node:fs";
import { buildCatalogFromPublished, writeJson } from "../src/provider-catalog.mjs";

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

const generalManifest = JSON.parse(fs.readFileSync(generalPath, "utf8"));
const vfManifest = JSON.parse(fs.readFileSync(vfPath, "utf8"));
const catalog = buildCatalogFromPublished({ generalManifest, vfManifest });
writeJson(outputPath, catalog);

const vfCount = catalog.providers.filter((row) => row.projections.vf).length;
console.log(`provider catalog bootstrapped: providers=${catalog.providers.length} vf=${vfCount} output=${outputPath}`);
