## 2026-09-12 — TEMP retry 8 proves focused V33 stack except immediate-invocation ordering

- TEMP run **34719139951**, job **103621639170**, checked out branch head `c3ca0eb28b9023e90cf18227875d281aaadb929e` and passed durable V33/V21.10/V22.1 application.
- Focused tests proven green in this run before the red: movie catalogue identity V21.10; episodic identity V22.1; QuickJS/no-global-timer cancellation; **provider execution fail-fast V33**; and the complete synthetic manual-TV regression contract (verified HLS quality authority, 403 fail-closed, detailed language/uniform title, A→B→C stale suppression).
- Failure occurred next in `provider_latest_request_cancellation_test.py`: `Error: first request never started`.
- Root cause: V33 helper `invokeNativeWithBudget()` used `Promise.resolve().then(() => native.apply(...))`, adding one extra microtask before native provider execution. A second request could supersede the first before its first fetch started. This remained fail-closed (no stale result), but unnecessarily changed historical invocation ordering and broke the cancellation contract.
- Commit **8100f7937d9809e9db130d2d603c97791d56c888** fixes V33 generically: `native.apply(self,args)` is invoked immediately, then its result is normalized with `Promise.resolve(pending)` and raced against the request abort/deadline. This preserves old immediate-start semantics while retaining the 25 s deadline and V33 fail-fast.
- Retry 8 did not reach ProviderBase 96/96 because focused tests stopped at this ordering regression. `main` remains untouched.
- Next: authoritative retry must reprove the entire focused suite with immediate invocation, then proceed to ProviderBase 96/96 and all-96 bundle rebuild.
