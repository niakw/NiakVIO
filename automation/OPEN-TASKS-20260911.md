# NiakVIO — open-task recovery checkpoint — 2026-09-11

This checkpoint reconciles the current repository with the older GPT discussions, `MEMORY.md`, automation docs and current GitHub Actions evidence. Current repository state and exact run artifacts override stale chat summaries.

## Current scope / hard constraints

- Canonical catalogue remains **96 Provider Objects** for census/recoverability.
- **Exactly the 46 providers listed by `automation/evidence/hub-lab-matrix-46.json -> rows[].manifestId` are enabled.**
- The other **50 providers remain disabled**. Repair/Learn must not widen this activation set.
- Hub presence is discovery knowledge, not an execution backend. Registry-only entries in the 46 remain valid targets.
- Telegram (`t.me`, `telegram.me`, `telegram.dog`) is discovery-only: Domain Refresh may read it to recover a provider domain; ProviderBase must never execute provider media/API/search routes against Telegram.
- Repair is diagnostic/Learn authority, not publication authority. Do not manually relaunch broad Repair solely to manufacture activation. Publication still goes through controlled Core reconstruction/materialization.
- Do **not** publish a new public generation merely because structural/CI checks are green. The 46-target functional study remains the acceptance scope.

## Completed in the current workbench

- [x] Exhaustive **46/46 hub matrix** written to `automation/HUB-LAB-MATRIX-46.md` and `automation/evidence/hub-lab-matrix-46.json`.
- [x] 46/46 registry rows mapped to manifest providers; 36 have matching `hub == official_hub`, 10 are registry-only, 0 orphan/conflict.
- [x] Raw numeric TMDB route identity preserved when host metadata enrichment is unavailable; direct typed resolvers fail closed instead of emitting an empty `tmdb=` request.
- [x] Allwish false-positive root cause isolated: discovery hub `t.me` leaked into execution bases and replayed provider routes against Telegram.
- [x] Hub/runtime-origin separation implemented; Telegram additionally blocked from executable Provider DATA and runtime fetches while remaining available to Domain Refresh.
- [x] Exact activation policy validated by Actions run **34619962640**: root manifest **46 enabled / 50 disabled**; projections and overrides aligned; Repair finalizer preserves the same exact target set.
- [x] Non-regression contract and native codegen stale assertions repaired and validated together by Actions run **34620583849**.
- [x] International discovery infrastructure already exists: `.github/workflows/international-provider-discovery.yml` plus `research/international-provider-candidates.{json,csv,xlsx}`. This is not an unimplemented task; only a future manual refresh may be needed.
- [x] 96-provider catalogue/materialization architecture remains intact; disabled rows are not deleted to fake green metrics.

## Blocking current 46-provider study

- [ ] Let the ordinary PR checks validate the current human-authored checkpoint SHA; fix only real regressions, not stale assertions.
- [ ] **Do not merge/publish as a functional-success claim yet.** Use the workbench as the evidence candidate until the 46-target study is sufficiently complete.
- [ ] Re-evaluate the 46 providers with the corrected TMDB + hub/runtime contract. Reuse prior exact native artifacts when still valid; rerun a platform only when the changed runtime invalidates that evidence.
- [ ] Produce a nominative list of providers whose site/runtime mechanism remains genuinely **opaque or not safely analyzable**, with the reason for each. `0 streams` alone is not “opaque”.
- [ ] For each of the 46, classify first proven blocker: domain/hub resolution, metadata identity, search/detail route, API/player extraction, anti-bot/network, stream transport, content identity, native player, or unknown/opaque.
- [ ] Keep Allwish fail-closed until work identity is proven; two URLs or an HLS-looking payload are insufficient.
- [ ] Recheck PlayIMDb/VidEasy/Papadustream cross-runtime after the raw-TMDB fix; previous TV positives with Desktop/iOS zeros are evidence of runtime divergence, not provider death.
- [ ] Recheck Frenchstream transport: previous extraction existed but HLS transport returned 403.

## Native Labs still requiring final same-candidate proof

Exactly five first-class proofs remain the final device acceptance set:

1. TV Android — NuvioTV.
2. Mobile Android — NuvioMobile.
3. Mobile iOS — NuvioMobile.
4. Desktop macOS — NuvioDesktop.
5. Desktop Windows — NuvioDesktop.

Open points:
- [ ] Android Mobile must be rerun when needed because the previous 46-matrix evidence was invalid (`client UI launch failed`, brains incomplete).
- [ ] Desktop macOS/Windows evidence predates the raw-TMDB preservation fix and must not be treated as final proof for affected direct-TMDB providers.
- [ ] Final Labs must reference one exact NiakVIO candidate SHA and record exact Nuvio client refs.
- [ ] Native Labs remain observational: do not patch official Nuvio client behavior merely to turn a Lab green.

## Domain Refresh debt — still separate from the runtime hub fix

The Telegram/hub execution leak is fixed, but the complete Domain Refresh transaction described in `MEMORY.md` remains a separate backlog unless newer evidence proves otherwise:

- [ ] Make structured source authority explicit for domain changes.
- [ ] Replace old official-site-only mutation assumptions in scope validator/tests.
- [ ] Rebuild the **full Provider CONFIG** on domain refresh instead of updating only `officialSite`.
- [ ] Preserve current source-qualified/content-addressed filename rules.
- [ ] Add generic old-host -> new-host reconciliation for logo/icon/favicon with synthetic A->B proof.
- [ ] Prove domain-only refresh leaves ProviderBase/Core bytes unchanged.
- [ ] Update Domain Refresh documentation/docstrings to distinguish discovery hubs from execution origins.

## Documentation / durable-memory debt

`MEMORY.md` still starts from a 2026-09-07 checkpoint and contains publication/branch assumptions that are now stale. After the current functional scope stabilizes:

- [ ] Update `MEMORY.md` with the 46-target activation authority, raw-TMDB fix, Telegram discovery-only rule, exact run IDs and final native evidence.
- [ ] Reconcile `CHANGELOG.md` with actual release history.
- [ ] Recheck/update `VALIDATION.json` release metadata.
- [ ] Recheck README EN/FR, `ARCHITECTURE.md`, `VALIDATION.md` for old official-site-only / branch-publication wording.
- [ ] Regenerate/recheck `ARCHITECTURE.docx` only after architecture wording is final.
- [ ] Recheck `.github/triggers/nuvio-client-lab.json` for stale release/frozen route counters.
- [ ] Recheck `automation/provider-v3-architecture.json` and ownership tests for obsolete branch-based publication assumptions versus CAS/atomic-main publication.

## Security closure

- [ ] Final publication candidate must pass repository `SEC - CodeQL` / extended security checks without weakening rules.
- [ ] Run/verify `npm audit --omit=dev --audit-level=high` on the final publication SHA.
- [ ] Do not claim historical code-scanning alerts individually closed unless exact evidence is available.

## Older-chat items reviewed

- **International provider discovery / Excel / manual rerun job:** infrastructure and artifacts exist; not forgotten. Preserve country balance and substantial UHD/4K representation on future refreshes.
- **Weekly upstream/provider comparator:** current CI includes the upstream provider watch contract; verify actual scheduled execution separately from its unit test before declaring the operational watch closed.
- **Provider logos / visible branding:** badge/logo asset contracts exist, but the older request was specifically visible provider-logo propagation in official Nuvio UI. Treat that as **verification-needed**, not automatically solved by asset tests; do not modify official Nuvio repos just to satisfy it.
- **Brain multi-day learning audit:** tests for Brain continuity exist, but a real several-day differential audit (learned providers, repairs, regressions, preserved state) still needs an evidence review before marking the old request complete.
- **Kehflix:** historically delegated to Learning after manual runtime-empty results. Do not restart a broad manual Repair just for Kehflix; include it only if it belongs to the current 46 target set/evidence path.
- **Reader/player bugs:** keep them in the five-Lab evidence classification. A player/transport failure is not a provider extraction failure.

## Completion rule

The 46-target task is not complete merely because manifests show 46 enabled. It is complete only when every target has a defensible evidence classification, systemic/runtime fixes have been retested where applicable, opaque sites are listed explicitly, and the final candidate has the required native/security/publication proof without silently widening activation beyond the 46.
