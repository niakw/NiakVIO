import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  applyCommittedProviderLogos,
  buildCatalogFromPublished,
  manifestsFromCatalog,
  validateProviderCatalog,
  writeJson,
  loadProviderCatalog,
} from "../src/provider-catalog.mjs";
import { applyCommittedProviderNames } from "../src/provider-branding.mjs";

const general = JSON.parse(fs.readFileSync("manifest.json", "utf8"));
const vf = JSON.parse(fs.readFileSync("vf/manifest.json", "utf8"));
const catalog = buildCatalogFromPublished({ generalManifest: general, vfManifest: vf });

assert.equal(catalog.providers.length, general.scrapers.length, "catalog must preserve every general provider");
assert.equal(catalog.manifestOrder.vf.length, vf.scrapers.length, "catalog must preserve every VF provider");
assert.equal(catalog.policy.repairBeforeTriage, true);
assert.equal(catalog.policy.retainLastKnownGoodOnInconclusive, true);
assert.equal(catalog.policy.quickRefreshMayRepairAndPublish, true);

const rendered = manifestsFromCatalog(catalog);
assert.deepEqual(rendered.general, general, "general manifest must round-trip byte-semantically through catalog");
assert.deepEqual(rendered.vf, vf, "VF manifest must round-trip byte-semantically through catalog");

const brandingIndex = JSON.parse(fs.readFileSync("assets/providers/emojis.json", "utf8"));
const brandingCatalog = applyCommittedProviderNames(structuredClone(catalog), brandingIndex);
const expectedNameRows = catalog.providers.length;
assert.equal(brandingCatalog.policy.committedProviderNames, true);
assert.equal(
  brandingCatalog.policy.committedProviderNameCount,
  expectedNameRows,
  "catalog must bind every currently published provider display name",
);
assert.ok(
  Object.keys(brandingIndex.providers ?? {}).length >= catalog.providers.length,
  "branding registry may pre-register providers from a pending transaction but must cover the current catalog",
);
const brandingRendered = manifestsFromCatalog(brandingCatalog);
for (const scraper of brandingRendered.general.scrapers) {
  const branding = brandingIndex.providers?.[String(scraper.id).toLowerCase()];
  assert.ok(branding, `${scraper.id}: branding row missing`);
  assert.equal(scraper.name, `${branding.emoji} ${branding.name}`, `${scraper.id}: general display branding mismatch`);
}
for (const scraper of brandingRendered.vf.scrapers) {
  const branding = brandingIndex.providers?.[String(scraper.id).toLowerCase()];
  assert.ok(branding, `${scraper.id}: VF branding row missing`);
  assert.equal(scraper.name, `${branding.emoji} ${branding.name}`, `${scraper.id}: VF display branding mismatch`);
}
const incompleteBranding = structuredClone(brandingIndex);
delete incompleteBranding.providers[Object.keys(incompleteBranding.providers)[0]];
assert.throws(
  () => applyCommittedProviderNames(structuredClone(catalog), incompleteBranding),
  /coverage mismatch/i,
  "catalog must reject incomplete provider branding coverage",
);
const forwardBranding = structuredClone(brandingIndex);
forwardBranding.providers["future-provider-pending"] = { name: "Future Provider Pending", emoji: "🇫" };
assert.doesNotThrow(
  () => applyCommittedProviderNames(structuredClone(catalog), forwardBranding),
  "branding registry must tolerate providers pre-registered for a pending transaction",
);

const logoIndex = JSON.parse(fs.readFileSync("assets/providers/index.json", "utf8"));
const logoCatalog = applyCommittedProviderLogos(structuredClone(catalog), logoIndex);
const expectedLogoRows = Object.values(logoIndex.providers ?? {}).filter(
  (row) => typeof row?.urls?.["96x40"] === "string" && row.urls["96x40"].length > 0,
);
assert.equal(logoCatalog.policy.committedProviderLogos, true);
assert.equal(
  logoCatalog.policy.committedProviderLogoCount,
  expectedLogoRows.length,
  "catalog must bind every committed 96x40 provider logo",
);
const logoRendered = manifestsFromCatalog(logoCatalog);
const indexedIds = new Set(Object.keys(logoIndex.providers ?? {}).map((value) => value.toLowerCase()));
for (const scraper of logoRendered.general.scrapers) {
  if (!indexedIds.has(String(scraper.id).toLowerCase())) continue;
  assert.match(
    String(scraper.logo ?? ""),
    /^https:\/\/raw\.githubusercontent\.com\/niakw\/NiakVIO\/main\/assets\/providers\/96x40\//,
    `${scraper.id}: general manifest must use committed NiakVIO logo`,
  );
}
for (const scraper of logoRendered.vf.scrapers) {
  if (!indexedIds.has(String(scraper.id).toLowerCase())) continue;
  assert.match(
    String(scraper.logo ?? ""),
    /^https:\/\/raw\.githubusercontent\.com\/niakw\/NiakVIO\/main\/assets\/providers\/96x40\//,
    `${scraper.id}: VF manifest must use committed NiakVIO logo`,
  );
}
const unsafeLogoIndex = structuredClone(logoIndex);
unsafeLogoIndex.futurePolicy = "network-regeneration";
assert.throws(
  () => applyCommittedProviderLogos(structuredClone(catalog), unsafeLogoIndex),
  /committed-assets-only/i,
  "catalog must reject a logo index that permits recurring network regeneration",
);

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "niakvio-catalog-"));
const file = path.join(dir, "provider_catalog.json");
writeJson(file, catalog);
assert.deepEqual(loadProviderCatalog(file), catalog, "written catalog must reload unchanged");

const duplicate = structuredClone(catalog);
duplicate.providers.push(structuredClone(duplicate.providers[0]));
assert.throws(() => validateProviderCatalog(duplicate), /duplicate provider/i);

const unsafe = structuredClone(catalog);
unsafe.policy.repairBeforeTriage = false;
assert.throws(() => validateProviderCatalog(unsafe), /repair-before-triage/i);

console.log(
  `provider catalog tests passed: general=${general.scrapers.length} vf=${vf.scrapers.length} committed_names=${expectedNameRows} committed_logos=${expectedLogoRows.length}`,
);
