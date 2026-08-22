#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
node = (ROOT / "engine_v2/scripts/purify-provider.mjs").read_text(encoding="utf-8")
helper = (ROOT / "scripts/provider_purification.py").read_text(encoding="utf-8")
deep = (ROOT / "scripts/run_adaptive_deep_repair.py").read_text(encoding="utf-8")
reader_prepare = (ROOT / "scripts/prepare_native_reader_acceptance.py").read_text(encoding="utf-8")
reader_purify = (ROOT / "scripts/purify_native_reader_repair.py").read_text(encoding="utf-8")

# Phase 1 is deliberately conservative: no identifier mangling, no unsafe Terser
# transforms, names are retained, and self-source/dynamic-code providers fall back
# to formatting-only minification before runtime proof.
for required in (
    'EXPECTED_TERSER_VERSION = "5.50.0"',
    "mangle: false",
    "unsafe: false",
    "keep_classnames: true",
    "keep_fnames: true",
    'flags.includes("dynamic_eval")',
    'flags.includes("dynamic_function_constructor")',
    'flags.includes("function_source_introspection")',
    "const compress = risky ? false",
):
    assert required in node, required

# The build-only dependency is exact/pinned and never becomes a Nuvio runtime dep.
for required in (
    'TERSER_VERSION = "5.50.0"',
    '"--no-save", "--package-lock=false"',
    'f"terser@{TERSER_VERSION}"',
    "validate_provider_artifact.cjs",
    '"type": "provider_purification"',
    '"requiresRuntimeRetest": True',
    '"repair_candidates_must_repurify": True',
):
    assert required in helper, required

# Deep proves the exact purified baseline and every later Brain/runtime mutation.
assert "purify_registry(stage, output / \"provider-purification.json\")" in deep
assert "purify_candidate(Path(stage), repaired)" in deep
assert "The deep result therefore proves the exact optimized bytes" in deep

# Native-reader Brain candidates must be purified before they are copied into the
# official Nuvio TV acceptance source; manifest/report SHA references are rewritten.
assert "maybe_purify_reader_repair_manifest(manifest_path)" in reader_prepare
assert "purify_native_reader_repair.py" in reader_prepare
for required in (
    "purify_file(path)",
    'proposal["candidateSha256"] = new_sha',
    'manifest_row["filename"] = relative',
    'policy["providerPurificationRequiredBeforeRetest"] = True',
    'policy["purificationMangleAllowed"] = False',
):
    assert required in reader_purify, required

print("provider purification contract tests passed")
