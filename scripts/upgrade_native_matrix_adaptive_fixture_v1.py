#!/usr/bin/env python3
"""Teach native matrix gate to classify arbitrary adaptive fixture slugs by lane."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/gate_native_declared_provider_matrix.py"
MARKER = "NATIVE_MATRIX_ADAPTIVE_FIXTURE_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    original = text
    if MARKER in text:
        validate(text)
        return False

    text = once(
        text,
        "from pathlib import Path\n",
        "from pathlib import Path\n\nfrom rotating_corpus import canonical_lane, fixture_by_slug\n",
        "adaptive fixture import",
    )
    text = once(
        text,
        '''def route(provider: str, media_type: str) -> tuple[str, str]:\n    return (provider.casefold(), media_type.casefold())\n\n\n''',
        '''def route(provider: str, media_type: str) -> tuple[str, str]:\n    return (provider.casefold(), media_type.casefold())\n\n\n# NATIVE_MATRIX_ADAPTIVE_FIXTURE_V1\ndef fixture_lane(slug: str, legacy_fixture_by_type: dict[str, str]) -> str:\n    """Resolve any global/adaptive fixture to movie|tv|anime.\n\n    Exact historical regression slugs remain supported by rotating_corpus, while\n    the legacy three-fixture mapping is only a compatibility fallback.\n    """\n    value = str(slug or "").strip()\n    if not value:\n        return ""\n    try:\n        return canonical_lane(fixture_by_slug(value))\n    except (KeyError, ValueError):\n        return next(\n            (kind for kind in TYPES if str(legacy_fixture_by_type.get(kind) or "") == value),\n            "",\n        )\n\n\n''',
        "adaptive fixture resolver",
    )
    text = once(
        text,
        '''    missing_fixture_types = [kind for kind in TYPES if not str(fixture_by_type.get(kind) or "").strip()]\n    if missing_fixture_types:\n        raise SystemExit("missing representative fixture mapping for: " + ",".join(missing_fixture_types))\n''',
        '''    # Adaptive Labs no longer require one hard-coded representative slug per\n    # type. The three global pools in rotating-popular-corpus.json are authoritative;\n    # fixture_by_type remains accepted only for old targeted evidence.\n''',
        "remove static fixture requirement",
    )
    text = once(
        text,
        '''                    fixture = f.get("fixture", "")\n                    media_type = next((kind for kind in TYPES if str(fixture_by_type.get(kind) or "") == fixture), "")\n''',
        '''                    fixture = f.get("fixture", "")\n                    media_type = fixture_lane(fixture, fixture_by_type)\n''',
        "ios terminal fixture lane",
    )
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return text != original


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    required = (
        MARKER,
        "from rotating_corpus import canonical_lane, fixture_by_slug",
        "def fixture_lane(",
        "media_type = fixture_lane(fixture, fixture_by_type)",
        "Adaptive Labs no longer require one hard-coded representative slug per",
    )
    missing = [needle for needle in required if needle not in value]
    if missing:
        raise AssertionError("adaptive native matrix markers missing: " + ",".join(missing))
    if "missing representative fixture mapping for:" in value:
        raise AssertionError("static three-fixture mapping is still a matrix prerequisite")


def main() -> int:
    changed = patch()
    validate()
    print(f"NATIVE_MATRIX_ADAPTIVE_FIXTURE_V1_OK changed={str(changed).lower()} global_lists=3 static_fixture_gate=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
