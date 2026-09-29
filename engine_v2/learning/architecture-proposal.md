# NiakVIO Brain architecture evolution

Review-only self-evolution proposal generated from sanitized Learning evidence.

- Proposals: 1
- Policy changed: false
- Human merge required: true

## repair_strategy_exhaustion_cohort

Priority: critical

1 provider(s) exhausted every bounded Core Repair experiment variant and were explicitly deferred for a new strategy.

Recommendation:
Synthesize one or more new bounded repair/evidence strategies from the common failure cohorts and independent Lab observations. Do not recycle the exhausted bounded g2..g5 family or increase retry counts. Each new strategy must have an explicit causal trigger, negative-memory signature, playback/identity acceptance proof and regression test before it may re-enter Core Repair.

Targets: scripts/brain_repair_runtime.py, scripts/run_brain_learning_queue.py, scripts/run_brain_learning_sandbox.py, tests/brain_*
