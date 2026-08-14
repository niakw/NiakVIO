#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "reapply_published_overrides.py"


def main() -> int:
    text = PATH.read_text(encoding="utf-8")

    mode_anchor = 'AUDIT_QUARANTINE_MODE = "catalogue_audit_safety_quarantine"\n'
    blocker_line = 'AUDIT_QUARANTINE_BLOCKER = "catalogue_audit_playable_identity_contradiction"\n'
    if blocker_line not in text:
        if mode_anchor not in text:
            raise SystemExit("audit quarantine mode constant missing")
        text = text.replace(mode_anchor, mode_anchor + blocker_line, 1)

    # Every inert quarantine is terminal for byte mutation, but only bundles
    # explicitly published with the audit-quarantine filename family inherit the
    # transient catalogue-audit activation blocker. Durable configured
    # quarantines (for example a client-lab duration contradiction) keep their
    # own configured_safety_quarantine evidence path.
    old_terminal = '''        provider_provenance = provenance_rows.get(provider_id) if provenance_rows else None
        audit_terminal_quarantine = (
            AUDIT_QUARANTINE_MARKER.encode("utf-8") in original
        )
        if audit_terminal_quarantine:
            patched = original
            records = []
        else:
'''
    new_terminal = '''        provider_provenance = provenance_rows.get(provider_id) if provenance_rows else None
        terminal_quarantine = (
            AUDIT_QUARANTINE_MARKER.encode("utf-8") in original
        )
        audit_terminal_quarantine = (
            terminal_quarantine
            and "--nuvio-audit-quarantine--" in relative
        )
        if terminal_quarantine:
            patched = original
            records = []
        else:
'''
    if old_terminal in text:
        text = text.replace(old_terminal, new_terminal, 1)
    elif new_terminal not in text:
        raise SystemExit("terminal quarantine split anchor missing")

    old_update = '''        provenance_updates[provider_id] = {
            "old": relative,
            "new": new_relative,
            "sha256": digest,
            "records": records,
            "audit_terminal_quarantine": audit_terminal_quarantine,
        }
'''
    new_update = '''        provenance_updates[provider_id] = {
            "old": relative,
            "new": new_relative,
            "sha256": digest,
            "records": records,
            "terminal_quarantine": terminal_quarantine,
            "audit_terminal_quarantine": audit_terminal_quarantine,
        }
'''
    if old_update in text:
        text = text.replace(old_update, new_update, 1)
    elif new_update not in text:
        raise SystemExit("provenance update anchor missing")

    old_sha = '''            if update.get("audit_terminal_quarantine") or "patched_sha256" in row or update["records"]:
                row["patched_sha256"] = update["sha256"]
'''
    new_sha = '''            if update.get("terminal_quarantine") or "patched_sha256" in row or update["records"]:
                row["patched_sha256"] = update["sha256"]
'''
    if old_sha in text:
        text = text.replace(old_sha, new_sha, 1)
    elif new_sha not in text:
        raise SystemExit("patched SHA anchor missing")

    old_configured = '''                blockers = [
                    str(value) for value in (row.get("activation_blockers") or [])
                    if str(value) and str(value) != "configured_safety_quarantine"
                ]
                row["activation_blockers"] = blockers + ["configured_safety_quarantine"]
'''
    new_configured = '''                blockers = [
                    str(value) for value in (row.get("activation_blockers") or [])
                    if str(value) and str(value) not in {"configured_safety_quarantine", AUDIT_QUARANTINE_BLOCKER}
                ]
                row["activation_blockers"] = blockers + ["configured_safety_quarantine"]
'''
    if old_configured in text:
        text = text.replace(old_configured, new_configured, 1)
    elif new_configured not in text:
        raise SystemExit("configured quarantine blocker anchor missing")

    PATH.write_text(text, encoding="utf-8")
    print("configured/catalogue quarantine provenance separation patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
