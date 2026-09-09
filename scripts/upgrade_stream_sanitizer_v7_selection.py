#!/usr/bin/env python3
"""Select terminal stream sanitizer V7 in deterministic build/release sources."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "scripts" / "apply_provider_overrides.py"
HASHES = ROOT / "scripts" / "generate_release_hashes.py"
MARKER = "NUVIO_STREAM_SANITIZER_V7_SELECTION"
V7 = "scripts/provider_patches/stream_output_sanitizer_v7.py"


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_overrides() -> bool:
    text = OVERRIDES.read_text(encoding="utf-8")
    original = text
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
    text = once(
        text,
        '    "scripts/provider_patches/stream_output_sanitizer_v6.py",\n',
        '    "scripts/provider_patches/stream_output_sanitizer_v6.py",\n'
        f'    "{V7}",\n',
        "release-core-sanitizer-v7",
    )
    HASHES.write_text(text, encoding="utf-8")
    validate_hashes(text)
    return text != original


def validate_overrides(text: str | None = None) -> None:
    value = text if text is not None else OVERRIDES.read_text(encoding="utf-8")
    assert value.count(MARKER) == 1, f"selection marker count={value.count(MARKER)}"
    assert f'GLOBAL_STREAM_SANITIZER = "{V7}"' in value
    assert V7 in value
    assert "NUVIO_STREAM_OUTPUT_CORRELATED_PLAYER_FALLBACK_V7" in value


def validate_hashes(text: str | None = None) -> None:
    value = text if text is not None else HASHES.read_text(encoding="utf-8")
    assert V7 in value


def main() -> int:
    changed_overrides = patch_overrides()
    changed_hashes = patch_hashes()
    print(
        "STREAM_SANITIZER_V7_SELECTION_OK "
        f"overrides_changed={str(changed_overrides).lower()} hashes_changed={str(changed_hashes).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
