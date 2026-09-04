#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def replace(path: str, old: str, new: str, expected: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: anchor count={count} expected={expected}: {old[:120]!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


def replace_all(path: str, old: str, new: str, minimum: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count < minimum:
        raise SystemExit(f"{path}: anchor count={count} minimum={minimum}: {old[:120]!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    # One native wall-clock budget.
    replace(".github/triggers/nuvio-client-lab.json", '"provider_timeout_ms": 40000', '"provider_timeout_ms": 25000')
    replace(".github/triggers/nuvio-client-lab.json", '"retry_provider_timeout_ms": 40000', '"retry_provider_timeout_ms": 25000')
    replace(".github/triggers/nuvio-client-lab.json", '"playback_timeout_ms": 18000', '"playback_timeout_ms": 25000')
    replace_all(
        ".github/workflows/native-mobile-android-reader.yml",
        'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS: "15000"',
        'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS: "25000"',
    )

    # Anime remains a logical selection type; the Nuvio runtime ABI receives tv.
    media = Path("scripts/native_media_type_contract.py")
    media_text = media.read_text(encoding="utf-8")
    if "def fixture_runtime_media_type(" in media_text:
        raise SystemExit("native media runtime projection already exists unexpectedly")
    media_text += '''\n\ndef provider_runtime_media_type(\n    value: Any,\n    *,\n    category: Any = None,\n    metadata: dict[str, Any] | None = None,\n) -> str:\n    canonical = canonical_media_type(value, category=category, metadata=metadata)\n    return "tv" if canonical == "anime" else canonical\n\n\ndef fixture_runtime_media_type(fixture: dict[str, Any]) -> str:\n    # Provider selection still consumes fixture_media_type() so anime-only\n    # providers remain eligible. The Nuvio plugin ABI itself is movie|tv.\n    logical = fixture_media_type(fixture)\n    return "tv" if logical == "anime" else logical\n'''
    media.write_text(media_text, encoding="utf-8")

    replace(
        "scripts/prepare_native_corpus_validation.py",
        "from native_media_type_contract import fixture_media_type  # noqa: E402",
        "from native_media_type_contract import fixture_runtime_media_type  # noqa: E402",
    )
    replace(
        "scripts/prepare_native_corpus_validation.py",
        'provider_timeout_ms = max(5_000, min(int(config.get("provider_timeout_ms") or 40_000), 120_000))',
        'provider_timeout_ms = max(5_000, min(int(config.get("provider_timeout_ms") or 25_000), 120_000))',
    )
    replace(
        "scripts/prepare_native_corpus_validation.py",
        '"media_type": kotlin_string(fixture_media_type(fixture)),',
        '"media_type": kotlin_string(fixture_runtime_media_type(fixture)),',
    )
    replace(
        "scripts/prepare_native_corpus_validation.py",
        '"season": "null" if season in (None, "") else str(int(season)),\n        "episode": "null" if episode in (None, "") else str(int(episode)),',
        '"season": "null" if season is None or season == "" else str(int(season)),\n        "episode": "null" if episode is None or episode == "" else str(int(episode)),',
    )
    replace(
        "scripts/prepare_native_corpus_validation.py",
        'os.environ.get("NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS", "15000")',
        'os.environ.get("NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS", "25000")',
    )
    replace(
        "scripts/prepare_native_corpus_validation.py",
        "android_timeout_ms = 15_000",
        "android_timeout_ms = 25_000",
    )
    replace(
        "scripts/prepare_native_corpus_validation.py",
        '''                val rows = try {{\n                    providerFuture.get({f['provider_timeout_ms']}L, java.util.concurrent.TimeUnit.MILLISECONDS)\n                }} catch (timeout: java.util.concurrent.TimeoutException) {{\n                    providerFuture.cancel(true)\n                    throw RuntimeException("provider_hard_timeout_ms={f['provider_timeout_ms']}", timeout)\n                }} finally {{\n                    providerFuture.cancel(true)\n                    providerExecutor.shutdownNow()\n                }}\n''',
        '''                var providerTimedOut = false\n                val rows = try {{\n                    providerFuture.get({f['provider_timeout_ms']}L, java.util.concurrent.TimeUnit.MILLISECONDS)\n                }} catch (timeout: java.util.concurrent.TimeoutException) {{\n                    providerTimedOut = true\n                    providerFuture.cancel(true)\n                    throw RuntimeException("provider_hard_timeout_ms={f['provider_timeout_ms']}", timeout)\n                }} finally {{\n                    if (providerTimedOut) {{\n                        providerExecutor.shutdownNow()\n                    }} else {{\n                        providerExecutor.shutdown()\n                    }}\n                }}\n''',
    )

    # Mobile player observation settles once: success cannot be overwritten by a late error.
    replace(
        "scripts/native_player_diagnostics_codegen.py",
        '        val errorRef = AtomicReference<String?>(null)\n',
        '        val errorRef = AtomicReference<String?>(null)\n        val terminalStateRef = AtomicReference<String?>(null)\n',
    )
    replace(
        "scripts/native_player_diagnostics_codegen.py",
        '''                            if (snapshot.isEnded || (!snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || snapshot.durationMs > 0L))) {\n                                terminal.countDown()\n                            }\n''',
        '''                            if ((snapshot.isEnded || (!snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || snapshot.durationMs > 0L))) &&\n                                terminalStateRef.compareAndSet(null, "success")\n                            ) {\n                                terminal.countDown()\n                            }\n''',
    )
    replace(
        "scripts/native_player_diagnostics_codegen.py",
        '''                            if (!message.isNullOrBlank()) {\n                                errorRef.compareAndSet(null, message)\n                                terminal.countDown()\n                            }\n''',
        '''                            if (!message.isNullOrBlank() && terminalStateRef.compareAndSet(null, "error")) {\n                                errorRef.set(message)\n                                terminal.countDown()\n                            }\n''',
    )
    replace(
        "scripts/native_player_diagnostics_codegen.py",
        '''            terminal.await(__PLAYER_TIMEOUT_MS__L, TimeUnit.MILLISECONDS)\n            val error = errorRef.get()\n            val snapshot = snapshotRef.get()\n            if (!error.isNullOrBlank()) {\n''',
        '''            terminal.await(__PLAYER_TIMEOUT_MS__L, TimeUnit.MILLISECONDS)\n            val terminalState = terminalStateRef.get()\n            val error = errorRef.get()\n            val snapshot = snapshotRef.get()\n            if (terminalState == "error" && !error.isNullOrBlank()) {\n''',
    )
    replace(
        "scripts/native_player_diagnostics_codegen.py",
        '                shortMedia -> NativePlayerProbe("short_media", "nuvio-mobile-production", "", "", 0, "duration_identity", host, durationSeconds)\n                snapshot?.isEnded == true -> NativePlayerProbe("ended", "nuvio-mobile-production", "", "", 0, "none", host, durationSeconds)\n                snapshot != null && !snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || snapshot.durationMs > 0L) ->\n',
        '                terminalState == "success" && shortMedia -> NativePlayerProbe("short_media", "nuvio-mobile-production", "", "", 0, "duration_identity", host, durationSeconds)\n                terminalState == "success" && snapshot?.isEnded == true -> NativePlayerProbe("ended", "nuvio-mobile-production", "", "", 0, "none", host, durationSeconds)\n                terminalState == "success" && snapshot != null && !snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || snapshot.durationMs > 0L) ->\n',
    )
    replace(
        "scripts/native_player_diagnostics_codegen.py",
        '.replace("__PLAYER_TIMEOUT_MS__", "22000")',
        '.replace("__PLAYER_TIMEOUT_MS__", "25000")',
    )

    # Transport/capability diagnostics are best-effort; reader/runtime truth remains gating.
    replace(
        "scripts/analyze_native_corpus_results.cjs",
        '''// Capability probes are discovery evidence. Their failures never turn a healthy\n// declared provider contract into a regression. Only published-route anomalies\n// affect this analyzer's status.\nif (\n  declaredRuntimeErrors.length ||\n  declaredContradictions.length ||\n  transportFailures.length ||\n  readerFailures.length\n) {\n''',
        '''// Transport/capability probes are best-effort discovery evidence. They are\n// emitted and reported, but cannot turn authoritative provider/player success\n// into a regression. Runtime contradictions and reader failures still gate.\nif (\n  declaredRuntimeErrors.length ||\n  declaredContradictions.length ||\n  readerFailures.length\n) {\n''',
    )
    replace(
        "scripts/analyze_native_corpus_collection.cjs",
        "if (row.state === 'ready' && row.failure_stage === 'none') {",
        "if ((row.state === 'ready' || row.state === 'ended') && row.failure_stage === 'none') {",
    )

    # Explicitly bound common catalogue alias recovery: 3 queries x 3 base origins.
    p = Path("scripts/provider_base_store.py")
    text = p.read_text(encoding="utf-8")
    start = text.find("const searchQueries = _uniq([")
    if start < 0:
        raise SystemExit("provider_base_store.py: searchQueries anchor missing")
    suffix = "].map(_text).filter(Boolean));"
    end = text.find(suffix, start)
    if end < 0:
        raise SystemExit("provider_base_store.py: searchQueries terminator missing")
    bounded = "].map(_text).filter(Boolean)).slice(0, 3);"
    text = text[:end] + bounded + text[end + len(suffix):]
    old_loop = "for (const query of searchQueries.slice(0, 3))"
    if text.count(old_loop) != 1:
        raise SystemExit(f"provider_base_store.py: alias loop count={text.count(old_loop)}")
    text = text.replace(old_loop, "for (const query of searchQueries)", 1)
    if "const candidates = baseList.slice(0, 3);" not in text:
        raise SystemExit("provider_base_store.py: base recovery bound missing")
    p.write_text(text, encoding="utf-8")

    # Existing source-lock tests must track the new budget.
    replace(
        "tests/native_corpus_device_lab_test.py",
        'assert corpus.get("provider_timeout_ms") == 40000',
        'assert corpus.get("provider_timeout_ms") == 25000',
    )
    replace_all(
        "tests/native_corpus_device_lab_test.py",
        'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS", "15000"',
        'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS", "25000"',
    )
    replace_all(
        "tests/native_corpus_device_lab_test.py",
        'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS: "15000"',
        'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS: "25000"',
    )
    player_test = Path("tests/native_player_diagnostics_codegen_test.py")
    player_test_text = player_test.read_text(encoding="utf-8")
    if "22000" in player_test_text:
        player_test.write_text(player_test_text.replace("22000", "25000"), encoding="utf-8")

    print("one-shot native runtime migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
