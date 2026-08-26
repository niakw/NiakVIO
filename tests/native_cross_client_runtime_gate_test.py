#!/usr/bin/env python3
from __future__ import annotations

import base64
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/gate_native_cross_client_runtime.cjs"
SENTINEL = "__NIAKVIO_RUNTIME_ERROR__"


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def result(
    client: str,
    fixture: str,
    provider: str,
    count: int,
    request_type: str = "movie",
    *,
    enabled: bool = True,
) -> str:
    return (
        f"FIELD_NATIVE_RESULT client={client} fixture={fixture} provider64={b64(provider)} "
        f"request_type={request_type} route_mode=declared enabled={str(enabled).lower()} duration_ms=1 count={count}"
    )


def sentinel(client: str, fixture: str, provider: str, request_type: str = "movie") -> str:
    return (
        f"FIELD_NATIVE_ROW client={client} fixture={fixture} provider64={b64(provider)} "
        f"request_type={request_type} route_mode=declared index=0 title64={b64(SENTINEL)} "
        f"name64={b64(SENTINEL)} quality64= language64= type64={b64(SENTINEL)} host64= media_hint64="
    )


def run_gate(directory: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "node",
            str(GATE),
            "--dir",
            str(directory),
            "--require-clients",
            "mobile,tv",
            "--min-comparisons",
            "3",
            *extra,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="niakvio-cross-runtime-") as tmp:
    root = Path(tmp)
    mobile = root / "mobile-native-corpus-representative.log"
    tv = root / "tv-native-corpus-representative.log"

    # Both clients return streams on the same routes: healthy proof.
    mobile.write_text("\n".join(result("mobile", f"fixture-{i}", f"provider-{i}", 1) for i in range(3)) + "\n")
    tv.write_text("\n".join(result("tv", f"fixture-{i}", f"provider-{i}", 1) for i in range(3)) + "\n")
    completed = run_gate(root)
    assert completed.returncode == 0, completed.stderr
    assert "state=passed" in completed.stdout

    # One provider-specific discrepancy is evidence, not a systemic runtime failure.
    mobile.write_text(
        "\n".join(
            [result("mobile", "fixture-0", "provider-0", 0)]
            + [result("mobile", f"fixture-{i}", f"provider-{i}", 1) for i in range(1, 4)]
        )
        + "\n"
    )
    tv.write_text("\n".join(result("tv", f"fixture-{i}", f"provider-{i}", 1) for i in range(4)) + "\n")
    completed = run_gate(root)
    assert completed.returncode == 0, completed.stderr
    assert "divergences=1" in completed.stdout

    # Many provider-specific extraction gaps must still reach Brain when that same
    # official client proves a healthy runtime on other comparable routes. This is
    # the shape observed by the green TV/Mobile Labs: provider asymmetry, not a
    # collapsed client runtime.
    mobile.write_text("\n".join(result("mobile", f"fixture-{i}", f"provider-{i}", 2) for i in range(8)) + "\n")
    tv.write_text(
        "\n".join(
            result("tv", f"fixture-{i}", f"provider-{i}", 0 if i < 6 else 1)
            for i in range(8)
        )
        + "\n"
    )
    completed = run_gate(root)
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert "state=passed" in completed.stdout
    assert "divergences=6" in completed.stdout

    # Disabled providers are not runtime acceptance evidence and cannot turn a
    # healthy client into an apparent cross-runtime failure.
    mobile.write_text(
        "\n".join(
            [result("mobile", f"fixture-{i}", f"disabled-{i}", 2, enabled=False) for i in range(3)]
            + [result("mobile", f"healthy-{i}", f"healthy-{i}", 1) for i in range(3)]
        )
        + "\n"
    )
    tv.write_text(
        "\n".join(
            [result("tv", f"fixture-{i}", f"disabled-{i}", 0, enabled=False) for i in range(3)]
            + [result("tv", f"healthy-{i}", f"healthy-{i}", 1) for i in range(3)]
        )
        + "\n"
    )
    completed = run_gate(root)
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert "divergences=0" in completed.stdout

    # A client returning zero everywhere while its official peer succeeds is a
    # complete runtime collapse and remains blocking.
    mobile.write_text("\n".join(result("mobile", f"fixture-{i}", f"provider-{i}", 0) for i in range(3)) + "\n")
    tv.write_text("\n".join(result("tv", f"fixture-{i}", f"provider-{i}", 2) for i in range(3)) + "\n")
    completed = run_gate(root)
    assert completed.returncode == 1, (completed.stdout, completed.stderr)
    assert "systemic_cross_client_divergence" in completed.stderr
    assert '"client":"mobile"' in completed.stderr
    assert '"reason":"complete_zero_collapse"' in completed.stderr

    # Swallowed QuickJS exceptions are represented by the diagnostic sentinel and
    # count as runtime failures even though the official client reports count=1.
    mobile.write_text(
        "\n".join(
            line
            for i in range(3)
            for line in (
                result("mobile", f"fixture-{i}", f"provider-{i}", 1),
                sentinel("mobile", f"fixture-{i}", f"provider-{i}"),
            )
        )
        + "\n"
    )
    tv.write_text("\n".join(result("tv", f"fixture-{i}", f"provider-{i}", 1) for i in range(3)) + "\n")
    completed = run_gate(root)
    assert completed.returncode == 1, (completed.stdout, completed.stderr)
    assert "runtime_sentinels=3" in completed.stderr
    assert '"reason":"runtime_errors"' in completed.stderr

    # Requiring a client that has no evidence must fail closed rather than silently
    # reducing the matrix to whichever client happened to upload an artifact.
    tv.unlink()
    completed = run_gate(root)
    assert completed.returncode == 2, (completed.stdout, completed.stderr)
    assert "missing_required_clients" in completed.stderr

print("native cross-client runtime gate tests passed")
