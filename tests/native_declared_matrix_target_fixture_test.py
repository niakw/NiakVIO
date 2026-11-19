#!/usr/bin/env python3
"""Focused real-reader suites may not claim missing unrequested lanes or FULL."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/gate_native_declared_provider_matrix.py"

with tempfile.TemporaryDirectory(prefix="niakvio-native-target-matrix-") as directory:
    root = Path(directory)
    manifest = root / "manifest.json"
    corpus = root / "nuvio-client-lab.json"
    scope = root / "scope.json"
    log = root / "tv-native-corpus-jujutsu-kaisen-s01e01.log"
    manifest.write_text(json.dumps({"scrapers": [
        {"id": "FRENCH-MANGA", "enabled": True, "supportedTypes": ["anime", "tv"]},
        {"id": "SADISFLIX", "enabled": True, "supportedTypes": ["movie", "tv"]},
        {"id": "DISABLED", "enabled": False, "supportedTypes": ["anime"]},
    ]}), encoding="utf-8")
    corpus.write_text(json.dumps({
        "native_reader_acceptance": {
            "fixture_by_type": {
                "movie": "interstellar",
                "tv": "spartacus-s00e01",
                "anime": "jujutsu-kaisen-s01e01",
            },
        },
    }), encoding="utf-8")
    scope.write_text(json.dumps({
        "providerCount": 1, "hubCount": 1,
        "rows": [{"provider": "FRENCH-MANGA", "manifestId": "FRENCH-MANGA"}],
    }), encoding="utf-8")
    log.write_text(
        "FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=jujutsu-kaisen-s01e01 "
        "provider=FRENCH-MANGA request_type=anime\n"
        "FIELD_NATIVE_RESULT client=tv fixture=jujutsu-kaisen-s01e01 "
        "provider=FRENCH-MANGA request_type=anime count=2\n"
        "FIELD_NATIVE_PROVIDER_END client=tv fixture=jujutsu-kaisen-s01e01 "
        "provider=FRENCH-MANGA request_type=anime\n",
        encoding="utf-8",
    )
    base = [
        sys.executable, str(SCRIPT), "--client", "tv", "--manifest", str(manifest),
        "--corpus", str(corpus), "--scope-matrix", str(scope),
    ]

    def run(extra: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(base + extra + [str(log)],
                              cwd=ROOT, capture_output=True, text=True, timeout=20)

    full = run([])
    assert full.returncode == 1, (full.stdout, full.stderr)
    assert "mode=full" in full.stdout and "type=tv" in full.stdout
    assert "status=PARTIAL" in full.stdout, full.stdout

    targeted = run(["--target-fixture", "jujutsu-kaisen-s01e01"])
    assert targeted.returncode == 0, (targeted.stdout, targeted.stderr)
    assert "state=passed" in targeted.stdout and "mode=targeted" in targeted.stdout
    assert "routes=1" in targeted.stdout and "anime=1" in targeted.stdout
    assert "status=TARGETED_CANDIDATE" in targeted.stdout, targeted.stdout
    assert "FULL=0" in targeted.stdout and "PARTIAL=0" in targeted.stdout

    unrelated = run(["--target-fixture", "interstellar"])
    assert unrelated.returncode != 0
    assert "no requested fixture lane" in (unrelated.stdout + unrelated.stderr)

    unknown = run(["--target-fixture", "unknown-fixture-xyz"])
    assert unknown.returncode != 0
    assert "unknown targeted native fixture lane" in (unknown.stdout + unknown.stderr)

    # Even in targeted mode, the requested lane still needs a real begin and
    # result/error terminal. Never hide missing executions by narrowing scope.
    log.write_text("FIELD_NATIVE_PROVIDER_BEGIN client=tv "
                   "provider=FRENCH-MANGA request_type=anime\n", encoding="utf-8")
    incomplete = run(["--target-fixture", "jujutsu-kaisen-s01e01"])
    assert incomplete.returncode == 1
    assert "reason=missing_terminal" in incomplete.stdout
    assert "status=TARGETED_UNOBSERVED" in incomplete.stdout

    # A build/Gradle failure may leave a readable log but never launch the
    # provider. It is a missing native execution, NOT a catalogue search miss.
    log.write_text("Gradle: resolver missing transitive dependency\n", encoding="utf-8")
    not_started = run(["--target-fixture", "jujutsu-kaisen-s01e01"])
    assert not_started.returncode == 1, (not_started.stdout, not_started.stderr)
    assert "missing_begin=1" in not_started.stdout
    assert "status=TARGETED_UNOBSERVED" in not_started.stdout
    assert "TARGETED_CATALOG_MISS=0" in not_started.stdout

    # A genuine executed 0-stream return still retains the sampled-catalogue
    # uncertainty label, distinct from missing execution and technical error.
    log.write_text(
        "FIELD_NATIVE_PROVIDER_BEGIN client=tv provider=FRENCH-MANGA request_type=anime\n"
        "FIELD_NATIVE_RESULT client=tv provider=FRENCH-MANGA request_type=anime count=0\n",
        encoding="utf-8",
    )
    catalog_zero = run(["--target-fixture", "jujutsu-kaisen-s01e01"])
    assert catalog_zero.returncode == 0, (catalog_zero.stdout, catalog_zero.stderr)
    assert "status=TARGETED_CATALOG_MISS" in catalog_zero.stdout
    assert "TARGETED_UNOBSERVED=0" in catalog_zero.stdout

    log.write_text(
        "FIELD_NATIVE_PROVIDER_BEGIN client=tv provider=FRENCH-MANGA request_type=anime\n"
        "FIELD_NATIVE_ERROR client=tv provider=FRENCH-MANGA request_type=anime error=runtime\n",
        encoding="utf-8",
    )
    technical = run(["--target-fixture", "jujutsu-kaisen-s01e01"])
    assert technical.returncode == 0, (technical.stdout, technical.stderr)
    assert "status=TARGETED_TECHNICAL" in technical.stdout
    assert "TARGETED_CATALOG_MISS=0" in technical.stdout

workflow = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text("utf-8")
assert "MATRIX_FIXTURE_ARGS" in workflow
assert '"${MATRIX_FIXTURE_ARGS[@]}"' in workflow
assert "TARGET_FIXTURE" in workflow
print("Targeted native declared-route matrix preserves strict coverage and avoids false FULL")
