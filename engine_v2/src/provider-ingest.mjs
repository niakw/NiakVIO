import { normalizeMediaType } from "./contracts.mjs";

export function normalizeUpstreamScraper(raw = {}, source = {}) {
  const id = text(raw.id)?.toLowerCase();
  if (!id) throw new Error("upstream scraper id is required");
  const filename = text(raw.filename);
  if (!filename) throw new Error(`${id}: filename is required`);

  const supportedTypes = unique((raw.supportedTypes ?? ["movie", "tv"]).map((type) => normalizeMediaType(type)));
  const languages = uniqueStrings(raw.contentLanguage).map(normalizeLanguageCode);
  const formats = uniqueStrings(raw.supportedFormats ?? raw.formats);

  return {
    id,
    name: text(raw.name) ?? id,
    description: text(raw.description),
    version: text(raw.version),
    author: text(raw.author),
    filename,
    enabledUpstream: raw.enabled !== false,
    hasSettings: raw.hasSettings === true,
    limited: raw.limited === true,
    supportsExternalPlayer: raw.supportsExternalPlayer === true,
    supportedTypes,
    languages: unique(languages),
    formats,
    supportedPlatforms: uniqueStrings(raw.supportedPlatforms),
    disabledPlatforms: uniqueStrings(raw.disabledPlatforms),
    source: {
      upstreamId: source.upstreamId ?? null,
      repository: source.repository ?? null,
      ref: source.ref ?? null,
      manifestSha: source.manifestSha ?? null,
      filename,
    },
    raw: structuredClone(raw),
  };
}

export function buildProviderInventory(sourceManifests = []) {
  const variants = [];
  for (const source of sourceManifests) {
    for (const scraper of source.manifest?.scrapers ?? []) {
      variants.push(normalizeUpstreamScraper(scraper, {
        upstreamId: source.upstreamId,
        repository: source.repository,
        ref: source.ref,
        manifestSha: source.manifestSha,
      }));
    }
  }

  const grouped = new Map();
  for (const variant of variants) {
    if (!grouped.has(variant.id)) grouped.set(variant.id, []);
    grouped.get(variant.id).push(variant);
  }

  const providers = [...grouped.entries()].map(([id, providerVariants]) => mergeProviderVariants(id, providerVariants));
  providers.sort((a, b) => a.id.localeCompare(b.id));

  return {
    providerCount: providers.length,
    variantCount: variants.length,
    duplicateProviderCount: providers.filter((provider) => provider.variants.length > 1).length,
    providers,
  };
}

export function mergeProviderVariants(id, variants) {
  if (!variants.length) throw new Error(`${id}: no variants`);
  return {
    id,
    names: unique(variants.map((v) => v.name).filter(Boolean)),
    supportedTypes: unique(variants.flatMap((v) => v.supportedTypes)),
    languages: unique(variants.flatMap((v) => v.languages)),
    formats: unique(variants.flatMap((v) => v.formats)),
    hasSettings: variants.some((v) => v.hasSettings),
    limited: variants.some((v) => v.limited),
    supportsExternalPlayer: variants.some((v) => v.supportsExternalPlayer),
    supportedPlatforms: unique(variants.flatMap((v) => v.supportedPlatforms)),
    disabledPlatforms: unique(variants.flatMap((v) => v.disabledPlatforms)),
    upstreamEnabledStates: Object.fromEntries(variants.map((v) => [v.source.upstreamId, v.enabledUpstream])),
    sources: variants.map((v) => v.source),
    variants,
    selection: null,
    state: "unobserved",
  };
}

export function inventoryStats(inventory) {
  const providers = inventory.providers ?? [];
  return {
    providers: providers.length,
    variants: inventory.variantCount ?? providers.reduce((sum, p) => sum + p.variants.length, 0),
    duplicates: providers.filter((p) => p.variants.length > 1).length,
    withSettings: providers.filter((p) => p.hasSettings).length,
    withPlatformConstraints: providers.filter((p) => p.supportedPlatforms.length || p.disabledPlatforms.length).length,
    movie: providers.filter((p) => p.supportedTypes.includes("movie")).length,
    tv: providers.filter((p) => p.supportedTypes.includes("tv")).length,
    anime: providers.filter((p) => p.supportedTypes.includes("anime")).length,
  };
}

function normalizeLanguageCode(value) {
  const code = String(value).trim().toLowerCase();
  const aliases = { hin: "hi", tam: "ta", tel: "te", eng: "en", fre: "fr", fra: "fr", jpn: "ja" };
  return aliases[code] ?? code;
}

function uniqueStrings(value) {
  const list = Array.isArray(value) ? value : value == null ? [] : [value];
  return unique(list.map(text).filter(Boolean).map((v) => v.toLowerCase()));
}

function unique(values) {
  return [...new Set(values)];
}

function text(value) {
  if (value == null) return null;
  const out = String(value).trim();
  return out || null;
}
