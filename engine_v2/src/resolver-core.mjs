import { normalizeResolveRequest, normalizeStreamCandidate } from "./contracts.mjs";
import { addEvidenceError, newEvidenceRecord, recordStage, summarizeEvidence } from "./evidence.mjs";
import { planRepair } from "./repair-brain.mjs";

const PIPELINE = Object.freeze(["homepage", "search", "identity", "detail", "episode", "player", "media"]);

export class ResolverCore {
  constructor(options = {}) {
    this.maxRepairHypotheses = Math.max(1, Math.min(3, Number(options.maxRepairHypotheses ?? 3)));
  }

  async resolve({ provider, adapter, request, fixtureId = "adhoc", clientRef = "unknown", runtimeCompatibility = null }) {
    const canonical = normalizeResolveRequest(request);
    if (!provider?.id) throw new Error("provider id is required");
    if (!adapter || typeof adapter !== "object") throw new Error("adapter is required");

    const evidence = newEvidenceRecord({
      providerId: provider.id,
      fixtureId,
      mediaType: canonical.mediaType,
      language: canonical.languages[0] ?? "und",
      device: canonical.device,
      clientRef,
    });
    evidence.request = canonical;
    evidence.invoked = true;

    const context = {
      provider,
      request: canonical,
      state: {},
      evidence,
      streams: [],
    };

    try {
      if (typeof adapter.discover === "function") {
        const discovery = await adapter.discover(context);
        context.state.discovery = discovery ?? {};
        recordStage(evidence, "dns", normalizeDiscoveryEvidence(discovery));
        if (discovery?.ok === false) return this.#finish(context, runtimeCompatibility);
      } else {
        recordStage(evidence, "dns", { ok: true, skipped: true, reason: "adapter-has-no-discovery-stage" });
      }

      for (const stage of PIPELINE) {
        if (!stageApplies(stage, canonical, adapter)) {
          recordStage(evidence, stage, { skipped: true, reason: "not-applicable" });
          continue;
        }
        const handler = adapter[stage];
        if (typeof handler !== "function") {
          recordStage(evidence, stage, { skipped: true, reason: "adapter-stage-omitted" });
          continue;
        }

        try {
          const result = await handler(context);
          context.state[stage] = result;
          recordStage(evidence, stage, stageEvidence(stage, result));
          if (stage === "media") {
            context.streams = normalizeStreams(result, provider.id);
            evidence.playableStreams = context.streams.filter((stream) => stream.playable !== false).length;
          }
          if (isTerminalFailure(stage, result, canonical)) break;
        } catch (error) {
          addEvidenceError(evidence, `${stage}: ${error?.message ?? error}`);
          recordStage(evidence, stage, { attempted: true, error: String(error?.message ?? error), ok: false });
          break;
        }
      }
    } catch (error) {
      addEvidenceError(evidence, error);
    }

    return this.#finish(context, runtimeCompatibility);
  }

  #finish(context, runtimeCompatibility) {
    const repair = planRepair({
      ...context.evidence,
      request: context.request,
      stages: context.evidence.stages,
      playableStreams: context.evidence.playableStreams,
    }, {
      maxHypotheses: this.maxRepairHypotheses,
      runtimeCompatibility,
    });
    return {
      providerId: context.provider.id,
      request: context.request,
      streams: context.streams,
      evidence: context.evidence,
      evidenceSummary: summarizeEvidence(context.evidence),
      repair,
    };
  }
}

function stageApplies(stage, request, adapter) {
  if (stage === "episode") return request.mediaType === "tv" || request.mediaType === "anime";
  if (adapter.pipeline && Array.isArray(adapter.pipeline)) return adapter.pipeline.includes(stage);
  return true;
}

function normalizeDiscoveryEvidence(result) {
  if (result == null) return { ok: true, attempted: true };
  return {
    attempted: true,
    ok: result.ok !== false,
    host: result.host ?? null,
    url: result.url ?? null,
    status: result.status ?? null,
    source: result.source ?? null,
  };
}

function stageEvidence(stage, result) {
  const value = result ?? {};
  const common = {
    attempted: true,
    ok: value.ok !== false,
    status: value.status ?? null,
  };
  switch (stage) {
    case "homepage": return { ...common, reachable: value.reachable ?? value.ok !== false };
    case "search": return { ...common, matches: Number(value.matches?.length ?? value.matches ?? 0) };
    case "identity": return { ...common, matched: value.matched !== false };
    case "detail": return { ...common, found: value.found !== false };
    case "episode": return { ...common, found: value.found !== false, season: value.season ?? null, episode: value.episode ?? null };
    case "player": return { ...common, found: value.found !== false, host: value.host ?? null };
    case "media": {
      const streams = Array.isArray(value) ? value : value.streams ?? [];
      const found = streams.length > 0 || value.found === true;
      const playable = streams.some((stream) => stream?.playable !== false) || value.playable === true;
      return { ...common, found, playable, streamCount: streams.length };
    }
    default: return common;
  }
}

function normalizeStreams(result, providerId) {
  const streams = Array.isArray(result) ? result : result?.streams ?? [];
  const out = [];
  for (const raw of streams) {
    try {
      const normalized = normalizeStreamCandidate(raw, { providerId, source: "resolver-v2" });
      out.push({ ...normalized, playable: raw?.playable !== false });
    } catch {
      // Malformed candidates are evidence failures, never publication candidates.
    }
  }
  return out;
}

function isTerminalFailure(stage, result, request) {
  if (result?.ok === false) return true;
  if (stage === "search" && Number(result?.matches?.length ?? result?.matches ?? 0) === 0) return true;
  if (stage === "identity" && result?.matched === false) return true;
  if (["detail", "episode", "player"].includes(stage) && result?.found === false) return true;
  if (stage === "media") {
    const streams = Array.isArray(result) ? result : result?.streams ?? [];
    return streams.length === 0 && result?.found !== true;
  }
  return false;
}
