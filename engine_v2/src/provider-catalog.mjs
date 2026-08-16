import fs from "node:fs";
import path from "node:path";

export const PROVIDER_CATALOG_SCHEMA_VERSION = 2;

export function canonicalProviderId(value) {
  const id = String(value ?? "").trim();
  if (!id) throw new Error("provider id is required");
  return id.toLowerCase();
}

export function buildCatalogFromPublished({ generalManifest, vfManifest }) {
  const general = assertManifest(generalManifest, "general");
  const vf = assertManifest(vfManifest, "vf");
  const generalById = new Map();

  for (const scraper of general.scrapers) {
    const canonicalId = canonicalProviderId(scraper.id);
    if (generalById.has(canonicalId)) {
      throw new Error(`general manifest contains duplicate provider id: ${scraper.id}`);
    }
    generalById.set(canonicalId, structuredClone(scraper));
  }

  const vfOrder = [];
  for (const scraper of vf.scrapers) {
    const canonicalId = canonicalProviderId(scraper.id);
    if (vfOrder.includes(canonicalId)) {
      throw new Error(`vf manifest contains duplicate provider id: ${scraper.id}`);
    }
    if (!generalById.has(canonicalId)) {
      throw new Error(`vf provider is absent from general manifest: ${scraper.id}`);
    }
    const generalScraper = generalById.get(canonicalId);
    if (!deepEqual(generalScraper, scraper)) {
      throw new Error(`vf provider metadata diverges from general manifest: ${scraper.id}`);
    }
    vfOrder.push(canonicalId);
  }

  const generalOrder = general.scrapers.map((scraper) => canonicalProviderId(scraper.id));
  const vfSet = new Set(vfOrder);
  const providers = generalOrder.map((canonicalId) => {
    const scraper = generalById.get(canonicalId);
    return {
      canonicalId,
      scraper,
      projections: {
        general: true,
        vf: vfSet.has(canonicalId),
      },
    };
  });

  const catalog = {
    schemaVersion: PROVIDER_CATALOG_SCHEMA_VERSION,
    sourceOfTruth: true,
    policy: {
      repairBeforeTriage: true,
      retainLastKnownGoodOnInconclusive: true,
      quickRefreshMayRepairAndPublish: true,
      deepRefreshRebuildsKnowledge: true,
    },
    manifestMeta: {
      general: withoutScrapers(generalManifest),
      vf: withoutScrapers(vfManifest),
    },
    manifestOrder: {
      general: generalOrder,
      vf: vfOrder,
    },
    providers,
  };

  validateProviderCatalog(catalog);
  return catalog;
}

export function validateProviderCatalog(catalog) {
  if (!catalog || typeof catalog !== "object") throw new Error("provider catalog must be an object");
  if (catalog.schemaVersion !== PROVIDER_CATALOG_SCHEMA_VERSION) {
    throw new Error(`unsupported provider catalog schema: ${catalog.schemaVersion}`);
  }
  if (catalog.sourceOfTruth !== true) throw new Error("provider catalog must declare sourceOfTruth=true");
  if (!Array.isArray(catalog.providers) || catalog.providers.length === 0) {
    throw new Error("provider catalog must contain providers");
  }

  const byId = new Map();
  for (const row of catalog.providers) {
    if (!row || typeof row !== "object") throw new Error("provider catalog row must be an object");
    const canonicalId = canonicalProviderId(row.canonicalId ?? row.scraper?.id);
    if (row.canonicalId !== canonicalId) {
      throw new Error(`provider canonicalId must be normalized: ${row.canonicalId}`);
    }
    if (byId.has(canonicalId)) throw new Error(`duplicate provider in catalog: ${canonicalId}`);
    if (!row.scraper || typeof row.scraper !== "object") throw new Error(`${canonicalId}: scraper metadata is required`);
    if (canonicalProviderId(row.scraper.id) !== canonicalId) throw new Error(`${canonicalId}: scraper id does not match canonical id`);
    if (!String(row.scraper.filename ?? "").trim()) throw new Error(`${canonicalId}: filename is required`);
    if (row.projections?.general !== true) throw new Error(`${canonicalId}: every catalog provider must project to general`);
    byId.set(canonicalId, row);
  }

  for (const projection of ["general", "vf"]) {
    const order = catalog.manifestOrder?.[projection];
    if (!Array.isArray(order)) throw new Error(`${projection}: manifest order is required`);
    const seen = new Set();
    for (const rawId of order) {
      const canonicalId = canonicalProviderId(rawId);
      if (seen.has(canonicalId)) throw new Error(`${projection}: duplicate order id ${canonicalId}`);
      const row = byId.get(canonicalId);
      if (!row) throw new Error(`${projection}: order references unknown provider ${canonicalId}`);
      if (row.projections?.[projection] !== true) {
        throw new Error(`${projection}: order references provider outside projection ${canonicalId}`);
      }
      seen.add(canonicalId);
    }

    const expected = catalog.providers
      .filter((row) => row.projections?.[projection] === true)
      .map((row) => row.canonicalId);
    if (seen.size !== expected.length || expected.some((id) => !seen.has(id))) {
      throw new Error(`${projection}: projection membership and order differ`);
    }
  }

  const policy = catalog.policy ?? {};
  if (policy.repairBeforeTriage !== true) throw new Error("catalog policy must keep repair-before-triage");
  if (policy.retainLastKnownGoodOnInconclusive !== true) throw new Error("catalog policy must retain LKG on inconclusive evidence");
  if (policy.quickRefreshMayRepairAndPublish !== true) throw new Error("quick refresh must be allowed to repair and publish");

  return catalog;
}

export function manifestsFromCatalog(catalog) {
  validateProviderCatalog(catalog);
  const byId = new Map(catalog.providers.map((row) => [row.canonicalId, row]));
  return {
    general: {
      ...(structuredClone(catalog.manifestMeta?.general) ?? {}),
      scrapers: catalog.manifestOrder.general.map((id) => structuredClone(byId.get(id).scraper)),
    },
    vf: {
      ...(structuredClone(catalog.manifestMeta?.vf) ?? {}),
      scrapers: catalog.manifestOrder.vf.map((id) => structuredClone(byId.get(id).scraper)),
    },
  };
}

export function loadProviderCatalog(filePath = "provider_catalog.json") {
  return validateProviderCatalog(JSON.parse(fs.readFileSync(filePath, "utf8")));
}

export function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(path.resolve(filePath)), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function assertManifest(manifest, label) {
  if (!manifest || typeof manifest !== "object") throw new Error(`${label} manifest must be an object`);
  if (!Array.isArray(manifest.scrapers)) throw new Error(`${label} manifest scrapers must be an array`);
  return manifest;
}

function withoutScrapers(manifest) {
  const copy = structuredClone(manifest);
  delete copy.scrapers;
  return copy;
}

function deepEqual(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}
