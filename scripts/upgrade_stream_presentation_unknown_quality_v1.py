#!/usr/bin/env python3
"""Remove meaningless quality fields before native clients rebuild stream labels.

Core already omits a quality suffix when no real quality can be inferred, but older
provider rows may still carry quality='Unknown'/'Inconnu'. Some Nuvio clients project
that raw field back into their own stream title. When no real resolution is proven,
remove the raw quality field (and a meaningless resolution alias) entirely.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py"
MARKER = 'else if("quality" in out)delete out.quality'
OLD = 'if(f.quality)out.quality=f.quality;if(f.language)out.language=f.language;'
NEW = (
    'if(f.quality)out.quality=f.quality;'
    'else if("quality" in out)delete out.quality;'
    'if(!f.quality&&("resolution" in out)&&!meaningful(out.resolution))delete out.resolution;'
    'if(f.language)out.language=f.language;'
)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        if text.count(MARKER) != 1:
            raise AssertionError(f"unknown-quality cleanup marker count={text.count(MARKER)}")
        return False
    if text.count(OLD) != 1:
        raise AssertionError(f"unknown-quality cleanup anchor count={text.count(OLD)}")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    return True


def validate() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if text.count(MARKER) != 1:
        raise AssertionError("stream presentation must delete unresolved raw quality exactly once")
    for token in (
        'if(f.quality)out.quality=f.quality;',
        'else if("quality" in out)delete out.quality;',
        'if(!f.quality&&("resolution" in out)&&!meaningful(out.resolution))delete out.resolution;',
        'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"")',
    ):
        if token not in text:
            raise AssertionError(f"unknown-quality projection contract missing: {token}")


def main() -> int:
    changed = patch()
    validate()
    print(
        "STREAM_PRESENTATION_UNKNOWN_QUALITY_OK "
        f"changed={str(changed).lower()} raw_unknown_quality=removed "
        "unknown_resolution_alias=removed title_suffix=real_quality_only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
