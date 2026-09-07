## 2026-09-07 — Proof-v5 request-spec validator fixed to current runtime selection

- Run 34123692126 exposed an obsolete validator expectation in `scripts/upgrade_route_recovery_request_specs_v1.py`: it still required direct `patch["learned_routes"] = execution_routes` assignment.
- Current route recovery intentionally uses `select_runtime_routes(existing_routes, candidate_routes, execution_routes)` so a weak new census cannot demote a richer already-proven runtime plan. Directly restoring the old assignment would have weakened route authority/dataflow safety.
- Durable fix commit: **`44b245ae333c4092cc2901468a6fd4c618e21dee`** (`fix(routes): validate current proof-v5 runtime selection`).
- Repair workflow `TEMP - Route Request Spec Validator V2`, run **34124033946**, completed success. It proved the request-spec migrator, route-authority v5 migrator, Python compilation, provider route-proof authority, manifest policy and empty-route bootstrap tests; the migrator also passed a second execution in the same run.
- The validator now requires semantic current wiring: `executionRoutes`, `generic_execution_route`, reusable request specs, conservative `select_runtime_routes`, `patch/model routes = runtime_routes`, `genericExecutionRouteCount`, and `runtimePlanPreserved`; it also explicitly rejects reintroduction of the obsolete direct execution-route overwrite.
- This correction preserves the core rule: only live-proven executable routes may enter runtime DATA, while static/candidate routes stay non-executable unless separately proven.
