#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
PATCH = ROOT / "scripts" / "provider_patches" / "nuvio_tv_target_media_v4.py"
OLD = "scripts/provider_patches/nuvio_tv_direct_media_v2.py"
TARGET = "scripts/provider_patches/nuvio_tv_target_media_v4.py"
SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v5.py"
DESKTOP = "scripts/provider_patches/desktop_runtime_compat_v1.py"
V4_MARKER = "/* NUVIO_TV_TARGET_MEDIA_V4 */"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("streamzo_target_media_v4_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    provider = data["provider_patches"]["streamzo"]
    scripts = provider.get("patch_scripts") or []
    assert TARGET in scripts, scripts
    assert SANITIZER in scripts, scripts
    assert OLD not in scripts, scripts
    assert scripts.index(TARGET) < scripts.index(SANITIZER) < scripts.index(DESKTOP), scripts
    options = (provider.get("patch_script_options") or {}).get(TARGET) or {}
    assert options.get("provider_name") == "StreamZo", options
    assert options.get("strip_legacy_direct_media_v2") is True, options
    assert options.get("force_rewrap_target_media") is True, options
    assert int(options.get("max_candidates") or 0) >= 20, options
    assert "fstream.top" in (options.get("blocked_hosts") or []), options

    module = load_module(PATCH)

    # Removing a legacy V2 wrapper must be bounded to that wrapper. Recovery
    # hooks appended after an older published V2 bundle must survive the first
    # reapply pass, otherwise they reappear only on pass two and change hashes.
    legacy = (
        "native-provider-code\n"
        "/* NUVIO_TV_DIRECT_MEDIA_V2:deadbeef */\n"
        ";(function(g,c){return c})(typeof globalThis!==\"undefined\"?globalThis:this,{\"x\":1});\n"
        "/* NUVIO_VF_CATALOGUE_RECOVERY_V1:feedface */\n"
        "catalogue-recovery-tail\n"
    )
    stripped = module.strip_legacy_direct_media(legacy, True)
    assert "NUVIO_TV_DIRECT_MEDIA_V2" not in stripped
    assert "NUVIO_VF_CATALOGUE_RECOVERY_V1:feedface" in stripped
    assert stripped.endswith("catalogue-recovery-tail\n")

    # Regression for the durable reapply pipeline: once v4 has been
    # materialized, a second discovery pass must be byte-for-byte identical.
    source = 'module.exports={getStreams:async function(){return []}};\n'
    first = module.apply(source, options=options)
    second = module.apply(first, options=options)
    assert first == second, "target-media v4 is not byte-idempotent"
    assert first.count(V4_MARKER) == 1, "target-media v4 marker must be unique"

    print("StreamZo target-media ordering, bounded legacy removal and byte-idempotence tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
