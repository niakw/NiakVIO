import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { buildCatalogFromPublished, manifestsFromCatalog, validateProviderCatalog, writeJson, loadProviderCatalog } from "../src/provider-catalog.mjs";

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

console.log(`provider catalog tests passed: general=${general.scrapers.length} vf=${vf.scrapers.length}`);
