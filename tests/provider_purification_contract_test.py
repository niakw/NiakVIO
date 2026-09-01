#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_patch_blocks import render_managed_fix  # noqa: E402
from provider_byte_stability import (  # noqa: E402
    BYTE_STABILITY_VERSION,
    split_owned_prefix_bootstraps,
    split_provider_core_tail,
    verify_bytes,
)

assert BYTE_STABILITY_VERSION == "raw-v1"
assert not (ROOT / "engine_v2/scripts/purify-provider.mjs").exists()
assert not (ROOT / "engine_v2/scripts/terser-clean.mjs").exists()

# Critical publication/runtime paths must contain no Terser implementation or
# metadata. Provider optimization stays disabled until runtime is stable.
critical_paths = (
    ROOT / "scripts/provider_byte_stability.py",
    ROOT / "scripts/reapply_published_overrides.py",
    ROOT / "scripts/verify_provider_publication_fixed_point.py",
    ROOT / "scripts/run_adaptive_deep_repair.py",
    ROOT / "scripts/purify_native_reader_repair.py",
    ROOT / ".github/workflows/core-media-finalize-main.yml",
)
for path in critical_paths:
    text = path.read_text(encoding="utf-8")
    assert "terser" not in text.casefold(), path.relative_to(ROOT)

runtime_prefix = '''/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */
;(function(g,rules){if(g)g.__nuvioDomainOverrideV1=rules;})(typeof globalThis!=="undefined"?globalThis:this,[["b2xkLmV4YW1wbGU=","new.example"]]);
'''
provider_body = 'module.exports={getStreams:async function(){return [];}};\n'
core_boundary = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
managed_core = render_managed_fix(
    "CORE.TEST.RAW_BYTES.V1",
    "globalThis.__nuvioRawByteTest=1;",
    data={"fixture": "raw-byte-preservation"},
)
source = (runtime_prefix + provider_body + core_boundary + "\n" + managed_core + "\n").encode("utf-8")

prefix, body = split_owned_prefix_bootstraps(source)
assert prefix.decode("utf-8") == runtime_prefix
provider_part, core_tail = split_provider_core_tail(body)
assert provider_part.decode("utf-8") == provider_body
assert core_tail.decode("utf-8") == core_boundary + "\n" + managed_core + "\n"

first, first_report = verify_bytes(source)
second, second_report = verify_bytes(first)
assert first == source
assert second == source
assert first_report["tool"] == "raw-bytes"
assert first_report["mode"] == "raw-preserve"
assert first_report["applied"] is False
assert first_report["fixedPointVerified"] is True
assert first_report["bytesSaved"] == 0
assert second_report["candidateSha256"] == first_report["candidateSha256"]

text = first.decode("utf-8")
assert text.count("/* START NIAKVIO_FIX:CORE.TEST.RAW_BYTES.V1 */") == 1
assert text.count("/* END NIAKVIO_FIX:CORE.TEST.RAW_BYTES.V1 */") == 1
assert "NIAKVIO_FIX_DATA_PAYLOAD:CORE.TEST.RAW_BYTES.V1:" in text

print("raw provider byte-stability contract passed")
