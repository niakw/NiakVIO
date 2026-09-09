# NiakVIO checkpoint — 2026-09-09 — runtime identity contract materialized + V3 harness correction

## Runtime compatibility is now durable and executable
- Runtime media-identity materialization workflow run **34344595051** completed **success**.
- Bot commit **2804a57480cc27d2754e55638a4fd26571ef7f7f** (`arch(runtime): materialize TMDB IMDb identity contract`) physically generated and committed the canonical runtime contract files.
- `automation/platform-runtime-contracts.json` now has audit date **2026-09-09**, capability `media_identity_hydration`, Desktop/Mobile marked with the current host-side identity gap, and Android TV marked as an equivalent `bridge` capability.
- `automation/nuvio-client-compatibility-matrix.json` now locks: positional `getStreams(tmdbId, mediaType, season, episode)` is transport rather than complete identity; canonical IMDb context path `__nuvioMediaContext.tmdbMetadata.external_ids.imdb_id`; canonical metadata cache `__nuvioTmdbMetadataCacheV1`; no end-user TMDB credential requirement; no TMDB secret projection requirement.
- Generated `automation/PLATFORM-RUNTIME-CONTRACTS.md` visibly contains the new `Hydratation identité TMDB ↔ IMDb` row and a dedicated canonical identity section, including the required host-bridge timing **after provider/Core initialization and before getStreams**.
- The one-shot materialization workflow was removed after proof in commit **e2e564277dd04e1779d4b0d638fc8c095ad97e70**. Keep the migration, renderer and executable gate; remove only temporary CI orchestration.

## Memory writer proof
- Branch-aware Memory run **34344670882** completed **success**.
- Workbench `MEMORY.md` was physically verified to contain the prior Desktop/Core/media-identity checkpoint; observed blob SHA **09801cc27a9b19a13fb79d86c629fec0e7555c98**.
- `automation/memory-checkpoint-pending-v2.md` was physically verified reset to `<!-- NIAKVIO_MEMORY_PENDING_EMPTY -->`. This proves workbench checkpoints now persist rather than remaining stranded outside MEMORY.

## V3 run 34344396120 is harness-invalid, not runtime evidence
- V3 A/B run **34344396120**, dual job **102442498820**, reached host IMDb resolution (`tt0816692`), protected-byte immutability and the V3 transform contract (`canonical_tmdb_cache=true post_core_init=true`).
- In the real suite, both human-UX checkout audits remained green and the V3 transform was applied to official NuvioDesktop `PluginRuntime.kt`.
- Execution then stopped immediately after `FIELD_NATIVE_DESKTOP_DUAL_ID_CONTEXT added=true version=3 ...`; no corpus log was produced, so PersianStremio itself was never executed in this run.
- Exact cause: the one-shot workflow still executed `grep -q 'NIAKVIO_LAB_DUAL_ID_CONTEXT_V2'` against the modified NuvioDesktop `PluginRuntime.kt`. The obsolete V2 marker existed only as a Python constant in the NiakVIO transform script and was never inserted into `PluginRuntime.kt`, so that grep necessarily returned 1.
- Therefore **34344396120 must never be interpreted as evidence that the V3 post-Core metadata-cache bridge failed**.
- Workflow commit **a7f2ad2cf917f8f91ac6320c28082ebcbb908d77** updates the harness to assert `NIAKVIO_LAB_DUAL_ID_CONTEXT_V3`, reports `canonical_tmdb_cache=true post_core_init=true`, and updates verdict wording to the canonical post-Core cache contract.
- Cleanup commit **cf1dc9c885935e4cffb0c95a82bb78ee20d563c8** removes the obsolete V2 compatibility marker entirely from the V3 transform.
- Final corrected A/B run **34344938190** is the first run on the clean V3 harness/transform pair. Success criteria remain: provider bytes unchanged, actual `/stream/movie/tt...json` route observed, and PersianStremio `FIELD_NATIVE_RESULT count>0`. Do not force the conclusion before this evidence exists.

## Continuation authority
1. Collect final V3 run **34344938190** and inspect the dual job log, actual route and count.
2. If V3 proves positive, persist the exact route/count/run/job and promote the mechanism from Lab evidence to the smallest backward-compatible Desktop/Mobile runtime contract, keeping the public four-argument provider ABI intact.
3. If V3 reaches IMDb but remains zero, inspect the backend response; if it fails before provider execution, fix the harness/runtime bridge and retry. Never collapse these cases into provider failure.
4. Remove `.github/workflows/desktop-dual-id-ab.yml` after decisive evidence is persisted; it is a one-shot diagnostic workflow.
5. Resume all-96 lane-scoped Repair and then the five mandatory Native Labs. Protected green lanes remain byte-immutable unless live A/B proves a non-regressing replacement.
