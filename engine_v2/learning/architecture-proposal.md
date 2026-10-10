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

1 repeatedly failing repair profile(s) show that known methods are not solving the provider.

Recommendation:
Propose a genuinely different repair/evidence capability or compose existing capabilities differently; do not widen an arbitrary retry counter.

Targets: scripts/run_brain_learning_sandbox.py, tests/brain_*

## New strategy blueprints

### route_transition_graph_v6 — route-to-terminal|html_scraper

Providers: 4khdhub, moviebox

Trigger: catalogue/detail route is live and identity-qualified but no terminal/player media is reached

Method: derive and implement a genuinely new executable Repair strategy route_transition_graph_v6 from negative evidence for exhausted route_transition_graph_v1; preserve the causal intent of the prior method without reusing its implementation, register the new profile in Repair planning/runtime, and require targeted playback/identity proof

Acceptance: playback-verified media; content identity not contradicted; no green-lane regression

### route_transition_graph_v6 — route-to-terminal|mixed_embed_resolver

Providers: anime-ultime, animesultra, yflix

Trigger: catalogue/detail route is live and identity-qualified but no terminal/player media is reached

Method: derive and implement a genuinely new executable Repair strategy route_transition_graph_v6 from negative evidence for exhausted route_transition_graph_v1; preserve the causal intent of the prior method without reusing its implementation, register the new profile in Repair planning/runtime, and require targeted playback/identity proof

Acceptance: playback-verified media; content identity not contradicted; no green-lane regression

### route_transition_graph_v2 — route-to-terminal|api_stream_resolver

Providers: animevost-fr

Trigger: catalogue/detail route is live and identity-qualified but no terminal/player media is reached

Method: replay already installed executable Repair strategy route_transition_graph_v2 against current-byte evidence before another FORCE evolution; preserve playback/identity/non-regression gates

Acceptance: playback-verified media; content identity not contradicted; no green-lane regression

### route_transition_graph_v5 — route-to-terminal|iframe_player

Providers: vidfast

Trigger: catalogue/detail route is live and identity-qualified but no terminal/player media is reached

Method: replay already installed executable Repair strategy route_transition_graph_v5 against current-byte evidence before another FORCE evolution; preserve playback/identity/non-regression gates

Acceptance: playback-verified media; content identity not contradicted; no green-lane regression

### terminal_transition_graph_v4 — terminal-extraction|direct_media

Providers: allanime

Trigger: retained chain hit reaches player/resolver territory but media extraction/validation is incomplete

Method: derive and implement a genuinely new executable Repair strategy terminal_transition_graph_v4 from negative evidence for exhausted terminal_transition_graph_v1; preserve the causal intent of the prior method without reusing its implementation, register the new profile in Repair planning/runtime, and require targeted playback/identity proof

Acceptance: playback-verified media; terminal identity preserved; no green-lane regression

### terminal_transition_graph_v2 — terminal-extraction|html_scraper

Providers: mallumv

Trigger: retained chain hit reaches player/resolver territory but media extraction/validation is incomplete

Method: replay already installed executable Repair strategy terminal_transition_graph_v2 against current-byte evidence before another FORCE evolution; preserve playback/identity/non-regression gates

Acceptance: playback-verified media; terminal identity preserved; no green-lane regression
