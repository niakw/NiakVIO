#!/usr/bin/env python3
"""Keep final published-provider security hardening outside provider state branches.

The published reapply path historically skipped apply_overrides() for terminal
quarantines. Security hardening is not an activation decision, so it must run on
every published bundle after provider/runtime transforms and before final
purification/content addressing, including disabled/quarantined artifacts.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"
IMPORT = "from provider_security_hardening import assert_hardened, harden_bytes\n"
MARKER = "all-published-provider-security-finalization-v1"


def normalize(text: str) -> str:
    if IMPORT not in text:
        anchor = "from provider_purification import purify_bytes\n"
        if anchor not in text:
            raise ValueError("published provider purification import anchor missing")
        text = text.replace(anchor, anchor + IMPORT, 1)

    if MARKER not in text:
        anchor = "        # Final provider bytes are purified only after every Core/provider/runtime\n"
        if anchor not in text:
            raise ValueError("final provider purification anchor missing")
        block = '''        # all-published-provider-security-finalization-v1\n        # Security is independent from activation/quarantine state. Run this after\n        # either branch above so disabled and terminal-quarantined bundles receive\n        # the same mandatory global hardening as active providers.\n        security_hardened, security_report = harden_bytes(patched)\n        if security_hardened != patched:\n            records = list(records) + [{\n                "type": "provider_security_hardening",\n                "phase": "final-post-transform",\n                "revision": 1,\n                "scope": "all-published-providers",\n                "structured_parse_changes": int(security_report.get("structuredParseChanges") or 0),\n                "literal_decode_changes": int(security_report.get("literalDecodeChanges") or 0),\n                "hostname_changes": int(security_report.get("hostnameChanges") or 0),\n                "percent_decode_changes": int(security_report.get("percentDecodeChanges") or 0),\n                "html_entity_decode_reorders": int(security_report.get("htmlEntityDecodeReorders") or 0),\n                "console_sink_changes": int(security_report.get("consoleSinkChanges") or 0),\n                "console_shadow": bool(security_report.get("consoleShadow")),\n            }]\n        patched = security_hardened\n        assert_hardened(patched.decode("utf-8", errors="strict"))\n'''
        text = text.replace(anchor, block + anchor, 1)

    post_anchor = "        patched = purified\n"
    post_assert = "        assert_hardened(patched.decode(\"utf-8\", errors=\"strict\"))\n"
    if post_assert not in text[text.index(post_anchor): text.index(post_anchor) + 300]:
        if post_anchor not in text:
            raise ValueError("post-purification assignment anchor missing")
        text = text.replace(post_anchor, post_anchor + post_assert, 1)

    return text


def assert_contract(text: str) -> None:
    required = (
        IMPORT.strip(),
        MARKER,
        "security_hardened, security_report = harden_bytes(patched)",
        '"scope": "all-published-providers"',
        'assert_hardened(patched.decode("utf-8", errors="strict"))',
        "purified, purification = purify_bytes(patched)",
    )
    for value in required:
        if value not in text:
            raise AssertionError(f"missing published security finalization contract: {value}")
    terminal = text.index("        if terminal_quarantine:")
    hardening = text.index("security_hardened, security_report = harden_bytes(patched)")
    purification = text.index("purified, purification = purify_bytes(patched)")
    digest = text.index("digest = hashlib.sha256(patched).hexdigest()")
    if not (terminal < hardening < purification < digest):
        raise AssertionError("published security finalization order is not provider-state independent")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = REAPPLY.read_text(encoding="utf-8")
    normalized = normalize(current)
    assert_contract(normalized)
    if args.check:
        if current != normalized:
            raise SystemExit("published security finalization normalization required")
        print("published security finalization contract is normalized")
        return 0
    if current != normalized:
        REAPPLY.write_text(normalized, encoding="utf-8")
        print("published security finalization contract normalized")
    else:
        print("published security finalization contract already normalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
