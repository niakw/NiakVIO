# Provider Recognition & Repair V6

## Ownership

Provider route recognition and correction has one executable owner:

- workflow: `.github/workflows/provider-recognition-repair-v6.yml`
- engine: `scripts/run_provider_repair_pipeline_v6.py`
- modes: `learn`, `force`, `repair`

The mode changes scheduling/operator intent only. It does **not** select a different repair implementation.

`LEARN - Brain Repair Lab` remains responsible for broad evidence, cross-day learning, native-reader memory and reviewable proposals. It is not an independent route-reconstruction authority. `CORE - Verify & Publish` remains verify/publish-only and does not repair Provider DATA or Provider JS.

## Portfolio rule

A provider that has already been demonstrated functional/corrected is stored in `automation/provider-repair-skip.json` and is not network re-probed by portfolio repair. Global deterministic tests may still rebuild/check its bytes when shared Core/ProviderBase code changes.

A newly repaired provider is added to the skip set only after its reconstructed Provider produces a positive representative result and the relevant deterministic contracts pass. Subsequent repair iterations operate on the remaining unresolved set.

## Canonical pipeline

For unresolved providers only:

1. Apply deterministic shared migrations.
2. Execute the real upstream/LKG Provider JS (or NiakVIO-native source where no upstream mapping exists).
3. Trace exact sanitized HTTP requests, including method, safe headers and body. `fetch(Request)` bodies are read from a clone so recognition does not consume or mutate the real request.
4. Promote only successful live-observed requests into proof DATA. Static strings remain candidate knowledge, never executable authority by themselves.
5. Generalize fixture/provider response values into reusable placeholders.
6. Build reusable request recipes, including terminal POST search APIs when the live search request itself returned streams.
7. Merge targeted proof rows with the last accepted rows for providers deliberately not re-probed.
8. Apply proof DATA and materialize ProviderBase + DATA + managed Core/Provider Lego deterministically.
9. Run global non-network runtime/identity/presentation/cancellation contracts.
10. Run representative post-reconstruction yield only for the targeted providers.
11. Hard-fail when a representative upstream-positive provider/type becomes reconstructed-zero (`upstream-positive -> reconstructed-positive`).
12. Produce a candidate artifact and diagnostics. The repair engine never publishes to `main` itself.

## Runtime crawl budget

The generic crawler must not spend the provider deadline following a bare unrelated external origin root. Direct media remains eligible and meaningful player/resolver paths remain eligible. This rule addresses the class where a discovered resolver landing page (for example a bare external root) stalls until the global timeout and causes already-discovered provider results to be lost.

## Publication

Repair/Learn/Force output is candidate-only. Publication requires the normal accepted-release path, content-addressed public Provider filenames, release hashes/integrity, live regression comparison, and the five Native Labs where required.
