## 2026-09-09 — Main-only recovery, V21 runtime/player checkpoint

Repository authority / topology:
- Active work authority is **main only**.
- `brain-learning/proposals` is the sole retained secondary branch and is immutable; never mutate/delete it during cleanup.
- All workbench and Dependabot branches have been removed after useful history/content was consolidated. Current repository branch set is exactly `main` + `brain-learning/proposals`.
- Do not recreate persistent repair branches unless the user explicitly changes this policy.

Release/versioning:
- A real regression was detected after consolidation: historical published release reached **5.21.39**, while current main bytes regressed to **5.21.37**.
- `scripts/sync_release_versions.py` now has a history-backed anti-downgrade floor: explicit or automatic finalization cannot go below the highest release version found on main first-parent history.
- `tests/release_version_sync_test.py` reproduces the exact 5.21.39 -> 5.21.37 failure and requires the next changed generation to resolve to **5.21.40**.
- Final release candidate must synchronize package.json, package-lock.json, all four manifests, sources.json, provider_catalog.json, visible manifest names (`NiakVIO vX.Y.Z ...`), release hashes and integrity artifacts. Current main manifest bytes may still show 5.21.37 until finalization; do not expose that as a finished candidate.

Workflow/security cleanup:
- `.github/workflows/provider-repair-fast-targeted.yml` and the full parallel sweep now run from main.
- Legacy V14 workflow is manual diagnostic only; deleted workbench branch triggers were removed.
- Full sweep is fixed at 96 Provider Objects (24 groups x 4) and uses the current targeted runner rather than stale v1-only logic.
- `workflow_security_policy_test.py` requires every external GitHub Action to use a full 40-character commit SHA.
- A recurring regression reintroduced `actions/checkout@v4`, setup actions by tags and `upload-artifact@v4` in the targeted workflow. Fixed on main: checkout/setup-node/setup-python/upload-artifact are all full-SHA pinned.
- Targeted and full-sweep plan jobs now execute `python3 tests/workflow_security_policy_test.py` **before network proof**, so this cannot waste another long provider run before detection.
- Run 72 (`34291236317`) proved the new targeted security preflight green.

Provider objective / acceptance:
- Target remains **all 96 Provider Objects**, including disabled/off rows for recoverability.
- Never treat a few repaired providers or a green structural test as completion.
- Required chain: targeted live-positive preservation -> neighbor/family non-regression -> 96/96 global proof -> five independent native Labs (TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows) -> UX/player/metadata/latency/session checks -> final version/hashes/integrity -> publication.
- Device behavior must be cross-compared but never inferred blindly across Nuvio repos/runtimes.

Targeted recovery history / current root causes:
- Earlier upstream proof established live positives for AnimeSama (`animesama-co`), AnimeVOSTFR and French-Manga.
- V20.3 fixed `{slug}` projection and urlencoded-form capture; V20.4 fixed static form constants + state updates; V20.5/V20.5.1 added strict id/slug readiness, dependency passes, deeper correlated steps and nested JSON HTTP value extraction.
- Run 70 showed V20.5.1 contracts green but live preservation still 0/3.
- Exact run-70 divergence:
  - AnimeSama materialized plan exists but reconstructed path did not reach useful provider network before falling through metadata/fallback authority.
  - AnimeVOSTFR still incurred broad generic WordPress/fallback traversal instead of a short causal chain, contributing to latency and wrong identity order.
  - French-Manga reached search -> episode API -> player embed; remaining failure is shared player extraction. One observed embed family exposes a fake `/troll/master.m3u8` and encodes the real HLS through base64 + reverse + hostname-derived XOR.

V21 current work on main:
- `scripts/upgrade_provider_shared_player_trace_v21.py` adds a provider-agnostic shared player decoder for the **content shape** above, rejecting the decoy HLS. No provider ids/hosts/titles are hard-coded into executable runtime logic.
- V21 also extends provider-value runtime evidence from one last-state row to a sanitized bounded history of max 48 lifecycle rows (`plan_selected`, identity, step/deferred/fetch/response, etc.). No response body, credentials, cookies or request headers are stored.
- `scripts/nuvio_tv_probe_tmdb_ci.cjs` now exports `provider_value_trace_history_v21` for CI diagnosis with step indices up to 7.
- `tests/provider_shared_player_trace_v21_test.py` executes the actual generated shared decoder against synthetic neutral encoded HLS content and validates trace/privacy constraints.
- First V21 run 72 did not reach live recovery because the V21 trace privacy validator scoped its scan too broadly and falsely found `authorization` in neighboring security helpers. The validator is now scoped only to `_spv184Trace`; the regex SyntaxWarning was also cleaned.
- Current retry trigger schema 26 targets `animesama-co`, `animevostfr`, `french-manga`, publicationAllowed=false.

Native/client evidence / UX blockers:
- User macOS log: Interstellar displayed 0 streams in that Desktop run while provider/network work occurred; several dead/failing DNS routes were visible. Absence of literal provider name in Desktop logs is not proof the provider was not selected/executed.
- TV Android previously produced Interstellar streams including Purstream/Castle/Cineby after cache clear. Therefore macOS 0-stream must not be generalized into common DATA failure.
- User wants Desktop macOS logged test + raw TV Android test on the **same candidate SHA/version**. Do not ask for that test until the candidate provider generation is stable and versioned.
- Historical stale-loading complaint means old title provider jobs may continue after navigation. This is not yet proven identically across runtimes; cancellation/native HTTP/stale-completion must be tested per client repo/device.
- `Purstream - Inconnue` on *Les Fils de l'homme* is a **stream title/technical metadata** regression, not manifest provider branding. Preserve real quality/language/source/host/size when available; never invent a quality merely to hide `Inconnue`.
- Reduced stream count is also blocking; latency must not be "fixed" by dropping providers/streams.

Next execution order:
1. Finish V21 targeted retry; fix real live failure until all known upstream-positive representative pairs are preserved.
2. Retest AnimeZey, Cineby, MovieBlast and other immediate neighbors/families.
3. Run all 96 with current V21 contracts and no stale skip exemption.
4. Materialize exact candidate and finalize as **5.21.40** with visible version names, hashes and integrity validation.
5. Run Desktop macOS logged + TV Android raw on identical SHA/version, then Mobile Android, Mobile iOS, Desktop Windows independently; compare runtime divergences.
6. Fix remaining player, metadata, cancellation/session and latency defects; rerun 96 + five Labs.
7. Security/docs/minimizer/fixed-point final clean; publish only after the entire chain is green.
