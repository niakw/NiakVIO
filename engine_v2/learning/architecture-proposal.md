# NiakVIO Brain architecture evolution

Review-only self-evolution proposal generated from sanitized Learning evidence.

- Proposals: 3
- Policy changed: false
- Human merge required: true

## repair_strategy_exhaustion_cohort

Priority: critical

10 provider(s) exhausted every bounded Core Repair experiment variant and were explicitly deferred for a new strategy.

Recommendation:
Synthesize one or more new bounded repair/evidence strategies from the common failure cohorts and independent Lab observations. Do not recycle the exhausted bounded g2..g5 family or increase retry counts. Each new strategy must have an explicit causal trigger, negative-memory signature, playback/identity acceptance proof and regression test before it may re-enter Core Repair.

Targets: scripts/brain_repair_runtime.py, scripts/run_brain_learning_queue.py, scripts/run_brain_learning_sandbox.py, tests/brain_*

## method_exhaustion

Priority: high

1 repeatedly failing repair profile(s) show that known methods are not solving the provider.

Recommendation:
Propose a genuinely different repair/evidence capability or compose existing capabilities differently; do not widen an arbitrary retry counter.

Targets: scripts/run_brain_learning_sandbox.py, tests/brain_*

## route_discovery_blind_spot

Priority: high

1 access-failure provider(s) produced no usable route evidence with the current search chain.

Recommendation:
Evolve route discovery with a new evidence source or extraction method before mutating provider code.

Targets: scripts/resolve_provider_hubs.py, scripts/resolve_provider_hub_search_fallback.py, scripts/run_brain_learning_queue.py, tests/brain_*

## New strategy blueprints

### route_transition_graph_v1 — route-to-terminal|mixed_embed_resolver

Providers: yflix

Trigger: catalogue/detail route is live and identity-qualified but no terminal/player media is reached

Method: start from retained route proof; traverse only identity-correlated detail/player/server transitions; learn reusable route shapes without copying provider domains

Acceptance: playback-verified media; content identity not contradicted; no green-lane regression

### terminal_transition_graph_v1 — terminal-extraction|html_scraper

Providers: moviebox

Trigger: retained chain hit reaches player/resolver territory but media extraction/validation is incomplete

Method: replay retained chain hit first; classify terminal host/player family; apply bounded extractor/resolver capability and follow only scored player/media transitions

Acceptance: playback-verified media; terminal identity preserved; no green-lane regression

### route_transition_graph_v1 — route-to-terminal|iframe_player

Providers: vidfast

Trigger: catalogue/detail route is live and identity-qualified but no terminal/player media is reached

Method: start from retained route proof; traverse only identity-correlated detail/player/server transitions; learn reusable route shapes without copying provider domains

Acceptance: playback-verified media; content identity not contradicted; no green-lane regression
