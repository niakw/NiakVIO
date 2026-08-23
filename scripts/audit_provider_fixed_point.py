#!/usr/bin/env python3
"""Audit provider publication fixed-point convergence with actionable provider IDs.

This runs the same durable normalizers and preparation stages as the authoritative
Core finalizer inside a disposable CI checkout, then records exactly which
content-addressed provider references change on each publication pass. It avoids
an expensive --check while provider refs are already known to be moving, and
fails early when the exact changed set repeats.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AUDIT_REVISION = "stagnation-ids-v2"
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, text=True, check=check,
    )


def refs() -> dict[str, str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        str(row.get("id") or "").strip().casefold(): str(row.get("filename") or "")
        for row in data.get("scrapers") or []
        if isinstance(row, dict) and row.get("id")
    }


def short_ref(value: str) -> str:
    name = Path(value).name
    stem = name[:-3] if name.endswith(".js") else name
    return stem.rsplit("--", 1)[-1][:16] if "--" in stem else stem[-16:]


def main() -> int:
    print(f"FIELD_PROVIDER_FIXED_POINT_AUDIT revision={AUDIT_REVISION}", flush=True)
    # Mirror Core step 8 before the media/rebuild loop. Auditing the repository
    # sources without these materialized contracts diagnoses the wrong pipeline.
    run("scripts/normalize_provider_rebuild_safety.py", "--apply")
    run("scripts/normalize_core_fixed_point_contract.py", "--apply")
    run("scripts/normalize_provider_branding_pipeline.py", "--apply")

    # Mirror Core step 9 preparation exactly. Keep this sequence visibly aligned
    # with core-media-finalize-main.yml so provider IDs reported here are authoritative.
    run("scripts/normalize_core_media_policy.py", "--apply")
    run("scripts/apply_runtime_capability_upgrade_v4.py")
    run("scripts/build_provider_runtime_profiles.py")

    previous_changed: tuple[str, ...] | None = None
    for pass_no in range(1, 7):
        before = refs()
        run(str(REAPPLY))
        after = refs()
        changed = tuple(sorted(pid for pid in set(before) | set(after) if before.get(pid) != after.get(pid)))
        transitions = ",".join(
            f"{pid}:{short_ref(before.get(pid, ''))}>{short_ref(after.get(pid, ''))}"
            for pid in changed
        ) or "-"
        print(
            "FIELD_PROVIDER_FIXED_POINT_PASS "
            f"pass={pass_no} changed_count={len(changed)} ids={','.join(changed) or '-'}",
            flush=True,
        )
        print(
            "FIELD_PROVIDER_FIXED_POINT_TRANSITIONS "
            f"pass={pass_no} values={transitions}",
            flush=True,
        )

        if not changed:
            checked = run(str(REAPPLY), "--check", check=False)
            if checked.returncode == 0:
                print(f"FIELD_PROVIDER_FIXED_POINT_RESULT status=converged pass={pass_no}", flush=True)
                return 0
            print(
                f"FIELD_PROVIDER_FIXED_POINT_RESULT status=metadata_stale pass={pass_no}",
                flush=True,
            )
            return 5

        if previous_changed is not None and changed == previous_changed:
            print(
                "FIELD_PROVIDER_FIXED_POINT_RESULT status=stagnant "
                f"pass={pass_no} changed_count={len(changed)} ids={','.join(changed)}",
                flush=True,
            )
            return 3
        previous_changed = changed

    print(
        "FIELD_PROVIDER_FIXED_POINT_RESULT status=nonconvergent "
        f"changed_count={len(previous_changed or ())} ids={','.join(previous_changed or ())}",
        flush=True,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
