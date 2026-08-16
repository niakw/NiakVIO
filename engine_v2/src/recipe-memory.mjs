import crypto from "node:crypto";

export function emptyRecipeMemory() {
  return { schemaVersion: 1, recipes: [] };
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

export function rememberSuccessfulRecipe(memory, recipe) {
  if (!recipe?.id || !recipe?.signature || !Array.isArray(recipe.actions) || recipe.actions.length === 0) {
    throw new Error("validated recipe requires id, signature and actions");
  }
  if (recipe.validated !== true) throw new Error("only validated successful recipes can be learned");
  const next = structuredClone(memory ?? emptyRecipeMemory());
  next.recipes ??= [];
  const key = recipeKey(recipe);
  const index = next.recipes.findIndex((item) => recipeKey(item) === key);
  const normalized = {
    ...structuredClone(recipe),
    successCount: Number(recipe.successCount ?? 1),
    failureCount: Number(recipe.failureCount ?? 0),
    learnedAt: recipe.learnedAt ?? new Date().toISOString(),
    lastValidatedAt: recipe.lastValidatedAt ?? new Date().toISOString(),
  };
  if (index >= 0) {
    const previous = next.recipes[index];
    normalized.successCount = Number(previous.successCount ?? 0) + 1;
    normalized.failureCount = Number(previous.failureCount ?? 0);
    normalized.learnedAt = previous.learnedAt ?? normalized.learnedAt;
    next.recipes[index] = normalized;
  } else {
    next.recipes.push(normalized);
  }
  return next;
}

export function findCompatibleRecipes(memory, { signature, failureClass, device, clientRef, invalidCapabilities = [] } = {}) {
  const invalid = new Set(invalidCapabilities);
  return (memory?.recipes ?? [])
    .filter((recipe) => recipe.validated === true)
    .filter((recipe) => !signature || recipe.signature === signature)
    .filter((recipe) => !failureClass || !recipe.failureClass || recipe.failureClass === failureClass)
    .filter((recipe) => runtimeAllows(recipe.runtime, device, clientRef))
    .filter((recipe) => !(recipe.capabilities ?? []).some((capability) => invalid.has(capability)))
    .sort((a, b) => recipeScore(b) - recipeScore(a));
}

export function invalidateRecipe(memory, recipeId, reason, clientRef = null) {
  const next = structuredClone(memory ?? emptyRecipeMemory());
  const recipe = (next.recipes ?? []).find((item) => item.id === recipeId);
  if (!recipe) return next;
  recipe.validated = false;
  recipe.invalidatedAt = new Date().toISOString();
  recipe.invalidationReason = reason;
  recipe.invalidatedByClientRef = clientRef;
  return next;
}

function runtimeAllows(runtime = {}, device, clientRef) {
  if (!device || !clientRef) return true;
  const rule = runtime?.[device];
  if (!rule) return true;
  if (Array.isArray(rule.acceptedRefs)) return rule.acceptedRefs.includes(clientRef);
  if (rule.minRef || rule.maxRef) return true; // Git SHA ordering is not semantic; explicit acceptedRefs wins.
  return true;
}

function recipeScore(recipe) {
  const successes = Number(recipe.successCount ?? 0);
  const failures = Number(recipe.failureCount ?? 0);
  return successes * 10 - failures * 20 + Number(recipe.confidence ?? 0);
}

function recipeKey(recipe) {
  return `${recipe.id}::${recipe.signature}::${stableStringify(recipe.runtime ?? {})}`;
}

function stableStringify(value) {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}
