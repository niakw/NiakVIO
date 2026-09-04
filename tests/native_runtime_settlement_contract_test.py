#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from native_media_type_contract import fixture_media_type, fixture_runtime_media_type
from prepare_native_corpus_validation import android_test, common_fixture_values


def main() -> int:
    corpus = json.loads((ROOT / ".github/triggers/nuvio-client-lab.json").read_text(encoding="utf-8"))
    assert corpus["provider_timeout_ms"] == 25_000
    assert corpus["retry_provider_timeout_ms"] == 25_000
    assert corpus["playback_timeout_ms"] == 25_000

    anime = {
        "slug": "anime-zero",
        "mediaType": "anime",
        "category": "anime",
        "season": 0,
        "episode": 0,
    }
    assert fixture_media_type(anime) == "anime"
    assert fixture_runtime_media_type(anime) == "tv"
    values = common_fixture_values(anime)
    assert values["media_type"] == '"tv"'
    assert values["season"] == "0"
    assert values["episode"] == "0"
    assert values["provider_timeout_ms"] == "25000"

    generated = android_test(
        anime,
        [{"id": "contract", "asset": "p000.js", "enabled": True, "logo": ""}],
        "mobile",
    )
    assert "provider_hard_timeout_ms=25000" in generated
    assert "var providerTimedOut = false" in generated
    provider_section = generated.split("var providerTimedOut = false", 1)[1].split('emit("FIELD_NATIVE_RESULT', 1)[0]
    assert "providerTimedOut = true" in provider_section
    assert "providerFuture.cancel(true)" in provider_section
    finally_tail = provider_section.split("} finally {", 1)[1]
    assert "providerFuture.cancel(true)" not in finally_tail
    assert "providerExecutor.shutdown()" in finally_tail
    assert "providerExecutor.shutdownNow()" in finally_tail

    player_codegen = (ROOT / "scripts/native_player_diagnostics_codegen.py").read_text(encoding="utf-8")
    assert 'compareAndSet(null, "success")' in player_codegen
    assert 'compareAndSet(null, "error")' in player_codegen
    assert '.replace("__PLAYER_TIMEOUT_MS__", "25000")' in player_codegen
    assert player_codegen.index("val reader = probeNativePlayer") < player_codegen.index("val transport = probeTransport")

    analyzer = (ROOT / "scripts/analyze_native_corpus_results.cjs").read_text(encoding="utf-8")
    gate = analyzer[analyzer.rfind("if (\n  declaredRuntimeErrors.length"):]
    gate = gate.split("process.exitCode = 1", 1)[0]
    assert "readerFailures.length" in gate
    assert "transportFailures.length" not in gate

    collection = (ROOT / "scripts/analyze_native_corpus_collection.cjs").read_text(encoding="utf-8")
    assert "state === 'ready' || state === 'ended'" in collection

    base_source = (ROOT / "scripts/provider_base_store.py").read_text(encoding="utf-8")
    assert "].map(_text).filter(Boolean)).slice(0, 3);" in base_source
    assert "const candidates = baseList.slice(0, 3);" in base_source
    assert "for (const query of searchQueries)" in base_source

    provenance_path = ROOT / "PROVENANCE.json"
    if provenance_path.stat().st_size > 0:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        providers = provenance.get("providers") or {}
        assert len(providers) == 96
        for provider_id, row in providers.items():
            base_file = ROOT / str(row.get("base_filename") or "")
            assert base_file.is_file(), (provider_id, base_file)
            base_text = base_file.read_text(encoding="utf-8")
            assert "].map(_text).filter(Boolean)).slice(0, 3);" in base_text, provider_id
            assert "const candidates = baseList.slice(0, 3);" in base_text, provider_id

    print("native runtime settlement contract passed: budget=25s anime_runtime=tv zero=0/0 aliases=3x3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
