#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "apply_provider_overrides.py"
MARKER = "CORE_RUNTIME_MEDIA_SAFETY_OUTERMOST_V1"

EARLY = '''        before = text
        text = _apply_patch_script(text, provider_id, GLOBAL_RUNTIME_MEDIA_SAFETY, safety_options, None)
        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_RUNTIME_MEDIA_SAFETY,
                "phase": phase,
                "scope": "global_runtime_media_safety",
            })

'''

LATE_ANCHOR = '''            if text != before:
                applied.append({
                    "type": "patch_script",
                    "path": GLOBAL_STREAM_SANITIZER,
                    "phase": phase,
                    "scope": "global_terminal_stream_sanitizer",
                })

        # END PROVIDER is the final byte boundary.
'''

LATE = '''            if text != before:
                applied.append({
                    "type": "patch_script",
                    "path": GLOBAL_STREAM_SANITIZER,
                    "phase": phase,
                    "scope": "global_terminal_stream_sanitizer",
                })

        # CORE_RUNTIME_MEDIA_SAFETY_OUTERMOST_V1
        # Safety is the final Core stream guard. Applying it after enrichment,
        # playback integrity, identity/presentation/branding and the terminal
        # sanitizer makes its wrapper outermost while preserving the sanitizer's
        # strict fail-closed verdicts underneath it.
        before = text
        text = _apply_patch_script(text, provider_id, GLOBAL_RUNTIME_MEDIA_SAFETY, safety_options, None)
        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_RUNTIME_MEDIA_SAFETY,
                "phase": phase,
                "scope": "global_runtime_media_safety",
            })

        # END PROVIDER is the final byte boundary.
'''


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print("CORE_RUNTIME_MEDIA_SAFETY_OUTERMOST_V1_ALREADY_CURRENT")
        return 0
    if text.count(EARLY) != 1:
        raise SystemExit(f"early safety application count={text.count(EARLY)}")
    if text.count(LATE_ANCHOR) != 1:
        raise SystemExit(f"sanitizer anchor count={text.count(LATE_ANCHOR)}")
    text = text.replace(EARLY, "", 1)
    text = text.replace(LATE_ANCHOR, LATE, 1)
    TARGET.write_text(text, encoding="utf-8")
    print("CORE_RUNTIME_MEDIA_SAFETY_OUTERMOST_V1_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
