# NiakVIO — open-task recovery checkpoint — updated 2026-09-13

This is the operational recovery list for the active branch `fix/labs-5.21.44-20260912`. `MEMORY.md`, exact repository state and current GitHub Actions evidence override stale chat summaries. The durable anti-forgetting list is also mirrored in `automation/SECONDARY-TASKS-DURABLE.md`.

## Hard constraints / architecture

- Canonical catalogue remains **96 Provider Objects**; do not delete providers to fake green yield.
- Current Hub/Lab campaign remains the exact **46-provider** scope from `automation/evidence/hub-lab-matrix-46.json`; the other 50 catalogue rows remain outside that active scope unless a later explicit activation decision changes it.
- Wrong title/type/season/episode is worse than zero. Identity/media integrity remains fail-closed.
- Hub/registry presence is discovery knowledge, never execution proof. Telegram (`t.me`, `telegram.me`, `telegram.dog`) remains discovery-only and must never become a ProviderBase search/API/media execution origin.
- Runtime/client portability is **Core-global Lego**, never provider-specific patch ownership. Timers (`setTimeout`/`clearTimeout`), URL/fetch host portability, execution budgets, stale-generation suppression/cancellation, HTTP/media fail-closed rules such as 403 and terminal stream sanitation belong after the single global Core boundary. Provider Lego owns provider-specific DATA/transport/extraction only.
- Provider timeout stays **25 s** unless explicitly changed later. Preserve A→B→C latest-generation isolation even when fetch ignores `AbortSignal`.
- NiakVIO minimization is a **final-stage** operation after provider/runtime stabilization. Terser remains forbidden. The final minimizer must preserve STARTFIX/CLOSEFIX/FIXDATA/Core boundaries, runtime semantics, deterministic reverse rebuild and byte fixed point.
- `main` must not be touched by this repair phase without explicit authorization.

## Main priority — provider yield / parity

- [x] Upstream parity authority is `engine_v2/config/provider-upstreams.json`; old `sources.json` parity lookup is obsolete.
- [x] Parity states remain distinct: `FULL`, `REGRESSION`, `RESAMPLE`, `ZERO`. A clean zero/zero sample is not a local regression.
- [x] PlayIMDb proof-v5 typed resolver restored and committed. Live proof on run `34757794069`: Oppenheimer movie `raw/playable/verified=2/2/2`, HOTD S1E1 TV `3/3/3`, contradictions `0`; final repair commit after rebase `d6c6be8b...`.
- [ ] Complete the current wider Hub-46 parity / ZERO deep-rotation run `34763697601`: 6 samples/lane baseline, then up to 12 samples/lane for baseline ZERO providers.
- [ ] Build the repair queue only from **certain upstream-positive/local-zero regressions** discovered by that rotation; do not blindly mutate ZERO providers.
- [ ] Repair remaining certain regressions as a consolidated multi-provider transaction, rerun identical parity samples, and require the certain regression count not to worsen.
- [ ] Recheck/repair known historical debt where still reproduced: Cineby movie+TV, Coflix movie+TV, French-Manga anime, NetMirror movie, Papadustream TV, StreamZo movie, VoirAnime anime. Historical lists are hypotheses only; current wider parity is authoritative.
- [ ] After each repair wave, classify every 46 target by first proven blocker: domain/hub resolution, metadata identity, search/detail, API/player extraction, anti-bot/network, stream transport, content identity, native player, or unknown/opaque.
- [ ] Maintain a nominative list of genuinely opaque / not safely analyzable providers with a reason. `0 streams` alone is not opaque.
- [ ] Recheck cross-runtime PlayIMDb / VidEasy / Papadustream after current raw-TMDB/runtime changes and recheck Frenchstream extraction vs HLS 403 transport.
- [ ] Keep historical manual evidence for AnimeSalt/AnimePahe/Nakios/Vostfree/ZinkMovies/UHDMovies/etc. as knowledge only until current dynamic extraction/playback evidence proves strict green.

## Global Core / Desktop/runtime work

- [x] `CORE.RUNTIME_COMPAT.V1` is the global owner of missing timers plus Desktop URL/fetch portability.
- [x] `scripts/apply_provider_overrides.py` rejects Core-global modules from provider `patch_scripts`.
- [x] Terminal stream/media policy is Core-global. Base sanitizer treats HTTP 403/404/410 as conclusive invalidity; V8 publishes ordinary probed rows only on positive media proof.
- [x] Added `tests/global_core_runtime_ownership_test.py`: checks all 96 bundles have one runtime-compat and one terminal-sanitizer block after the Core boundary, and forbids provider-specific ownership of those bricks. Current Core-ownership checkpoint run `34764289070` is green.
- [ ] Consolidate duplicate timer responsibility only at the Core level if/when `desktop_runtime_compat_v1.py` is simplified; never move this into StreamFlix/Movix/provider-specific code.
- [ ] Reconcile stale `tests/vf_recovery_profiles_test.py` assumptions against current architecture; do not mutate StreamZo/provider code merely to satisfy that stale profile assertion.

## Hub-46 transport and Native Labs

- [x] Root-name transport 404 diagnosed: official Nuvio repository code strips literal `/manifest.json`; root `manifest-hub46.json` was not a valid official transport base.
- [x] Added terminal-name-safe physical transport `native-hub46/manifest.json` with 46 rows and immutable absolute provider URLs.
- [x] Native Desktop/Mobile/TV suite resolvers auto-select `native-hub46/manifest.json` for the Hub-46 campaign.
- [x] iOS workflow explicitly uses `native-hub46/manifest.json` for installation and exhaustive matrix verification.
- [x] Desktop workflow explicitly uses `native-hub46/manifest.json` for initial preparation, target manifest and matrix verification.
- [x] Persisted transport contract is green for `tests/native_hub46_transport_manifest_test.py` and provider-loading compatibility. The first small verification run was marked red only because its TEMP called removed `native_reader_bootstrap_test.py`; retry uses current `native_reader_runtime_bootstrap_test.py`.
- [ ] Align explicit Android TV/Mobile workflow manifest arguments to the physical Hub-46 manifest for consistency; suite auto-selection already prevents the old 404 path.
- [ ] **Regenerate `native-hub46/manifest.json` against the final repaired provider SHA.** The current file pins the historical infrastructure-proof provider SHA and must not be the final certification transport.
- [ ] Final acceptance must run exactly five first-class Labs on **one frozen NiakVIO SHA** and record exact official Nuvio client refs:
  1. TV Android — NuvioTV.
  2. Mobile Android — NuvioMobile.
  3. Mobile iOS — NuvioMobile.
  4. Desktop macOS — NuvioDesktop.
  5. Desktop Windows — NuvioDesktop.
- [ ] Android Mobile older evidence with UI launch failure / incomplete Brain is not final proof.
- [ ] Desktop evidence predating raw-TMDB/runtime fixes is not final proof for affected providers.
- [ ] Labs remain observational: do not patch official Nuvio clients just to turn a Lab green.
- [ ] Keep reader/player failures separate from provider extraction failures in final classifications.

## Domain Refresh

- [x] Old `official_site`-only description is obsolete. Current Domain Refresh is a full-CONFIG transaction v2.
- [x] Current contracts cover source authority, full CONFIG rebuild, source-qualified/content-hashed filenames, activation/projection/version synchronization, cycle/rollback safety, idempotence and Core/Lego invariance.
- [x] `VALIDATION.md` and `ARCHITECTURE.md` were updated to describe the current transaction model and related tests passed in the Hub-46 transport validation work.
- [ ] Keep generic old-host → new-host derivative reconciliation (logo/icon/favicon where applicable) and synthetic A→B proof covered as the implementation evolves.
- [ ] Reconcile older stale Domain Refresh wording in remaining docs/comments instead of reintroducing official-site-only behavior.

## Brain / Learning / discovery

- [x] Weekly upstream/provider discovery workflow is structurally scheduled (`37 3 * * 3`), read-only, covers the configured non-P2P upstreams and must not mutate catalogue/manifests/providers.
- [x] Stale TEMP workflow that attempted to remove the weekly watch has been deleted.
- [ ] Verify an actual scheduled weekly execution/artifact before declaring the operational watch closed; schedule definition/unit tests alone are insufficient.
- [ ] Review real multi-day Brain differential evidence: learned providers, repairs, regressions and state preservation across days.
- [ ] Preserve international discovery infrastructure and candidate JSON/CSV/XLSX; future refreshes must keep country balance and substantial UHD/4K representation.

## Provider presentation / UI

- [ ] Preserve 72×32 and 96×40 compressed WebP provider-logo assets and first-letter fallback behavior for missing logos.
- [ ] Revalidate branding, language labels and quality metadata after final materialization.
- [ ] Verify **visible provider-logo propagation in official Nuvio UI/Labs**. Asset-contract tests alone do not close the old UI request, and official Nuvio repos must not be patched just to force success.

## Repository hygiene / docs

- [x] Durable secondary-task ledger exists in `automation/SECONDARY-TASKS-DURABLE.md` and is mirrored into `MEMORY.md`.
- [x] Completed/stale TEMP workflows removed in this pass include the Hub-46 migration workflow, weekly-watch removal workflow, memory-sync workflow and intermediate minimizer audit workflow.
- [ ] Remove remaining obsolete `temp-*.yml` workflows only after extracting useful evidence from diagnostics such as NetMirror and VoirAnime/Coflix.
- [ ] Reconcile `CHANGELOG.md`, `VALIDATION.json`, README EN/FR, Lab triggers/matrices and `automation/provider-v3-architecture.json` with the final candidate.
- [ ] Explicitly document 96 global catalogue vs 46 current Hub/Lab scope wherever installation/validation docs remain ambiguous.
- [ ] Regenerate/recheck `ARCHITECTURE.docx` only after architecture wording is final.
- [ ] Keep `MEMORY.md` updated with every important provider repair, global architecture correction, Lab candidate, failure and final proof.

## Final minimizer / deterministic publication gate

- [ ] **Only after functional stabilization**, run the NiakVIO-safe Provider v3 minimizer contract/preview/published tests on all 96 bundles.
- [ ] Run byte-stability, deterministic reverse rebuild, content-hash/source-qualified filename synchronization, projection consistency and fixed-point/idempotence.
- [ ] Do not use Terser and do not make minification an intermediate provider-repair criterion.
- [ ] Measure final bundle size and prove runtime semantics/managed marker cardinality are unchanged.

## Security / final certification

- [ ] Final frozen SHA must pass repository CodeQL / extended security workflows without weakening rules.
- [ ] Run/verify dependency audit (`npm audit --omit=dev --audit-level=high` or current repository equivalent) on the final candidate.
- [ ] Validate release hashes/integrity and retain final Labs/security evidence.

## Completion rule

The work is not complete merely because 46 rows are enabled or structural CI is green. Completion requires: current REGRESSION/ZERO debt resolved or precisely classified; all 46 have defensible evidence/blocker/opaque status; global Core/runtime rules remain shared rather than provider-specific; final Hub-46 transport is regenerated on the repaired frozen SHA; all five native Labs run against that exact candidate with exact client refs; final minimizer/reverse-rebuild/fixed-point is green; security gates are green; visible UI/logo and reader-vs-provider evidence is reconciled; docs and `MEMORY.md` are current; obsolete TEMP workflows are removed; and every residual issue is explicitly recorded with evidence/reason.
