#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_REPOSITORY:?}"
: "${ELIGIBLE_CSV:?}"
FORCE_MODE="${FORCE_MODE:-false}"
PUBLISH_PROPOSAL="${PUBLISH_PROPOSAL:-false}"
BATCH_PLAN="${BATCH_PLAN:-automation/provider-repair-batch-plan-latest.json}"
STATUS="${STATUS:-automation/provider-census-status.json}"
MAX_COHORTS="${MAX_COHORTS:-8}"
LEARNING_SELECTION="${LEARNING_SELECTION:-}"

cohort_filters=()
family_deferred=0
if [ "$FORCE_MODE" = "true" ]; then
  cohort_filters=("$ELIGIBLE_CSV")
else
  family_plan="${RUNNER_TEMP:-/tmp}/fast-learning-family-dispatch.json"
  learning_memory="${RUNNER_TEMP:-/tmp}/fast-learning-family-memory.json"
  rm -f "$learning_memory"
  if git fetch --quiet origin "+refs/heads/brain-learning/proposals:refs/remotes/origin/brain-learning/proposals" 2>/dev/null \
     && git show "refs/remotes/origin/brain-learning/proposals:engine_v2/learning/latest.json" > "$learning_memory" 2>/dev/null; then
    echo "FIELD_BRAIN_LEARNING_FAMILY_MEMORY available=true source=brain-learning/proposals"
  else
    rm -f "$learning_memory"
    echo "FIELD_BRAIN_LEARNING_FAMILY_MEMORY available=false source=none"
  fi
  planner_args=(
    python scripts/plan_learning_family_dispatch.py
    --providers "$ELIGIBLE_CSV"
    --batch-plan "$BATCH_PLAN"
    --status "$STATUS"
    --max-cohorts "$MAX_COHORTS"
    --output "$family_plan"
  )
  if [ -s "$learning_memory" ]; then
    planner_args+=(--learning-memory "$learning_memory")
  fi
  "${planner_args[@]}"
  readarray -t cohort_filters < <(jq -r '.cohorts[]?.providerFilter // empty' "$family_plan")
  family_deferred="$(jq -r '(.deferredProviders // []) | length' "$family_plan")"
fi

dispatched=0
dispatch_failed=0
for cohort_filter in "${cohort_filters[@]}"; do
  [ -n "$cohort_filter" ] || continue
  dispatch_fingerprint=""
  if [ -n "$LEARNING_SELECTION" ] && [ -s "$LEARNING_SELECTION" ]; then
    dispatch_fingerprint="$(jq -r --arg provider "$cohort_filter" '.eligible[]? | select((.provider // "") == $provider) | .fingerprint // empty' "$LEARNING_SELECTION" | head -n 1)"
    if [ -n "$dispatch_fingerprint" ] && ! [[ "$dispatch_fingerprint" =~ ^[0-9a-f]{64}$ ]]; then
      echo "invalid Learning dispatch fingerprint for $cohort_filter" >&2
      exit 1
    fi
  fi
  if [ -n "$dispatch_fingerprint" ]; then
    queued_titles=""
    running_titles=""
    if ! queued_titles="$(gh run list --repo "$GITHUB_REPOSITORY" --workflow brain-learning-lab.yml --status queued --limit 100 --json displayTitle --jq '.[].displayTitle' 2>/dev/null)"; then
      dispatch_failed=$((dispatch_failed + 1))
      echo "FIELD_PROVIDER_FAST_REPAIR_LEARNING_FAMILY cohort=$cohort_filter dispatch=false reason=inflight-query-unavailable state=queued fingerprint=${dispatch_fingerprint:0:12}"
      continue
    fi
    if ! running_titles="$(gh run list --repo "$GITHUB_REPOSITORY" --workflow brain-learning-lab.yml --status in_progress --limit 100 --json displayTitle --jq '.[].displayTitle' 2>/dev/null)"; then
      dispatch_failed=$((dispatch_failed + 1))
      echo "FIELD_PROVIDER_FAST_REPAIR_LEARNING_FAMILY cohort=$cohort_filter dispatch=false reason=inflight-query-unavailable state=in_progress fingerprint=${dispatch_fingerprint:0:12}"
      continue
    fi
    if printf '%s\n%s\n' "$queued_titles" "$running_titles" | grep -Fq "$dispatch_fingerprint"; then
      echo "FIELD_PROVIDER_FAST_REPAIR_LEARNING_FAMILY cohort=$cohort_filter dispatch=false reason=fingerprint-in-flight fingerprint=${dispatch_fingerprint:0:12}"
      continue
    fi
  fi
  args=(
    --repo "$GITHUB_REPOSITORY" --ref main
    -f publish_proposal="$PUBLISH_PROPOSAL"
    -f target_providers="$cohort_filter"
    -f slot_remaining_minutes=90
    -f slot_phase=1
  )
  if [ -n "$dispatch_fingerprint" ]; then
    args+=(-f dispatch_fingerprint="$dispatch_fingerprint")
  fi
  if [ "$FORCE_MODE" = "true" ]; then
    args+=(-f architecture_force=true)
  fi
  if gh workflow run brain-learning-lab.yml "${args[@]}"; then
    dispatched=$((dispatched + 1))
    echo "FIELD_PROVIDER_FAST_REPAIR_LEARNING_FAMILY cohort=$cohort_filter dispatch=true architecture_force=$FORCE_MODE fingerprint=${dispatch_fingerprint:0:12}"
  else
    dispatch_failed=$((dispatch_failed + 1))
    echo "FIELD_PROVIDER_FAST_REPAIR_LEARNING_FAMILY cohort=$cohort_filter dispatch=false reason=github_api_unavailable persisted=true architecture_force=$FORCE_MODE"
  fi
done

if [ "$dispatched" -gt 0 ]; then
  dispatched_any=true
else
  dispatched_any=false
fi
echo "FIELD_PROVIDER_FAST_REPAIR_LEARNING_PARALLEL eligible=$ELIGIBLE_CSV dispatched_cohorts=$dispatched failed_cohorts=$dispatch_failed family_deferred=$family_deferred learning_dispatch=$dispatched_any architecture_force=$FORCE_MODE publish_proposal=$PUBLISH_PROPOSAL"

# Dispatch failures never erase durable handoff debt. The parent Fast Repair
# remains successful and a later Autopilot/scheduled Learning pass may retry.
exit 0
