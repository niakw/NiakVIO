#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "stream_output_sanitizer_v6.py"

spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v6_test", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    source = "module.exports={getStreams:async function(){return [];}};\n"
    options = {
        "probe_direct_media": True,
        "probe_all_urls": True,
        "max_probes": 20,
        "probe_timeout_ms": 6000,
        "blocked_hosts": ["fstream.top"],
        "blocked_path_patterns": [
            "/wp-admin/",
            "/wp-json/",
            "/wp-content/plugins/ajax-search-lite/",
        ],
        "min_vod_duration_seconds": 60,
    }
    first = module.apply(source, options=options)
    second = module.apply(first, options=options)
    assert second == first, "fail-closed sanitizer must be byte-idempotent"
    assert first.count(module.MARKER) == 1
    assert '"probeAllUrls":true' in first
    assert '"maxProbes":20' in first
    assert module.NEW in first
    assert module.OLD not in first
    for path in options["blocked_path_patterns"]:
        assert f'"{path}"' in first

    # A changed V5 configuration must not be hidden by the static V6 marker.
    changed_options = dict(options)
    changed_options["max_probes"] = 12
    changed = module.apply(first, options=changed_options)
    assert changed != first
    assert '"maxProbes":12' in changed
    assert '"maxProbes":20' not in changed
    assert module.apply(changed, options=changed_options) == changed
    assert changed.count(module.MARKER) == 1
    assert module.NEW in changed

    # Durable/LKG reapplication can append a freshly force-rewrapped target-media
    # adapter after an already-materialized sanitizer. Reapplying V6 must move
    # the sanitizer IIFE after that target-media layer so final media is probed.
    stale_order = first.rstrip() + "\n/* NUVIO_TV_TARGET_MEDIA_V3:fixture */\n"
    relocated = module.apply(stale_order, options=options)
    sanitizer_pos = relocated.find(module.SANITIZER_PREFIX)
    target_pos = relocated.rfind("/* NUVIO_TV_TARGET_MEDIA_V3:fixture */")
    assert target_pos >= 0 and sanitizer_pos > target_pos, (target_pos, sanitizer_pos)
    assert relocated.count(module.SANITIZER_PREFIX) == 1
    assert relocated.count(module.MARKER) == 1
    assert module.apply(relocated, options=options) == relocated

    print("fail-closed all-URL stream sanitizer tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
