#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_REPOSITORY:?}"
: "${GITHUB_SHA:?}"
: "${GITHUB_RUN_ID:?}"
: "${GITHUB_EVENT_NAME:?}"

git fetch --quiet origin main
remote_main="$(git rev-parse origin/main)"
if [ "$remote_main" = "$GITHUB_SHA" ]; then
  echo "FIELD_PROVIDER_FAST_REPAIR_EARLY_SOURCE current=true sha=$GITHUB_SHA"
  exit 0
fi

executable_paths=(
  scripts
  engine_v2
  providers
  provider-bases
  provider-overrides.json
  manifest.json
  vf/manifest.json
  no-anime/manifest.json
  vf-no-anime/manifest.json
  provider-v3-materialization.json
  automation/brain-repair-memory.json
  automation/brain-positive-program-memory.json
  automation/brain-repair-experience.json
  automation/provider-repair-batch-plan-latest.json
  automation/provider-repair-batch-refined-latest.json
  automation/provider-repair-candidate-evidence.json
  provider-v3-quick-yield.json
  .github/workflows/provider-fast-repair.yml
)
if git merge-base --is-ancestor "$GITHUB_SHA" "$remote_main" \
   && git diff --quiet "$GITHUB_SHA" "$remote_main" -- "${executable_paths[@]}"; then
  echo "FIELD_PROVIDER_FAST_REPAIR_EARLY_SOURCE current=false executable_drift=false source=$GITHUB_SHA remote=$remote_main action=continue"
  exit 0
fi

target_provider="${DISPATCH_PROVIDER:-}"
target_providers="${DISPATCH_PROVIDERS:-}"
waves="${DISPATCH_WAVES:-1}"
budget="${DISPATCH_BUDGET:-1200}"
rounds="${DISPATCH_MAX_ROUNDS:-3}"
publish="${DISPATCH_PUBLISH:-true}"
force="${DISPATCH_FORCE:-false}"
prior_fast_run_id="${DISPATCH_PRIOR_FAST_RUN_ID:-}"
source_kind="dispatch-inputs"

source_trigger_blob="$(git rev-parse "$GITHUB_SHA:.github/triggers/provider-fast-repair.json" 2>/dev/null || true)"
remote_trigger_blob="$(git rev-parse "origin/main:.github/triggers/provider-fast-repair.json" 2>/dev/null || true)"
if [ -n "$remote_trigger_blob" ] && { [ "$GITHUB_EVENT_NAME" = "push" ] || [ "$remote_trigger_blob" != "$source_trigger_blob" ]; }; then
  trigger="$RUNNER_TEMP/provider-fast-repair-early-trigger.json"
  git show "origin/main:.github/triggers/provider-fast-repair.json" > "$trigger"
  waves="$(jq -r '(.waves // 1) | tostring' "$trigger")"
  budget="$(jq -r '(.timeBudgetSeconds // 1200) | tostring' "$trigger")"
  rounds="$(jq -r '(.maxRoundsPerBatch // 3) | tostring' "$trigger")"
  publish="$(jq -r 'if .publishValidated == false then "false" else "true" end' "$trigger")"
  target_providers="$(jq -r '[.targetProviders[]? | tostring | ascii_downcase | gsub("_"; "-")] | join(",")' "$trigger")"
  force="$(jq -r 'if .architectureForce == true then "true" else "false" end' "$trigger")"
  prior_fast_run_id="$(jq -r '(.priorFastRunId // "") | tostring' "$trigger")"
  target_provider=""
  source_kind="remote-main-trigger"
fi

args=(gh workflow run provider-fast-repair.yml
  --repo "$GITHUB_REPOSITORY" --ref main
  -f waves="$waves"
  -f time_budget_seconds="$budget"
  -f max_rounds_per_batch="$rounds"
  -f publish_validated="$publish"
  -f architecture_force="$force")
if [[ "$prior_fast_run_id" =~ ^[0-9]{6,20}$ ]]; then
  args+=(-f prior_fast_run_id="$prior_fast_run_id")
fi
if [ -n "$target_providers" ]; then
  args+=(-f target_providers="$target_providers")
elif [ -n "$target_provider" ]; then
  args+=(-f target_provider="$target_provider")
fi
"${args[@]}"
echo "FIELD_PROVIDER_FAST_REPAIR_EARLY_REQUEUE source=$GITHUB_SHA remote=$remote_main config=$source_kind providers=${target_providers:-${target_provider:-none}} waves=$waves budget=$budget rounds=$rounds prior_fast_run_id=${prior_fast_run_id:-none}"

# Requeue first, then self-cancel. This run has obsolete executable semantics.
if gh run cancel "$GITHUB_RUN_ID" --repo "$GITHUB_REPOSITORY"; then
  echo "FIELD_PROVIDER_FAST_REPAIR_EARLY_CANCEL run=$GITHUB_RUN_ID requested=true"
else
  echo "FIELD_PROVIDER_FAST_REPAIR_EARLY_CANCEL run=$GITHUB_RUN_ID requested=false reason=github-api-unavailable" >&2
  exit 1
fi
