#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_SHA:?}"
: "${GITHUB_RUN_ID:?}"
: "${GITHUB_OUTPUT:?}"
: "${RUNNER_TEMP:?}"

BRANCH="brain-learning/proposals"
MAX_ATTEMPTS="${BRAIN_MEMORY_PUBLISH_ATTEMPTS:-8}"
case "$MAX_ATTEMPTS" in
  ''|*[!0-9]*) MAX_ATTEMPTS=8 ;;
esac
if [ "$MAX_ATTEMPTS" -lt 1 ]; then MAX_ATTEMPTS=1; fi
if [ "$MAX_ATTEMPTS" -gt 12 ]; then MAX_ATTEMPTS=12; fi

dispatch_fingerprint="$(printf '%s' "${LEARNING_DISPATCH_FINGERPRINT:-}" | tr '[:upper:]' '[:lower:]' | xargs)"
dispatch_cohort="$(printf '%s' "${LEARNING_DISPATCH_PROVIDER:-}" | tr '[:upper:]_' '[:lower:]-' | tr -d '[:space:]')"
dispatch_provider=""
if [ -n "$dispatch_fingerprint" ]; then
  [[ "$dispatch_fingerprint" =~ ^[0-9a-f]{64}$ ]] || {
    echo "invalid persisted Learning dispatch fingerprint" >&2
    exit 1
  }
  IFS=',' read -r -a dispatch_providers <<< "$dispatch_cohort"
  [ "${#dispatch_providers[@]}" -gt 0 ] || {
    echo "Learning dispatch fingerprint requires a safe provider cohort" >&2
    exit 1
  }
  for provider in "${dispatch_providers[@]}"; do
    [[ "$provider" =~ ^[a-z0-9][a-z0-9-]{0,95}$ ]] || {
      echo "Learning dispatch fingerprint contains an unsafe provider id" >&2
      exit 1
    }
  done
  # The family dispatcher intentionally fingerprints the cohort oracle (first
  # provider). Siblings are executed in the same sandbox and contribute durable
  # experiment/family memory, but this dispatch receipt marks only the exact
  # oracle fingerprint supplied by the parent gate.
  dispatch_provider="${dispatch_providers[0]}"
fi

candidate_root="$RUNNER_TEMP/brain-learning-memory-candidate-$GITHUB_RUN_ID"
rm -rf "$candidate_root"
mkdir -p "$candidate_root"
cp brain-learning-output/latest.json "$candidate_root/latest.json"
cp brain-learning-output/latest.md "$candidate_root/latest.md"
cp brain-sandbox/brain-llm/guidance.json "$candidate_root/guidance.json"
cp brain-learning-input/previous.json "$candidate_root/base.json"

candidate_ms="$(node -e "const x=require('$candidate_root/latest.json');const t=Date.parse(x.generatedAt||'');if(!Number.isFinite(t))process.exit(2);process.stdout.write(String(t))")"
candidate_guidance_source="$(node -e "const x=require('$candidate_root/guidance.json');process.stdout.write(String(x.sourceSha||''))")"

git config user.name "niakvio-brain"
git config user.email "actions@users.noreply.github.com"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  git switch --detach "$GITHUB_SHA" >/dev/null 2>&1
  git reset --hard "$GITHUB_SHA" >/dev/null
  rm -rf brain-learning-output brain-learning-input brain-sandbox/brain-llm
  mkdir -p brain-learning-output brain-learning-input brain-sandbox/brain-llm
  cp "$candidate_root/latest.json" brain-learning-output/latest.json
  cp "$candidate_root/latest.md" brain-learning-output/latest.md
  cp "$candidate_root/guidance.json" brain-sandbox/brain-llm/guidance.json
  cp "$candidate_root/base.json" brain-learning-input/previous.json
  rm -f "$RUNNER_TEMP/brain-learning-existing.json" "$RUNNER_TEMP/brain-learning-existing-guidance.json"
  rm -f "$RUNNER_TEMP/brain-learning-dispatch-ledger.json" "$RUNNER_TEMP/brain-learning-dispatch-selection.json"

  git fetch --quiet origin main || true
  git fetch --force origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH" >/dev/null 2>&1 || true

  existing_ms=""
  existing_guidance_source=""
  if git cat-file -e "refs/remotes/origin/$BRANCH:engine_v2/learning/latest.json" 2>/dev/null; then
    git show "refs/remotes/origin/$BRANCH:engine_v2/learning/latest.json" > "$RUNNER_TEMP/brain-learning-existing.json"
    existing_ms="$(node -e "const fs=require('fs');const x=JSON.parse(fs.readFileSync(process.env.RUNNER_TEMP+'/brain-learning-existing.json','utf8'));const t=Date.parse(x.generatedAt||'');if(Number.isFinite(t))process.stdout.write(String(t))")"
  fi
  if git cat-file -e "refs/remotes/origin/$BRANCH:engine_v2/learning/llm-guidance.json" 2>/dev/null; then
    git show "refs/remotes/origin/$BRANCH:engine_v2/learning/llm-guidance.json" > "$RUNNER_TEMP/brain-learning-existing-guidance.json"
    existing_guidance_source="$(node -e "const fs=require('fs');const x=JSON.parse(fs.readFileSync(process.env.RUNNER_TEMP+'/brain-learning-existing-guidance.json','utf8'));process.stdout.write(String(x.sourceSha||''))")"
  fi

  if git cat-file -e "refs/remotes/origin/$BRANCH:engine_v2/learning/dispatch-ledger.json" 2>/dev/null; then
    git show "refs/remotes/origin/$BRANCH:engine_v2/learning/dispatch-ledger.json" > "$RUNNER_TEMP/brain-learning-dispatch-ledger.json"
  elif [ -s automation/provider-learning-dispatch-ledger.json ]; then
    cp automation/provider-learning-dispatch-ledger.json "$RUNNER_TEMP/brain-learning-dispatch-ledger.json"
  else
    printf '%s\n' '{"schemaVersion":2,"providers":{},"privateContentRetained":false}' > "$RUNNER_TEMP/brain-learning-dispatch-ledger.json"
  fi
  if [ -n "$dispatch_fingerprint" ]; then
    python - "$dispatch_provider" "$dispatch_fingerprint" "$RUNNER_TEMP/brain-learning-dispatch-selection.json" <<'PY'
import json,sys
provider,fingerprint,path=sys.argv[1:]
json.dump({
    "schemaVersion": 1,
    "eligible": [{
        "provider": provider,
        "fingerprint": fingerprint,
        "signatureHash": fingerprint[:20],
    }],
},open(path,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
PY
    python scripts/provider_learning_dispatch_gate.py mark \
      --ledger "$RUNNER_TEMP/brain-learning-dispatch-ledger.json" \
      --selection "$RUNNER_TEMP/brain-learning-dispatch-selection.json" \
      --learning-run-id "$GITHUB_RUN_ID"
    echo "FIELD_BRAIN_DISPATCH_LEDGER_MARK provider=$dispatch_provider cohort=${dispatch_cohort:-none} fingerprint=${dispatch_fingerprint:0:12} execution=successful-sandbox"
  fi

  if [ -n "$existing_guidance_source" ] && [ "$candidate_guidance_source" != "$existing_guidance_source" ]; then
    if git merge-base --is-ancestor "$candidate_guidance_source" "$existing_guidance_source"; then
      echo "FIELD_BRAIN_MEMORY_PUBLISH skipped=stale-source candidate=$candidate_guidance_source existing=$existing_guidance_source"
      echo "published=false" >> "$GITHUB_OUTPUT"
      exit 0
    fi
    git merge-base --is-ancestor "$existing_guidance_source" "$candidate_guidance_source" || {
      echo "refusing divergent Learning guidance sources candidate=$candidate_guidance_source existing=$existing_guidance_source" >&2
      exit 1
    }
  fi

  candidate_older=false
  if [ -n "$existing_ms" ] && [ "$candidate_ms" -le "$existing_ms" ]; then
    candidate_older=true
    echo "FIELD_BRAIN_MEMORY_PUBLISH stale_generated_state=true candidate_ms=$candidate_ms existing_ms=$existing_ms action=merge-experiment-delta attempt=$attempt"
  fi

  if [ -s "$RUNNER_TEMP/brain-learning-existing.json" ]; then
    python scripts/merge_brain_learning_latest_memory.py \
      --base brain-learning-input/previous.json \
      --previous "$RUNNER_TEMP/brain-learning-existing.json" \
      --current brain-learning-output/latest.json \
      --output brain-learning-output/latest.json
    if [ "$candidate_older" = "true" ] && git cat-file -e "refs/remotes/origin/$BRANCH:engine_v2/learning/latest.md" 2>/dev/null; then
      git show "refs/remotes/origin/$BRANCH:engine_v2/learning/latest.md" > brain-learning-output/latest.md
    fi
  elif [ "$candidate_older" = "true" ]; then
    echo "FIELD_BRAIN_MEMORY_PUBLISH skipped=stale-without-three-way-base candidate_ms=$candidate_ms existing_ms=$existing_ms"
    echo "published=false" >> "$GITHUB_OUTPUT"
    exit 0
  fi

  if [ -s "$RUNNER_TEMP/brain-learning-existing-guidance.json" ]; then
    python scripts/merge_brain_llm_guidance_memory.py \
      --previous "$RUNNER_TEMP/brain-learning-existing-guidance.json" \
      --current brain-sandbox/brain-llm/guidance.json \
      --output brain-sandbox/brain-llm/guidance.json \
      --repo-root "$GITHUB_WORKSPACE"
  fi
  python scripts/filter_brain_learning_guidance.py \
    --input brain-sandbox/brain-llm/guidance.json \
    --output brain-sandbox/brain-llm/guidance.json \
    --negative-memory automation/brain-repair-memory.json

  expected_sha=""
  if git rev-parse --verify "refs/remotes/origin/$BRANCH" >/dev/null 2>&1; then
    expected_sha="$(git rev-parse "refs/remotes/origin/$BRANCH")"
  fi

  tmp_branch="brain-learning-memory-$GITHUB_RUN_ID-$attempt"
  git switch --orphan "$tmp_branch" >/dev/null
  git rm -rf . >/dev/null 2>&1 || true
  mkdir -p engine_v2/learning
  cp brain-learning-output/latest.json engine_v2/learning/latest.json
  cp brain-learning-output/latest.md engine_v2/learning/latest.md
  cp brain-sandbox/brain-llm/guidance.json engine_v2/learning/llm-guidance.json
  cp "$RUNNER_TEMP/brain-learning-dispatch-ledger.json" engine_v2/learning/dispatch-ledger.json
  git add engine_v2/learning/latest.json engine_v2/learning/latest.md engine_v2/learning/llm-guidance.json engine_v2/learning/dispatch-ledger.json
  git commit -m "brain: refresh sandbox repair learning" >/dev/null

  tracked="$(git ls-files | sort)"
  expected="$(printf '%s\n' engine_v2/learning/latest.json engine_v2/learning/latest.md engine_v2/learning/llm-guidance.json engine_v2/learning/dispatch-ledger.json | sort)"
  test "$tracked" = "$expected" || {
    echo "refusing non-minimal Brain memory tree" >&2
    printf 'tracked:\n%s\n' "$tracked" >&2
    exit 1
  }

  if git push --force-with-lease="$BRANCH:$expected_sha" origin HEAD:"$BRANCH"; then
    echo "FIELD_BRAIN_MEMORY_PUBLISH mode=orphan-memory-only files=4 attempt=$attempt lease_retry=true dispatch_marked=$([ -n "$dispatch_fingerprint" ] && echo true || echo false)"
    echo "published=true" >> "$GITHUB_OUTPUT"
    exit 0
  fi

  echo "FIELD_BRAIN_MEMORY_PUBLISH retry=true attempt=$attempt reason=lease-or-transient-push-conflict" >&2
  sleep "$attempt"
done

echo "Brain memory publication exhausted optimistic lease retries" >&2
exit 1
