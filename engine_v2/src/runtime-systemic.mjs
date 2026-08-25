export const SYSTEMIC_EXTRACTION_MIN_PROVIDERS = 3;
export const SYSTEMIC_EXTRACTION_MIN_WITH_HEALTHY_PEERS = 2;

function text(value) {
  return String(value ?? '').trim().toLowerCase();
}

export function extractionRouteKey(row) {
  return [text(row.provider), text(row.requestType), String(row.fixture ?? '')].join('\u0000');
}

export function extractionExecutionKey(row) {
  return [
    text(row.client || 'unknown'),
    String(row.fixture || 'unknown'),
    text(row.provider),
    text(row.requestType || 'unknown'),
    text(row.routeMode || 'declared'),
  ].join('\u0000');
}

function clientFixtureKey(row) {
  return [
    text(row.client || 'unknown'),
    String(row.fixture || 'unknown'),
    text(row.requestType || 'unknown'),
    text(row.routeMode || 'declared'),
  ].join('\u0000');
}

export function classifySystemicExtraction(resultRows = []) {
  const declaredEnabled = resultRows.filter((row) => row && row.enabled === true && text(row.routeMode || 'declared') !== 'capability_probe');
  const healthyByRoute = new Map();
  for (const row of declaredEnabled) {
    if (Number(row.count || 0) <= 0) continue;
    const key = extractionRouteKey(row);
    if (!healthyByRoute.has(key)) healthyByRoute.set(key, new Set());
    healthyByRoute.get(key).add(text(row.client || 'unknown'));
  }

  const groups = new Map();
  for (const row of declaredEnabled) {
    if (Number(row.count || 0) !== 0) continue;
    const key = clientFixtureKey(row);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }

  const systemicExecutionKeys = new Set();
  const systemicGroups = [];
  for (const rows of groups.values()) {
    const providers = [...new Set(rows.map((row) => text(row.provider)).filter(Boolean))];
    const healthyPeerProviders = [...new Set(rows.filter((row) => {
      const peers = healthyByRoute.get(extractionRouteKey(row));
      const currentClient = text(row.client || 'unknown');
      return peers && [...peers].some((client) => client !== currentClient);
    }).map((row) => text(row.provider)).filter(Boolean))];

    const systemic = providers.length >= SYSTEMIC_EXTRACTION_MIN_PROVIDERS
      || (providers.length >= SYSTEMIC_EXTRACTION_MIN_WITH_HEALTHY_PEERS
        && healthyPeerProviders.length >= SYSTEMIC_EXTRACTION_MIN_WITH_HEALTHY_PEERS);
    if (!systemic) continue;

    for (const row of rows) systemicExecutionKeys.add(extractionExecutionKey(row));
    systemicGroups.push({
      client: rows[0]?.client || 'unknown',
      fixture: rows[0]?.fixture || 'unknown',
      requestType: text(rows[0]?.requestType || 'unknown'),
      routeMode: text(rows[0]?.routeMode || 'declared'),
      providers: providers.sort(),
      healthyPeerProviders: healthyPeerProviders.sort(),
      providerCount: providers.length,
      healthyPeerProviderCount: healthyPeerProviders.length,
      failureClass: 'runtime_contract_drift',
      failureDomain: 'client_runtime',
      layer: 'core_runtime_compat',
      providerMutationEligible: false,
      coreOrManifestProposalAllowed: true,
      confidence: healthyPeerProviders.length >= SYSTEMIC_EXTRACTION_MIN_WITH_HEALTHY_PEERS ? 'confirmed_by_healthy_peers' : 'correlated_multi_provider',
    });
  }

  return { systemicExecutionKeys, systemicGroups };
}
