# NiakVIO — Recovery Memory

Last authoritative rewrite: 2026-09-03.
This file is the recovery source of truth if ChatGPT/session context is lost. Prefer the latest repository state over older chat summaries.

## Hard branch safety
- Active development branch: `workbench/provider-v3-performance-playback`.
- DO NOT write to `main` while this workbench is being completed.
- Production/main was intentionally frozen for user testing at SHA `8116f02289226ab8fb823f7ae03e204f73926a83`.
- Production manifest at freeze: 5.21.31, 96 providers, MOVIX disabled, PURSTREAM restricted to movie/tv.
- All current architecture/runtime/lab/minifier changes stay on workbench until final manual acceptance.

## Primary product goal
Build the most stable possible NiakVIO baseline:
1. clean Provider v3 architecture;
2. stable structured DATA;
3. stable shared CORE Lego;
4. provider JS immutable during routine automation;
5. good speed without premature provider aborts;
6. rich standard stream metadata/badges consumed correctly by Nuvio clients;
7. playback/readability verified on official Nuvio clients;
8. deterministic manual full reconstruction available only when explicitly needed;
9. LEARN is the only automated code-evolution/repair system;
10. eventual NiakVIO-aware JS minifier that preserves the comment/Lego architecture exactly.

## Provider v3 invariant
- Catalogue size: 96 providers.
- A runtime Provider JS is built conceptually from:
  - clean ProviderBase;
  - structured provider DATA;
  - PROVIDER.* Lego;
  - CORE.* Lego.
- Legacy/upstream/published old Provider JS is knowledge/reference only and must never become an executable reconstruction seed.
- Provider envelope markers are mandatory:
  - `/* BEGIN NIAKVIO_PROVIDER */`
  - `/* END NIAKVIO_PROVIDER */`
- Managed Lego markers are mandatory and ordered:
  - PROVIDER.* blocks first;
  - CORE.* blocks after;
  - every managed block uses STARTFIX/CLOSEFIX and managed FIXDATA.
- Routine automation must not modify the structure/order/content of these blocks.

## Automation ownership — simplified architecture
There is ONE routine workflow:
- `.github/workflows/sync.yml`
- display name: `CORE - Verify & Publish`

### Quick profile
Purpose: fast event-driven safety gate.
Triggers:
- push;
- PR;
- manual dispatch;
- Domain Refresh follow-up.
Responsibilities:
- exact 96 published-byte static audit;
- critical DATA/Core/runtime unit contracts;
- playback policy / stream presentation / type safety contracts;
- no full network health;
- no manifest publication;
- no provider reconstruction;
- no repair;
- no provider/Core/Fix mutation.
Quick is NOT scheduled.

### Deep profile
Purpose: full verification + publication, still non-repairing and non-reconstructing.
Triggers:
- schedule Tuesday + Friday at 04:47 UTC;
- manual dispatch mode=deep.
Responsibilities:
- everything in Quick;
- full structural contracts;
- read-only hub observation;
- full runtime/network health observation of the exact 96 published JS;
- regenerate language manifest projections from observed health;
- regenerate reports and integrity inventories;
- publish only reports/manifests/hashes if changed.
Deep NEVER:
- repairs providers;
- promotes candidates;
- reconstructs Provider JS;
- edits DATA/Core/Fix/runtime code.

The removed duplicate routine workflow `.github/workflows/core-media-finalize-main.yml` must remain deleted.

## Domain Refresh — the only routine production DATA-write exception
Workflow: `.github/workflows/domain-refresh.yml`.
Purpose: maintain availability when an authoritative provider hub changes its PRIMARY DOMAIN.

Strict scope:
- may update ONLY `provider_patches.<provider>.official_site`;
- may update domain history;
- may update the corresponding `PROVIDER.<ID>.CONFIG.V1` officialSite value and content-addressed filename/reference;
- must prove every byte outside that CONFIG Lego is identical;
- must not run provider/Core repair or reconstruction;
- must not change official_api, routes, replacements, api_recipe, patch options, patch scripts, CORE, PROVIDER fix logic or provider capabilities.

Trust model:
- provider must have an authoritative hub source;
- domain-only resolver considers hub / public Telegram / redirect-derived authoritative candidates;
- direct/search fallback must never autonomously replace official_site;
- if the captured URL is not safely validated, keep the previous site;
- if nothing changed, do nothing and do not rewrite/reapply.

Important architectural decoupling:
- `CORE.CATALOGUE_ALIAS_RECOVERY` no longer serializes the provider domain into CORE bytes.
- It reads `NIAKVIO_PROVIDER_MODEL.officialSite` at runtime.
- Commit that introduced this decoupling: `3dd72f7b90d3b46481244f3795fdaaed5898eb73`.

Domain helper scripts currently present:
- `scripts/validate_domain_refresh_scope.py`
- `scripts/update_provider_v3_domain_config.py`
- `scripts/audit_provider_v3_static.py`

## LEARN — exclusive code evolution owner
Workflow: `.github/workflows/brain-learning-lab.yml`.
LEARN is the only automated component allowed to TRY to evolve/repair NiakVIO code.

Responsibilities:
- observe failing/weak providers, including disabled/off providers;
- investigate CORE/Provider fix weaknesses;
- attempt repairs only in Learning sandbox/workspace;
- validate candidate changes;
- persist sanitized learning/proposals;
- open/refresh review PRs (brain-repair proposal flow).

Hard restrictions:
- no direct production runtime publication;
- no direct main mutation for repair;
- human review/merge remains the promotion gate.

Provider issues remaining after the stable baseline should be handled through LEARN proposals, not daily reconstruction.

## Manual reconstruction
Workflow: `.github/workflows/provider-v3-reconstruct-all.yml`.
This is the ONLY intended full 96/96 reconstruction path.
It is manual-only.
It must:
- rebuild from clean ProviderBase + DATA + owned Lego;
- never use legacy/upstream Provider JS as seed;
- reconstruct all 96;
- prove reverse reconstruction byte identity;
- run runtime/integrity tests;
- refuse direct commit to main;
- optionally commit the verified reconstruction only to a selected non-main branch.
Normal Quick/Deep/Domain/Labs must never call the full materializer.

## Current runtime tuning on workbench
Commit `58425bf9c0d7b8883c05a63ef532217f3840daea` introduced the intended shared Core tuning:
- TV Provider v3 internal budget: 25s (was ~10s);
- Mobile/Desktop Provider v3 internal budget: 30s (was ~18s);
- native lab observation budget target: 40s.

Why:
- official NuvioTV plugin execution allows about 120s;
- official NuvioMobile/NuvioDesktop execution allows about 60s;
- NiakVIO was self-aborting too early and providers could appear red around 10–15s even though the client still allowed them to finish.

Important:
- keep individual network/fetch deadlines short;
- the longer provider envelope budget is not permission for hung requests;
- optimize providers to yield useful streams early rather than simply waiting longer.

## Stream presentation / metadata work
Target problem observed by user:
- Interstellar returned only a few providers before timeout/red;
- stream titles could show e.g. `Kehflix - Inconnue`;
- quality and badges were often missing.

Shared presentation V18 direction:
- infer quality from normal fields AND safe URL facts;
- inspect quality/resolution/height/width/label;
- normalize FHD -> 1080p;
- HD -> 720p;
- SD -> 480p;
- retain 2160p/4K and other numeric resolution recognition.
Important client fact:
- custom NiakVIO badgeIds/displayBadges alone are not enough;
- official Nuvio clients derive much of the UI from standard stream fields/text;
- enrich standard fields first and avoid extra network probes when facts are already locally available.

## Native client labs
Required proof platforms:
1. TV Android (official NuvioTV);
2. Mobile Android (official NuvioMobile);
3. Mobile iOS (official NuvioMobile);
4. Desktop macOS (official NuvioDesktop);
5. Desktop Windows (official NuvioDesktop).

Representative corpus currently used:
- Interstellar (movie);
- Breaking Bad S01E01 (series);
- Jujutsu Kaisen S01E01 (anime).

Lab goals:
- provider discovery/latency;
- stream count and provider count;
- stream metadata quality/badges;
- playable transport reach;
- navigation/session isolation;
- no stale result bleed between works/types;
- exact workbench Provider JS bytes should be tested;
- Labs are evidence, never repair engines.

Known lab cleanup still required:
- Desktop mutating fixed-point/reapply canary was removed from the lab; Desktop now observes only.
- Full iOS provider timeout is 40s; Learning-only targeted iOS mode remains 8s.
- Android TV/Mobile lab timeout is 40s.
- `tests/native_lab_observational_purity_test.py` now fails if any native lab reintroduces Provider reconstruction/repair/apply steps.

## Nuvio upstream issues
Two earlier issues were auto-closed because of missing tags:
- NuvioTV #3314
- NuvioDesktop #569

Decision as of 2026-09-03:
- do NOT republish yet;
- our previous 10/18s NiakVIO budget could create similar symptoms;
- re-run navigation/session scenarios in the five labs on the corrected workbench first;
- if the lifecycle/session problem still reproduces with fresh evidence, republish properly with labels + current logs;
- otherwise leave closed.

## Workflow simplification commits / milestones
Useful recent workbench commits:
- `58425bf9c0d7b8883c05a63ef532217f3840daea` — 25/30s provider budget + stream facts work.
- `b45048241b1857a7be2a02a2c6ab6340fc0dbe5c` — Quick/Deep verification-only direction.
- `3dd72f7b90d3b46481244f3795fdaaed5898eb73` — Core domain lookup reads Provider CONFIG runtime DATA.
- `639b927c75881c731994274990c3dbac17026a5f` — collapse duplicate routine workflows into one CORE workflow.
- `193a750c2d50f38ccdf26a9fc44af6971b4b7987` — Quick and Deep assigned distinct roles.

## Current CI observation
The first CORE run after `193a750...` failed before meaningful runtime tests because `tests/provider_v3_workflow_ownership_test.py` still expected the superseded cron `17 5 * * *`.
Correct target cron is `47 4 * * 2,5`.
This is a stale contract-test failure, not a provider/runtime failure.
The next commit after this MEMORY rewrite fixes that assertion.

Earlier Quick attempt also showed that `provider_base_store.py validate` reports historical contaminated ProviderBase state (anime-sama first). ProviderBase-store cleanup is a reconstruction concern, not a routine Quick gate. The manual reconstruction path must eventually clean/validate the reconstruction source before the one controlled workbench rebuild.

## Next execution order
1. Make CORE Quick green with the updated workflow contract.
2. Remove all provider mutation/materialization from the native Labs.
3. Align full iOS lab provider timeout to 40s.
4. Harden LEARN contract so disabled/off providers are explicitly eligible for proposals and only PR output is allowed.
5. Clean/validate ProviderBase reconstruction source in the manual reconstruction path.
6. Execute ONE controlled full 96/96 reconstruction on the workbench to materialize current Core changes (25/30s, presentation V18, domain/Core decoupling, etc.).
7. Prove 96/96 reverse rebuild on that one generation.
8. Run TVAndroid / MobileAndroid / MobileIOS / DesktopMACOS / DesktopWindows labs on those exact bytes.
9. Fix every architecture/runtime/playback/metadata issue found, using shared Core/Data where appropriate and provider-specific fixes only where truly necessary.
10. Re-run the relevant labs until stable.
11. Build the NiakVIO JS minifier only after runtime/architecture gates are stable.

## Minifier / minifizer requirements
Do not use generic Terser blindly.
The future NiakVIO minifier must understand the Provider architecture and preserve:
- BEGIN/END NIAKVIO_PROVIDER;
- STARTFIX/CLOSEFIX markers;
- FIXDATA blocks/payloads;
- Provider/Core Lego ordering;
- comments used as machine-readable ownership boundaries;
- ability to replace/remove one managed Lego later without guessing source shape.
It must never do unsafe global string replacement.
It should minify only safe JS payload regions between protected architecture boundaries.
Before enablement require:
- byte-safe marker preservation tests;
- parse/syntax equivalence;
- runtime behavioral parity;
- reconstruction/minification determinism;
- five-client lab parity on representative corpus.
Keep it disabled in production until all proofs are green.

## Five-lab gate is explicit
- The acceptance surface is exactly five first-class platforms: TVAndroid, MobileAndroid, MobileIOS, DesktopMACOS, DesktopWindows.
- `tests/native_five_lab_coverage_test.py` enforces all five and their workbench trigger coverage.
- The Android workflow contains two separate labs (TV + Mobile), iOS is its own macOS/iOS job, and Desktop expands to macOS + Windows matrix jobs.

## One controlled reconstruction trigger
- Manual workflow now also accepts the explicit workbench-only trigger file `.github/triggers/provider-v3-reconstruct-all.json`.
- The trigger has no schedule and cannot run from ordinary workbench changes.
- Before reconstruction it may run `provider_base_store.py repair-derived` ONLY as deterministic ProviderBase layering cleanup, then validates all bases including artifacts.
- This is not Learning repair and does not alter provider behavior; it strips leaked generated/publication tails.
- An explicit workbench trigger commits the verified cleaned ProviderBase/PROVENANCE + reconstructed 96/96 outputs back to the workbench only.

## 2026-09-03 — canonical Provider/Core boundary realignment
- Run 33699439253 proved the new canonical ProviderBase v3 store is valid 96/96:
  - providers=96
  - unique_bases=96
  - clean=96
  - reconstruction_required=0
  - artifact_validation=true
  - provider_js_seed=false
  - upstream_js_seed=false
- The next failure was not ProviderBase: `provider_brick_portfolio_audit_test.py` was auditing bare ProviderBase files as if they were already composed Provider JS. That produced 96 missing Core-boundary errors and apparent second-pass Castle/Movix Provider Lego insertions.
- Canonical runtime layout is now explicitly:
  1. BEGIN NIAKVIO_PROVIDER
  2. common ProviderBase v3
  3. PROVIDER.<ID>.CONFIG.V1 structured DATA
  4. all provider-specific PROVIDER.* Lego
  5. exactly one `/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */`
  6. all CORE.* Lego
  7. END NIAKVIO_PROVIDER
- `apply_provider_overrides.py` now strips stale Core Lego + stale Core boundary before recomposition, applies PROVIDER.* first, then inserts exactly one Core boundary before Core composition.
- `provider_brick_portfolio_audit_test.py --published --require-all` audits the exact JS referenced by the current manifest. Quick and post-reconstruction validation use this mode; bare ProviderBase is no longer confused with a composed provider.
- `materialize_provider_v3_all.py` and `audit_provider_v3_static.py` both fail closed unless all PROVIDER.* blocks are before the Core boundary and every CORE.* block is after it.
- Workbench HEAD at this checkpoint: `559eed2ad529f95c9f7bfe10ad425ba3d8c36bad`.

## 2026-09-03 — Core unit-contract cleanup before 96/96 rebuild
- The 5.21.0 capability gate now records Purstream's intentional current semantic scope as movie/tv while preserving historical 5.21.0 types for audit context.
- CORE.MEDIA_TYPE_RESOLUTION.V1 moved to revision `tmdb-data-contract-launch-gate-v26-authoritative-context-reconcile`.
- v26 fixes deferred-TMDB positive-output reconciliation: if TMDB confirms the same canonical/provider transport, NiakVIO does NOT execute the provider a second time. It promotes the authoritative context and reconciles only diagnostic fields already present in returned rows.
- A dedicated unit test proves stable Dark Matter TV verification performs exactly one provider execution and one TMDB request while clearing `degraded`.
- `normalize_stream_presentation_v12.py` is now a compatibility validator for committed V18, not a mutating normalizer. It validates `all-providers-standard-fields-url-facts-v18` read-only.
- `global_stream_presentation_test.py` now validates V18 fixed-point directly with no apply/mutation semantics.

## 2026-09-03 — V18 presentation syntax fix
- Manual reconstruction retry 9 reached the V18 presentation unit test after ProviderBase 96/96, 5.21 capability and media-type v26 gates were green.
- A real syntax bug was found in `global_stream_presentation_v1.py`: because the JS wrapper is a Python raw string, one separator was written as literal `\\nfunction blob(...)` instead of an actual newline.
- Node rejected the generated provider with `SyntaxError: Invalid or unexpected token`.
- Commit `421bd5c62fdf431a4d557cb28e6ea5b9a83c45ff` replaces that single literal escape with a real source newline.
- `global_stream_presentation_test.py` now statically rejects any literal `\\nfunction` in the canonical V18 patch source before executing runtime cases.

## 2026-09-03 — pre-reconstruction gate fully green / canonical span fix
- Manual reconstruction retry 10 was the first run where the complete pre-reconstruction gate passed:
  - ProviderBase v3 store 96/96 clean + artifact-valid;
  - clean reconstruction contract;
  - 5.21 capability regression;
  - media-type v26;
  - stream presentation V18.
- The run then entered `Reconstruct all 96 providers from DATA + Lego` for the first time.
- Its first failure was in the materializer boundary assertion itself, not Anime-Sama/runtime: the new assertion reconstructed an obsolete `START NIAKVIO_FIX` marker string while Provider v3 uses canonical `STARTFIX/CLOSEFIX`.
- `materialize_provider_v3_all.py` now imports and uses `provider_patch_blocks.owned_span()` for all Provider/Core Lego positions. Boundary validation and reverse-code ownership therefore share one parser/source of truth.

## 2026-09-03 — first full 96/96 generation + reverse proof
- Retry 11 successfully materialized all 96 providers:
  - generation `949d251de7e3cb4d`
  - `FIELD_PROVIDER_V3_ALL_MATERIALIZED providers=96`
  - reverse reconstruction `PROVIDER_V3_REVERSE_REBUILD_OK providers=96 generation=949d251de7e3cb4d byte_identical=96/96`
  - workspace context only; mainTouched=false.
- The subsequent published-byte portfolio gate found all 96 non-idempotent only because a second Core recomposition accumulated one blank line before `NUVIO_GLOBAL_CORE_START_BOUNDARY_V1`; `changed_blocks=none` on every reported provider.
- `apply_provider_overrides._strip_generated_core_tail()` now removes the Core boundary together with its owned following newline, restoring the exact pre-Core Provider bytes before recomposition.
- This is a byte-idempotence fix only; no Provider/Core Lego behavior changed.

## 2026-09-03 — retry 12–14 post-gate fixture alignment
- Retry 12 again materialized all 96 providers and proved reverse reconstruction generation `949d251de7e3cb4d` byte-identical 96/96. The boundary-newline idempotence fix held; the next red was a stale static ownership-order assertion, subsequently corrected by `20785a91947a70ae50fa9adbba4aa16d4a59f8b4`.
- Retry 13 again reached 96/96 + reverse 96/96, and `PROVIDER_V3_STATIC_AUDIT_OK providers=96 reconstruction=false` passed. The next failure was isolated to `global_stream_presentation_pipeline_test.py`: its synthetic source had BEGIN/END Provider markers but no `NIAKVIO_PROVIDER_BASE_OWNED_V3`, so the HLS Core Lego correctly classified it as legacy and the idempotence reapply then rejected the escaped Core block.
- Retry 14 reproduced the same fixture-only failure after another successful 96/96 materialization/reverse proof; static audit, media-type resolution and stream presentation V18 were green before that failure. No reconstructed files were committed and main remained untouched.
- Synthetic Core pipeline/playback/future-provider tests now model a minimal clean-v3 Provider envelope instead of a hybrid legacy/v3 envelope. Production clean-v3 detection remains strict; no runtime Lego behavior was relaxed.
- Next controlled reconstruction is retry 15 on the workbench only.

## 2026-09-03 — retry 15 removed stale native catalogue budget contract
- Retry 15 again proved ProviderBase 96/96 clean, materialization 96/96, generation `949d251de7e3cb4d`, reverse rebuild byte-identical 96/96, published brick audit green, static audit green, media-type Core green, presentation V18 green, presentation pipeline green and stream identity green.
- The next failure was not provider/runtime output: `runtime_capability_media_safety_v4_test.py` still launched `native_catalogue_recovery_budget_test.py`, which imported deleted `scripts/provider_patches/native_catalogue_recovery_budget_v1.py`.
- Current `CORE.CATALOGUE_ALIAS_RECOVERY.V2` is positive-output identity protection only; it does not perform shared zero-result catalogue network recovery. Therefore a separate native catalogue recovery budget Lego is obsolete.
- Removed stale `tests/native_catalogue_recovery_budget_test.py` and `scripts/apply_native_catalogue_recovery_budget_upgrade_v1.py`; neither was referenced by provider-overrides, CORE Quick/Deep, reconstruction or LEARN.
- `runtime_capability_media_safety_v4_test.py` now retains only the still-active native HLS budget and synchronous target-order companion regressions.
- No provider behavior was relaxed and main remains untouched. Next controlled reconstruction: retry 16.

## 2026-09-03 — retry 16 legacy native target-order cleanup
- Retry 16 again proved ProviderBase 96/96 clean, materialization 96/96 and reverse rebuild byte-identical 96/96, then passed published brick audit, static audit, media-type resolution, V18 presentation, presentation pipeline and stream identity.
- The next failure was `native_hls_integrity_budget_test.py` asserting the obsolete `START NIAKVIO_FIX` syntax although managed Lego now use canonical `STARTFIX/CLOSEFIX`.
- Pre-retry audit also found `native_sync_fetch_target_order_test.py` importing deleted `native_sync_fetch_target_order_v1.py`. Its old `apply_runtime_capability_upgrade_v4.py` still referenced that deleted patch plus the deleted minified compatibility patch, contradicting the current runtime contract: target traversal/order is Core-owned and no legacy source-shape target-order patch is replayed.
- Updated the active HLS budget test to canonical STARTFIX/CLOSEFIX markers.
- Removed stale `tests/native_sync_fetch_target_order_test.py` and `scripts/apply_runtime_capability_upgrade_v4.py` instead of resurrecting obsolete source-shape patchers.
- `runtime_capability_media_safety_v4_test.py` now keeps only the active native HLS companion. No runtime policy was weakened; main remains untouched. Next controlled reconstruction: retry 17.

## 2026-09-03 — retry 17 reached canonical post-rebuild contracts
- Manual reconstruction retry 17 again materialized all 96 providers at generation `949d251de7e3cb4d` and proved reverse reconstruction byte-identical 96/96.
- Published brick audit, Provider v3 static audit, media-type v26, stream presentation V18, presentation pipeline, stream identity and runtime capability media safety all passed on the reconstructed workspace bytes.
- The first red was a stale test contract in `global_playback_integrity_policy_test.py`: StreamZo HLS options moved from legacy `patch_script_options` to `core_options.hls_runtime_integrity`; runtime configuration itself was present and correct.
- The same cleanup batch aligns HLS/sanitizer assertions to canonical STARTFIX/CLOSEFIX helper markers, removes the obsolete Terser-specific test wording, and upgrades the published Lego contract from legacy marker/v20 assumptions to canonical ownership helpers + media-type v26 launch/positive-output gates.
- No provider behavior is weakened and main remains untouched. Next controlled reconstruction: retry 18.

## 2026-09-03 — retry 18 passed runtime post-gates; workspace activation report drift isolated
- Retry 18 again materialized all 96 providers and proved generation `949d251de7e3cb4d` reverse byte identity 96/96.
- The previously stale contracts are now proven fixed: published brick audit, static audit, media-type v26, presentation V18/pipeline, stream identity, runtime media safety, playback integrity, stream sanitizer and published Provider Lego v26 all passed on reconstructed bytes.
- Release integrity then failed only because MOVIX is intentionally disabled in the checked-out published baseline while the committed historical Deep `health-report.json` still says `preserved-current-enabled-ci-uncertain / enabled=true`.
- Manual Provider v3 reconstruction is a non-publishing workspace operation and does not own activation decisions. Activation preservation now defers an unchanged baseline-disabled provider in `NUVIO_PROVIDER_V3_CONTEXT=workspace` even when the historical Deep report is stale; production/Deep retains the strict requirement that its current report must also say disabled.
- A regression test covers workspace acceptance, production rejection of stale enabled reports, and production acceptance when both baseline and current report are disabled.
- No activation flag, provider runtime, or main byte is changed. Next controlled reconstruction: retry 19.

## 2026-09-03 — retry 19 completed and committed the canonical 96/96 workspace
- Retry 19 completed successfully end-to-end.
- ProviderBase v3 remained clean and artifact-valid; all 96 providers were reconstructed from DATA + owned Lego at generation `949d251de7e3cb4d`.
- Reverse reconstruction remained byte-identical 96/96.
- Runtime/release post-gates all passed, including published brick audit, Provider v3 static audit, media-type v26, presentation V18/pipeline, stream identity, runtime media safety, playback integrity, terminal sanitizer, published Provider Lego contract, release hashes and release integrity.
- The verified reconstruction artifact uploaded successfully.
- GitHub committed the reconstructed workspace as `72a99271f59c81a64fd8c9a353b6ba86827f39ac` with message `chore: reconstruct Provider v3 96/96`.
- Main remains untouched.
- Because the verified provider commit is emitted by GitHub Actions and therefore does not cascade another push workflow, a provider-byte-neutral ownership-test hardening commit is used to trigger CORE Quick while preserving the exact reconstructed provider bytes.

## 2026-09-03 — CORE Quick green on reconstructed Provider v3 bytes; five labs triggered next
- CORE Quick run `33708888221` / run number 1783 completed successfully on commit `552f8dd6d478c823bb820f598d6220a26d6f4c6d`.
- That commit is provider-byte-neutral relative to the verified reconstruction commit `72a99271f59c81a64fd8c9a353b6ba86827f39ac`; it only hardens the manual-workspace ownership test and records state in MEMORY.
- Quick therefore validated the exact reconstructed 96 provider bytes: five-lab coverage/purity, Provider v3 static audit, published brick portfolio, 5.21 capability regression, media-type v26, presentation V18/pipeline, stream identity, runtime media safety, playback integrity and terminal sanitizer all passed.
- The shared five-lab trigger is now advanced once for TVAndroid, MobileAndroid, MobileIOS, DesktopMACOS and DesktopWindows. All five labs must observe these same Provider JS bytes; Labs remain observational evidence only and never repair/reconstruct.
- Main remains untouched.

