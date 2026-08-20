import { normalizeResolveRequest, normalizeStreamCandidate } from "./contracts.mjs";
import { addEvidenceError, newEvidenceRecord, recordStage, summarizeEvidence } from "./evidence.mjs";
import { validateMediaCandidates } from "./media-validator.mjs";
import { planRepair } from "./repair-brain.mjs";

const PIPELINE = Object.freeze(["homepage", "search", "identity", "detail", "episode", "player", "media", "validation"]);

export class ResolverCore {
  constructor(options = {}) {
    this.maxRepairHypotheses = Math.max(1, Math.min(3, Number(options.maxRepairHypotheses ?? 3)));
    this.mediaValidator = options.mediaValidator ?? validateMediaCandidates;
    this.mediaValidationOptions = options.mediaValidationOptions ?? {};
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
        if (!stageApplies(stage, canonical, adapter, context)) {
          recordStage(evidence, stage, { skipped: true, reason: "not-applicable" });
          continue;
        }

        try {
          let result;
          if (stage === "validation") {
            result = typeof adapter.validation === "function"
              ? await adapter.validation(context)
              : await this.mediaValidator(context.streams, this.mediaValidationOptions);
          } else {
            const handler = adapter[stage];
            if (typeof handler !== "function") {
              recordStage(evidence, stage, { skipped: true, reason: "adapter-stage-omitted" });
              continue;
            }
            result = await handler(context);
          }

          context.state[stage] = result;

          if (stage === "media") {
            context.streams = normalizeStreams(result, provider.id);
            evidence.playableStreams = 0;
            recordStage(evidence, stage, stageEvidence(stage, { ...asObject(result), streams: context.streams }));
          } else if (stage === "validation") {
            applyValidationResult(context, result);
            recordStage(evidence, stage, stageEvidence(stage, result));
          } else {
            recordStage(evidence, stage, stageEvidence(stage, result));
          }

          if (isTerminalFailure(stage, result, canonical, context)) break;
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
    if (context.evidence.stages.runtime?.observed !== true) {
      recordStage(context.evidence, "runtime", {
        attempted: true,
        accepted: Number(context.evidence.playableStreams ?? 0) > 0,
        device: context.request.device,
      });
    }
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

function stageApplies(stage, request, adapter, context) {
  if (stage === "episode") return request.mediaType === "tv" || request.mediaType === "anime";
  if (stage === "validation") return context.streams.length > 0;
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
      return { ...common, found: streams.length > 0 || value.found === true, streamCount: streams.length };
    }
    case "validation": {
      const results = value.results ?? [];
      return {
        ...common,
        playable: value.playable === true || Number(value.playableCount ?? 0) > 0,
        playableCount: Number(value.playableCount ?? 0),
        testedCount: Array.isArray(results) ? results.length : 0,
        statuses: Array.isArray(results)
          ? [...new Set(results.map((row) => row?.validation?.status).filter((status) => status != null))]
          : [],
        reasons: Array.isArray(results)
          ? [...new Set(results.map((row) => row?.validation?.reason).filter(Boolean))]
          : [],
      };
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
      out.push({ ...normalized, playable: false, validation: null });
    } catch {
      // Malformed candidates are never publication candidates.
    }
  }
  return out;
}

function applyValidationResult(context, result = {}) {
  const rows = Array.isArray(result.results) ? result.results : [];
  const byUrl = new Map(rows.map((row) => [row?.candidate?.url, row?.validation]));
  const rankedRows = Array.isArray(result.rankedResults) ? result.rankedResults : [];
  const rankByUrl = new Map();
  for (const row of rankedRows) {
    const url = row?.candidate?.url;
    if (url && !rankByUrl.has(url)) rankByUrl.set(url, rankByUrl.size);
  }

  const annotated = context.streams.map((stream, originalIndex) => {
    const validation = byUrl.get(stream.url) ?? null;
    return {
      originalIndex,
      rank: rankByUrl.has(stream.url) ? rankByUrl.get(stream.url) : Number.POSITIVE_INFINITY,
      stream: {
        ...stream,
        playable: validation?.playable === true,
        validation,
      },
    };
  });

  // Validation/ranking is part of the canonical Core contract, not a device hack.
  // Proven playable rows lead; the validator can therefore prefer a stable 1080p
  // fallback over a flaky 2160p route while leaving untested rows in stable order.
  annotated.sort((a, b) => a.rank - b.rank || a.originalIndex - b.originalIndex);
  context.streams = annotated.map((row) => row.stream);
  context.evidence.playableStreams = context.streams.filter((stream) => stream.playable === true).length;
}

function isTerminalFailure(stage, result, request, context) {
  if (result?.ok === false) return true;
  if (stage === "search" && Number(result?.matches?.length ?? result?.matches ?? 0) === 0) return true;
  if (stage === "identity" && result?.matched === false) return true;
  if (["detail", "episode", "player"].includes(stage) && result?.found === false) return true;
  if (stage === "media") return context.streams.length === 0;
  return false;
}

function asObject(value) {
  if (Array.isArray(value)) return { streams: value };
  return value && typeof value === "object" ? value : {};
}
