#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
prepare = (ROOT / "scripts/prepare_native_client_validation.py").read_text(encoding="utf-8")
tv_suite = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text(encoding="utf-8")
targeted_workflow = (ROOT / ".github/workflows/native-corpus-device-targeted.yml").read_text(encoding="utf-8")
target_media_entry = (ROOT / "scripts/provider_patches/nuvio_tv_target_media_v4.py").read_text(encoding="utf-8")
target_media = (ROOT / "scripts/provider_patches/nuvio_tv_target_media_v5.py").read_text(encoding="utf-8")

# Historical positive sentinel: StreamZo must continue resolving Mon Ninja et
# moi 3 through the real site -> player/embed -> final-media chain on Desktop.
assert "StreamZo must keep resolving Mon ninja et moi 3 on Desktop" in prepare
assert "StreamZo Desktop must expose HLS" in prepare

# Android TV remains independently observable, but the old one-shot final runner
# is retired. The standard Lab is nonblocking and type-bounded; exact StreamZo /
# Mon Ninja regression evidence remains available through the targeted corpus lane.
assert "FIELD_TV_STREAMZO_COMPATIBILITY status=empty expected=known_gap" in prepare
assert "FIELD_TV_STREAMZO_COMPATIBILITY status=resolved expected=known_gap_improved" in prepare
assert "mon-ninja-et-moi-3" in targeted_workflow
assert 'TARGET_PROVIDER="${NIAKVIO_TARGET_PROVIDER:-declared-type}"' in tv_suite
assert 'TARGET_FIXTURE="${NIAKVIO_TARGET_FIXTURE:-}"' in tv_suite
assert 'PROVIDER_ARGS=(--provider "$TARGET_PROVIDER")' in tv_suite
assert "NIAKVIO_REQUIRE_READER_SUCCESS" in tv_suite

# Provider overrides intentionally retain the stable V4 patch path, but V4 is
# now a compatibility facade over V5. Static contract validation must inspect
# the effective implementation instead of mistaking delegation for capability
# loss.
assert 'nuvio_tv_target_media_v5.py' in target_media_entry

# Root compatibility fix: the pinned NuvioTV fetch bridge exposes text/json but
# no arrayBuffer. Target-media traversal must therefore prove textual HLS via
# Response.text() while keeping binary proof strict on richer runtimes.
assert "NUVIO_TV_TEXT_ONLY_FETCH_COMPAT_V1" in target_media
assert 'typeof r.arrayBuffer==="function"' in target_media
assert 'typeof r.text==="function"' in target_media
assert 'text=String(await r.text()||"").slice(0,300000)' in target_media

# V5 additionally owns the site -> player -> media request context required by
# Media3/OkHttp TV playback.
assert "NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT" in target_media
assert "captureCookies" in target_media
assert "cookieHeader" in target_media
assert 'setHeader(out,"Referer",ref)' in target_media
assert 'setHeader(out,"Origin",o)' in target_media

# Mobile remains independently observed; targeted TV evidence must not silently
# make Mobile failures equivalent to TV compatibility failures.
assert "FIELD_MOBILE_STREAMZO_COMPATIBILITY status=empty expected=diagnostic" in prepare

print("StreamZo native platform contract tests passed")
