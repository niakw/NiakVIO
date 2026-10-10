#!/usr/bin/env bash
# Preserve a completed Repair experiment when another workflow advances main
# between its fetch/rebase and push. Never publish stale provider or census bytes.
set -euo pipefail
report="${1:-}"
run_id="${2:-}"
tested_sha="${3:-}"
if [[ ! "$run_id" =~ ^[0-9]{6,20}$ ]] || [[ ! "$tested_sha" =~ ^[a-f0-9]{40}$ ]] || [ ! -s "$report" ]; then
  echo "FIELD_REPAIR_EVIDENCE_RACE invalid-arguments" >&2
  exit 2
fi
python - "$report" <<'PY'
import json,sys
data=json.load(open(sys.argv[1],encoding="utf-8"))
if data.get("schemaVersion") not in (1,2) or not isinstance(data.get("selectedProviders"),list):
    raise SystemExit("stale Repair artifact missing schema or selected providers")
PY
for attempt in 1 2 3; do
  git fetch --quiet origin main
  main_sha="$(git rev-parse origin/main)"
  # We explicitly discard the previously staged candidate/census. The only
  # surviving bytes are the immutable per-run report and its provenance.
  git reset --hard origin/main
  mkdir -p automation
  report_path="automation/provider-brain-repair-$run_id.json"
  proof_path="automation/provider-brain-repair-$run_id-stale-provenance.json"
  cp "$report" "$report_path"
  python - "$proof_path" "$tested_sha" "$main_sha" "$run_id" <<'PY'
import json,sys
from pathlib import Path
data={
 "schemaVersion":1,
 "role":"historical-non-authoritative-repair-experiment",
 "runId":sys.argv[4],
 "testedSha":sys.argv[2],
 "recoveryMainSha":sys.argv[3],
 "publicationAllowed":False,
 "currentBytePlaybackAuthority":False,
 "requiresFreshMaterializationAndReplay":True,
}
Path(sys.argv[1]).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
  git add -- "$report_path" "$proof_path"
  if git diff --cached --quiet; then
    echo "FIELD_REPAIR_EVIDENCE_RACE preserved=true already-current run=$run_id main=$main_sha"
    exit 0
  fi
  git commit -m "ci(repair): preserve non-authoritative stale evidence $run_id"
  if git push origin HEAD:main; then
    echo "FIELD_REPAIR_EVIDENCE_RACE preserved=true evidence_only=true run=$run_id tested=$tested_sha new_sha=$(git rev-parse HEAD)"
    exit 0
  fi
  echo "FIELD_REPAIR_EVIDENCE_RACE retry=$attempt reason=concurrent-main"
done
echo "FIELD_REPAIR_EVIDENCE_RACE preserved=false reason=three-concurrent-main-pushes" >&2
exit 1
