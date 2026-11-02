#!/usr/bin/env python3
"""Keep paid targeted Learning work alive when a duplicate dispatch arrives."""

from pathlib import Path

workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
concurrency = workflow.split("\nconcurrency:\n", 1)[1].split("\n\njobs:\n", 1)[0]

# Exact provider cohort remains the isolation key: unrelated cohorts can
# proceed independently, and explicit architecture FORCE has its own lane.
assert "niakvio-brain-learning-force-{0}" in concurrency
assert "niakvio-brain-learning-target-{0}" in concurrency
assert "inputs.target_providers || inputs.target_provider" in concurrency

# A second targeted workflow_dispatch must queue, never cancel the already
# running sandbox. Push-triggered Learning can still supersede stale push work.
assert "cancel-in-progress: ${{ github.event_name == 'push' }}" in concurrency
assert "cancel-in-progress: ${{ github.event_name == 'push' ||" not in concurrency
assert "cancel-in-progress: true" not in concurrency

print("brain_learning_concurrency_workflow_test: ok")
