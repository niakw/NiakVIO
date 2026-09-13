# NiakVIO — open-task recovery checkpoint — updated 2026-09-13

This is the operational recovery list for the active candidate branch `fix/labs-5.21.44-20260912`. `MEMORY.md`, exact repository state and current GitHub Actions evidence override stale chat summaries. `main` remains untouched by this repair campaign until explicit publication authorization.

## Hard constraints / architecture

- Canonical catalogue remains **96 Provider Objects**; never delete providers to manufacture a green yield.
- Current native Hub/Lab campaign is the exact **46-provider** scope from `automation/evidence/hub-lab-matrix-46.json`; the other 50 catalogue rows remain outside this physical campaign, not deleted.
- Wrong title/type/season/episode is worse than zero. Identity/media integrity stays fail-closed.
- Hub/registry presence is discovery knowledge, never execution proof. Telegram remains discovery-only.
- Runtime/client portability is Core-global Lego. Timer shims, fetch/URL portability, stale-generation suppression, HTTP 403/media fail-closed and terminal sanitation must never become provider-specific runtime patches.
- Provider timeout remains **25 s**. Preserve A→B→C latest-generation isolation even if fetch ignores `AbortSignal`.
- Terser is forbidden. Provider v3 minimization happens only after functional stabilization and must preserve managed boundaries, deterministic reverse rebuild and byte fixed point.

## Main priority — provider yield / parity

- [x] Upstream parity authority uses `engine_v2/config/provider-upstreams.json`; the old `sources.json` lookup is obsolete.
- [x] Parity semantics are strict: only exact `upstream_ok_niakvio_ko` is a certain NiakVIO regression. ZERO/technical inconclusive is not auto-repair debt.
- [x] PlayIMDb proof-v5 typed resolver was restored; exact movie+TV live proof is green.
- [x] Fail-closed batch quarantine repair run `34766893110` replaced all-or-nothing retries. Accepted after strict-yield + recent parity: `animevost-fr`, `playimdb`, `uhdmovies`. Failed-provider mutations were hard-reset and did not survive.
- [x] Full-reserve parity run `34766524150` scanned the 15 historical ZERO rows plus three active-loss exceptions through up to **32 recent candidates per declared lane**. Result: **3 certain regressions, 15 ZERO/technical-inconclusive, 0 provider-level RESAMPLE**.
- [x] The 15 rows that remain ZERO/inconclusive and must **not** be blindly mutated are: `4khdhub`, `allanime`, `allwish`, `anikototv`, `anime-ultime`, `animesalt`, `animetsu`, `flemmix`, `fullanime`, `moviebox`, `moviesmod`, `showbox`, `vidfast`, `vidlove`, `vostfree`.
- [ ] Repair the only three current full32 certain regressions as one evidence-driven wave:
  - `animevostfr`: movie `superman-2025` + anime `tokyo-ghoul-2014-s01e01`;
  - `kurage`: anime `high-school-of-the-dead-2010-s01e01`;
  - `voiranime`: anime `tokyo-ghoul-2014-s01e01`.
  Current diagnostic run: `34768054363`.
- [ ] After the trio repair, rerun the identical exact cases **and** full32 parity for the trio; require zero certain regression and zero wrong-content contradiction before retaining any mutation.
- [ ] Reclassify the former historical hypotheses (Cineby/Coflix/French-Manga/NetMirror/Papadustream/StreamZo/etc.) from current parity evidence only. They are no longer an automatic repair queue merely because they appeared in older runs.
- [ ] Maintain a nominative blocker list for the remaining 46: domain/hub, metadata identity, search/detail, API/player extraction, anti-bot/network, stream transport, content identity, native player, or unknown/opaque. `0 streams` alone is not opaque.

## Global Core / Desktop/runtime work

- [x] `CORE.RUNTIME_COMPAT.V1` owns missing timer globals and Desktop URL/fetch portability.
- [x] Provider-specific ownership of Core-global runtime modules is rejected.
- [x] Terminal stream/media policy is Core-global; HTTP 403/404/410 and terminal sanitizer remain fail-closed.
- [x] `tests/global_core_runtime_ownership_test.py` checks all 96 bundles and is green.
- [x] Explicit no-timer execution proof is green: `GLOBAL_RUNTIME_NO_TIMER_EXECUTION_OK rows=1 setTimeout=function clearTimeout=function`. A Desktop-like host with no timer globals is Core-shimmed without provider disappearance.
- [ ] Reconcile any remaining stale profile test assumptions (not provider code) if final fixed-point suite exposes them.

## Hub-46 transport and Native Labs

- [x] Root-name repository 404 root cause is closed: official Nuvio strips literal `/manifest.json`.
- [x] Physical transport is `native-hub46/manifest.json`, exactly 46 rows, terminal filename `manifest.json`, provider files pinned by immutable absolute URLs.
- [x] Desktop, Mobile and TV suites select the physical nested manifest during the Hub-46 campaign; iOS and Desktop workflows are explicit.
- [x] Android **prebuild** also switches to `native-hub46/manifest.json` when the scope matrix is active, so preparation/prebuild/runtime agree before QEMU.
- [x] Adaptive native corpus contract is **32 movie + 32 TV + 32 anime**, starts **1+1+1**, rotates one-at-a-time only on clean zero, and stops on positive/error/wrong-content evidence.
- [ ] **Regenerate `native-hub46/manifest.json` against the final frozen repaired provider SHA.** Current pinned provider SHA is infrastructure-era and is not final certification transport.
- [ ] Run exactly five first-class native Labs on one frozen NiakVIO SHA and record exact official client refs:
  1. TV Android — NuvioTV;
  2. Mobile Android — NuvioMobile;
  3. Mobile iOS — NuvioMobile;
  4. Desktop macOS — NuvioDesktop;
  5. Desktop Windows — NuvioDesktop.
- [ ] Keep reader/player failures separate from provider extraction failures. Never patch official Nuvio clients merely to turn a Lab green.

## Domain Refresh

- [x] Domain Refresh is the full-CONFIG transaction v2, not the obsolete `official_site`-only updater.
- [x] Source authority, CONFIG rebuild, source-qualified/content-hashed filenames, projections/versioning, cycle/rollback safety, idempotence and Core/Lego invariance are covered by current contracts.
- [x] `VALIDATION.md` and `ARCHITECTURE.md` describe the current Domain Refresh transaction.
- [ ] Keep generic old-host → new-host derivative reconciliation and synthetic A→B proof covered if this subsystem changes again.

## Brain / Learning / discovery

- [x] Weekly upstream/provider discovery is structurally scheduled (`37 3 * * 3`), read-only and non-P2P.
- [x] Obsolete TEMP workflow that tried to remove the weekly watch is gone.
- [ ] Verify an actual scheduled weekly execution/artifact before declaring operational scheduling proven historically.
- [ ] Review real multi-day Brain differential evidence before treating Learning state as production authority.
- [ ] Preserve international discovery candidate data and country/UHD balance.

## Provider presentation / UI

- [ ] Preserve 72×32 and 96×40 compressed WebP provider-logo assets and first-letter fallback.
- [ ] Revalidate branding, language labels and quality metadata after final materialization/minimization.
- [ ] Verify visible provider-logo propagation in the official Nuvio UI/Labs without patching official clients.

## Repository hygiene / docs

- [x] README EN/FR and `VALIDATION.md` now explicitly distinguish **96 catalogue / 46 physical Lab scope / 3×32 adaptive reserve / 1+1+1 initial sampling**.
- [x] `VALIDATION.json` was upgraded from obsolete 5.15.0-era metadata to current 5.21.43/candidate contracts, with final certification explicitly pending a frozen candidate SHA; machine-summary validation passed.
- [x] `ARCHITECTURE.md` now documents the explicit candidate-branch policy and Hub-46 adaptive Lab model rather than claiming every repair must write directly to `main`.
- [x] Completed/stale TEMP workflows already removed include the old Domain Refresh, Brain smoke, manual-TV/V34, mobile V36, V35 rebuild, positive-output audits, Hub46/docs/prebuild migrations, batch repair, full32 parity, old Mugiwara diagnostic, old parallel Lab dispatcher and old VF pre-main smoke.
- [ ] Keep `temp-full32-regression-trio-diagnosis.yml` only until its current evidence is consumed, then delete it.
- [ ] Extract/supersede unique evidence from `temp-netmirror-movie-diag.yml`, `temp-voiranime-coflix-payload-probe.yml` and `temp-animesalt-runner-recheck.yml`, then delete them if no longer operationally useful.
- [ ] Update the top/current-state sections of `MEMORY.md` after the trio repair; its header/topology still contains 2026-09-07-era branch/publication wording.
- [ ] Reconcile `CHANGELOG.md`, Lab triggers/matrices and `automation/provider-v3-architecture.json` on the frozen candidate.
- [ ] Regenerate/recheck `ARCHITECTURE.docx` only after architecture wording and final candidate are frozen.

## Final minimizer / deterministic publication gate

- [ ] Only after provider behavior is frozen, run Provider v3 minimizer contract/preview/published tests across all 96.
- [ ] Run byte stability, deterministic reverse rebuild, content-hash/source-qualified filename synchronization, manifest projections and fixed-point/idempotence.
- [ ] Measure final bundle size and prove managed marker/runtime semantics unchanged.

## Security / final certification

- [ ] Frozen SHA must pass CodeQL `security-extended` across Actions, Python, JS/TS source, providers and provider-bases without weakening rules.
- [ ] Run `npm audit --omit=dev --audit-level=high` (or current repository equivalent) on that same candidate.
- [ ] Validate release hashes/integrity and retain final Labs/security evidence.

## Completion rule

The work is complete only when the three current proven regressions are repaired or precisely fail-closed with evidence; the 15 full32 ZERO rows remain correctly classified rather than force-fixed; all 46 have defensible evidence/blocker status; the Hub-46 manifest is regenerated on the frozen provider SHA; minimizer/reverse-rebuild/fixed-point/security are green; all five native Labs execute that exact candidate; UI/logo evidence is reconciled; `MEMORY.md`/docs are current; obsolete TEMP workflows are removed; and every residual issue is recorded with an exact reason/evidence.