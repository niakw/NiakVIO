#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def constant(source: str, name: str) -> int:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*([0-9_]+)\s*;", source)
    if not match:
        raise AssertionError(f"missing {name}")
    return int(match.group(1).replace("_", ""))


def main() -> int:
    lab = (ROOT / "scripts/nuvio_client_lab.cjs").read_text(encoding="utf-8")
    provider_timeout = constant(lab, "DEFAULT_TIMEOUT_MS")
    playback_timeout = constant(lab, "DEFAULT_PLAYBACK_TIMEOUT_MS")
    assert provider_timeout >= 60_000, provider_timeout
    assert playback_timeout >= 18_000, playback_timeout

    presentation = (ROOT / "engine_v2/src/stream-presentation.mjs").read_text(encoding="utf-8")
    for token in (
        "const streamTitle =",
        "title: streamTitle",
        "name: streamTitle",
        "badgeIds: buildBadgeIds(facts)",
        "displayBadges: buildBadges(facts)",
        "presentationFacts: facts",
    ):
        assert token in presentation, token

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest.get("scrapers") or []) == 96

    # Historical 12-15 s TV compatibility publisher must stay dormant. It is
    # retained for provenance/tests only and must not be called by a workflow.
    authority = "publish_nuvio_tv_compat_v2.py"
    workflow_refs = []
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        if authority in text:
            workflow_refs.append(workflow.name)
    assert workflow_refs == [], f"legacy 12-15s TV compatibility publisher became authoritative: {workflow_refs}"

    print(
        "core runtime non-regression contract passed "
        f"providers=96 provider_timeout_ms={provider_timeout} playback_timeout_ms={playback_timeout} "
        "presentation=quality-bearing-title+name badges=preserved legacy_15s_publisher=dormant"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
