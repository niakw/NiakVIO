export function buildProviderSpec({ inventoryProvider, knowledgeProvider, domainObservation = null, legacyHub = null }) {
  if (!inventoryProvider?.id || !knowledgeProvider?.id || inventoryProvider.id !== knowledgeProvider.id) {
    throw new Error("matching inventory and knowledge provider are required");
  }
  const warnings = [];
  const requirements = [];
  const types = inventoryProvider.supportedTypes ?? [];

  if (!domainObservation?.selected) warnings.push("no-current-domain-proof");
  if (types.some((type) => type === "tv" || type === "anime") && !knowledgeProvider.observedStages?.episode) {
    requirements.push("reconstruct-episode-strategy");
  }
  if (knowledgeProvider.observedHeaders?.cookie) requirements.push("cookie-aware-transport");
  if (knowledgeProvider.observedHeaders?.referer) requirements.push("referer-aware-transport");
  if (knowledgeProvider.observedHeaders?.origin) requirements.push("origin-aware-transport");
  if (inventoryProvider.hasSettings || knowledgeProvider.requiresSettings) requirements.push("runtime-settings");
  if ((inventoryProvider.variants ?? []).length > 1) requirements.push("compare-upstream-implementations");
  if ((knowledgeProvider.domainRegistries ?? []).length > 0) requirements.push("dynamic-domain-registry");

  return {
    schemaVersion: 1,
    id: inventoryProvider.id,
    name: inventoryProvider.names?.[0] ?? inventoryProvider.id,
    aliases: unique([...(inventoryProvider.names ?? []), inventoryProvider.id]),
    state: "spec-seeded-unverified",
    publishable: false,
    capabilities: {
      supportedTypes: inventoryProvider.supportedTypes ?? [],
      languages: inventoryProvider.languages ?? [],
      formats: knowledgeProvider.formats ?? inventoryProvider.formats ?? [],
      hasSettings: inventoryProvider.hasSettings || knowledgeProvider.requiresSettings,
      limited: inventoryProvider.limited === true,
      supportsExternalPlayer: inventoryProvider.supportsExternalPlayer === true,
      supportedPlatforms: inventoryProvider.supportedPlatforms ?? [],
      disabledPlatforms: inventoryProvider.disabledPlatforms ?? [],
    },
    discovery: {
      hub: legacyHub?.hub ?? null,
      domainRegistries: knowledgeProvider.domainRegistries ?? [],
      observedDomain: domainObservation?.selected ?? null,
      candidateHosts: knowledgeProvider.providerCandidateHosts ?? [],
      playerHosts: knowledgeProvider.playerHosts ?? [],
      auxiliaryHosts: knowledgeProvider.auxiliaryHosts ?? [],
    },
    strategies: {
      kindCandidates: knowledgeProvider.strategyKinds ?? [],
      observedStages: knowledgeProvider.observedStages ?? {},
      routeHints: knowledgeProvider.routeHints ?? [],
      transport: {
        referer: knowledgeProvider.observedHeaders?.referer === true,
        origin: knowledgeProvider.observedHeaders?.origin === true,
        cookies: knowledgeProvider.observedHeaders?.cookie === true,
        userAgent: knowledgeProvider.observedHeaders?.userAgent === true,
        authorization: knowledgeProvider.observedHeaders?.authorization === true,
      },
    },
    implementationCandidates: (inventoryProvider.variants ?? []).map((variant) => ({
      upstreamId: variant.source?.upstreamId ?? null,
      repository: variant.source?.repository ?? null,
      ref: variant.source?.ref ?? null,
      manifestSha: variant.source?.manifestSha ?? null,
      filename: variant.filename ?? variant.source?.filename ?? null,
      version: variant.version ?? null,
      enabledUpstream: variant.enabledUpstream !== false,
      hasSettings: variant.hasSettings === true,
      supportedTypes: variant.supportedTypes ?? [],
      languages: variant.languages ?? [],
      formats: variant.formats ?? [],
      disabledPlatforms: variant.disabledPlatforms ?? [],
    })),
    requirements: unique(requirements),
    warnings: unique(warnings),
    provenance: {
      sourceCount: inventoryProvider.variants?.length ?? 0,
      upstreamEnabledStates: inventoryProvider.upstreamEnabledStates ?? {},
      knowledgeState: knowledgeProvider.state,
      domainObservedAt: domainObservation?.generated_at ?? null,
    },
  };
}

export function buildProviderSpecs({ inventory, knowledge, domains = null, hubs = null }) {
  const knowledgeById = new Map((knowledge.providers ?? []).map((provider) => [provider.id, provider]));
  const domainsById = new Map((domains?.providers ?? []).map((provider) => [provider.id, provider]));
  const specs = [];
  const errors = [];
  for (const provider of inventory.providers ?? []) {
    const knowledgeProvider = knowledgeById.get(provider.id);
    if (!knowledgeProvider) {
      errors.push({ id: provider.id, error: "missing-knowledge" });
      continue;
    }
    try {
      specs.push(buildProviderSpec({
        inventoryProvider: provider,
        knowledgeProvider,
        domainObservation: domainsById.get(provider.id) ?? null,
        legacyHub: hubs?.providers?.[provider.id] ?? null,
      }));
    } catch (error) {
      errors.push({ id: provider.id, error: String(error?.message ?? error) });
    }
  }
  return {
    specs,
    errors,
    stats: {
      specs: specs.length,
      errors: errors.length,
      withCurrentDomainProof: specs.filter((spec) => spec.discovery.observedDomain).length,
      duplicateImplementations: specs.filter((spec) => spec.implementationCandidates.length > 1).length,
      requireSettings: specs.filter((spec) => spec.capabilities.hasSettings).length,
      requireCookies: specs.filter((spec) => spec.strategies.transport.cookies).length,
      requireReferer: specs.filter((spec) => spec.strategies.transport.referer).length,
      requireOrigin: specs.filter((spec) => spec.strategies.transport.origin).length,
      requireEpisodeReconstruction: specs.filter((spec) => spec.requirements.includes("reconstruct-episode-strategy")).length,
    },
  };
}

function unique(values) {
  return [...new Set(values.filter((value) => value != null && value !== ""))];
}
