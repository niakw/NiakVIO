#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / ".github" / "workflows" / "domain-refresh.yml").read_text(encoding="utf-8")

assert "permissions:\n  contents: read" in text
assert "persist-credentials: false" in text
assert "python scripts/resolve_provider_hubs.py" in text
assert "--apply" not in text, "domain observer must never apply migrations"
assert "git push" not in text and "git commit" not in text, (
    "domain observer must never publish provider state"
)
assert "provider_catalog.json" in text and "git diff --exit-code" in text, (
    "domain observation must prove that catalog/manifests/provider state remains unchanged"
)
assert "actions/upload-artifact" in text, "domain observations must be exported as CI evidence"
assert ".github/workflows/sync.yml" not in text, (
    "domain observation must not implement or proxy a second publication orchestrator"
)

sync = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")
assert "python scripts/resolve_provider_hubs.py" in sync and "--apply" in sync, (
    "only the canonical ARCHI2 pipeline applies validated hub/domain changes"
)

print("ARCHI2 observation-only domain workflow test passed")
