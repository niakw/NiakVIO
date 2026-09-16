#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / "scripts/apply_provider_overrides.py"
SAFETY = ROOT / "scripts/provider_patches/runtime_capability_media_safety_v4.py"
OWNERSHIP = ROOT / "tests/global_core_runtime_ownership_test.py"


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
        '# NUVIO_STREAM_SANITIZER_V10_SELECTION\nGLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v10.py"',
        "sanitizer selection",
    )
    managed_anchor = '    "scripts/provider_patches/stream_output_sanitizer_v8.py",\n}'
    if '"scripts/provider_patches/stream_output_sanitizer_v10.py",' not in apply:
        if managed_anchor not in apply:
            raise SystemExit("managed sanitizer anchor missing")
        apply = apply.replace(
            managed_anchor,
            '    "scripts/provider_patches/stream_output_sanitizer_v8.py",\n'
            '    "scripts/provider_patches/stream_output_sanitizer_v9.py",\n'
            '    "scripts/provider_patches/stream_output_sanitizer_v10.py",\n}',
            1,
        )
    marker_anchor = '    "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8",\n'
    if '    "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9",\n' not in apply:
        if marker_anchor not in apply:
            raise SystemExit("v8 marker anchor missing")
        apply = apply.replace(marker_anchor, marker_anchor + '    "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9",\n', 1)
    if '    "NUVIO_STREAM_OUTPUT_CORRELATED_HANDOFF_V10",\n' not in apply:
        anchor = '    "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9",\n'
        if anchor not in apply:
            raise SystemExit("v9 marker anchor missing")
        apply = apply.replace(anchor, anchor + '    "NUVIO_STREAM_OUTPUT_CORRELATED_HANDOFF_V10",\n', 1)
    APPLY.write_text(apply, encoding="utf-8")

    safety = SAFETY.read_text(encoding="utf-8")
    helper_anchor = '  function staticSafety(row){\n'
    helper = r'''  /* NUVIO_RUNTIME_MEDIA_SAFETY_PRIVATE_PROOF_CLEANUP_V2 */
  function clearPrivateProofs(row){
    if(row&&typeof row==="object"){
      try{delete row.__nuvioCorrelatedPlayerFallbackV1}catch(_e){}
      try{delete row.__nuvioCoreMediaProofV1}catch(_e){}
    }
    return row;
  }
'''
    if "NUVIO_RUNTIME_MEDIA_SAFETY_PRIVATE_PROOF_CLEANUP_V2" not in safety:
        if helper_anchor not in safety:
            raise SystemExit("runtime safety helper anchor missing")
        safety = safety.replace(helper_anchor, helper + helper_anchor, 1)
    safety = replace_once(
        safety,
        'if(nativeRuntime)return rebuild(v,x,staticRows);',
        'if(nativeRuntime)return rebuild(v,x,staticRows.map(clearPrivateProofs));',
        "native safety cleanup",
    )
    safety = replace_once(
        safety,
        'return rebuild(v,x,kept)};wrap.__nuvioRuntimeCapabilitySafetyV4=true;',
        'return rebuild(v,x,kept.map(clearPrivateProofs))};wrap.__nuvioRuntimeCapabilitySafetyV4=true;',
        "web safety cleanup",
    )
    SAFETY.write_text(safety, encoding="utf-8")

    ownership = OWNERSHIP.read_text(encoding="utf-8")
    ownership = ownership.replace(
        'assert \'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v8.py"\' in APPLY',
        'assert \'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v10.py"\' in APPLY',
    )
    if 'SANITIZER_V10 =' not in ownership:
        anchor = 'SANITIZER_V8 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v8.py").read_text(encoding="utf-8")\n'
        if anchor in ownership:
            ownership = ownership.replace(
                anchor,
                anchor
                + 'SANITIZER_V9 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v9.py").read_text(encoding="utf-8")\n'
                + 'SANITIZER_V10 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v10.py").read_text(encoding="utf-8")\n',
                1,
            )
    ownership = ownership.replace(
        'CORE_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v8.py"',
        'CORE_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v10.py"',
    )
    if "NUVIO_STREAM_OUTPUT_CORRELATED_HANDOFF_V10" not in ownership:
        anchor = 'assert \'return verdict===true?clearPrivateProofs(item.stream):null;\' in SANITIZER_V8\n'
        if anchor in ownership:
            ownership = ownership.replace(
                anchor,
                anchor
                + 'assert \'NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9\' in SANITIZER_V9\n'
                + 'assert \'NUVIO_STREAM_OUTPUT_CORRELATED_HANDOFF_V10\' in SANITIZER_V10\n'
                + 'assert \'clearCoreProofOnly(item.stream)\' in SANITIZER_V10\n',
                1,
            )
    OWNERSHIP.write_text(ownership, encoding="utf-8")

    print("CORRELATED_PLAYER_OUTER_SAFETY_V2_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
