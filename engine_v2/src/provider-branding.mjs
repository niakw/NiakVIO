import { canonicalProviderId, validateProviderCatalog } from "./provider-catalog.mjs";

/**
 * Apply the committed text branding map to provider metadata.
 *
 * The manifest/provider name is allowed to carry the emoji fallback because local
 * Nuvio stream rows do not currently expose scraper.logo. README rendering uses the
 * clean `name` value from this same map and deliberately omits the emoji beside logos.
 */
export function applyCommittedProviderNames(catalog, brandingIndex) {
  validateProviderCatalog(catalog);
  if (!brandingIndex || typeof brandingIndex !== "object") {
    throw new Error("provider branding index is required");
  }
  if (brandingIndex.policy !== "committed-provider-default-emoji") {
    throw new Error("provider branding index must declare committed-provider-default-emoji policy");
  }
  const indexed = brandingIndex.providers;
  if (!indexed || typeof indexed !== "object") {
    throw new Error("provider branding index providers must be an object");
  }

  const byId = new Map(catalog.providers.map((row) => [row.canonicalId, row]));
  const indexedIds = new Set(Object.keys(indexed).map((value) => canonicalProviderId(value)));
  const catalogIds = new Set(byId.keys());
  const missing = [...catalogIds].filter((id) => !indexedIds.has(id));
  const unknown = [...indexedIds].filter((id) => !catalogIds.has(id));
  if (missing.length || unknown.length) {
    throw new Error(
      `provider branding coverage mismatch: missing=${missing.join(",") || "none"} unknown=${unknown.join(",") || "none"}`,
    );
  }

  let applied = 0;
  for (const [rawId, branding] of Object.entries(indexed)) {
    const canonicalId = canonicalProviderId(rawId);
    const row = byId.get(canonicalId);
    const cleanName = String(branding?.name ?? "").trim();
    const emoji = String(branding?.emoji ?? "").trim();
    if (!cleanName || !emoji) {
      throw new Error(`${canonicalId}: provider branding requires clean name and emoji`);
    }
    row.scraper.name = `${emoji} ${cleanName}`;
    applied += 1;
  }

  catalog.policy.committedProviderNames = true;
  catalog.policy.committedProviderNameCount = applied;
  validateProviderCatalog(catalog);
  return catalog;
}
