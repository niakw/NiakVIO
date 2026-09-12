## 2026-09-12 — TEMP manual-TV run 34718923736 failed before tests; validator-only V22.1 defect fixed

- Run **34718923736**, job **103621052981**, failed in `Apply durable common fixes` before focused tests or any ProviderBase/bundle rebuild.
- Successful steps before the failure: manual-TV prepatch applied verified-HLS-quality authority, V33 provider execution fail-fast migration completed (`provider_budget_ms=25000`, `fetch_slice_ms=7000`, `max_hard_failures=3`), and V21.10 movie catalogue identity migration completed.
- Failure was **not runtime behavior**: `upgrade_provider_episode_identity_guard_v22_1.py` applied its changes but its own validator searched for `async function _resolveApiRecipe` *after* the V22.1 marker. In current ProviderBase ordering `_resolveApiRecipe` is earlier than the episode helper region, so `value.index(...)` raised `ValueError: substring not found`.
- Fix commit on branch: `958cd1a77f1574dd6340cdb306e5467db037e3cc`. V22.1 validation now bounds its provider-specific-token audit from the marker to the later `async function _resolveHtml`, which actually contains the integrated episode guard region.
- No generated ProviderBase/provider artifacts from the failed runner were committed. `main` remains untouched.
- Next action: retrigger the same branch workflow; first required milestone is all focused V33/V21.10/V22.1/no-timer/navigation/quality/403/presentation contracts green, then ProviderBase 96/96.
