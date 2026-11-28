#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_REPOSITORY:?}"
: "${ELIGIBLE_CSV:?}"
FORCE_MODE="${FORCE_MODE:-false}"
PUBLISH_PROPOSAL="${PUBLISH_PROPOSAL:-false}"
BATCH_PLAN="${BATCH_PLAN:-automation/provider-repair-batch-plan-latest.json}"
STATUS="${STATUS:-automation/provider-census-status.json}"
MAX_COHORTS="${MAX_COHORTS:-8}"

cohort_filters=()
family_deferred=0
if [ "$FORCE_MODE" = "true" ]; then
  cohort_filters=("$ELIGIBLE_CSV")
else
  family_plan="${RUNNER_TEMP:-/tmp}/fast-learning-family-dispatch.json"
  python scripts/plan_learning_family_dispatch.py \
    --providers "$ELIGIBLE_CSV" \
    --batch-plan "$BATCH_PLAN" \
    --status "$STATUS" \
    --max-cohorts "$MAX_COHORTS" \
    --output "$family_plan"
  readarray -t cohort_filters < <(jq -r '.cohorts[]?.providerFilter // empty' "$family_plan")
  family_deferred="$(jq -r '(.deferredProviders // []) | length' "$family_plan")"
fi

dispatched=0
dispatch_failed=0
for cohort_filter in "${cohort_filters[@]}"; do
  [ -n "$cohort_filter" ] || continue
  args=(
    --repo "$GITHUB_REPOSITORY" --ref main
    -f publish_proposal="$PUBLISH_PROPOSAL"
    -f target_providers="$cohort_filter"
    -f slot_remaining_minutes=90
    -f slot_phase=1
  )
  if [ "$FORCE_MODE" = "true" ]; then
    args+=(-f architecture_force=true)
  fi
  if gh workflow run brain-learning-lab.yml "${args[@]}"; then
    dispatched=$((dispatched + 1))
    echo "FIELD_PROVIDER_FAST_REPAIR_LEARNING_FAMILY cohort=$cohort_filter dispatch=true architecture_force=$FORCE_MODE"
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
