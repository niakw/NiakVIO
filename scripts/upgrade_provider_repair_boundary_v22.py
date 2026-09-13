#!/usr/bin/env python3
"""V22: make every Repair entrypoint use the current generic V21.12 boundary.

The fast targeted runner still declared V21.8 as its last live-census boundary,
while the long pipeline could replay the obsolete VoirAnime `.homes` V21.10
migration. Current live proof shows canonical VoirAnime upstream execution on
`voir-anime.to` and a direct replay of the old `.homes` plan returns zero.

This migration changes Repair orchestration only. It does not mutate provider
DATA, domains, manifests or bundles:
- Fast Repair explicitly applies/validates V21.12 before live recovery;
- long Repair stops replaying provider-specific stale V21.10;
- long Repair includes the provider-agnostic V21.12 migration;
- route-plan revision reports V21.12.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAST = ROOT / "scripts/run_provider_repair_fast_targeted_v20.py"
PIPE = ROOT / "scripts/run_provider_repair_pipeline_v6.py"
MARKER = "PROVIDER_REPAIR_CURRENT_BOUNDARY_V22"


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_fast() -> bool:
    text = FAST.read_text(encoding="utf-8")
    if MARKER in text:
        validate_fast(text)
        return False
    text = _once(
        text,
        '"""Run canonical targeted repair with V21.8 immediately before live recovery."""',
        '"""Run canonical targeted repair with the current V21.12 boundary before live recovery."""',
        "fast-docstring",
    )
    text = _once(
        text,
        'import upgrade_provider_composite_request_template_v21_8 as v218  # noqa: E402\n',
        'import upgrade_provider_composite_request_template_v21_8 as v218  # noqa: E402\n'
        'import upgrade_provider_runtime_reconstruction_v21_12 as v212  # noqa: E402\n',
        "fast-import-v212",
    )
    text = _once(
        text,
        '        v218.patch_materializer()\n        v218.patch_base()\n        sanitizer_v7.patch_overrides()\n',
        '        v218.patch_materializer()\n        v218.patch_base()\n'
        '        # PROVIDER_REPAIR_CURRENT_BOUNDARY_V22\n'
        '        # V21.12 is provider-agnostic and is the current live-recovery boundary.\n'
        '        v212.patch_recovery()\n'
        '        v212.patch_base()\n'
        '        sanitizer_v7.patch_overrides()\n',
        "fast-apply-v212",
    )
    text = _once(
        text,
        '        v218.validate_materializer()\n        v218.validate_base()\n        sanitizer_v7.validate_overrides()\n',
        '        v218.validate_materializer()\n        v218.validate_base()\n'
        '        v212.validate_recovery()\n'
        '        v212.validate_base()\n'
        '        sanitizer_v7.validate_overrides()\n',
        "fast-validate-v212",
    )
    text = _once(
        text,
        '            "all_v21_8_owners_before_census=1",\n            flush=True,\n        )\n',
        '            "all_v21_8_owners_before_census=1",\n            flush=True,\n        )\n'
        '        print(\n'
        '            "FIELD_PROVIDER_V21_12_BOUNDARY ready=true revision=v21.12 "\n'
        '            "explicit_season_mismatch_fail_closed=1 correlated_player_fallback=1 "\n'
        '            "identity_keyed_search_role_gated=1 obsolete_voiranime_homes_replay=0 "\n'
        '            "provider_specific_rules=0",\n'
        '            flush=True,\n'
        '        )\n',
        "fast-v212-marker",
    )
    FAST.write_text(text, encoding="utf-8")
    validate_fast(text)
    return True


def patch_pipeline() -> bool:
    text = PIPE.read_text(encoding="utf-8")
    changed = False
    stale_migration = '        "scripts/upgrade_provider_voiranime_homes_authority_v21_10.py",\n'
    if stale_migration in text:
        text = text.replace(stale_migration, "", 1)
        changed = True
    stale_test = '        "tests/provider_voiranime_homes_authority_v21_10_test.py",\n'
    if stale_test in text:
        text = text.replace(stale_test, "", 1)
        changed = True
    current_migration = '        "scripts/upgrade_provider_runtime_reconstruction_v21_12.py",\n'
    if current_migration not in text:
        anchor = '        "scripts/retire_provider_neko_sama_v21_11.py",\n'
        if text.count(anchor) != 1:
            raise AssertionError("pipeline-v211-anchor drifted")
        text = text.replace(anchor, anchor + current_migration, 1)
        changed = True
    if '"routePlanRevision": "v21.11"' in text:
        text = text.replace('"routePlanRevision": "v21.11"', '"routePlanRevision": "v21.12"', 1)
        changed = True
    marker_anchor = "    # This order is canonical. V16 (chained by base runtime V11) requires Source\n"
    if MARKER not in text:
        if text.count(marker_anchor) != 1:
            raise AssertionError("pipeline-comment-anchor drifted")
        text = text.replace(
            marker_anchor,
            f"    # {MARKER}\n"
            "    # V21.10's provider-specific `.homes` authority is historical evidence only;\n"
            "    # current Repair must not replay it. V21.12 is the generic live boundary.\n"
            + marker_anchor,
            1,
        )
        changed = True
    PIPE.write_text(text, encoding="utf-8")
    validate_pipeline(text)
    return changed


def validate_fast(text: str | None = None) -> None:
    value = text if text is not None else FAST.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "import upgrade_provider_runtime_reconstruction_v21_12 as v212",
        "v212.patch_recovery()",
        "v212.patch_base()",
        "v212.validate_recovery()",
        "v212.validate_base()",
        "FIELD_PROVIDER_V21_12_BOUNDARY ready=true revision=v21.12",
    ):
        if needle not in value:
            raise AssertionError(f"Fast Repair missing current boundary: {needle}")


def validate_pipeline(text: str | None = None) -> None:
    value = text if text is not None else PIPE.read_text(encoding="utf-8")
    if MARKER not in value:
        raise AssertionError("pipeline V22 marker missing")
    if '"scripts/upgrade_provider_runtime_reconstruction_v21_12.py"' not in value:
        raise AssertionError("pipeline does not apply V21.12")
    if '"scripts/upgrade_provider_voiranime_homes_authority_v21_10.py"' in value:
        raise AssertionError("pipeline still replays obsolete VoirAnime .homes authority")
    if '"tests/provider_voiranime_homes_authority_v21_10_test.py"' in value:
        raise AssertionError("pipeline still gates on obsolete VoirAnime .homes test")
    if '"routePlanRevision": "v21.12"' not in value:
        raise AssertionError("pipeline revision is not V21.12")


def main() -> int:
    fast_changed = patch_fast()
    pipeline_changed = patch_pipeline()
    validate_fast(); validate_pipeline()
    print(
        "PROVIDER_REPAIR_CURRENT_BOUNDARY_V22_OK "
        f"fast_changed={str(fast_changed).lower()} pipeline_changed={str(pipeline_changed).lower()} "
        "live_boundary=v21.12 obsolete_voiranime_homes_replay=0 provider_data_mutated=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
