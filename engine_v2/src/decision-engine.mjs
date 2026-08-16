export const PROVIDER_STATES = Object.freeze([
  "enabled-current-proof",
  "enabled-lkg-grace",
  "repairable-disabled",
  "hold-suspicious",
  "quarantine",
  "unobserved",
]);

export function decideProviderState(input = {}) {
  const currentPlayableProofs = Number(input.currentPlayableProofs ?? 0);
  const suspicious = input.suspicious === true;
  const unsafe = input.unsafe === true;
  const confirmedIdentityMismatch = input.confirmedIdentityMismatch === true;
  const hardQuarantine = input.hardQuarantine === true;
  const lkg = input.lkg ?? null;
  const repairable = input.repairable !== false;

  if (hardQuarantine || unsafe || confirmedIdentityMismatch) {
    return {
      state: "quarantine",
      publish: false,
      repair: false,
      reason: hardQuarantine ? "explicit-hard-quarantine" : unsafe ? "unsafe-evidence" : "confirmed-identity-mismatch",
    };
  }

  if (suspicious) {
    return {
      state: "hold-suspicious",
      publish: false,
      repair: true,
      shadowTest: true,
      reason: "suspicion-requires-independent-proof",
    };
  }

  if (currentPlayableProofs > 0) {
    return {
      state: "enabled-current-proof",
      publish: true,
      repair: false,
      reason: "current-playable-proof",
    };
  }

  if (lkgIsUsable(lkg, input.now)) {
    return {
      state: "enabled-lkg-grace",
      publish: true,
      repair: true,
      reason: "recent-lkg-with-current-repair-pending",
      lkgAgeHours: lkgAgeHours(lkg, input.now),
    };
  }

  if (repairable) {
    return {
      state: "repairable-disabled",
      publish: false,
      repair: true,
      reason: input.failureClass ?? "no-current-proof",
    };
  }

  return {
    state: "unobserved",
    publish: false,
    repair: false,
    reason: "insufficient-evidence",
  };
}

export function lkgIsUsable(lkg, now = null) {
  if (!lkg?.validatedAt || lkg.playable !== true) return false;
  const maxAgeHours = Number(lkg.maxAgeHours ?? 72);
  return lkgAgeHours(lkg, now) <= maxAgeHours;
}

export function lkgAgeHours(lkg, now = null) {
  const start = Date.parse(lkg?.validatedAt ?? "");
  const end = now == null ? Date.now() : new Date(now).getTime();
  if (!Number.isFinite(start) || !Number.isFinite(end)) return Infinity;
  return Math.max(0, (end - start) / 3_600_000);
}
