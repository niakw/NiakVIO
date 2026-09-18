#!/usr/bin/env python3
"""V2: do not fall back to a different Mugiwara episode.

The specialized Mugiwara runtime reads the site's structured ``animeServer``
season table. If an episodic request cannot be matched there, returning the
provider's earlier native result is unsafe: that native result may have been
resolved from the catalogue's default/season-1 page. Movies retain the old
fallback behavior; episodic requests fail closed unless the structured resolver
proves the requested season/episode and returns streams.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/provider_patches/mugiwarastream_packed_runtime_v1.py"
MARKER = "NIAKVIO_MUGIWARA_EPISODE_FAIL_CLOSED_V2"

OLD = '''if(pageUrl){var specialized=await fallback(pageUrl,q);if(Array.isArray(specialized)&&specialized.length)return specialized}if(Array.isArray(nativeResult)&&nativeResult.length)return nativeResult;return[]'''
NEW = '''if(pageUrl){var specialized=await fallback(pageUrl,q);if(Array.isArray(specialized)&&specialized.length)return specialized;/* NIAKVIO_MUGIWARA_EPISODE_FAIL_CLOSED_V2 */if(q.type!=="movie")return[]}if(Array.isArray(nativeResult)&&nativeResult.length)return nativeResult;return[]'''
CURRENT_NO_MARKER = '''/* NIAKVIO_MUGIWARA_SPECIALIZED_FALLBACK_PRIORITY_V1 */if(pageUrl){var specialized=await fallback(pageUrl,q);if(Array.isArray(specialized)&&specialized.length)return specialized;if(q.type!=="movie")return[]}'''
CURRENT_WITH_MARKER = '''/* NIAKVIO_MUGIWARA_SPECIALIZED_FALLBACK_PRIORITY_V1 */if(pageUrl){var specialized=await fallback(pageUrl,q);if(Array.isArray(specialized)&&specialized.length)return specialized;/* NIAKVIO_MUGIWARA_EPISODE_FAIL_CLOSED_V2 */if(q.type!=="movie")return[]}'''



def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    if text.count(OLD) == 1:
        text = text.replace(OLD, NEW, 1)
    elif text.count(CURRENT_NO_MARKER) == 1 and text.count('if(q.type!=="movie")return[]') >= 2:
        # A newer discovery-first runtime already contains the V2 behavior but
        # was authored after the original text migration and lost its marker.
        # Preserve those bytes semantically; only restore the durable marker.
        text = text.replace(CURRENT_NO_MARKER, CURRENT_WITH_MARKER, 1)
    else:
        raise AssertionError(
            "Mugiwara episodic fail-closed behavior/anchor missing: "
            f"legacy={text.count(OLD)} current={text.count(CURRENT_NO_MARKER)} "
            f"episodic_guards={text.count('if(q.type!==\"movie\")return[]')}"
        )
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    required = (
        MARKER,
        'if(q.type!=="movie")return[]',
        'if(Array.isArray(specialized)&&specialized.length)return specialized',
        'if(Array.isArray(nativeResult)&&nativeResult.length)return nativeResult',
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"Mugiwara fail-closed V2 missing {needle}")
    window = value[value.index(MARKER) - 300:value.index(MARKER) + 500].casefold()
    for forbidden in ("hell mode", "hellmode", "ragna", "mushoku", "saison 1", "saison1"):
        if forbidden in window:
            raise AssertionError(f"fixture-specific Mugiwara rule leaked: {forbidden}")


def main() -> int:
    changed = patch()
    print(f"MUGIWARA_EPISODE_FAIL_CLOSED_V2_OK changed={str(changed).lower()} movie_fallback=preserved episodic_native_fallback=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
