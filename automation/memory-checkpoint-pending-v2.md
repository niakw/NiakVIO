## 2026-09-12 — TEMP retry 6 reached focused tests; no-timer behavior green, assertion drift fixed

- TEMP run **34718984024**, job **103621212371**, passed `Apply durable common fixes`: manual-TV prepatch, V33 fail-fast, V21.10 movie identity and V22.1 episode identity all applied successfully.
- Focused executable results before the red: `MOVIE_CATALOGUE_IDENTITY_V21_10_OK`, `EPISODE_IDENTITY_V22_1_OK`, and **`NO_TIMER_RUNTIME_OK ["https://provider.example/second"]`**. This proves the QuickJS-like runtime with global `setTimeout`/`clearTimeout` undefined correctly superseded a hanging first request and returned the latest request without stale leakage.
- Run 34718984024 then failed only on a stale *source-text assertion* inside `tests/provider_no_timer_runtime_test.py`: it still expected V32 token `typeof setTimeout!=="function"||remaining<=0`, while V33 correctly renamed the per-fetch bound to `slice`.
- Commit **82b81553220572b5b14444c8e052e9d99e27f26f** updates the test to assert the actual V33 no-timer branch (`slice<=0`) and also locks the no-timer `Promise.race([base.apply(this,args),abortPromise])` path. Runtime behavior was not changed by this test fix.
- Memory writer race handling was itself proven by run **34719075767** success; pending reset to the empty sentinel after durable append despite concurrent branch movement.
- No ProviderBase 96/96 rebuild was reached in retry 6. `main` remains untouched.
- Next authoritative verifier must include commit 82b8155... before focused tests, then continue to ProviderBase 96/96.
