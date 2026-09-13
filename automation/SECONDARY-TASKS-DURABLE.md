# NiakVIO — durable secondary task ledger

This file is a durable anti-forgetting ledger for secondary work. `MEMORY.md` remains the recovery source of truth and must mirror this ledger at every checkpoint.
Last audited against the active repair branch: 2026-09-13.

## Priority rule

1. Provider yield first: resolve current `REGRESSION` cases in batches by shared root cause, then widen `ZERO` sampling and repair every newly proven upstream-positive/local-zero case.
2. Do not manufacture green by shrinking the 96-provider catalogue or by accepting wrong title/type/season/episode media. Wrong media is worse than zero; keep fail-closed identity and media integrity.
3. Secondary tasks below remain mandatory and must not be silently dropped while provider repair is active.
4. Runtime/client compatibility adaptations are **Core-global Lego**, never provider-by-provider hacks: timers (`setTimeout`/`clearTimeout`), HTTP/403 fail-closed policy, stale-generation suppression, execution budgets and client-runtime portability belong after the global Core boundary. Provider Lego may supply provider-specific transport/data/options only.

## Secondary tasks — mandatory

- **JavaScript minimization/minification — FINAL STAGE only**
  - Do **not** use minification as a routine provider-repair or intermediate runtime gate. Stabilize provider yield, global Core/runtime behavior and the candidate first; run minimization near the very end, before final fixed-point/release certification.
  - Production bundles must go through the NiakVIO Provider v3 minimizer (`scripts/provider_v3_minimizer.py`), not Terser.
  - Preserve managed Lego markers/comments/structure and deterministic reverse reconstruction.
  - Re-run minimizer/fixed-point/byte-stability tests after batch provider changes and before the final Hub-46 freeze/publication candidate.
  - Measure resulting bundle sizes and ensure minimization does not change runtime semantics, provider identity evidence, headers, routes, timers, or Core/Provider ownership.
  - Keep source-qualified/content-hashed filenames synchronized with manifests/projections after minimization.

- **Exact 46 evidence classification**
  - Produce/maintain a nominative list for all 46 current Hub/Lab providers with the first proven blocker: domain/hub resolution, metadata identity, search/detail route, API/player extraction, anti-bot/network, stream transport, content identity, native player, or unknown/opaque.
  - Maintain a separate explicit list of genuinely opaque / not safely analyzable providers with the reason for each. `0 streams` alone is not opaque.
  - Preserve the discovery-vs-execution boundary: registry/hub presence is knowledge only, never proof that an execution route is valid.
  - Telegram (`t.me`, `telegram.me`, `telegram.dog`) remains discovery-only; Domain Refresh may use it to discover a domain, but ProviderBase must never execute search/API/media routes against Telegram.
  - Keep Allwish fail-closed until title/work identity is actually proved; HLS-looking output alone is insufficient.

- **Cross-runtime/provider follow-ups**
  - Recheck PlayIMDb, VidEasy and Papadustream across Desktop/TV/Mobile after raw-TMDB/runtime repairs; historical TV-positive/Desktop-or-iOS-zero evidence is runtime divergence, not provider death.
  - Recheck Frenchstream extraction vs HLS transport; previous extraction existed while transport returned 403.
  - Keep known manual/provider-specific evidence (AnimeSalt/AnimePahe/Nakios/Vostfree/ZinkMovies/UHDMovies/NetMirror/etc.) as route knowledge, but require dynamic extraction + common playback verification before strict green.
  - Reader/player failures must remain classified separately from provider extraction failures.

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
  - Record the exact NiakVIO candidate SHA and exact NuvioTV/NuvioMobile/NuvioDesktop refs used by every final Lab.
  - Android Mobile must not reuse the older invalid evidence where client UI launch failed / Brain evidence was incomplete.
  - Desktop macOS/Windows evidence that predates raw-TMDB/runtime fixes is not final evidence for affected direct-TMDB providers.
  - Keep official client behavior observational; do not patch official Nuvio clients merely to make Labs green.

- **Desktop/runtime robustness**
  - Desktop/runtime fixes are Core-global. `CORE.RUNTIME_COMPAT.V1` owns timer shims and URL/fetch portability for every composed bundle; do not add StreamFlix/Movix/provider-specific timer hacks.
  - Audit direct provider `setTimeout` / `clearTimeout` usage only to prove the global shim covers it; provider code must not become the owner of client-runtime compatibility.
  - 403/404/410 and terminal media validity are Core-global sanitizer policy; never patch a named provider merely to hide a forbidden/dead returned row.
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
  - Maintain synthetic A→B domain-change proof, including generic logo/icon/favicon old-host -> new-host reconciliation where applicable, and projection/version synchronization.
  - Prove domain-only refresh leaves ProviderBase/Core bytes unchanged.
  - Do not regress to official-site-only mutation.

- **Brain / Learning / scheduled discovery**
  - Weekly upstream/provider discovery stays read-only and scheduled; it must report new candidates without mutating catalogue/manifests/providers.
  - Verify an actual scheduled execution/artifact, not only the unit-test/schedule definition, before marking operational watch closed.
  - Learning/Brain proposals must consume current provider truth and must not treat telemetry/materialization green as live-stream proof.
  - Perform/review the older requested real multi-day Brain differential evidence: learned providers, repairs, regressions, and state preservation across days.
  - Preserve the international provider-discovery infrastructure and XLSX/CSV/JSON candidate artifacts; future refreshes should keep country balance and substantial UHD/4K representation.

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
  - Verify actual visible provider-logo propagation in the official Nuvio UI/Labs; asset-contract tests alone do not close the old UI request, and official Nuvio repos must not be patched just to force a green result.

- **Security / final certification**
  - Run CodeQL/security workflows on the final frozen SHA.
  - Run dependency audit (`npm audit --omit=dev --audit-level=high` or current repository equivalent) on the final candidate.
  - Validate hashes/integrity and retain Labs/security artifacts as evidence.
  - Do not weaken security gates to obtain green CI.

## Completion gate

This ledger is not complete merely because provider yield improves. Final completion requires: provider REGRESSION/ZERO work resolved or precisely classified; all 46 current Hub/Lab providers have a defensible blocker/green/opaque classification; final provider bundles minimized and fixed-point stable; Hub-46 regenerated on the final provider SHA; all five Labs executed against that same frozen candidate with exact client refs; visible UI/logo and reader/player-vs-provider distinctions verified; manifests/projections consistent; scheduled watch and Brain multi-day evidence reviewed; security gates complete; documentation and `MEMORY.md` current; obsolete TEMP workflows removed; and every remaining open item explicitly recorded with evidence/reason.
