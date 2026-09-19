#!/usr/bin/env python3
"""Contract tests for the production NiakVIO-safe one-line Provider v3 minimizer."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/provider_v3_minimizer.py"

spec = importlib.util.spec_from_file_location("provider_v3_minimizer", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

from provider_patch_blocks import (  # noqa: E402
    replace_core_fix,
    replace_provider_fix,
    validate_managed_fixes,
)

assert module.PRODUCTION_ENABLED is True
assert module.TERSER_ALLOWED is False
assert module.TRANSFORMATIONS_ENABLED == [
    "one-physical-line",
    "code-linebreak-to-space",
    "post-linebreak-indentation-removal",
    "unmanaged-comment-removal",
    "untagged-template-linebreak-escape",
    "asi-restricted-linebreak-to-semicolon",
]

EXPECTED = len(module.provider_files())
assert EXPECTED > 0

sample = """/* BEGIN NIAKVIO_PROVIDER */
/* NIAKVIO_PROVIDER_ID:demo */
/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
// removable explanatory comment with a `documentation tick`
const title = "  literal indentation stays";
/* STARTFIX:PROVIDER.DEMO.CONFIG.V1 */
/* FIXDATA:PROVIDER.DEMO.CONFIG.V1:e30= */
const payload = `line one
    ${title}
line three`;
/* CLOSEFIX:PROVIDER.DEMO.CONFIG.V1 */
/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
/*! license payload */
//# sourceURL=provider-demo.js
function getStreams(){ return []; }
/* END NIAKVIO_PROVIDER */
"""
result = module.minimize_text(sample)
module.validate_transform(sample, result.text)
module._node_check(result.text, "contract-sample.js")
assert result.saved_bytes > 0
assert result.transformed_lines > 0
assert "\n" not in result.text and "\r" not in result.text
assert '"  literal indentation stays"' in result.text
assert "removable explanatory comment" not in result.text
assert "STARTFIX:PROVIDER.DEMO.CONFIG.V1" in result.text
assert "FIXDATA:PROVIDER.DEMO.CONFIG.V1:e30=" in result.text
assert "CLOSEFIX:PROVIDER.DEMO.CONFIG.V1" in result.text
assert "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1" in result.text
assert "`line one\\n    ${title}\\nline three`" in result.text
assert "license payload" in result.text
assert "sourceURL=provider-demo.js" in result.text
assert module.minimize_text(result.text).text == result.text

# Regex literals may contain quote/backtick-looking bytes and must remain opaque.
regex_sample = r'''const r=/["'`/]+\/x/gi; const ok=r.test("x");'''
regex_result = module.minimize_text(regex_sample).text
assert regex_result == regex_sample
module._node_check(regex_result, "regex-sample.js")

# Tagged templates can observe String.raw and therefore fail closed rather than
# silently changing semantics while forcing one physical line.
try:
    module.minimize_text("const x = tag`a\nb`;\n")
except ValueError as exc:
    assert "tagged template" in str(exc)
else:
    raise AssertionError("tagged template must fail closed")

# Restricted-production newlines that JavaScript ASI already terminates are
# encoded explicitly so one-line publication preserves the original semantics.
return_asi = module.minimize_text("function x(){return\n1;}\n").text
assert "return;" in return_asi and "\n" not in return_asi
module._node_check(return_asi, "asi-return.js")

yield_asi = module.minimize_text("function* g(){yield\n1;}\n").text
assert "yield;" in yield_asi and "\n" not in yield_asi
module._node_check(yield_asi, "asi-yield.js")

break_asi = module.minimize_text("while(true){break\nlabel:{break label}}\n").text
assert "break;" in break_asi and "\n" not in break_asi
module._node_check(break_asi, "asi-break.js")

continue_asi = module.minimize_text("let i=0;while(i++<1){continue\nlabel:{}}\n").text
assert "continue;" in continue_asi and "\n" not in continue_asi
module._node_check(continue_asi, "asi-continue.js")

async_asi = module.minimize_text("async\nfunction f(){}\n").text
assert "async;" in async_asi and "\n" not in async_asi
module._node_check(async_asi, "asi-async.js")

# throw followed by a physical newline is illegal JavaScript and remains
# fail-closed rather than being silently repaired.
try:
    module.minimize_text("function x(){throw\nnew Error('x');}\n")
except ValueError as exc:
    assert "throw" in str(exc)
else:
    raise AssertionError("illegal throw newline must fail closed")

# Editing remains supported after publication is one-line: missing Provider/Core
# Lego blocks may be inserted, decoded by marker ownership, then minimized again.
editable = module.minimize_text(
    """/* BEGIN NIAKVIO_PROVIDER */
/* NIAKVIO_PROVIDER_ID:edit-demo */
/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
const seed = 1;
/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
/* END NIAKVIO_PROVIDER */
"""
).text
assert "\n" not in editable
edited = replace_provider_fix(
    editable,
    "PROVIDER.EDIT-DEMO.RUNTIME.V1",
    "const providerEdit = true;",
    data={"revision": 1},
)
edited = replace_core_fix(
    edited,
    "CORE.EDIT-DEMO.RUNTIME.V1",
    "const coreEdit = true;",
    data={"revision": 1},
)
assert validate_managed_fixes(edited) == [
    "CORE.EDIT-DEMO.RUNTIME.V1",
    "PROVIDER.EDIT-DEMO.RUNTIME.V1",
]
republished = module.minimize_text(edited).text
module._node_check(republished, "edited-republished.js")
assert "\n" not in republished and "\r" not in republished
assert republished.count("STARTFIX:") == 2
assert republished.count("CLOSEFIX:") == 2
assert validate_managed_fixes(republished) == [
    "CORE.EDIT-DEMO.RUNTIME.V1",
    "PROVIDER.EDIT-DEMO.RUNTIME.V1",
]

# The whole actual active portfolio must both become one-line and still parse in
# Node. This replaces the old false invariant that counted raw backticks inside
# removable comments as though they were template delimiters.
report = module.portfolio_report(syntax_check=True)
assert report["mode"] == "niakvio-safe-one-line-minimizer"
assert report["production_enabled"] is True
assert report["terser_allowed"] is False
assert report["provider_count"] == EXPECTED
assert len(report["providers"]) == EXPECTED
assert report["totals"]["bytes_after"] <= report["totals"]["bytes_before"]
assert report["totals"]["one_line_providers"] == EXPECTED

for row in report["providers"]:
    assert row["after"]["markers"]["BEGIN NIAKVIO_PROVIDER"] == 1, row["file"]
    assert row["after"]["markers"]["END NIAKVIO_PROVIDER"] == 1, row["file"]
    assert row["after"]["markers"]["NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"] == 1, row["file"]
    assert row["after"]["physical_linebreaks"] == 0, row["file"]
    assert row["after"]["bytes"] <= row["before"]["bytes"], row["file"]

with tempfile.TemporaryDirectory() as tmp:
    preview = Path(tmp) / "preview"
    preview_report = module.write_preview(preview, syntax_check=True)
    assert preview_report["provider_count"] == EXPECTED
    assert len(list(preview.glob("*.js"))) == EXPECTED
    for path in preview.glob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert "\n" not in text and "\r" not in text, path.name

print(
    "PROVIDER_V3_MINIMIZER_CONTRACT_OK "
    f"providers={EXPECTED} saved_preview={report['totals']['saved_bytes']} "
    "one_line=1 edit_roundtrip=1 template_safe=1 regex_safe=1 markers_safe=1 node_parse=1 terser=0"
)
