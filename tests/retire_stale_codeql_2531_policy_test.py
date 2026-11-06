#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"scripts/retire_stale_codeql_2531.py").read_text()
workflow=(ROOT/".github/workflows/retire-stale-codeql-2531.yml").read_text()
assert "LEGACY_ALERT=2531" in source
assert 'LEGACY_KEY=".github/workflows/codeql.yml:analyze"' in source
assert "start_line" in source and "scope:core" in source
assert "verify_current_source()" in source
assert 'row.get("commit_sha")==expected' in source
assert "code-scanning/analyses" in source
assert "dismissed_comment" in source
assert "main moved" in source.lower() or "Main moved" in source
assert 'security-events: write' in workflow
assert 'github.event.workflow_run.conclusion == \'success\'' in workflow
assert 'github.event.workflow_run.head_sha == github.sha' in workflow
assert "pull_request_target" not in workflow
print("CODEQL_STALE_CATEGORY_LIFECYCLE_POLICY_OK")
