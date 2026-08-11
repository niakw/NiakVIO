#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTER = ROOT / "scripts" / "promote_candidates.py"
TEST = ROOT / "tests" / "ci_preservation_policy_test.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one migration anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    text = PROMOTER.read_text(encoding="utf-8")

    text = replace_once(
        text,
        'LKG_PATH = ROOT / "provider-lkg.json"\n',
        'LKG_PATH = ROOT / "provider-lkg.json"\nACTIVATION_LKG_PATH = ROOT / "provider-activation-lkg.json"\n',
        "activation LKG constant",
    )

    text = replace_once(
        text,
        '    availability_states = availability.get("providers", {})\n\n    entries: dict[str, dict[str, Any]] = {}\n',
        '    availability_states = availability.get("providers", {})\n'
        '    activation_lkg_payload = load_json(ACTIVATION_LKG_PATH, {}) or {}\n'
        '    activation_lkg_ids = {\n'
        '        canonical_id(str(value))\n'
        '        for value in activation_lkg_payload.get("active_ids", [])\n'
        '        if str(value).strip()\n'
        '    }\n\n'
        '    entries: dict[str, dict[str, Any]] = {}\n',
        "activation LKG load",
    )

    old_preserve = '''            old_filename = old_entry.get("filename") if isinstance(old_entry, dict) else None
            old_target = (ROOT / old_filename).resolve() if isinstance(old_filename, str) else None
            old_artifact_available = bool(
                old_target
                and is_under(old_target, ROOT / "providers")
                and old_target.exists()
            )
            preserve_current = (
                not enabled
                and bool(old_entry.get("enabled", False))
                and not auto_disabled
                and upstream_enabled
                and old_artifact_available
                and observed_status in preserve_statuses
                and not metadata_is_excluded(old_entry, sources)
            )
'''
    new_preserve = '''            old_filename = old_entry.get("filename") if isinstance(old_entry, dict) else None
            old_target = (ROOT / old_filename).resolve() if isinstance(old_filename, str) else None
            old_artifact_available = bool(
                old_target
                and is_under(old_target, ROOT / "providers")
                and old_target.exists()
            )
            old_was_enabled = bool(old_entry.get("enabled", False))
            current_ci_inconclusive = (
                str(selected.get("health", {}).get("ci_classification") or "")
                == "inconclusive"
            )
            restore_activation_lkg = bool(
                cid in activation_lkg_ids
                and current_ci_inconclusive
                and gates.get("01_policy_safe_no_p2p", {}).get("passed", False)
            )
            preserve_current = (
                not enabled
                and (old_was_enabled or restore_activation_lkg)
                and not auto_disabled
                and upstream_enabled
                and old_artifact_available
                and observed_status in preserve_statuses
                and not metadata_is_excluded(old_entry, sources)
            )
'''
    text = replace_once(text, old_preserve, new_preserve, "CI-inconclusive LKG restoration")

    text = replace_once(
        text,
        '                    "preserved_reason": "ci_uncertain_kept_last_published_artifact",\n                    "preserved_candidate_key": selected.get("key"),\n',
        '                    "preserved_reason": "ci_uncertain_kept_last_published_artifact",\n'
        '                    "restored_from_activation_lkg": bool(restore_activation_lkg and not old_was_enabled),\n'
        '                    "preserved_candidate_key": selected.get("key"),\n',
        "provenance LKG restoration marker",
    )

    text = replace_once(
        text,
        '                        "action": "preserved-current-enabled-ci-uncertain",\n                        "enabled": True,\n',
        '                        "action": (\n'
        '                            "restored-activation-lkg-enabled-ci-uncertain"\n'
        '                            if restore_activation_lkg and not old_was_enabled\n'
        '                            else "preserved-current-enabled-ci-uncertain"\n'
        '                        ),\n'
        '                        "enabled": True,\n'
        '                        "restored_from_activation_lkg": bool(restore_activation_lkg and not old_was_enabled),\n',
        "report LKG restoration marker",
    )

    PROMOTER.write_text(text, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    anchor = "assert 'old_artifact_available' in promoter\n"
    additions = (
        anchor
        + "assert 'ACTIVATION_LKG_PATH' in promoter\n"
        + "assert 'activation_lkg_ids' in promoter\n"
        + "assert 'current_ci_inconclusive' in promoter\n"
        + "assert 'restore_activation_lkg' in promoter\n"
        + "assert 'restored-activation-lkg-enabled-ci-uncertain' in promoter\n"
        + "assert 'restored_from_activation_lkg' in promoter\n"
        + "assert 'gates.get(\"01_policy_safe_no_p2p\", {}).get(\"passed\", False)' in promoter\n"
    )
    if "assert 'restore_activation_lkg' in promoter" not in test:
        if test.count(anchor) != 1:
            raise SystemExit("CI preservation test anchor changed")
        test = test.replace(anchor, additions, 1)
    TEST.write_text(test, encoding="utf-8")

    # Strong migration-time assertions: the old enabled-only predicate must be
    # gone from the preservation branch, while all safety predicates remain.
    final = PROMOTER.read_text(encoding="utf-8")
    required = [
        'ACTIVATION_LKG_PATH = ROOT / "provider-activation-lkg.json"',
        "cid in activation_lkg_ids",
        '== "inconclusive"',
        'gates.get("01_policy_safe_no_p2p", {}).get("passed", False)',
        "and not auto_disabled",
        "and upstream_enabled",
        "and old_artifact_available",
        "and observed_status in preserve_statuses",
        "restored-activation-lkg-enabled-ci-uncertain",
    ]
    missing = [value for value in required if value not in final]
    if missing:
        raise SystemExit("post-migration promoter assertions failed: " + ", ".join(missing))

    print("activation LKG inconclusive restoration migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
