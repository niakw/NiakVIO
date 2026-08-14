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

    old_update = '''        provenance_updates[provider_id] = {
            "old": relative,
            "new": new_relative,
            "sha256": digest,
            "records": records,
        }
'''
    new_update = '''        provenance_updates[provider_id] = {
            "old": relative,
            "new": new_relative,
            "sha256": digest,
            "records": records,
            "audit_terminal_quarantine": audit_terminal_quarantine,
        }
'''
    if old_update in text:
        text = text.replace(old_update, new_update, 1)
    elif new_update not in text:
        raise SystemExit("provenance update anchor missing")

    old_sha = '''            if "patched_sha256" in row or update["records"]:
                row["patched_sha256"] = update["sha256"]
'''
    new_sha = '''            if update.get("audit_terminal_quarantine") or "patched_sha256" in row or update["records"]:
                row["patched_sha256"] = update["sha256"]
'''
    if old_sha in text:
        text = text.replace(old_sha, new_sha, 1)
    elif new_sha not in text:
        raise SystemExit("patched SHA anchor missing")

    old_policy = '''            manifest_overrides = configured_manifest_overrides(override_config, provider_id)
            if manifest_overrides.get("enabled") is False:
                row["activation_eligible"] = False
                row["strict_activation_eligible"] = False
                row["strict_grace_eligible"] = False
                row["historical_quality_grace_eligible"] = False
                row["runtime_evidence_eligible"] = False
                row["activation_mode"] = "configured_safety_quarantine"
                blockers = [
                    str(value) for value in (row.get("activation_blockers") or [])
                    if str(value) and str(value) != "configured_safety_quarantine"
                ]
                row["activation_blockers"] = blockers + ["configured_safety_quarantine"]
'''
    new_policy = '''            manifest_overrides = configured_manifest_overrides(override_config, provider_id)
            if update.get("audit_terminal_quarantine"):
                row["activation_eligible"] = False
                row["strict_activation_eligible"] = False
                row["strict_grace_eligible"] = False
                row["historical_quality_grace_eligible"] = False
                row["runtime_evidence_eligible"] = False
                row["activation_mode"] = AUDIT_QUARANTINE_MODE
                blockers = [
                    str(value) for value in (row.get("activation_blockers") or [])
                    if str(value) and str(value) not in {AUDIT_QUARANTINE_BLOCKER, "configured_safety_quarantine"}
                ]
                row["activation_blockers"] = blockers + [AUDIT_QUARANTINE_BLOCKER]
            elif manifest_overrides.get("enabled") is False:
                row["activation_eligible"] = False
                row["strict_activation_eligible"] = False
                row["strict_grace_eligible"] = False
                row["historical_quality_grace_eligible"] = False
                row["runtime_evidence_eligible"] = False
                row["activation_mode"] = "configured_safety_quarantine"
                blockers = [
                    str(value) for value in (row.get("activation_blockers") or [])
                    if str(value) and str(value) != "configured_safety_quarantine"
                ]
                row["activation_blockers"] = blockers + ["configured_safety_quarantine"]
'''
    if old_policy in text:
        text = text.replace(old_policy, new_policy, 1)
    elif new_policy not in text:
        raise SystemExit("activation provenance policy anchor missing")

    PATH.write_text(text, encoding="utf-8")
    print("audit quarantine provenance migration patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
