#!/usr/bin/env python3
"""Prevent the legacy structured-body scanner from double-validating V9 `$text`.

The V9 text-body branch already performs stricter bounded/sensitive checks and
fixture abstraction. The older generic raw-body loop must therefore ignore only
its internal `$text` evidence slot; all other body kinds/fields remain unchanged.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_route_proof.py"
MARKER = "PROVIDER_ROUTE_PROOF_TEXT_BODY_RESIDUE_V9_1"


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    if "PROVIDER_ROUTE_PROOF_TEXT_BODY_V9" not in text:
        raise AssertionError("V9.1 requires V9 text-body proof first")
    old = '''    for key, raw in raw_body.items():
        value = str(raw if raw is not None else "")
'''
    new = '''    # PROVIDER_ROUTE_PROOF_TEXT_BODY_RESIDUE_V9_1
    for key, raw in raw_body.items():
        if body_kind == "text" and str(key) == "$text":
            continue
        value = str(raw if raw is not None else "")
'''
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"V9.1 raw-body loop anchor count={count}")
    text = text.replace(old, new, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        'if body_kind == "text" and str(key) == "$text":',
        "def _text_body_template",
        'raw_body.get("$text")',
    ):
        if needle not in value:
            raise AssertionError(f"V9.1 missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_TEXT_BODY_REQUEST_V9_1_OK changed={str(changed).lower()} "
        "legacy_double_residue=0 text_branch_single_owner=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
