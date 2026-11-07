/**
 * Bounded, provider-fair retention for sanitized Brain experiment records.
 *
 * A global recency-first cap can let a high-volume provider evict all negative
 * experience of a newly onboarded hub. Keep minimumPerProvider rows
 * per distinct provider first, then spend remaining capacity on the
 * globally most relevant entries. This does not grant mutation/playback proof.
 */
export function retainBoundedBrainExperiments(records, {
  limit = 1000,
  minimumPerProvider = 12,
} = {}) {
  const bounded = (value, fallback, lower, upper) => {
    const number = Number(value);
    return Number.isFinite(number)
      ? Math.max(lower, Math.min(upper, Math.trunc(number)))
      : fallback;
  };
  const cap = bounded(limit, 1000, 1, 20000);
  const floor = bounded(minimumPerProvider, 12, 1, 32);
  const ranked = (Array.isArray(records) ? records : [])
    .filter((row) => row && typeof row === 'object' && !Array.isArray(row))
    .sort((a, b) => (
      String(b.lastSeenAt || '').localeCompare(String(a.lastSeenAt || ''))
      || Number(b.consecutiveFailures || 0) - Number(a.consecutiveFailures || 0)
      || Number(b.failures || 0) - Number(a.failures || 0)
      || String(a.providerId || '').localeCompare(String(b.providerId || ''))
      || String(a.signature || '').localeCompare(String(b.signature || ''))
      || String(a.profile || '').localeCompare(String(b.profile || ''))
    ));
  if (ranked.length <= cap) return ranked;
  const byProvider = new Map();
  for (let i = 0; i < ranked.length; i += 1) {
    const provider = String(ranked[i].providerId || '').trim().toLowerCase().replaceAll('_', '-');
    if (!byProvider.has(provider)) byProvider.set(provider, []);
    byProvider.get(provider).push(i);
  }
  const providers = [...byProvider.keys()].sort();
  const selected = new Set();
  for (let depth = 0; depth < floor && selected.size < cap; depth += 1) {
    for (const provider of providers) {
      const index = byProvider.get(provider)[depth];
      if (index !== undefined && selected.size < cap) selected.add(index);
    }
  }
  for (let i = 0; i < ranked.length && selected.size < cap; i += 1) {
    selected.add(i);
  }
  return ranked.filter((_row, index) => selected.has(index));
}
