const STAGES = Object.freeze(["dns", "homepage", "search", "identity", "detail", "episode", "player", "media", "validation", "runtime"]);

export function makeEvidenceKey({ providerId, fixtureId, mediaType, language = "und", device, clientRef = "unknown" }) {
  for (const [name, value] of Object.entries({ providerId, fixtureId, mediaType, device })) {
    if (!value) throw new Error(`${name} is required`);
  }
  return [providerId, fixtureId, mediaType, language || "und", device, clientRef].map(safePart).join("::");
}

export function newEvidenceRecord(input) {
  const now = new Date().toISOString();
  return {
    schemaVersion: 1,
    key: makeEvidenceKey(input),
    providerId: input.providerId,
    fixtureId: input.fixtureId,
    mediaType: input.mediaType,
    language: input.language ?? "und",
    device: input.device,
    clientRef: input.clientRef ?? "unknown",
    observedAt: now,
    invoked: null,
    playableStreams: 0,
    stages: Object.fromEntries(STAGES.map((stage) => [stage, { observed: false }])),
    errors: [],
    notes: [],
  };
}

export function recordStage(record, stage, patch = {}) {
  if (!STAGES.includes(stage)) throw new Error(`unknown evidence stage: ${stage}`);
  record.stages[stage] = {
    ...record.stages[stage],
    ...structuredClone(patch),
    observed: true,
    observedAt: new Date().toISOString(),
  };
  record.observedAt = new Date().toISOString();
  return record;
}

export function addEvidenceError(record, error) {
  record.errors.push({
    message: typeof error === "string" ? error : String(error?.message ?? error),
    at: new Date().toISOString(),
  });
  return record;
}

export function summarizeEvidence(record) {
  const firstMissingStage = STAGES.find((stage) => record.stages?.[stage]?.observed !== true) ?? null;
  const observedStages = STAGES.filter((stage) => record.stages?.[stage]?.observed === true);
  return {
    key: record.key,
    providerId: record.providerId,
    fixtureId: record.fixtureId,
    device: record.device,
    clientRef: record.clientRef,
    playableStreams: Number(record.playableStreams ?? 0),
    observedStages,
    firstMissingStage,
    complete: firstMissingStage == null,
    errorCount: record.errors?.length ?? 0,
  };
}

export function aggregateProviderEvidence(records = []) {
  const byDevice = {};
  let playableProofs = 0;
  let latestAt = null;
  for (const record of records) {
    const device = record.device ?? "unknown";
    byDevice[device] ??= { proofs: 0, playable: 0, fixtures: new Set() };
    byDevice[device].proofs += 1;
    byDevice[device].fixtures.add(record.fixtureId);
    const playable = Number(record.playableStreams ?? 0) > 0 || record.stages?.validation?.playable === true;
    if (playable) {
      playableProofs += 1;
      byDevice[device].playable += 1;
    }
    if (!latestAt || String(record.observedAt) > latestAt) latestAt = record.observedAt;
  }
  return {
    proofCount: records.length,
    playableProofs,
    latestAt,
    byDevice: Object.fromEntries(Object.entries(byDevice).map(([device, value]) => [device, {
      proofs: value.proofs,
      playable: value.playable,
      fixtures: [...value.fixtures].sort(),
    }])),
  };
}

function safePart(value) {
  return String(value).trim().toLowerCase().replace(/[^a-z0-9._-]+/g, "-");
}
