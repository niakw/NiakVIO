import crypto from "node:crypto";

export function emptyRecipeMemory() {
  return { schemaVersion: 2, recipes: [] };
}

export function evidenceSignature(evidence = {}) {
  const stages = evidence.stages ?? {};
  const normalized = {
    failureClass: evidence.failureClass ?? null,
    mediaType: evidence.request?.mediaType ?? null,
    device: evidence.request?.device ?? evidence.device ?? null,
    statuses: Object.fromEntries(Object.entries(stages).map(([name, stage]) => [name, stage?.status ?? null])),
    flags: {
      invoked: evidence.invoked ?? null,
      dns: evidence.dns?.ok ?? stages.dns?.ok ?? null,
      searchMatches: stages.search?.matches ?? null,
      identityMatched: stages.identity?.matched ?? null,
      detailFound: stages.detail?.found ?? null,
      episodeFound: stages.episode?.found ?? null,
      playerFound: stages.player?.found ?? null,
      mediaFound: stages.media?.found ?? null,
      mediaPlayable: stages.media?.playable ?? null,
    },
  };
  return crypto.createHash("sha256").update(stableStringify(normalized)).digest("hex").slice(0, 24);
}

export function rememberSuccessfulRecipe(memory, recipe, policy = {}) {
  if (!recipe?.id || !recipe?.signature || !Array.isArray(recipe.actions) || recipe.actions.length === 0) {
    throw new Error("validated recipe requires id, signature and actions");
  }
  if (recipe.validated !== true) throw new Error("only validated successful recipes can be learned");
  const next = structuredClone(memory ?? emptyRecipeMemory());
  next.schemaVersion = Math.max(2, Number(next.schemaVersion ?? 0));
  next.recipes ??= [];
  const key = recipeKey(recipe);
  const index = next.recipes.findIndex((item) => recipeKey(item) === key);
  const providerId = String(recipe.providerId ?? "").toLowerCase();
  const normalized = {
    ...structuredClone(recipe),
    successCount: Number(recipe.successCount ?? 1),
    failureCount: Number(recipe.failureCount ?? 0),
    provenOnProviders: providerId ? [providerId] : [...new Set(recipe.provenOnProviders ?? [])],
    learnedAt: recipe.learnedAt ?? new Date().toISOString(),
    lastValidatedAt: recipe.lastValidatedAt ?? new Date().toISOString(),
  };
  if (index >= 0) {
    const previous = next.recipes[index];
    normalized.successCount = Number(previous.successCount ?? 0) + 1;
    normalized.failureCount = Number(previous.failureCount ?? 0);
    normalized.provenOnProviders = [...new Set([...(previous.provenOnProviders ?? []), ...normalized.provenOnProviders])];
    normalized.learnedAt = previous.learnedAt ?? normalized.learnedAt;
    next.recipes[index] = normalized;
  } else {
    next.recipes.push(normalized);
  }
  const stored = next.recipes[index >= 0 ? index : next.recipes.length - 1];
  Object.assign(stored, maturityFor(stored, policy));
  return next;
}

export function recordRecipeFailure(memory, recipeId, signature, providerId = null, policy = {}) {
  const next = structuredClone(memory ?? emptyRecipeMemory());
  const recipe = (next.recipes ?? []).find((item) => item.id === recipeId && (!signature || item.signature === signature));
  if (!recipe) return next;
  recipe.failureCount = Number(recipe.failureCount ?? 0) + 1;
  recipe.lastFailedAt = new Date().toISOString();
  if (providerId) recipe.failedOnProviders = [...new Set([...(recipe.failedOnProviders ?? []), String(providerId).toLowerCase()])];
  Object.assign(recipe, maturityFor(recipe, policy));
  return next;
}

export function findCompatibleRecipes(memory, {
  signature, failureClass, device, clientRef, providerId,
  invalidCapabilities = [], allowExperimental = true,
} = {}) {
  const invalid = new Set(invalidCapabilities);
  const wantedProvider = String(providerId ?? "").toLowerCase();
  return (memory?.recipes ?? [])
    .filter((recipe) => recipe.validated === true)
    .filter((recipe) => !signature || recipe.signature === signature || recipe.scope?.generalized === true)
    .filter((recipe) => !failureClass || !recipe.failureClass || recipe.failureClass === failureClass)
    .filter((recipe) => runtimeAllows(recipe.runtime, device, clientRef))
    .filter((recipe) => !(recipe.capabilities ?? []).some((capability) => invalid.has(capability)))
    .filter((recipe) => allowExperimental || recipe.autoApply === true || (wantedProvider && (recipe.provenOnProviders ?? []).includes(wantedProvider)))
    .sort((a, b) => recipeScore(b) - recipeScore(a));
}

export function findAutoApplicableSkills(memory, query = {}) {
  return findCompatibleRecipes(memory, { ...query, allowExperimental: false }).filter((recipe) => recipe.autoApply === true);
}

export function invalidateRecipe(memory, recipeId, reason, clientRef = null) {
  const next = structuredClone(memory ?? emptyRecipeMemory());
  const recipe = (next.recipes ?? []).find((item) => item.id === recipeId);
  if (!recipe) return next;
  recipe.validated = false;
  recipe.autoApply = false;
  recipe.maturity = "invalidated";
  recipe.invalidatedAt = new Date().toISOString();
  recipe.invalidationReason = reason;
  recipe.invalidatedByClientRef = clientRef;
  return next;
}

export function maturityFor(recipe, policy = {}) {
  const successes = Number(recipe.successCount ?? 0);
  const failures = Number(recipe.failureCount ?? 0);
  const providers = new Set(recipe.provenOnProviders ?? []).size;
  const total = successes + failures;
  const confidence = total > 0 ? successes / total : 0;
  const candidateSuccesses = Number(policy.candidateSuccesses ?? 2);
  const trustedSuccesses = Number(policy.trustedSuccesses ?? 3);
  const trustedProviders = Number(policy.trustedProviders ?? 2);
  const minimumConfidence = Number(policy.minimumConfidence ?? 0.8);
  const trusted = successes >= trustedSuccesses && providers >= trustedProviders && confidence >= minimumConfidence;
  const maturity = trusted ? "trusted" : successes >= candidateSuccesses ? "candidate" : "experimental";
  return { maturity, confidence: Number(confidence.toFixed(4)), autoApply: trusted };
}

function runtimeAllows(runtime = {}, device, clientRef) {
  if (!device || !clientRef) return true;
  const rule = runtime?.[device];
  if (!rule) return true;
  if (Array.isArray(rule.acceptedRefs)) return rule.acceptedRefs.includes(clientRef);
  return true;
}
function recipeScore(recipe) {
  const successes = Number(recipe.successCount ?? 0);
  const failures = Number(recipe.failureCount ?? 0);
  const maturityBonus = recipe.autoApply ? 100 : recipe.maturity === "candidate" ? 20 : 0;
  return maturityBonus + successes * 10 - failures * 20 + Number(recipe.confidence ?? 0);
}
function recipeKey(recipe) {
  return `${recipe.id}::${recipe.signature}::${stableStringify(recipe.runtime ?? {})}`;
}
function stableStringify(value) {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}
