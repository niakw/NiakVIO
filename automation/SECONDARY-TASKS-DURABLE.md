# NiakVIO — durable secondary task ledger

This file is a durable anti-forgetting ledger for secondary work. `MEMORY.md` remains the recovery source of truth and must mirror this ledger at every checkpoint.

## Priority rule

1. Provider yield first: resolve current `REGRESSION` cases in batches by shared root cause, then widen `ZERO` sampling and repair every newly proven upstream-positive/local-zero case.
2. Do not manufacture green by shrinking the 96-provider catalogue or by accepting wrong title/type/season/episode media. Wrong media is worse than zero; keep fail-closed identity and media integrity.
3. Secondary tasks below remain mandatory and must not be silently dropped while provider repair is active.

## Secondary tasks — mandatory

- **JavaScript minimization/minification**
  - Production bundles must go through the NiakVIO Provider v3 minimizer (`scripts/provider_v3_minimizer.py`), not Terser.
  - Preserve managed Lego markers/comments/structure and deterministic reverse reconstruction.
  - Re-run minimizer/fixed-point/byte-stability tests after batch provider changes and before the final Hub-46 freeze/publication candidate.
  - Measure resulting bundle sizes and ensure minimization does not change runtime semantics, provider identity evidence, headers, routes, timers, or Core/Provider ownership.
  - Keep source-qualified/content-hashed filenames synchronized with manifests/projections after minimization.

- **Hub-46 native transport**
  - Keep global catalogue at 96 providers while Labs use the exact physical 46-provider scope.
  - Finish native workflow wiring to `native-hub46/manifest.json`, including iOS and explicit Desktop/Android consistency.
  - The transport manifest must end in literal `manifest.json` for official Nuvio repository base resolution.
  - Regenerate Hub-46 against the final repaired provider SHA; do not certify Labs against the historical infrastructure-proof provider SHA.

- **Five native Labs on one frozen SHA**
  - TV Android / NuvioTV.
  - Mobile Android / NuvioMobile.
  - Mobile iOS / NuvioMobile.
  - Desktop macOS / NuvioDesktop.
  - Desktop Windows / NuvioDesktop.
  - Keep official client behavior observational; do not patch official Nuvio clients merely to make Labs green.

- **Desktop/runtime robustness**
  - Audit active provider bundles for direct `setTimeout` / `clearTimeout` assumptions and guarantee Desktop-safe timer handling, not only StreamFlix.
  - Preserve Core timeout at 25 s unless a later explicit decision changes it.
  - Preserve navigation A→B→C generation isolation even when fetch ignores AbortSignal.
  - Preserve stale-request suppression and no reinjection from superseded generations.
  - Preserve 403 fail-closed behavior; blocked/forbidden player URLs must not be surfaced as playable streams.

- **Identity and media safety**
  - Capability/type gate before network work.
  - TMDB/IMDb dual identity, `series -> tv`, anime semantic separation.
  - Movie year strictness only for movie; episodic year must not influence TV/anime identity.
  - Title/type/season/episode correctness before yield; wrong episode/title is worse than zero.
  - Revalidate HLS/direct media integrity, HLS audio-child handling, short/fake media rejection, and Unknown handling.

- **Provider parity / upstream truth**
  - Use `engine_v2/config/provider-upstreams.json` as upstream authority.
  - Keep `FULL`, `REGRESSION`, `RESAMPLE`, `ZERO` distinct.
  - Expand ZERO/RESAMPLE rotation before declaring dead providers.
  - Re-run parity after each repair batch and again on the final frozen SHA.

- **Domain Refresh**
  - Keep full-CONFIG transaction semantics, source authority, source-qualified filenames/content hashes, Core/Lego invariance, cycle/rollback safety and idempotence.
  - Maintain synthetic A→B domain-change proof and projection/version synchronization.
  - Do not regress to official-site-only mutation.

- **Brain / Learning / scheduled discovery**
  - Weekly upstream/provider discovery stays read-only and scheduled; it must report new candidates without mutating catalogue/manifests/providers.
  - Learning/Brain proposals must consume current provider truth and must not treat telemetry/materialization green as live-stream proof.
  - Verify scheduled execution and artifacts on the stabilized branch/final candidate when possible.

- **Repository hygiene / temporary automation**
  - Remove obsolete `temp-*.yml` workflows after extracting useful evidence.
  - Never rearm stale contradictory cleanup workflows such as removal of the weekly upstream watch.
  - Remove obsolete temp scripts/triggers only after confirming they are not referenced by tests/docs.
  - Keep branch cleanup for the end; do not touch `main` during the current `fix/labs-5.21.44-20260912` repair phase without explicit authorization.

- **Manifests, projections and fixed point**
  - Keep root 96-provider catalogue and all projections internally consistent.
  - Regenerate root/VF/no-anime/VF-no-anime/Hub-46 projections from the same final provider state.
  - Validate content hashes, source-qualified filenames, deterministic rebuild, reverse reconstruction and fixed-point/idempotence.
  - Do not certify stale pinned bytes.

- **Documentation / durable memory**
  - Update `MEMORY.md` at every important correction, failure, architecture decision, publication candidate, native proof or security proof.
  - Keep this ledger mirrored into `MEMORY.md`; this is specifically intended to prevent repeated loss of secondary tasks.
  - Reconcile `automation/OPEN-TASKS-20260911.md`, `CHANGELOG.md`, `VALIDATION.json`, README EN/FR, `ARCHITECTURE.md`, `VALIDATION.md`, `ARCHITECTURE.docx`, Lab triggers/matrices and any stale release/branch assumptions.
  - Document explicitly: 96 global catalogue vs 46 current Hub/Lab scope.

- **Provider presentation assets / metadata**
  - Preserve provider logo work: 72×32 and 96×40 compressed WebP assets; missing logos use generated first-letter fallback where required.
  - Active-provider presentation must derive from manifests/current provider truth rather than a hand-maintained stale list.
  - Revalidate branding, language labels and quality metadata after final materialization.

- **Security / final certification**
  - Run CodeQL/security workflows on the final frozen SHA.
  - Run dependency audit (`npm audit --omit=dev --audit-level=high` or current repository equivalent) on the final candidate.
  - Validate hashes/integrity and retain Labs/security artifacts as evidence.
  - Do not weaken security gates to obtain green CI.

## Completion gate

This ledger is not complete merely because provider yield improves. Final completion requires: provider REGRESSION/ZERO work resolved or precisely classified; final provider bundles minimized and fixed-point stable; Hub-46 regenerated on the final provider SHA; all five Labs executed against that same frozen candidate; manifests/projections consistent; security gates complete; documentation and `MEMORY.md` current; obsolete TEMP workflows removed; and every remaining open item explicitly recorded with evidence/reason.
