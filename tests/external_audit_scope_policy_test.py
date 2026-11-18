#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/external_audit/classify_findings.py"
spec = importlib.util.spec_from_file_location("external_audit_classifier", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert mod.norm_path(".github/workflows/native-mobile-android-reader.yml") == ".github/workflows/native-mobile-android-reader.yml"
assert mod.norm_path("./.github/workflows/native-mobile-android-reader.yml") == ".github/workflows/native-mobile-android-reader.yml"
assert mod.scope(".github/workflows/native-mobile-android-reader.yml") == "maintained"
assert mod.scope("providers/demo--nuvio--1234.js") == "generated"
assert mod.scope("provider-disabled/demo--nuvio--1234.js") == "generated"
assert mod.scope("provider-old/demo.js") == "historical"
assert mod.scope("scripts/provider_patches/demo.py") == "maintained"

print("external audit scope policy passed: dot-github preserved disabled-provider-bundles=generated")

# The same scanner may report long-retired paths alongside a real maintained
# source finding. Only paths demonstrably present in the audited checkout may
# block the maintained-source gate; no rule/code is broadly suppressed.
with tempfile.TemporaryDirectory(prefix="niakvio-external-source-") as temp:
    checkout = Path(temp)
    audit = checkout / "audit/ai-external"
    for name in ("sonar", "deepsource", "codescene"):
        (audit / name).mkdir(parents=True)
    (checkout / "scripts").mkdir()
    (checkout / ".github/workflows").mkdir(parents=True)
    (checkout / "scripts/live.py").write_text("def live(): return 1\n", encoding="utf-8")
    (checkout / ".github/workflows/live.yml").write_text("name: Live\n", encoding="utf-8")
    (audit / "sonar/issues.json").write_text(json.dumps({"issues": [
        {"component": "scripts/live.py", "rule": "python:S3776", "message": "live complexity"},
    ]}), encoding="utf-8")
    (audit / "deepsource/findings.json").write_text(json.dumps([
        {"path": "./.github/workflows/live.yml", "shortcode": "SCT-A000", "message": "live candidate"},
        {"path": "./.github/workflows/deleted.yml", "shortcode": "SCT-A000", "message": "retired workflow"},
        {"path": "provider-disabled/archived--nuvio--old.js", "shortcode": "SCT-A000", "message": "disabled bundle"},
        {"path": "providers/active--nuvio--generated.js", "shortcode": "SCT-A000", "message": "derived bundle"},
        {"path": "audit/ai-external/result.json", "shortcode": "SCT-A000", "message": "evidence"},
    ]), encoding="utf-8")
    (audit / "codescene/analysis-latest.json").write_text(json.dumps({"findings": [
        {"file": "retired_test.py", "rule": "code-health-defects", "message": "removed test"}
    ]}), encoding="utf-8")
    (audit / "codescene/files.json").write_text("[]\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(audit), "--strict"],
        cwd=checkout, capture_output=True, text=True, check=False,
    )
    assert completed.returncode != 0
    assert "external audit has 2 unresolved maintained-source findings" in completed.stderr, completed.stderr
    result = json.loads((audit / "maintained-source.json").read_text(encoding="utf-8"))
    assert result["raw_findings"] == 7
    assert result["maintained_unresolved_count"] == 2
    assert result["maintained_reviewed_count"] == 0
    assert result["by_scope"] == {
        "maintained": 2, "stale_external_source": 2,
        "generated": 2, "evidence": 1,
    }, result["by_scope"]
    assert {row["path"] for row in result["maintained_unresolved"]} == {
        "scripts/live.py", ".github/workflows/live.yml",
    }
    assert "exact-SHA snapshot freshness remains strict" in result["policy"]["stale_external_source"]
assert "scripts/external_audit/validate_snapshot.py" in (
    ROOT / ".github/workflows/external-code-audit.yml"
).read_text(encoding="utf-8")
print("external audit exact live-source vs removed-source contract passed")
