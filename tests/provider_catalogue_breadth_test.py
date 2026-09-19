#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_provider_catalogue_breadth.py"
POLICY = json.loads((ROOT / ".github/provider-portfolio-policy.json").read_text(encoding="utf-8"))


def load_module():
    spec = importlib.util.spec_from_file_location("provider_catalogue_breadth", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    fixtures = module.build_fixtures()
    minimum = int(POLICY["retirement_guard"]["minimum_breadth_fixtures_before_redundancy_deactivation"])
    assert len(fixtures) >= minimum, (len(fixtures), minimum)

    identities = [module.fixture_identity(row["fixture"]) for row in fixtures]
    assert len(identities) == len(set(identities)), "breadth fixtures must be identity-deduplicated"
    groups = Counter(row["group"] for row in fixtures)
    assert groups["movie"] >= 9, groups
    assert groups["tv"] >= 8, groups
    assert groups["anime"] >= 8, groups
    assert groups["anime_movie"] >= 3, groups

    titles = {str(row["fixture"].get("title") or row["fixture"].get("label") or "") for row in fixtures}
    assert "Mon ninja et moi 3" in titles, titles
    assert "Revenant" in titles, titles
    assert "Mushoku Tensei: Jobless Reincarnation" in titles, titles
    assert "Interstellar" in titles, titles

    tasks, planned_fixtures, _vf_ids = module.build_plan()
    assert len(planned_fixtures) == len(fixtures)
    providers = {task["identity"]["provider_id"] for task in tasks}
    assert "streamzo" in providers, providers
    assert "anime-sama" in providers, providers
    assert any(
        task["identity"]["provider_id"] == "streamzo"
        and task["fixture"]["title"] == "Mon ninja et moi 3"
        for task in tasks
    ), "StreamZo must be measured on the rare Mon ninja fixture"

    # Breadth must continue measuring disabled providers, but no particular
    # provider is required to stay disabled forever: Quick repair and scoped
    # quarantine are explicitly allowed to reactivate recovered scopes.
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    disabled_ids = {
        str(row.get("id") or "").casefold()
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("enabled") is False
    }
    assert disabled_ids, "fixture expects at least one currently disabled provider"
    planned_disabled = {
        task["identity"]["provider_id"]
        for task in tasks
        if task["identity"]["provider_id"] in disabled_ids
    }
    assert planned_disabled, "disabled providers must remain measurable for repair/re-evaluation"

    assert module.french_audio_evidence({"language": "fr", "title": "1080p VF"}) is True
    assert module.french_audio_evidence({"language": "fr", "title": "1080p VOSTFR"}) is False
    assert module.french_audio_evidence({"language": "en", "title": "French audio 1080p"}) is True
    assert module.french_audio_evidence({"language": "en", "title": "VOSTFR"}) is False

    retirement = POLICY["retirement_guard"]
    assert retirement["portfolio_ranking_is_advisory"] is True
    assert retirement["automatic_deactivation_from_portfolio"] is False
    assert retirement["require_broad_catalogue_evidence_before_redundancy_deactivation"] is True
    assert retirement["require_no_unique_fixture_coverage"] is True
    assert retirement["require_no_unique_vf_fixture_coverage"] is True

    print(
        "provider catalogue breadth tests passed "
        f"({len(fixtures)} fixtures, {len(providers)} providers, {len(tasks)} planned executions, "
        f"{len(planned_disabled)} disabled providers still measurable)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
