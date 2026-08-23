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
  `provider catalog tests passed: general=${general.scrapers.length} vf=${vf.scrapers.length} committed_logos=${expectedLogoRows.length}`,
);
