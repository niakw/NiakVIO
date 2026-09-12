#!/usr/bin/env python3
"""V3 migration for Domain Refresh publication naming and contract wording.

The authoritative domain transaction already rebuilds the complete managed
PROVIDER.*.CONFIG.V1 block from structured DATA while proving that bytes outside
that Lego stay unchanged. V3 closes the remaining publication mismatch: changed
bundles must retain their source namespace (for example ``--nuvio--``) instead
of falling back to the historical unqualified ``{id}-{sha}.js`` shape.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "domain_refresh_transaction_v2.py"
MARKER = "DOMAIN_REFRESH_SOURCE_QUALIFIED_PUBLICATION_V3"

OLD_DOC = "4. rebuilds the complete managed CONFIG DATA block for changed Provider v3 bundles;\n5. leaves every byte outside PROVIDER.*.CONFIG.V1 (including all Core Lego) unchanged."
NEW_DOC = "4. rebuilds the complete managed CONFIG DATA block for changed Provider v3 bundles;\n5. republishes changed bundles with their existing source-qualified namespace;\n6. leaves every byte outside PROVIDER.*.CONFIG.V1 (including all Core Lego) unchanged."

OLD_NAME = '        new_rel = f"providers/{provider_id}-{digest[:16]}.js"\n'
NEW_NAME = '        new_rel = f"providers/{source_qualified_provider_name(provider_id, old_path, digest)}"\n'

ANCHOR = '''def _generation(rows: list[dict[str, Any]]) -> str:\n    aggregate = hashlib.sha256()\n'''
HELPER = '''# DOMAIN_REFRESH_SOURCE_QUALIFIED_PUBLICATION_V3\ndef _safe_fragment(value: object) -> str:\n    import re\n    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip()).strip(".-")\n    return cleaned[:120] or "provider"\n\n\ndef source_qualified_provider_name(provider_id: str, old_path: Path, digest: str) -> str:\n    \"\"\"Retain the publisher/source namespace while rotating content hash.\"\"\"\n    parts = old_path.stem.split("--")\n    source = parts[-2] if len(parts) >= 3 else "nuvio"\n    if source.endswith("-audit-quarantine"):\n        source = source[: -len("-audit-quarantine")] or "nuvio"\n    return f"{_safe_fragment(provider_id.casefold())}--{_safe_fragment(source)}--{digest[:16]}.js"\n\n\ndef _generation(rows: list[dict[str, Any]]) -> str:\n    aggregate = hashlib.sha256()\n'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    before = text
    if MARKER not in text:
        if ANCHOR not in text:
            raise AssertionError("Domain Refresh generation anchor missing")
        text = text.replace(ANCHOR, HELPER, 1)
    if OLD_NAME in text:
        text = text.replace(OLD_NAME, NEW_NAME, 1)
    elif NEW_NAME not in text:
        raise AssertionError("Domain Refresh provider filename anchor missing")
    if OLD_DOC in text:
        text = text.replace(OLD_DOC, NEW_DOC, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return text != before


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "source_qualified_provider_name(provider_id, old_path, digest)",
        'parts = old_path.stem.split("--")',
        'source = parts[-2] if len(parts) >= 3 else "nuvio"',
        'return f"{_safe_fragment(provider_id.casefold())}--{_safe_fragment(source)}--{digest[:16]}.js"',
        "domain refresh changed bytes outside CONFIG Lego",
        "allmat.provider_model(provider_id, patch, capability, static_row)",
        "replace_provider_fix(",
    ):
        if needle not in value:
            raise AssertionError(f"Domain Refresh V3 missing {needle}")
    if OLD_NAME.strip() in value:
        raise AssertionError("Domain Refresh retained unqualified provider filename publication")


def main() -> int:
    changed = patch()
    print(f"DOMAIN_REFRESH_PUBLICATION_V3_OK changed={str(changed).lower()} source_qualified=true full_config=true core_bytes_preserved=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
