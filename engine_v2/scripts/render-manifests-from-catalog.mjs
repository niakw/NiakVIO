#!/usr/bin/env node
import { loadProviderCatalog, manifestsFromCatalog, writeJson } from "../src/provider-catalog.mjs";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const key = process.argv[i];
  if (!key.startsWith("--")) continue;
  const value = process.argv[i + 1] && !process.argv[i + 1].startsWith("--") ? process.argv[++i] : true;
  args.set(key, value);
}

function excludedFromNoAnime(scraper) {
  const rawTypes = Array.isArray(scraper?.supportedTypes)
    ? scraper.supportedTypes
    : typeof scraper?.supportedTypes === "string" ? [scraper.supportedTypes] : [];
  const types = rawTypes.map((value) => String(value).trim().toLowerCase()).filter(Boolean);
  const animeOnly = types.length > 0 && new Set(types).size === 1 && types[0] === "anime";
  const identity = [scraper?.id, scraper?.name].filter(Boolean).join(" ").toLowerCase();
  return animeOnly || identity.includes("anim");
}

function noAnimeProjection(source) {
  const copy = structuredClone(source);
  copy.name = String(source.name || "Nuvio Curated Providers") + " — Without anime providers";
  copy.scrapers = (source.scrapers || []).filter((row) => !excludedFromNoAnime(row));
  return copy;
}

const catalogPath = String(args.get("--catalog") || "provider_catalog.json");
const generalPath = String(args.get("--general") || "manifest.json");
const vfPath = String(args.get("--vf") || "vf/manifest.json");
const generalNoAnimePath = String(args.get("--no-anime") || "no-anime/manifest.json");
const vfNoAnimePath = String(args.get("--vf-no-anime") || "vf-no-anime/manifest.json");
const catalog = loadProviderCatalog(catalogPath);
const manifests = manifestsFromCatalog(catalog);
const generalNoAnime = noAnimeProjection(manifests.general);
const vfNoAnime = noAnimeProjection(manifests.vf);
writeJson(generalPath, manifests.general);
writeJson(vfPath, manifests.vf);
writeJson(generalNoAnimePath, generalNoAnime);
writeJson(vfNoAnimePath, vfNoAnime);
console.log(
  "rendered manifests from " + catalogPath +
  ": general=" + manifests.general.scrapers.length +
  " vf=" + manifests.vf.scrapers.length +
  " general_no_anime=" + generalNoAnime.scrapers.length +
  " vf_no_anime=" + vfNoAnime.scrapers.length,
);
