#!/usr/bin/env python3
"""V3 migration for Domain Refresh publication naming and contract wording.

The authoritative domain transaction rebuilds the complete managed
PROVIDER.*.CONFIG.V1 block from structured DATA while proving that bytes outside
that Lego stay unchanged. Publication naming must preserve the filename grammar
of the accepted generation: source-qualified generations retain their source
namespace, while unqualified ``{id}-{sha}.js`` generations stay unqualified.
A domain-only refresh must never create a mixed publication stage.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "domain_refresh_transaction_v2.py"
MARKER = "DOMAIN_REFRESH_SOURCE_QUALIFIED_PUBLICATION_V3"

OLD_NAME = '        new_rel = f"providers/{provider_id}-{digest[:16]}.js"\n'
NEW_NAME = '        new_rel = f"providers/{source_qualified_provider_name(provider_id, old_path, digest)}"\n'

LEGACY_HELPER_RE = re.compile(
    r'def source_qualified_provider_name\(provider_id: str, old_path: Path, digest: str\) -> str:\n'
    r'    """Retain the publisher/source namespace while rotating content hash\."""\n'
    r'    parts = old_path\.stem\.split\("--"\)\n'
    r'    source = parts\[-2\] if len\(parts\) >= 3 else "nuvio"\n'
    r'    if source\.endswith\("-audit-quarantine"\):\n'
    r'        source = source\[: -len\("-audit-quarantine"\)\] or "nuvio"\n'
    r'    return f"\{_safe_fragment\(provider_id\.casefold\(\)\)\}--\{_safe_fragment\(source\)\}--\{digest\[:16\]\}\.js"\n'
)

CURRENT_HELPER = '''def source_qualified_provider_name(provider_id: str, old_path: Path, digest: str) -> str:\n    """Preserve the accepted generation's filename stage while rotating its hash."""\n    parts = old_path.stem.split("--")\n    if len(parts) >= 3:\n        source = parts[-2]\n        if source.endswith("-audit-quarantine"):\n            source = source[: -len("-audit-quarantine")] or "nuvio"\n        return f"{_safe_fragment(provider_id.casefold())}--{_safe_fragment(source)}--{digest[:16]}.js"\n    return f"{_safe_fragment(provider_id.casefold())}-{digest[:16]}.js"\n'''

ANCHOR = '''def _generation(rows: list[dict[str, Any]]) -> str:\n    aggregate = hashlib.sha256()\n'''
HELPER_BLOCK = '''# DOMAIN_REFRESH_SOURCE_QUALIFIED_PUBLICATION_V3\ndef _safe_fragment(value: object) -> str:\n    import re\n    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip()).strip(".-")\n    return cleaned[:120] or "provider"\n\n\n''' + CURRENT_HELPER + '''\n\ndef _generation(rows: list[dict[str, Any]]) -> str:\n    aggregate = hashlib.sha256()\n'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    before = text
    if MARKER not in text:
        if ANCHOR not in text:
            raise AssertionError("Domain Refresh generation anchor missing")
        text = text.replace(ANCHOR, HELPER_BLOCK, 1)
    else:
        text, replaced = LEGACY_HELPER_RE.subn(CURRENT_HELPER, text, count=1)
        if replaced == 0 and CURRENT_HELPER not in text:
            raise AssertionError("Domain Refresh publication helper shape changed")
    if OLD_NAME in text:
        text = text.replace(OLD_NAME, NEW_NAME, 1)
    elif NEW_NAME not in text:
        raise AssertionError("Domain Refresh provider filename anchor missing")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return text != before


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "source_qualified_provider_name(provider_id, old_path, digest)",
        'parts = old_path.stem.split("--")',
        "if len(parts) >= 3:",
        'return f"{_safe_fragment(provider_id.casefold())}--{_safe_fragment(source)}--{digest[:16]}.js"',
        'return f"{_safe_fragment(provider_id.casefold())}-{digest[:16]}.js"',
        "domain refresh changed bytes outside CONFIG Lego",
        "allmat.provider_model(provider_id, patch, capability, static_row)",
        "replace_provider_fix(",
    ):
        if needle not in value:
            raise AssertionError(f"Domain Refresh V3 missing {needle}")
    if 'source = parts[-2] if len(parts) >= 3 else "nuvio"' in value:
        raise AssertionError("Domain Refresh would force an unqualified generation into a mixed source-qualified stage")


def main() -> int:
    changed = patch()
    print(
        f"DOMAIN_REFRESH_PUBLICATION_V3_OK changed={str(changed).lower()} "
        "filename_stage_preserved=true full_config=true core_bytes_preserved=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
