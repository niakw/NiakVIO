# NiakVIO Brain architecture evolution

Review-only self-evolution proposal generated from sanitized Learning evidence.

- Proposals: 2
- Policy changed: false
- Human merge required: true

## repair_strategy_exhaustion_cohort

Priority: critical

9 provider(s) exhausted every bounded Core Repair experiment variant and were explicitly deferred for a new strategy.

Recommendation:
Synthesize one or more new bounded repair/evidence strategies from the common failure cohorts and independent Lab observations. Do not recycle the exhausted bounded g2..g5 family or increase retry counts. Each new strategy must have an explicit causal trigger, negative-memory signature, playback/identity acceptance proof and regression test before it may re-enter Core Repair.

Targets: scripts/brain_repair_runtime.py, scripts/run_brain_learning_queue.py, scripts/run_brain_learning_sandbox.py, tests/brain_*

## method_exhaustion

Priority: high

142 repeated failed method/signature observations indicate the current toolbox may be too narrow.

Recommendation:
Propose a different method or capability type instead of repeating a known failed method.

Targets: scripts/run_brain_learning_sandbox.py, tests/brain_*

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
