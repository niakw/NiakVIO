#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = load("native_player_diagnostics_codegen", "scripts/native_player_diagnostics_codegen.py")
finalizer = load("finalize_native_android_reader_source", "scripts/finalize_native_android_reader_source.py")
PLAYER_REACH_GATE = ROOT / "scripts/gate_native_player_reached.cjs"


def source(client: str) -> str:
    return f'''package example\n\nimport android.util.Log\nimport androidx.test.platform.app.InstrumentationRegistry\nimport org.junit.Test\n\nclass Sample {{\n    private fun b64(v: Any?) = ""\n    private fun hostOnly(v: String) = ""\n    private fun probeTransport(url: String, headers: Map<String,String>?) = TODO()\n\n    @Test\n    fun run() {{\n        val fixtureSlug = "sinners"\n        val provider = object {{ val id = "MOVIESDRIVE" }}\n        val rows = emptyList<dynamic>()\n                rows.firstOrNull()?.let {{ row ->\n                    val probe = probeTransport(row.url, row.headers)\n                    emit("FIELD_NATIVE_TRANSPORT client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=${{probe.state}} kind=${{probe.kind}} status=${{probe.status}} content_type64=${{b64(probe.contentType)}} extm3u=${{probe.extm3u}} audio_track_count=${{probe.audioTrackCount}} audio_track_languages64=${{b64(probe.audioTrackLanguages)}} subtitle_track_count=${{probe.subtitleTrackCount}} subtitle_track_languages64=${{b64(probe.subtitleTrackLanguages)}} audio_variant_matrix64=${{b64(probe.audioVariantMatrix)}} subtitle_variant_matrix64=${{b64(probe.subtitleVariantMatrix)}} variant_heights64=${{b64(probe.variantHeights)}} variant_codecs64=${{b64(probe.variantCodecs)}} duration_seconds=${{probe.durationSeconds ?: 0.0}} host64=${{b64(probe.host)}} media_hint64=${{b64(probe.mediaHint)}}")\n                }}\n    }}\n    private fun emit(v: String) {{}}\n}}\n'''


tv_generated = mod.augment_android_test(source("tv"), client="tv", expected_duration_minutes=137, max_player_probes=3)
tv = finalizer.finalize_source(tv_generated, "tv")
assert "com.nuvio.tv.MainActivity" in tv
assert "NuvioNavHost" in tv
assert "Screen.Player.createRoute" in tv
assert "LastPlaybackDiagnostics" in tv
assert "PlayerSettingsDataStore" in tv
assert "nuvio-tv-production" in tv
assert "rows.take(3)" in tv
assert "probeNativePlayer(row.url, row.headers, row.type, 137)" in tv
assert "ExoPlayer.Builder" not in tv
assert "PlayerPlaybackNetworking.createDataSourceFactory" not in tv
assert "FIELD_NATIVE_PLAYER_ENTRY client=tv" in tv
assert "FIELD_NATIVE_PLAYER_BEGIN client=tv" not in tv
assert "entry=nuvio-production-player" in tv
assert "production_surface=true" in tv
assert "UiDevice.getInstance(instrumentation)" in tv
assert "R.string.cd_audio_tracks" in tv
assert 'By.clazz("android.widget.RadioButton")' in tv
assert "val audioTracks = probeTvAudioTracks" in tv
assert "track.contentDescription" in tv
assert "findTvControlButton" in tv
assert "visibleTvLanguageNodes" in tv
assert 'By.text(java.util.regex.Pattern.compile(".+"))' in tv
assert "maxOf(radioRows.size, languages.size)" in tv
assert "visibleLanguages.first().second.click()" in tv
assert "Compose TV exposes Role.RadioButton inconsistently" in tv
assert "device.wait(Until.findObject(By.desc(label)), 500L)" in tv
assert "androidx.test.uiautomator.UiObject2?" in tv
assert 'Until.hasObject(By.clazz("android.widget.RadioButton")), 1200L' in tv
assert "Until.hasObject(By.text(builtIn)), 2500L" in tv
assert "normalizeTvVisibleLanguage" in tv
assert "Locale.getAvailableLocales()" in tv
assert "locale.getDisplayLanguage(java.util.Locale.ENGLISH)" in tv
assert r'Regex("""(^|[^\\p{L}])${Regex.escape(alias)}([^\\p{L}]|$)""")' in tv
assert r'Regex("""(^|[^\\\\p{L}])${Regex.escape(alias)}([^\\\\p{L}]|$)""")' not in tv
assert "locale.isO3Language.equals(direct" in tv
assert "audio_track_count=${reader.audioTrackCount}" in tv
assert "subtitle_track_count=${reader.subtitleTrackCount}" in tv
assert "video_height=${reader.videoHeight}" in tv
assert "diagnostic_first_frame_ms=${reader.diagnosticFirstFrameMs}" in tv
assert "diagnostic_played=${reader.diagnosticPlayed}" in tv
assert "diagnostic_late_format=${reader.diagnosticLateFormat}" in tv
assert "initialDiagnostics.videoResolution.isNullOrBlank()" in tv
assert "withTimeoutOrNull(0L)" in tv
assert "diagnosticFirstFrameMs = diagnostics.firstFrameMs" in tv
# The bounded late-format second observation belongs only to the exact-byte
# native candidate oracle. Normal cohorts must not pay a per-provider wait.
old_candidate_sha = os.environ.get("NIAKVIO_NATIVE_CANDIDATE_SHA256")
try:
    os.environ["NIAKVIO_NATIVE_CANDIDATE_SHA256"] = "a1" * 32
    tv_candidate = finalizer.finalize_source(
        mod.augment_android_test(source("tv"), client="tv", expected_duration_minutes=137), "tv"
    )
    assert "withTimeoutOrNull(4500L)" in tv_candidate
    assert "diagnosticLateFormat = diagnostics !== initialDiagnostics" in tv_candidate
    assert 'row.result.startsWith("Error", ignoreCase = true)' in tv_candidate
finally:
    if old_candidate_sha is None:
        os.environ.pop("NIAKVIO_NATIVE_CANDIDATE_SHA256", None)
    else:
        os.environ["NIAKVIO_NATIVE_CANDIDATE_SHA256"] = old_candidate_sha
assert 'diagnosticPlayed = diagnostics.result.startsWith("Played", ignoreCase = true)' in tv
assert "R.string.cd_subtitles" in tv
assert "R.string.subtitle_built_in" in tv
assert "diagnostics.videoResolution" in tv
# Kotlin triple-quoted regex is raw; a double backslash matches a literal
# "\d" instead of 1920x1080. Assert both the immediate and late-format readers.
assert tv.count(r'Regex("""(\d{2,5})x(\d{2,5})""")') == 2
assert r'Regex("""(\\d{2,5})x(\\d{2,5})""")' not in tv
assert "audio_track_count=${transport.audioTrackCount}" in tv
assert "subtitle_variant_matrix64=${b64(transport.subtitleVariantMatrix)}" in tv
assert "variant_codecs64=${b64(transport.variantCodecs)}" in tv

# Production Nuvio receives the provider output. Any sanitation/normalization after
# that belongs to Nuvio itself and is deliberately not reimplemented by the lab.
assert "headers = headers" in tv
assert 'playbackHeaders["Range"]' not in tv
assert "--add-opens" not in tv
assert "usesCleartextTraffic" not in tv

reader_call = tv.index("val reader = probeNativePlayer(row.url, row.headers, row.type, 137)")
transport_call = tv.index("val transport = probeTransport(row.url, row.headers)")
assert reader_call < transport_call

mobile_generated = mod.augment_android_test(source("mobile"), client="mobile", expected_duration_minutes=137, max_player_probes=2)
mobile = finalizer.finalize_source(mobile_generated, "mobile")
mobile_compare_generated = mod.augment_android_test(
    source("mobile"),
    client="mobile",
    expected_duration_minutes=137,
    max_player_probes=1,
    compare_engines=True,
)
mobile_compare = finalizer.finalize_source(mobile_compare_generated, "mobile")
assert "com.nuvio.app.MainActivity" in mobile
assert "PlatformPlayerSurface" in mobile
assert "nuvio-mobile-production" in mobile
assert "production_surface=true" in mobile
assert "forcedEngine: AndroidPlaybackEngine? = null" in mobile
assert "playbackEngine = forcedEngine" in mobile
assert "FIELD_NATIVE_ENGINE_COMPARE" not in mobile
assert "rows.take(2)" in mobile
assert "probeNativePlayer(row.url, row.headers, row.type, 137)" in mobile
assert "ExoPlayer.Builder" not in mobile
assert "PlatformPlaybackDataSourceFactory.create" not in mobile
assert "sourceHeaders = headers.orEmpty()" in mobile
assert "Auto mode intentionally emits null" in mobile
assert 'Intent().setClassName(' in mobile
assert "queryIntentActivities(launcherQuery, 0)" in mobile
assert "launchActivity.activityInfo.packageName," in mobile
assert "launchActivity.activityInfo.name," in mobile
assert "MainActivity::class.java.packageName," not in mobile
assert "context.packageName," not in mobile
assert '"com.nuviodebug.com",\n                MainActivity::class.java.name' not in mobile
assert "MainActivity::class.java.name" in mobile
assert "Intent(context, MainActivity::class.java)" not in mobile
assert "getLaunchIntentForPackage(context.packageName)" not in mobile
assert "PlayerEngineController" in mobile
assert "controllerRef.set(controller)" in mobile
assert "getAudioTracks()" in mobile
assert "getSubtitleTracks()" in mobile
assert "controllerRef.get()?.playbackEngine?.name" in mobile
assert "snapshot?.videoHeight" in mobile
assert "audio_track_count=${reader.audioTrackCount}" in mobile
assert "subtitle_track_count=${reader.subtitleTrackCount}" in mobile
assert "video_height=${reader.videoHeight}" in mobile
assert "audio_track_languages64=${b64(reader.audioTrackLanguages)}" in mobile
assert "audio_track_count=${transport.audioTrackCount}" in mobile
assert "audio_track_languages64=${b64(transport.audioTrackLanguages)}" in mobile
assert "FIELD_NATIVE_PLAYER_ENTRY client=mobile" in mobile
assert "FIELD_NATIVE_PLAYER_BEGIN client=mobile" not in mobile
assert mobile.index("val reader = probeNativePlayer(row.url, row.headers, row.type, 137)") < mobile.index("val transport = probeTransport(row.url, row.headers)")
assert "FIELD_NATIVE_ENGINE_COMPARE client=mobile" in mobile_compare
assert "AndroidPlaybackEngine.ExoPlayer" in mobile_compare
assert "AndroidPlaybackEngine.Libmpv" in mobile_compare
assert "same_source=true" in mobile_compare
assert "comparison_order=post_auto" in mobile_compare
auto_call = mobile_compare.index("val reader = probeNativePlayer(row.url, row.headers, row.type, 137)")
exo_call = mobile_compare.index("val exoReader = probeNativePlayer(")
libmpv_call = mobile_compare.index("val libmpvReader = probeNativePlayer(")
compare_emit = mobile_compare.index("FIELD_NATIVE_ENGINE_COMPARE client=mobile")
compare_transport = mobile_compare.index("val transport = probeTransport(row.url, row.headers)")
assert auto_call < exo_call < libmpv_call < compare_emit < compare_transport


def complete_reach_evidence(lines: list[str]) -> list[str]:
    player = next((line for line in lines if line.startswith("FIELD_NATIVE_PLAYER ")), "")
    parsed = dict(
        token.split("=", 1)
        for token in player.split()[1:]
        if "=" in token
    )
    client = parsed.get("client", "test")
    fixture = parsed.get("fixture", "sinners")
    provider = parsed.get("provider64", parsed.get("provider", "x"))
    request_type = parsed.get("request_type", "movie")
    return [
        f"FIELD_NATIVE_CORPUS_BEGIN client={client} fixture={fixture} providers=1",
        f"FIELD_NATIVE_RESULT client={client} fixture={fixture} provider64={provider} request_type={request_type} route_mode=declared state=ok count=0",
        *lines,
        f"FIELD_NATIVE_CORPUS_END client={client} fixture={fixture} providers=1",
    ]


def reach_gate(lines: list[str], *, blocking: bool = False, complete: bool = True):
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "reader.log"
        evidence = complete_reach_evidence(lines) if complete else lines
        log.write_text("\n".join(evidence) + "\n", encoding="utf-8")
        env = os.environ.copy()
        if blocking:
            env["NIAKVIO_NATIVE_PLAYER_GATE_BLOCKING"] = "1"
        else:
            env.pop("NIAKVIO_NATIVE_PLAYER_GATE_BLOCKING", None)
        return subprocess.run(
            ["node", str(PLAYER_REACH_GATE), str(log)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=env,
        )


# A setup attempt is not a reader reach, even if a terminal FIELD_NATIVE_PLAYER row
# exists. With a structurally complete corpus it remains negative evidence owned by
# the Brain rather than a Lab-infrastructure failure. Strict callers can explicitly
# restore exit 4.
no_launch_lines = [
    "FIELD_NATIVE_PLAYER client=mobile fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=error engine=nuvio-mobile http_status=0 failure_stage=player_setup error_code=NO_LAUNCH_INTENT"
]

# The fail-closed corpus rule remains independently enforced: an isolated player row
# is incomplete evidence and must never be downgraded to ordinary Brain evidence.
incomplete_no_launch = reach_gate(no_launch_lines, complete=False)
assert incomplete_no_launch.returncode == 5, (incomplete_no_launch.stdout, incomplete_no_launch.stderr)
assert "incomplete_native_evidence" in incomplete_no_launch.stderr
assert "blocking=true" in incomplete_no_launch.stderr
assert "owner=lab_infra" in incomplete_no_launch.stderr

no_launch = reach_gate(no_launch_lines)
assert no_launch.returncode == 0, (no_launch.stdout, no_launch.stderr)
assert "production_player_never_reached" in no_launch.stderr
assert "setup_rejected=1" in no_launch.stderr
assert "blocking=false" in no_launch.stderr
assert "owner=brain" in no_launch.stderr

strict_no_launch = reach_gate(no_launch_lines, blocking=True)
assert strict_no_launch.returncode == 4, (strict_no_launch.stdout, strict_no_launch.stderr)
assert "blocking=true" in strict_no_launch.stderr
assert "owner=brain" in strict_no_launch.stderr

setup_only = reach_gate([
    "FIELD_NATIVE_PLAYER client=mobile fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=error engine=nuvio-mobile-production http_status=0 failure_stage=player_setup error_code=WRONG_ACTIVITY"
])
assert setup_only.returncode == 0, (setup_only.stdout, setup_only.stderr)
assert "setup_rejected=1" in setup_only.stderr
assert "blocking=false" in setup_only.stderr
assert "owner=brain" in setup_only.stderr

real_player_error = reach_gate([
    "FIELD_NATIVE_PLAYER client=tv fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=error engine=nuvio-tv-production production_surface=true http_status=0 failure_stage=player error_code=HTTP_403"
])
assert real_player_error.returncode == 0, (real_player_error.stdout, real_player_error.stderr)
assert "production_playback_never_verified" in real_player_error.stderr
assert "production=1" in real_player_error.stderr
assert "playback_verified=0" in real_player_error.stderr
assert "playback_failed=1" in real_player_error.stderr

strict_player_error = reach_gate([
    "FIELD_NATIVE_PLAYER client=tv fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=error engine=nuvio-tv-production production_surface=true http_status=403 failure_stage=player error_code=HTTP_403"
], blocking=True)
assert strict_player_error.returncode == 4, (strict_player_error.stdout, strict_player_error.stderr)
assert "production_playback_never_verified" in strict_player_error.stderr

mobile_real_engine = reach_gate([
    "FIELD_NATIVE_PLAYER client=mobile fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=ready engine=ExoPlayer production_surface=true http_status=0 failure_stage=none video_width=1920 video_height=1080"
], blocking=True)
assert mobile_real_engine.returncode == 0, (mobile_real_engine.stdout, mobile_real_engine.stderr)
assert "playback_verified=1" in mobile_real_engine.stdout
assert "verified_clients=mobile:1" in mobile_real_engine.stdout

# A READY/23-minute metadata snapshot was observed for French-Manga on
# Android TV even though direct HLS transport answered 403 and no video
# dimensions were recorded. A nonzero duration is NOT video-track proof.
# Do not turn this native failure into a fake player/media FULL.
tv_ready_unproven = reach_gate([
    "FIELD_NATIVE_PLAYER client=tv fixture=jujutsu-kaisen-s01e01 "
    "provider64=x request_type=anime route_mode=declared index=0 "
    "state=ready engine=nuvio-tv-production production_surface=true "
    "http_status=0 failure_stage=none duration_seconds=1435.007 "
    "video_width=0 video_height=0 audio_track_count=0 "
    "diagnostic_first_frame_ms=500 diagnostic_played=true"
], blocking=True)
assert tv_ready_unproven.returncode == 4, (
    tv_ready_unproven.stdout, tv_ready_unproven.stderr,
)
assert "production_playback_never_verified" in tv_ready_unproven.stderr
assert "playback_verified=0" in tv_ready_unproven.stderr

tv_ready_partial = reach_gate([
    "FIELD_NATIVE_PLAYER client=tv fixture=jujutsu-kaisen-s01e01 "
    "provider64=x request_type=anime route_mode=declared index=0 "
    "state=ready engine=nuvio-tv-production production_surface=true "
    "http_status=0 failure_stage=none duration_seconds=1435.007 "
    "video_width=0 video_height=0 audio_track_count=0"
])
assert tv_ready_partial.returncode == 0
assert "production_playback_never_verified" in tv_ready_partial.stderr

short_media = reach_gate([
    "FIELD_NATIVE_PLAYER client=desktop fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=short_media engine=nuvio-desktop-production production_surface=true http_status=0 failure_stage=duration_identity"
], blocking=True)
assert short_media.returncode == 4, (short_media.stdout, short_media.stderr)
assert "production_playback_never_verified" in short_media.stderr

rows = [{"id": "A"}, {"id": "MOVIESDRIVE"}, {"id": "B"}]
assert [row["id"] for row in mod.filter_staged_providers(rows, "moviesdrive")] == ["MOVIESDRIVE"]
assert mod.filter_staged_providers(rows, "") == rows
try:
    mod.filter_staged_providers(rows, "missing")
except ValueError:
    pass
else:
    raise AssertionError("unknown targeted provider must fail closed")

print("native player diagnostics codegen tests passed")
