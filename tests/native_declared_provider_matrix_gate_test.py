#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "gate_native_declared_provider_matrix.py"


def run_gate(log_text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = root / "manifest.json"
        corpus = root / "corpus.json"
        log = root / "desktop.log"
        manifest.write_text(
            json.dumps(
                {
                    "scrapers": [
                        {"id": "AnimeOnly", "supportedTypes": ["anime"]},
                    ]
                }
            ),
            encoding="utf-8",
        )
        corpus.write_text(
            json.dumps(
                {
                    "native_reader_acceptance": {
                        "fixture_by_type": {
                            "movie": "interstellar",
                            "tv": "breaking-bad-s01e01",
                            "anime": "jujutsu-kaisen-s01e01",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        log.write_text(log_text, encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(GATE),
                "--client",
                "desktop",
                "--manifest",
                str(manifest),
                "--corpus",
                str(corpus),
                str(log),
            ],
            text=True,
            capture_output=True,
            check=False,
        )


def main() -> int:
    transported_as_tv = run_gate(
        "\n".join(
            [
                "FIELD_NATIVE_PROVIDER_BEGIN client=desktop fixture=jujutsu-kaisen-s01e01 provider=AnimeOnly request_type=tv",
                "FIELD_NATIVE_RESULT client=desktop fixture=jujutsu-kaisen-s01e01 provider=AnimeOnly request_type=tv count=0",
            ]
        )
        + "\n"
    )
    assert transported_as_tv.returncode == 0, transported_as_tv.stdout + transported_as_tv.stderr
    assert "state=passed" in transported_as_tv.stdout, transported_as_tv.stdout

    missing_terminal = run_gate(
        "FIELD_NATIVE_PROVIDER_BEGIN client=desktop fixture=jujutsu-kaisen-s01e01 provider=AnimeOnly request_type=tv\n"
    )
    assert missing_terminal.returncode == 1, missing_terminal.stdout + missing_terminal.stderr
    assert "reason=missing_terminal" in missing_terminal.stdout, missing_terminal.stdout

    incoherent_transport = run_gate(
        "\n".join(
            [
                "FIELD_NATIVE_PROVIDER_BEGIN client=desktop fixture=jujutsu-kaisen-s01e01 provider=AnimeOnly request_type=movie",
                "FIELD_NATIVE_RESULT client=desktop fixture=jujutsu-kaisen-s01e01 provider=AnimeOnly request_type=movie count=0",
            ]
        )
        + "\n"
    )
    assert incoherent_transport.returncode == 1, incoherent_transport.stdout + incoherent_transport.stderr
    assert "reason=missing_begin" in incoherent_transport.stdout, incoherent_transport.stdout
    assert "reason=undeclared_route" in incoherent_transport.stdout, incoherent_transport.stdout

    print("native declared provider matrix gate tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
