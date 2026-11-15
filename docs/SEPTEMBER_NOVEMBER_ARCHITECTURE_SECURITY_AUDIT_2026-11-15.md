# September–November 2026 architecture and security comparison

Date: 2026-11-15. This is a read-only historical comparison plus a maintained-test security correction, not a release or playback qualification.

## Reproducible baselines

| Repository | Date | Exact SHA | Manifest |
|---|---|---|---|
| NiakVIO | September 11 | `dba4bdd24604cff515424162008a5e9ce583c0a8` | 5.21.42 |
| NiakVIO | September 30 | `a9eee1bda5b95e1c0bf10e9194e31e9808a48b7c` | 5.21.90 |
| NiakVIO | November 15 | `1da6528063e07a9bdf924453fba3bfd0713a0b9d` | 5.21.146 |
| Brain-LLM | September 30 | `27fa6800ca83f696560bab2b6e5262b25dcf6592` | — |
| Brain-LLM | November 15 | `ffe1444c74529c3641d065711bb5dc434f8dd013` | — |

These dates are comparison points, not a proven boundary of Codex authorship. GitHub compare reports 10,734 commits since September 11 and 5,549 since September 30 in NiakVIO; the compare per-file result is capped at 300. Brain-LLM reports 430 commits and 124 changed files since September 30. Compare tree inventories independently; do not treat the first 300 paths as exhaustive.

## Functional evidence and scope

| Metric | Sep 11 | Sep 30 | Nov 15 |
|---|---:|---:|---:|
| Global manifest total | 96 | 44 | 95 |
| Global manifest enabled | 46 | 42 | 46 |
| France manifest total | 29 | 21 | 67 |
| France manifest enabled | 15 | 21 | 38 |
| Census FULL | unavailable | 27 | 13 |
| Census PARTIAL | unavailable | 2 | 1 |
| Census scope | unavailable | 46 | 110 |
| Top-level workflow directory entries | 49 | 105 | 130 |
| Top-level scripts directory entries | 414 | 586 | 658 |
| Top-level tests directory entries | 339 | 622 | 735 |

September census authority: run 36698522244, SHA 9979719fa511; 30 rows carried, 16 tested (all statuses). November authority: run 43663241740, SHA f0d818586444; 13/13 FULL and 1/1 PARTIAL tested per census header. No current-HEAD or same-corpus playback claim; the scope and proof requirements have changed.

All 46 September census identities still appear in November census. Of the 27 historical FULL identities, 9 retain FULL status, 17 are DISABLED, and 1 is REGRESSION PROVIDER. Both historical PARTIAL identities are now DISABLED. This is a material loss of historical positive availability, not evidence that every individual implementation regressed. Of 42 enabled Global rows in September, 10 remain enabled and 32 are disabled; of 21 enabled France rows, 7 remain enabled and 14 are disabled. Case-folded identity comparison; not a statement of authorization or current functionality.

## Architecture decisions

- Preserve exact media identity, independent playback proof, fail-closed versioning, provenance and security checks. A historical FULL label is not authorization to relax present safety checks.
- Investigate catalogue/manifest/static-knowledge/materialization inconsistencies before considering any production changes: lifecycle run 43711782764 failed on absent static knowledge; Domain Refresh 43707890774 reported 78 versus 42 identities; Learning run 43698686804 failed catalogue preservation during staging. These are infrastructure failures, not proof of provider-level failure.
- In the direct September 30–November directory comparison, scripts added 73 / removed 1 (temporary fixture repair script) / changed 105; tests added 113 / removed 0 / changed 145; workflows added 28 / removed 3 (temporary workflows) / changed 95. Four temp-prefixed workflows remain. No evidence of a wholesale test-suite removal. This inventory does not prove semantic preservation; review common contracts and remove only demonstrably redundant orchestration.
- Brain-LLM planner changed +2415/-191 lines and prompting +926/-102; live evidence module was added. New code volume is not proof of improvement. Historical versus current acceptance criteria and runtime inputs require controlled comparison using authorized, deterministic media fixtures; no general rollback justified by counts alone.
- Latest Repair documented in November census: 9 selected, zero candidates, zero validated (historical run 43580198030). No new repair demonstrated.

## Security

- Exact snapshot `1da6528063e07a9bdf924453fba3bfd0713a0b9d`: CodeQL analysis run 43714070820 succeeded across Actions, Python, JS Core and JS ProviderBase; Final Gate run 43714502370 failed. Its log explicitly reports 378 open alerts, one current high/critical, zero current-provider high/critical, and alert #2918 in `tests/provider_movy_wecollege_runtime_contract_test.py` (py/incomplete-url-substring-sanitization). The current file test correction compares parsed complete URL literals and rejects lookalike origins/userinfo rather than accepting a substring. Six isolated predicate checks passed in a local synthetic test; full repository test and fresh CodeQL scan remain required. No alert was dismissed or scanning rule changed.
- Historical Nov 7 audit classified 376 of 377 high alerts as unreferenced provider snapshots, with one maintained test alert #2531. That is not a verified classification of all 378 current alerts. Direct alert-list API is unsupported by this connector; the current total comes from Final Gate logs, not a complete current per-alert export.
- Category retirement run 43714502313 failed with `Security listing exceeded bounded pages`, also observed in 43675025754. Do not delete analyses or suppress findings merely to reduce the number; preserve historical evidence and resolve active code before retiring genuinely obsolete snapshots.
- External audit 43711225972: 55 unresolved maintained-source findings and stale Sonar/DeepSource/CodeScene snapshots; do not interpret these as CodeQL counts. Keep fail-closed until complete exact-SHA evidence is available.

## Brain branch cleanup

`fix/brain-observed-media-bridge-contract` at 17e3ca55285715cb3d0c32f5a60e9fa8dd9d9ada is 3 ahead / 166 behind main. PR #16 was closed unmerged and explicitly superseded by #17. PR #17 merged at b028d03255b332a45a5db9a0b414ca02f62d5a1a; current main descends from this merge (164 ahead, 0 behind). PR #17 reports 343 tests and privacy audit passed. It is reasonable to delete the obsolete branch if its head has not moved, without merging its alternate implementation. The connector has no branch-delete action; branch deletion not performed. Preserve main and niakvio-guidance.

## Verification status

This comparison does not execute external provider traffic, claim playback or authorize changes to production manifests. Only the maintained-source URL-assertion hardening is included. Revisit exact-SHA CodeQL, full contract test and the branch state before closing the work.
