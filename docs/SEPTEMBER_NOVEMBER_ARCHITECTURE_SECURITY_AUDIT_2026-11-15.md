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

## 2026-11-15 — Complete read-only CodeQL inventory follow-up

- Run [43716033052](https://github.com/niakw/NiakVIO/actions/runs/43716033052) on `4d210228b2017afc5cd7f1b18a718d1a5e43f0c1` completed successfully; six reference-classification assertions passed, 377 unique open High alert IDs exported, nine pinned paths and zero unresolved manifest references. Dependabot and secret-scanning remain unavailable/unverified.
- Current classification: 376 unreferenced provider-snapshot alerts, one maintained-source alert (#2531), zero release-referenced/pinned-path-match/lifecycle-archive alerts. The 376 alerts cover 115 distinct snapshot paths; comparison with the exact-SHA providers directory found 355 alerts on 106 absent paths and 21 alerts on nine present paths. An absent path on this tree does not establish historical release inaccessibility.
- Rule totals: double escaping 204; insecure randomness 148; missing regexp anchor 21; bad tag filtering 3; incomplete URL substring sanitization 1. #2531's current test uses exact URL-origin equality; the earlier category-retirement job still fails on bounded pagination. Do not dismiss findings or delete scanner analyses on the basis of this inventory.
- Prior exact-SHA Final Gate 43715324619 reported 377 open, zero current high/critical and zero current-provider high/critical after #2918's test correction. Core Workflow Gate and Verify & Publish remained red. Brain's obsolete fix branch is now absent, independently verified; this assistant did not execute its deletion.
- September 11 CodeQL included separate generated-provider shards. September 30 and November use maintained JS Core and ProviderBase categories. That coverage change predates the end-of-September baseline and is not a demonstrated Codex regression. A green maintained-source scan is not equivalent to full historical snapshot coverage. No new release or playback proof.


## 2026-11-15 — Historical snapshot security triage: physical presence and revocation

- Exact tree `5ac5be29d2a816823133ebae5e8e21ce2a72a91a`: rechecked all 377 distinct alert rows from inventory 43716033052 against providers/ and provider-security-revocations.json. The 376 unreferenced snapshot alerts split into 355 alerts on 106 absent paths and 21 alerts on nine present paths. All nine present paths are absent from the 18-entry revocation ledger and from SHA256SUMS.json (55 listed files). Absence from the current checksum index is not proof that historical URLs are unreachable.
- Read-only inventory now separates present/absent and revoked/unrevoked snapshot findings, with four synthetic state assertions and a reconciliation assertion. No alert dismissal, analysis deletion, provider modification, revocation or historical file removal is performed. Fresh workflow verification pending.
- Existing scanner/category retirement failure is separate from source remediation; retained files must be evaluated by the owner against historical compatibility and security obligations before removal. Current-source CodeQL 43716104204 completed successfully on the pre-change SHA. No client-visible release or playback change claimed.


## 2026-11-15 — Security revocation of nine retained historical bundles

- Pre-change authority: `6dc063d210dd7c01405de52afd3b1e493e6ee879`. Exact-SHA CodeQL inventory 43716697923 succeeded (377 open High findings; 21 findings on nine present unreferenced snapshots, 355 findings on absent snapshots, one on a previously corrected test). Security Final Gate 43716968670 succeeded. All nine paths were marked `referenced: false` in the retention ledger; the inventory found zero release-referenced or pinned-path matches. Six current manifests, provider-lkg.json and SHA256SUMS.json contained none of these filenames.
- Apply the existing security-revocation-overrides-generation-retention policy: conservatively revoke nine exact historical bundle paths associated with scanner findings, remove those paths from the current tree and retention ledger atomically, and record all 21 alert IDs. Do not dismiss findings or delete analysis records. No current manifest or executable provider is changed. Older caches pointing to the retired main-branch URLs may need refreshing; old immutable Git commit URLs are not revoked by this operation. This is not proof of exploitation, actual code repair or server-side alert closure.
- Fresh exact-SHA CI and alert state remain to be verified. No provider activation, playback or Brain repair is asserted.

| Revoked historical path | CodeQL IDs |
| --- | --- |
| `providers/anikototv--nuvio--13e07dfed89f7cdb.js` | #2844, #2840 |
| `providers/castle--nuvio--54edf2b1d0fa1785.js` | #2889, #2887 |
| `providers/french-manga--nuvio--26f0858b4d902c78.js` | #2904, #2902 |
| `providers/mugiwarastream--nuvio--155b18313644c23f.js` | #2695, #2692 |
| `providers/neko-sama--nuvio--c1affe06450da279.js` | #2742, #2702, #2699 |
| `providers/papadustream--nuvio--184868ea21a93673.js` | #2710, #2707, #2705 |
| `providers/purstream--nuvio--f05b40cb6ff33e38.js` | #2724, #2722 |
| `providers/sekai--nuvio--d207db1f3823c2cc.js` | #2579, #2574 |
| `providers/streamzo--nuvio--17fc1884018ef64b.js` | #2589, #2586, #2583 |
