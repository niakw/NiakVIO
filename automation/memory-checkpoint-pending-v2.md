## 2026-09-07 — Provider Recognition Repair V6 first execution red before network census

- Canonical workflow `LEARN/FORCE - Provider Recognition Repair V6`, run `34132887659`, job `101776987578`, branch `workbench/route-recognition-v6`, head `ebcbdcdf240404e356cb27c56300fbf7fbce0210`.
- Architecture/contract step passed: the same `scripts/run_provider_repair_pipeline_v6.py` is the executable implementation for `learn`, `force`, and `repair` modes.
- Repair scope correctly resolved to **87 unresolved providers** with **9 already-green providers excluded**: `allwish`, `anime-sama`, `castle`, `hindmoviez`, `kehflix`, `neko-sama`, `streamzo`, `videasy`, `wookafr`. The explicit post-step proving no skip-set overlap passed.
- No provider network census was executed in this run. Failure occurred during deterministic migration before `recover_provider_routes_from_upstreams.py` was reached.
- Exact blocker: `scripts/upgrade_provider_repair_v6.py::patch_base()` expected a regex-delimited `_crawlEligible -> _crawlUrlScore` source anchor and found 0 (`AssertionError: crawl helper insertion anchors=0`). This is a migration-anchor drift in the current ProviderBase source, not provider/network evidence and not a V29 regression.
- The earlier V2 worker migration itself passed (`PROVIDER_WORKER_ROUTE_PROOF_V2_OK changed=true`), and existing v9 runtime/request-spec/route-authority/source-plan migrations passed before the V10 insertion failure.
- Required next fix: insert the bounded external-root crawl helper using stable semantic anchors from the current ProviderBase source rather than a fragile whole-function regex; preserve the intended rule that a bare unrelated external origin root is not crawled, while direct media and meaningful player paths remain eligible.
