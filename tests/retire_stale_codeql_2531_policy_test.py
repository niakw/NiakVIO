#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
guard=(ROOT/"scripts/retire_stale_codeql_2531.py").read_text()
cleanup=(ROOT/"scripts/delete_stale_codeql_2531_configuration.py").read_text()
workflow=(ROOT/".github/workflows/retire-stale-codeql-2531.yml").read_text()
codeql=(ROOT/".github/workflows/codeql.yml").read_text()

assert "LEGACY_ALERT=2531" in guard
assert 'LEGACY_KEY=".github/workflows/codeql.yml:analyze"' in guard
assert "verify_current_source()" in cleanup
assert "scan_source_sha()" in cleanup
assert "evidence_only_drift" in cleanup
assert "scope:core" in cleanup
assert "code-scanning/analyses" in cleanup
assert '"DELETE"' in cleanup
assert "confirm_delete=true" in cleanup
assert "dismissed_comment" not in cleanup
assert "delete_stale_codeql_2531_configuration.py" in workflow
assert "security-events: write" in workflow
assert "github.event.workflow_run.conclusion == 'success'" in workflow
assert "pull_request_target" not in workflow
assert "CodeQL · JS Legacy Category Reconciliation" not in codeql
assert 'category: ".github/workflows/codeql.yml:analyze"' not in codeql
assert 'category: "/language:javascript-typescript/scope:core"' in codeql
print("CODEQL_STALE_CATEGORY_LIFECYCLE_POLICY_OK")
