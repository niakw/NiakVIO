#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
prepare = (ROOT / "scripts/prepare_native_client_validation.py").read_text(encoding="utf-8")
runner = (ROOT / "scripts/run_final_native_android_lab.sh").read_text(encoding="utf-8")
target_media = (ROOT / "scripts/provider_patches/nuvio_tv_target_media_v4.py").read_text(encoding="utf-8")

# Historical positive sentinel: StreamZo must continue resolving Mon Ninja et
# moi 3 through the real site -> player/embed -> final-media chain on Desktop.
assert "StreamZo must keep resolving Mon ninja et moi 3 on Desktop" in prepare
assert "StreamZo Desktop must expose HLS" in prepare

# Android TV is now a hard publication target. The Kotlin fixture still emits
# raw observations, while the native runner turns an empty/non-HLS StreamZo
# result into a blocking failure.
assert "TV_STREAMZO_COUNT" in runner
assert "TV_STREAMZO_HLS" in runner
assert "FIELD_TV_STREAMZO_SENTINEL status=failed expected=resolved path=site_player_media" in runner
assert "FIELD_TV_STREAMZO_SENTINEL status=resolved expected=resolved path=site_player_media" in runner
assert "StreamZo must resolve Mon ninja et moi 3 through site -> player -> media on Android TV" in runner
assert "TV_STATUS=96" in runner

# Root compatibility fix: the pinned NuvioTV fetch bridge exposes text/json but
# no arrayBuffer. Target-media traversal must therefore prove textual HLS via
# Response.text() while keeping binary proof strict on richer runtimes.
assert "NUVIO_TV_TEXT_ONLY_FETCH_COMPAT_V1" in target_media
assert 'typeof r.arrayBuffer==="function"' in target_media
assert 'typeof r.text==="function"' in target_media
assert 'text=String(await r.text()||"").slice(0,300000)' in target_media

# Mobile remains independently observed; this TV gate must not silently make
# Mobile failures equivalent to TV compatibility failures.
assert "FIELD_MOBILE_STREAMZO_COMPATIBILITY status=empty expected=diagnostic" in prepare

print("StreamZo native platform contract tests passed")
