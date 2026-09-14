#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / "scripts/apply_provider_overrides.py"
TEST = ROOT / "tests/global_core_runtime_ownership_test.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one old anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    apply = APPLY.read_text(encoding="utf-8")
    apply = replace_once(
        apply,
        '# NUVIO_STREAM_SANITIZER_V8_SELECTION\nGLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v8.py"',
        '# NUVIO_STREAM_SANITIZER_V9_SELECTION\nGLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v9.py"',
        "global sanitizer selection",
    )
    if '"scripts/provider_patches/stream_output_sanitizer_v9.py",' not in apply:
        anchor = '    "scripts/provider_patches/stream_output_sanitizer_v8.py",\n}'
        if anchor not in apply:
            raise SystemExit("managed sanitizer set anchor missing")
        apply = apply.replace(
            anchor,
            '    "scripts/provider_patches/stream_output_sanitizer_v8.py",\n    "scripts/provider_patches/stream_output_sanitizer_v9.py",\n}',
            1,
        )
    if '    "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9",\n' not in apply:
        anchor = '    "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8",\n'
        if anchor not in apply:
            raise SystemExit("generated Core tail marker anchor missing")
        apply = apply.replace(anchor, anchor + '    "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9",\n', 1)
    APPLY.write_text(apply, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    test = replace_once(
        test,
        'SANITIZER_V8 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v8.py").read_text(encoding="utf-8")',
        'SANITIZER_V8 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v8.py").read_text(encoding="utf-8")\nSANITIZER_V9 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v9.py").read_text(encoding="utf-8")',
        "ownership v9 source",
    )
    test = replace_once(
        test,
        'CORE_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v8.py"',
        'CORE_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v9.py"',
        "ownership core sanitizer constant",
    )
    test = replace_once(
        test,
        'assert \'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v8.py"\' in APPLY',
        'assert \'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v9.py"\' in APPLY',
        "ownership selection assertion",
    )
    anchor = 'assert \'return verdict===true?clearPrivateProofs(item.stream):null;\' in SANITIZER_V8\n'
    addition = (
        anchor
        + 'assert \'MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"\' in SANITIZER_V9\n'
        + 'assert \'NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9\' in SANITIZER_V9\n'
        + 'assert \'stream_output_sanitizer_v8.py\' in SANITIZER_V9\n'
        + 'assert \'status===403||status===404||status===410\' in SANITIZER_V9\n'
    )
    if 'NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9' not in test:
        if anchor not in test:
            raise SystemExit("ownership strict assertion anchor missing")
        test = test.replace(anchor, addition, 1)
    test = test.replace(
        'print("GLOBAL_CORE_RUNTIME_OWNERSHIP_OK providers=96 timers=core 403=core sanitizer_v8=strict provider_specific_runtime_hacks=forbidden")',
        'print("GLOBAL_CORE_RUNTIME_OWNERSHIP_OK providers=96 timers=core 403=core sanitizer_v9=full-manifest-strict provider_specific_runtime_hacks=forbidden")',
    )
    TEST.write_text(test, encoding="utf-8")
    print("STREAM_SANITIZER_V9_SELECTION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
