## 2026-09-12 — V33 provider isolation / fail-fast design checkpoint

- Added `scripts/upgrade_provider_execution_failfast_v33.py` as the durable common Core migration for provider execution isolation.
- V33 final Core revision target: `tmdb-data-contract-launch-gate-v33-25s-isolated-failfast`.
- Canonical per-provider budget is **25,000 ms** for TV and non-TV. The outer Native Lab timeout remains a larger harness timeout and is not provider runtime authority.
- V33 adds a default **7,000 ms per-fetch slice** (bounded/configurable) so one abort-ignoring/stalled fetch cannot consume the entire 25 s provider budget when timers exist.
- V33 keeps legitimate fallback: the **first 403/429/network failure never kills a provider**. Repeated strong HTTP/network failures are counted per invocation; default fail-fast threshold is 3. Once reached, later fallback fetches fail immediately instead of continuing network work.
- Hard-status tracking is generic and provider-independent. 404 is deliberately not a hard fail-fast status because search/catalogue providers legitimately probe missing routes/titles; successful/host-alive responses reset the consecutive hard-failure state.
- Per-fetch timeout uses its own AbortController where available; it does **not** abort the whole provider request. The 25 s request-level controller remains the global deadline owner. Native invocation itself is raced against that request controller so non-fetch hangs cannot silently exceed the provider deadline when timer primitives exist.
- QuickJS/no-global-timer compatibility is preserved: all timer usage checks `typeof setTimeout/clearTimeout` first. `tests/provider_no_timer_runtime_test.py` proves stale-request supersession still works with both globals undefined.
- Added `tests/provider_execution_failfast_v33_test.py`: proves first 403 -> second route success is preserved, repeated 403s stop later network calls, abort-ignoring stalled fetches fail fast, and a dead provider execution does not postpone an independently executing healthy provider.
- Updated the abort-ignorant cancellation and manual-TV regression contracts to V33. `scripts/prepatch_manual_tv_regressions_20260912.py` is now idempotent so successful branch commits can be rerun safely.
- These changes remain only on `fix/labs-5.21.44-20260912`; `main` is untouched.
- Next: wire V33 + identity migrations + ProviderBase-store regeneration into the temporary branch verifier, run targeted tests, rebuild ProviderBase 96/96, rebuild all 96 bundles, then inspect and repair any real regression exposed by CI.
