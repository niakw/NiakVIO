#!/usr/bin/env python3
"""Select terminal stream sanitizer V7 unless a newer Core sanitizer owns it.

This migration is historical and is still called by repair bootstraps. It must be
monotonic: a repository already on strict-probe V8 must never be downgraded to V7.
"""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "scripts" / "apply_provider_overrides.py"
HASHES = ROOT / "scripts" / "generate_release_hashes.py"
MARKER = "NUVIO_STREAM_SANITIZER_V7_SELECTION"
V7 = "scripts/provider_patches/stream_output_sanitizer_v7.py"
V8 = "scripts/provider_patches/stream_output_sanitizer_v8.py"
V9 = "scripts/provider_patches/stream_output_sanitizer_v9.py"
V10 = "scripts/provider_patches/stream_output_sanitizer_v10.py"
NEWER_SANITIZERS = {
    8: V8,
    9: V9,
    10: V10,
}
SELECTION_RE = re.compile(
    r'GLOBAL_STREAM_SANITIZER = "'
    r'(scripts/provider_patches/stream_output_sanitizer_v(?P<version>\d+)\.py)"'
)


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def _current_selection(text: str) -> tuple[int, str]:
    match = SELECTION_RE.search(text)
    if not match:
        return 0, ""
    return int(match.group("version")), match.group(1)


def _newer_current(text: str) -> bool:
    version, path = _current_selection(text)
    if version <= 7:
        return False
    expected = NEWER_SANITIZERS.get(version)
    if expected is not None and path != expected:
        raise AssertionError(
            f"sanitizer v{version} selection drifted: expected {expected}, got {path or '<missing>'}"
        )
    # Future versions remain monotonic even before this historical migration
    # learns their explicit constant; it must never downgrade a newer owner.
    return True


def patch_overrides() -> bool:
    text = OVERRIDES.read_text(encoding="utf-8")
    original = text
    if _newer_current(text):
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
    version, selected = _current_selection(overrides)
    desired = selected if version > 7 and selected else V7
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
    version, selected = _current_selection(value)
    if version > 7:
        assert selected
        expected = NEWER_SANITIZERS.get(version)
        if expected is not None:
            assert selected == expected, (version, selected, expected)
        assert f'GLOBAL_STREAM_SANITIZER = "{selected}"' in value
        assert f"NUVIO_STREAM_SANITIZER_V{version}_SELECTION" in value
        assert selected in value
        assert V7 in value, "newer sanitizer composition must retain V7 managed sanitizer knowledge"
        return
    assert value.count(MARKER) == 1, f"selection marker count={value.count(MARKER)}"
    assert f'GLOBAL_STREAM_SANITIZER = "{V7}"' in value
    assert V7 in value
    assert "NUVIO_STREAM_OUTPUT_CORRELATED_PLAYER_FALLBACK_V7" in value


def validate_hashes(text: str | None = None) -> None:
    value = text if text is not None else HASHES.read_text(encoding="utf-8")
    overrides = OVERRIDES.read_text(encoding="utf-8")
    version, selected = _current_selection(overrides)
    desired = selected if version > 7 and selected else V7
    assert desired in value, f"current sanitizer missing from release hash inventory: {desired}"


def main() -> int:
    changed_overrides = patch_overrides()
    changed_hashes = patch_hashes()
    version, _selected = _current_selection(OVERRIDES.read_text(encoding="utf-8"))
    current = f"v{version}" if version > 7 else "v7"
    print(
        "STREAM_SANITIZER_V7_SELECTION_OK "
        f"current={current} overrides_changed={str(changed_overrides).lower()} "
        f"hashes_changed={str(changed_hashes).lower()} monotonic=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
