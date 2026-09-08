<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-08-three-plan-advisory-frenchstream-fanout -->

## Runtime route-plan rule correction — 2026-09-08

The earlier shorthand “normally <=3 routes” must **never** be treated as a universal hard cap across all 96 providers.

Canonical interpretation:
- **3 is the normal target for independent top-level entry plans**, not a protocol invariant.
- Common shapes remain: one shared plan; movie/tv; or movie/tv/anime.
- A provider may legitimately need more than three distinct proven top-level plans. Do not disable, truncate, or reject it merely to satisfy a number.
- Most importantly, downstream hops inside one logical resolver path do **not** count as independent entry plans. Search/detail/episode/player/source fan-out is one protocol graph.
- Evidence-rich `routeData` remains complete and must not be flattened into “N routes = N independent runtime attempts”.
- Runtime optimization may merge equivalent plans or rank preferred authorities for latency, but it must preserve distinct evidence-backed fallbacks and fan-out.
- Execution-authority ordering is advisory/non-destructive: provider-value/API/external-id/search/flat-route owners may be sequential or complementary within the same semantic lane.

Canonical FrenchStream-style example:
`search(title) -> verify exact catalogue result -> detail -> multiple player/source branches`, potentially 4 players with separate VF/VOSTFR paths. This is **one logical search/detail resolver graph with downstream fan-out**, not 8 independent top-level routes to arbitrarily truncate.

Implementation checkpoint on `workbench/route-recognition-v14-search-plan`:
- `scripts/runtime_route_plan_cap_v1.py` changed from hard <=3 enforcement to a conservative normal-target policy. It compacts only simple interchangeable entry alternatives; multi-hop/fan-out/mixed or insufficiently modelled graphs are preserved and audited.
- `scripts/runtime_structured_plan_cap_v1.py` now merges protocol-equivalent structured plans but preserves distinct evidence-backed plans even when >3 remain.
- `scripts/runtime_execution_authority_cap_v1.py` now ranks preferred authorities only and no longer deletes lower-priority proven paths in the same semantic lane.
- `scripts/apply_provider_route_recovery_report.py` no longer fails merely because a valid provider has >3 routes/plans; correctness/proof/catalogue failures remain strict.
- `tests/runtime_route_plan_cap_v1_test.py` includes a FrenchStream-like search -> detail -> 4 players -> 4 sources fan-out regression and verifies non-destructive authority ranking.

Do not reintroduce a global hard count limit without provider-graph evidence proving it is safe for every affected provider.
