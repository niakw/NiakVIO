#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTER = ROOT / "scripts" / "promote_candidates.py"
TEST = ROOT / "tests" / "ci_preservation_policy_test.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = PROMOTER.read_text(encoding="utf-8")

    old = '''            old_entry = existing.get(cid, {})
            observed_status = str(selected.get("health", {}).get("status", "runtime_error"))
            upstream_enabled = bool(selected.get("metadata", {}).get("enabled", True))
            preserve_statuses = {
'''
    new = '''            old_entry = existing.get(cid, {})
            observed_status = str(selected.get("health", {}).get("status", "runtime_error"))
            selected_upstream_enabled = bool(selected.get("metadata", {}).get("enabled", True))
            # A published-baseline candidate reflects our previous local manifest,
            # not the current upstream activation declaration. When baseline
            # protection selects it because every live probe is inconclusive,
            # derive the upstream veto from current non-baseline manifests.
            live_upstream_variants = [
                variant
                for variant in variants
                if str(variant.get("source") or "") != "published-baseline"
            ]
            upstream_enabled = (
                any(
                    bool((variant.get("metadata") or {}).get("enabled", True))
                    for variant in live_upstream_variants
                )
                if live_upstream_variants
                else selected_upstream_enabled
            )
            if upstream_enabled and "upstream_disabled" in blockers:
                blockers = [value for value in blockers if value != "upstream_disabled"]
            preserve_statuses = {
'''
    text = replace_once(text, old, new, "live upstream preservation semantics")

    # Make the provenance/report explicit enough to diagnose future activation
    # decisions without confusing a local baseline flag with current upstream.
    old_prov = '''                    "restored_from_activation_lkg": bool(restore_activation_lkg and not old_was_enabled),
                    "preserved_candidate_key": selected.get("key"),
'''
    new_prov = '''                    "restored_from_activation_lkg": bool(restore_activation_lkg and not old_was_enabled),
                    "preservation_upstream_enabled": upstream_enabled,
                    "preservation_live_upstream_sources": sorted(
                        {
                            str(variant.get("source") or "")
                            for variant in live_upstream_variants
                            if str(variant.get("source") or "")
                        }
                    ),
                    "preserved_candidate_key": selected.get("key"),
'''
    text = replace_once(text, old_prov, new_prov, "preservation provenance")

    old_report = '''                        "restored_from_activation_lkg": bool(restore_activation_lkg and not old_was_enabled),
                        "activation_eligible": False,
'''
    new_report = '''                        "restored_from_activation_lkg": bool(restore_activation_lkg and not old_was_enabled),
                        "preservation_upstream_enabled": upstream_enabled,
                        "activation_eligible": False,
'''
    text = replace_once(text, old_report, new_report, "preservation report")

    PROMOTER.write_text(text, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    anchor = "assert 'restore_activation_lkg' in promoter\n"
    additions = (
        anchor
        + "assert 'live_upstream_variants' in promoter\n"
        + "assert 'published-baseline' in promoter\n"
        + "assert 'preservation_upstream_enabled' in promoter\n"
        + "assert 'preservation_live_upstream_sources' in promoter\n"
        + "assert 'if live_upstream_variants' in promoter\n"
        + "assert 'if upstream_enabled and \"upstream_disabled\" in blockers' in promoter\n"
    )
    if "assert 'live_upstream_variants' in promoter" not in test:
        if test.count(anchor) != 1:
            raise SystemExit("CI preservation test anchor changed")
        test = test.replace(anchor, additions, 1)
    TEST.write_text(test, encoding="utf-8")

    final = PROMOTER.read_text(encoding="utf-8")
    required = [
        'if str(variant.get("source") or "") != "published-baseline"',
        'bool((variant.get("metadata") or {}).get("enabled", True))',
        'if live_upstream_variants',
        'else selected_upstream_enabled',
        'if upstream_enabled and "upstream_disabled" in blockers',
        'preservation_upstream_enabled',
        'preservation_live_upstream_sources',
    ]
    missing = [value for value in required if value not in final]
    if missing:
        raise SystemExit("post-migration assertions failed: " + ", ".join(missing))

    print("live upstream activation preservation migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
