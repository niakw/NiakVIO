#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_purification import purify_bytes, split_owned_prefix_bootstraps  # noqa: E402

node_path = ROOT / "engine_v2/scripts/purify-provider.mjs"
cleaner_path = ROOT / "engine_v2/scripts/terser-clean.mjs"
node = node_path.read_text(encoding="utf-8")
terser_clean = cleaner_path.read_text(encoding="utf-8")
helper = (ROOT / "scripts/provider_purification.py").read_text(encoding="utf-8")
deep = (ROOT / "scripts/run_adaptive_deep_repair.py").read_text(encoding="utf-8")
reapply = (ROOT / "scripts/reapply_published_overrides.py").read_text(encoding="utf-8")
reader_prepare = (ROOT / "scripts/prepare_native_reader_acceptance.py").read_text(encoding="utf-8")
reader_purify = (ROOT / "scripts/purify_native_reader_repair.py").read_text(encoding="utf-8")

# Phase 1 is deliberately conservative: no identifier mangling, no unsafe Terser
# transforms, names are retained, and risky/self-source providers format only.
for required in (
    'EXPECTED_TERSER_VERSION = "5.50.0"',
    "mangle: false",
    "unsafe: false",
    "keep_classnames: true",
    "keep_fnames: true",
    'flags.includes("dynamic_eval")',
    'flags.includes("dynamic_function_constructor")',
    'flags.includes("function_source_introspection")',
    'process.argv.includes("--format-only")',
    'forceFormatOnly || risky',
    '"format-only"',
    'from "./terser-clean.mjs"',
    "await minifyAndClean(code, {",
    "const terserCandidate = result.code;",
    "Buffer.byteLength(terserCandidate) >= Buffer.byteLength(canonicalSource)",
    '"boundary-canonicalization"',
    "retainedAudioBoundaryCanonicalized",
    "floatedGeneratedMarkersCanonicalized",
):
    assert required in node, required

# The Terser gateway owns every post-minify cleanup. New direct Terser imports or
# requires anywhere else in tracked JS tooling are a contract failure: callers
# must not be able to forget boundary cleanup before validation/hash/publication.
for required in (
    'import { minify } from "terser";',
    'RETAINED_AUDIO_MARKER = "/* NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1 */"',
    "function canonicalizeRetainedCoreBoundary(code)",
    "function canonicalizeFloatedGeneratedMarkers(code)",
    "function canonicalizeOwnedBoundaries(code)",
    "function cleanTerserOutput(code)",
    "async function minifyAndClean(code, options)",
    "const result = await minify(code, options);",
    "const cleaned = cleanTerserOutput(result.code);",
):
    assert required in terser_clean, required

direct_terser = re.compile(r"(?:from\s+['\"]terser['\"]|require\(\s*['\"]terser['\"]\s*\))")
for suffix in ("*.js", "*.mjs", "*.cjs"):
    for path in ROOT.rglob(suffix):
        if any(part in {"node_modules", ".git"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if direct_terser.search(text):
            assert path.resolve() == cleaner_path.resolve(), f"direct Terser bypasses mandatory cleanup: {path.relative_to(ROOT)}"

# The build-only dependency is exact/pinned and every accepted body transform must
# be structurally valid and byte-stable under an identical second Terser pass.
for required in (
    'TERSER_VERSION = "5.50.0"',
    '"--no-save", "--package-lock=false"',
    'f"terser@{TERSER_VERSION}"',
    "validate_provider_artifact.cjs",
    'TemporaryDirectory(prefix="niakvio-provider-purify-", dir=ROOT)',
    'def _stable_candidate(',
    '_run_purifier(first, format_only=format_only)',
    '"--format-only"',
    '"fixedPointVerified": fixed_point_verified',
    '"fixed_point_verified": True',
    '"type": "provider_purification"',
    '"requiresRuntimeRetest": True',
    '"repair_candidates_must_repurify": True',
    "def split_owned_prefix_bootstraps(data: bytes)",
    '"ownedPrefixPreserved": True',
):
    assert required in helper, required

# Generated prefix bootstraps are Core-owned boundaries. They must remain exact
# source bytes while the actual provider/Core body is purified. This regression is
# intentionally executable: it proves the complete artifact is a fixed point under
# the same public purify_bytes() function used by Deep and publication.
runtime_prefix = '''/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */
;(function(g,rules){if(g)g.__nuvioDomainOverrideV1=rules;})(typeof globalThis!=="undefined"?globalThis:this,[["b2xkLmV4YW1wbGU=","new.example"]]);
'''
adaptive_prefix = '''/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN */
;(function(g,encoded){if(g)g.__nuvioAdaptiveDomainRecoveryV1=encoded;})(typeof globalThis!=="undefined"?globalThis:this,"eyJncm91cHMiOltdLCJyZXZpc2lvbiI6InRlc3QifQ==");
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */
'''
provider_body = 'module.exports={getStreams:async function(){const unused=1+1;return [];}};\n'
source = (runtime_prefix + adaptive_prefix + provider_body).encode("utf-8")
prefix, body = split_owned_prefix_bootstraps(source)
assert prefix.decode("utf-8") == runtime_prefix + adaptive_prefix
assert body.decode("utf-8") == provider_body
first, first_report = purify_bytes(source)
second, second_report = purify_bytes(first)
assert first.startswith(prefix)
assert second == first
assert first_report.get("ownedPrefixPreserved") is True
assert second_report.get("ownedPrefixPreserved") is True

# Terser preserves NUVIO comments, but its comment attachment must never turn the
# retained in-place HLS marker into a whitespace accumulator. This is the exact
# failure mode that previously made Einthusan and Moonflix rotate hashes forever.
# Crucially the canonical boundary must survive even when Terser has no accepted
# size gain: the JS purifier now picks canonical source bytes in that case.
audio_marker = "/* NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1 */"
core_boundary = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
retained_body = (
    'module.exports={getStreams:async function(){return [];}};\n\n\n\n\n'
    + audio_marker
    + '\n\n\n'
    + core_boundary
    + '\n'
).encode("utf-8")
retained_first, retained_first_report = purify_bytes(retained_body)
retained_second, _retained_second_report = purify_bytes(retained_first)
retained_text = retained_first.decode("utf-8")
assert retained_second == retained_first
assert retained_text.count(audio_marker) == 1
assert "\n\n" + audio_marker not in retained_text
assert audio_marker + "\n\n" not in retained_text
assert retained_first_report.get("retainedAudioBoundaryCanonicalized") is True

# A preserved generated comment may also float inside the provider export bridge,
# exactly as observed for AnimePahe and AnimeZey. Repair/prefix markers remain
# untouched; only this proven `marker */);(function` boundary is canonicalized so
# the strict export-floor parser never has to weaken its trust model.
floated_marker = "/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:test */"
floated_body = (
    'function getStreams(){return [];}\n'
    'typeof module!=="undefined"&&module.exports?module.exports={getStreams}:'
    '(global.getStreams=getStreams '
    + floated_marker
    + ');(function(g,c){g.__nuvioMediaTest=c;})(globalThis,{});\n'
).encode("utf-8")
floated_first, floated_report = purify_bytes(floated_body)
floated_second, _floated_second_report = purify_bytes(floated_first)
floated_text = floated_first.decode("utf-8")
assert floated_second == floated_first
assert floated_text.count(floated_marker) == 1
assert "getStreams " + floated_marker + ");(function" not in floated_text
assert ");\n" + floated_marker + "\n(function" in floated_text
assert int(floated_report.get("floatedGeneratedMarkersCanonicalized") or 0) >= 1

# Deep proves the exact purified baseline and every later Brain/runtime mutation.
assert "purify_registry(stage, output / \"provider-purification.json\")" in deep
assert "purify_candidate(Path(stage), repaired)" in deep
assert "The deep result therefore proves the exact optimized bytes" in deep

# Published provider bytes must end with the same pinned Terser purification.
# No provider/Core/runtime byte transform may happen between purification and the
# content-addressed digest used by manifests/provenance.
for required in (
    "from provider_purification import purify_bytes",
    "purified, purification = purify_bytes(patched)",
    '"phase": "final-post-transform"',
    '"tool": "terser"',
    '"mangle": False',
    "patched = purified",
):
    assert required in reapply, required
assert reapply.index("purified, purification = purify_bytes(patched)") < reapply.index("digest = hashlib.sha256(patched).hexdigest()")

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