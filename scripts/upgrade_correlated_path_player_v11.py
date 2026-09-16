#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / "scripts/apply_provider_overrides.py"
SAFETY = ROOT / "scripts/provider_patches/runtime_capability_media_safety_v4.py"
OWNERSHIP = ROOT / "tests/global_core_runtime_ownership_test.py"

OLD_RULE = 'if(/\\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return true;\n      if(/\\/(?:shell|video|stream)(?:\\.php|[/?#.-]|$)/i.test(path)){'
NEW_RULE = 'if(/\\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return true;\n      if(/^\\/stream\\/(?:[^/?#]+\\/){1,4}[^/?#]+\\/?$/i.test(path))return true;\n      if(/\\/(?:shell|video|stream)(?:\\.php|[/?#.-]|$)/i.test(path)){'


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
        '# NUVIO_STREAM_SANITIZER_V10_SELECTION\nGLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v10.py"',
        '# NUVIO_STREAM_SANITIZER_V11_SELECTION\nGLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v11.py"',
        "sanitizer selection",
    )
    if '"scripts/provider_patches/stream_output_sanitizer_v11.py",' not in apply:
        anchor = '    "scripts/provider_patches/stream_output_sanitizer_v10.py",\n}'
        if anchor not in apply:
            raise SystemExit("managed sanitizer v10 anchor missing")
        apply = apply.replace(anchor, '    "scripts/provider_patches/stream_output_sanitizer_v10.py",\n    "scripts/provider_patches/stream_output_sanitizer_v11.py",\n}', 1)
    if '    "NUVIO_STREAM_OUTPUT_PATH_PLAYER_V11",\n' not in apply:
        anchor = '    "NUVIO_STREAM_OUTPUT_CORRELATED_HANDOFF_V10",\n'
        if anchor not in apply:
            raise SystemExit("generated Core V10 marker anchor missing")
        apply = apply.replace(anchor, anchor + '    "NUVIO_STREAM_OUTPUT_PATH_PLAYER_V11",\n', 1)
    APPLY.write_text(apply, encoding="utf-8")

    safety = SAFETY.read_text(encoding="utf-8")
    safety = replace_once(safety, OLD_RULE, NEW_RULE, "runtime safety path player")
    SAFETY.write_text(safety, encoding="utf-8")

    ownership = OWNERSHIP.read_text(encoding="utf-8")
    ownership = ownership.replace(
        'SANITIZER_V10 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v10.py").read_text(encoding="utf-8")',
        'SANITIZER_V10 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v10.py").read_text(encoding="utf-8")\nSANITIZER_V11 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v11.py").read_text(encoding="utf-8")',
    )
    ownership = ownership.replace(
        'CORE_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v10.py"',
        'CORE_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v11.py"',
    )
    ownership = ownership.replace(
        'assert \'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v10.py"\' in APPLY',
        'assert \'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v11.py"\' in APPLY',
    )
    if "NUVIO_STREAM_OUTPUT_PATH_PLAYER_V11" not in ownership:
        anchor = "assert 'clearCoreProofOnly(item.stream)' in SANITIZER_V10\n"
        if anchor not in ownership:
            raise SystemExit("ownership V10 assertion anchor missing")
        ownership = ownership.replace(
            anchor,
            anchor + "assert 'NUVIO_STREAM_OUTPUT_PATH_PLAYER_V11' in SANITIZER_V11\nassert '/stream' in SANITIZER_V11\n",
            1,
        )
    ownership = ownership.replace(
        'sanitizer_v10=correlated-handoff',
        'sanitizer_v11=correlated-path-handoff',
    )
    OWNERSHIP.write_text(ownership, encoding="utf-8")
    print("CORRELATED_PATH_PLAYER_V11_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
