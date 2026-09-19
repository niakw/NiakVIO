#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "stream_output_sanitizer_v5.py"

spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v5", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    source = "module.exports={getStreams:async function(){return [];}};\n"
    initial_options = {
        "probe_direct_media": False,
        "probe_all_urls": False,
        "max_probes": 0,
    }
    first = module.apply(source, options=initial_options)
    assert module.apply(first, options=initial_options) == first

    strict_options = {
        "probe_direct_media": True,
        "probe_all_urls": True,
        "max_probes": 8,
        "blocked_path_patterns": ["/wp-admin/", "/wp-json/"],
    }
    second = module.apply(first, options=strict_options)
    assert module.apply(second, options=strict_options) == second

    assert second.count("/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:") == 1
    assert second.count("/* NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5 */") == 1
    assert '"probeAllUrls":true' in second
    assert '"probeDirectMedia":true' in second
    assert '"maxProbes":8' in second
    assert '"/wp-admin/"' in second
    assert '"/wp-json/"' in second
    assert r"\u00EF\u00BB\u00BF" in second
    assert '"probeAllUrls":false' not in second

    print("stream output sanitizer reconfiguration test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
