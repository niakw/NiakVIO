## 2026-09-12 — TEMP retry 9 focused regression suite fully green; ProviderBase 96/96 rebuild entered

- TEMP run **34719219904**, job **103621866958**, passed `Apply durable common fixes` and the complete `Focused regressions` step.
- This is the first retry in this branch sequence where the entire focused stack is green together after V33 immediate-invocation correction.
- Proven together in the same job: V21.10 movie catalogue semantic identity; V22.1 episodic identity; QuickJS/no-global-`setTimeout`; V33 first-failure fallback + repeated hard-failure fail-fast + stalled-fetch isolation + dead-provider/healthy-provider independence; manual-TV quality/403/language/A→B→C contract; latest-request cancellation; abort-ignoring native-fetch cancellation; HLS quality recovery; sanitizer fail-closed/direct normalization; Core runtime non-regression.
- V33 immediate-native invocation fix (`8100f7937d9809e9db130d2d603c97791d56c888`) restored the historical ordering contract without weakening supersession or the 25 s budget.
- After focused green, retry 9 entered `Rebuild owned ProviderBase store 96/96`. This is the first rebuild attempt after the anime-sama missing-base root cause was addressed by explicitly materializing the owned common ProviderBase store first.
- `main` remains untouched.
