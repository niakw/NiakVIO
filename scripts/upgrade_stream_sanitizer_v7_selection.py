#!/usr/bin/env python3
"""Select terminal stream sanitizer V7 unless a newer Core sanitizer owns it.

This migration is historical and is still called by repair bootstraps. It must be
monotonic: a repository already on strict-probe V8 must never be downgraded to V7.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "scripts" / "apply_provider_overrides.py"
HASHES = ROOT / "scripts" / "generate_release_hashes.py"
MARKER = "NUVIO_STREAM_SANITIZER_V7_SELECTION"
V7 = "scripts/provider_patches/stream_output_sanitizer_v7.py"
V8 = "scripts/provider_patches/stream_output_sanitizer_v8.py"
V8_SELECTION = "NUVIO_STREAM_SANITIZER_V8_SELECTION"


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def _v8_current(text: str) -> bool:
    return f'GLOBAL_STREAM_SANITIZER = "{V8}"' in text or V8_SELECTION in text


def patch_overrides() -> bool:
    text = OVERRIDES.read_text(encoding="utf-8")
    original = text
    if _v8_current(text):
        # V8 includes/calls the V7 correlated-player layer and is the newer Core
        # owner. Historical repair bootstrap must be a no-op, never a downgrade.
        validate_overrides(text)
        return False
    text = once(
        text,
        'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v6.py"',
        f'GLOBAL_STREAM_SANITIZER = "{V7}"',
        "global-sanitizer-selection",
    )
    text = once(
        text,
        '    "scripts/provider_patches/stream_output_sanitizer_v6.py",\n}',
        '    "scripts/provider_patches/stream_output_sanitizer_v6.py",\n'
        f'    "{V7}",\n'
        '}',
        "managed-sanitizer-set",
    )
    text = once(
        text,
        '    "NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6",\n',
        '    "NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6",\n'
        '    "NUVIO_STREAM_OUTPUT_CORRELATED_PLAYER_FALLBACK_V7",\n',
        "generated-tail-marker",
    )
    if f"# {MARKER}\n" not in text:
        anchor = f'GLOBAL_STREAM_SANITIZER = "{V7}"\n'
        text = text.replace(anchor, f"# {MARKER}\n" + anchor, 1)
    OVERRIDES.write_text(text, encoding="utf-8")
    validate_overrides(text)
    return text != original


def patch_hashes() -> bool:
    text = HASHES.read_text(encoding="utf-8")
    original = text
    overrides = OVERRIDES.read_text(encoding="utf-8")
    desired = V8 if _v8_current(overrides) else V7
    if desired not in text:
        anchor = f'    "{V7}",\n' if V7 in text else '    "scripts/provider_patches/stream_output_sanitizer_v6.py",\n'
        if text.count(anchor) != 1:
            raise AssertionError(f"release-core-sanitizer-current: expected one anchor, got {text.count(anchor)}")
        text = text.replace(anchor, anchor + f'    "{desired}",\n', 1)
    HASHES.write_text(text, encoding="utf-8")
    validate_hashes(text)
    return text != original


def validate_overrides(text: str | None = None) -> None:
    value = text if text is not None else OVERRIDES.read_text(encoding="utf-8")
    if _v8_current(value):
        assert f'GLOBAL_STREAM_SANITIZER = "{V8}"' in value
        assert V8 in value
        assert "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8" in value
        assert V7 in value, "V8 composition must retain V7 managed sanitizer knowledge"
        return
    assert value.count(MARKER) == 1, f"selection marker count={value.count(MARKER)}"
    assert f'GLOBAL_STREAM_SANITIZER = "{V7}"' in value
    assert V7 in value
    assert "NUVIO_STREAM_OUTPUT_CORRELATED_PLAYER_FALLBACK_V7" in value


def validate_hashes(text: str | None = None) -> None:
    value = text if text is not None else HASHES.read_text(encoding="utf-8")
    overrides = OVERRIDES.read_text(encoding="utf-8")
    desired = V8 if _v8_current(overrides) else V7
    assert desired in value, f"current sanitizer missing from release hash inventory: {desired}"


def main() -> int:
    changed_overrides = patch_overrides()
    changed_hashes = patch_hashes()
    current = "v8" if _v8_current(OVERRIDES.read_text(encoding="utf-8")) else "v7"
    print(
        "STREAM_SANITIZER_V7_SELECTION_OK "
        f"current={current} overrides_changed={str(changed_overrides).lower()} "
        f"hashes_changed={str(changed_hashes).lower()} monotonic=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
