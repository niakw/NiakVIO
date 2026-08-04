#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / ".github" / "workflows" / "domain-refresh.yml").read_text(encoding="utf-8")
stage = "python scripts/stage_published.py --stage staging"
validate = "python scripts/validate_override_pipeline.py --stage staging"
assert stage in text
assert "test -s staging/candidates.json" in text
assert validate in text
assert text.index(stage) < text.index(validate)
print("domain refresh workflow staging test passed")
