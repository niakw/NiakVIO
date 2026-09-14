#!/usr/bin/env python3
"""Contract tests for the production NiakVIO-safe Provider v3 minimizer."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/provider_v3_minimizer.py"
EXPECTED = 46

spec = importlib.util.spec_from_file_location("provider_v3_minimizer", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

assert module.PRODUCTION_ENABLED is True
assert module.TERSER_ALLOWED is False
assert module.TRANSFORMATIONS_ENABLED == [
    "code-line-leading-indentation",
    "code-line-trailing-whitespace",
    "code-blank-lines",
    "unmanaged-full-line-comments",
]
assert module.EXPECTED_PROVIDER_COUNT == EXPECTED

sample = """/* BEGIN NIAKVIO_PROVIDER */

  // removable explanatory comment
  const title = "  literal indentation stays";   
  function demo() {
    /* block comment
       indentation inside comment stays */
    return title;
  }
  /* removable one-line block comment */

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
assert "removable explanatory comment" not in result.text
assert "removable one-line block comment" not in result.text
assert "STARTFIX:PROVIDER.DEMO.CONFIG.V1" in result.text
assert "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1" in result.text
assert "\n\n" not in result.text
assert module.minimize_text(result.text).text == result.text

tick = chr(96)
template_payload = "line one\n    ${value}\n"
template = "  const x = " + tick + template_payload + tick + ";\n  let y = 2;\n"
template_result = module.minimize_text(template)
module.validate_transform(template, template_result.text)
assert template_result.text.startswith("const x = " + tick)
assert tick + template_payload + tick in template_result.text
assert template_result.text.endswith("let y = 2;\n")
assert template_result.skipped_reason == ""
assert module.minimize_text(template_result.text).text == template_result.text

nested_payload = "a ${" + tick + "nested ${z}" + tick + "} b"
nested = "  const x = " + tick + nested_payload + tick + ";\n  let y = 2;\n"
nested_result = module.minimize_text(nested)
assert tick + nested_payload + tick in nested_result.text
assert nested_result.text.endswith("let y = 2;\n")

protected = """/*! license */
// # sourceURL=provider.js
/* NIAKVIO_PROVIDER_SECURITY_MARKER_V1 */
/* NUVIO_PROVIDER_SECURITY_HARDENING_V1:deadbeef */
  const x = 1;
"""
protected_result = module.minimize_text(protected)
assert "/*! license */" in protected_result.text
assert "sourceURL=provider.js" in protected_result.text
assert "NIAKVIO_PROVIDER_SECURITY_MARKER_V1" in protected_result.text
assert "NUVIO_PROVIDER_SECURITY_HARDENING_V1" in protected_result.text

report = module.portfolio_report(syntax_check=False)
assert report["mode"] == "niakvio-safe-minimizer"
assert report["production_enabled"] is True
assert report["terser_allowed"] is False
assert report["provider_count"] == EXPECTED
assert len(report["providers"]) == EXPECTED
assert report["totals"]["bytes_after"] <= report["totals"]["bytes_before"]

for row in report["providers"]:
    assert row["after"]["markers"]["BEGIN NIAKVIO_PROVIDER"] == 1, row["file"]
    assert row["after"]["markers"]["END NIAKVIO_PROVIDER"] == 1, row["file"]
    assert row["after"]["markers"]["NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"] == 1, row["file"]
    assert row["after"]["bytes"] <= row["before"]["bytes"], row["file"]

with tempfile.TemporaryDirectory() as tmp:
    preview = Path(tmp) / "preview"
    preview_report = module.write_preview(preview, syntax_check=False)
    assert preview_report["provider_count"] == EXPECTED
    assert len(list(preview.glob("*.js"))) == EXPECTED

print(
    "PROVIDER_V3_MINIMIZER_CONTRACT_OK "
    f"providers={EXPECTED} saved_preview={report['totals']['saved_bytes']} "
    "template_safe=1 nested_template_safe=1 comment_safe=1 terser=0"
)
