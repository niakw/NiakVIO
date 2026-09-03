#!/usr/bin/env python3
"""Contract tests for the production NiakVIO-safe Provider v3 minimizer."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/provider_v3_minimizer.py"

spec = importlib.util.spec_from_file_location("provider_v3_minimizer", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

assert module.PRODUCTION_ENABLED is True
assert module.TERSER_ALLOWED is False
assert module.TRANSFORMATIONS_ENABLED == ["code-line-leading-indentation"]

sample = """/* BEGIN NIAKVIO_PROVIDER */
  const title = "  literal indentation stays";
  function demo() {
    /* block comment
       indentation inside comment stays */
    return title;
  }
/* STARTFIX:PROVIDER.DEMO.CONFIG.V1 */
/* FIXDATA:PROVIDER.DEMO.CONFIG.V1:e30= */
/* CLOSEFIX:PROVIDER.DEMO.CONFIG.V1 */
/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
/* END NIAKVIO_PROVIDER */
"""
result = module.minimize_text(sample)
module.validate_transform(sample, result.text)
assert result.saved_bytes > 0
assert result.transformed_lines > 0
assert '"  literal indentation stays"' in result.text
assert "       indentation inside comment stays */" in result.text
assert module.minimize_text(result.text).text == result.text

tick = chr(96)
template = "  const x = " + tick + "line one\n    ${value}\n" + tick + ";\n"
template_result = module.minimize_text(template)
assert template_result.text == template
assert template_result.skipped_reason == "template_literal"

report = module.portfolio_report(syntax_check=False)
assert report["mode"] == "niakvio-safe-minimizer"
assert report["production_enabled"] is True
assert report["terser_allowed"] is False
assert report["provider_count"] == 96
assert len(report["providers"]) == 96
assert report["totals"]["bytes_after"] <= report["totals"]["bytes_before"]

for row in report["providers"]:
    assert row["after"]["markers"]["BEGIN NIAKVIO_PROVIDER"] == 1, row["file"]
    assert row["after"]["markers"]["END NIAKVIO_PROVIDER"] == 1, row["file"]
    assert row["after"]["markers"]["NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"] == 1, row["file"]
    assert row["after"]["bytes"] <= row["before"]["bytes"], row["file"]

with tempfile.TemporaryDirectory() as tmp:
    preview = Path(tmp) / "preview"
    preview_report = module.write_preview(preview, syntax_check=False)
    assert preview_report["provider_count"] == 96
    assert len(list(preview.glob("*.js"))) == 96

print(
    "PROVIDER_V3_MINIMIZER_CONTRACT_OK "
    f"providers=96 saved_preview={report['totals']['saved_bytes']} "
    f"template_safe=1 terser=0"
)
