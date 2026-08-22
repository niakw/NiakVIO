#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/report_new_upstream_providers.py"
WORKFLOW = ROOT / ".github/workflows/weekly-upstream-provider-discovery.yml"
SOURCES = ROOT / "sources.json"


def load_module():
    spec = importlib.util.spec_from_file_location("weekly_upstream_provider_discovery", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate(
    cid: str,
    source: str,
    *,
    language: list[str] | None = None,
    types: list[str] | None = None,
    formats: list[str] | None = None,
    enabled: bool = True,
    manifest_origin: str = "live",
) -> dict:
    return {
        "canonical_id": cid,
        "upstream_id": cid.upper(),
        "source": source,
        "source_priority": {"gowaru": 0, "aio": 1, "yoru": 2}.get(source, 99),
        "manifest_origin": manifest_origin,
        "metadata": {
            "id": cid.upper(),
            "name": cid.title(),
            "enabled": enabled,
            "contentLanguage": language or [],
            "supportedTypes": types or [],
            "formats": formats or [],
        },
        "canonical_metadata": {
            "contentLanguage": language or [],
            "supportedTypes": types or [],
            "formats": formats or [],
        },
    }


def main() -> int:
    module = load_module()
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    assert set(sources.get("upstreams") or {}) == {"gowaru", "aio", "yoru"}

    catalog = {
        "providers": [
            {"canonicalId": "known"},
            {"canonicalId": "existing-provider"},
        ]
    }
    stage = {
        "upstreams": {
            "gowaru": {"status": "loaded"},
            "aio": {"status": "loaded"},
            "yoru": {"status": "loaded_from_upstream_lkg"},
        },
        "candidates": [
            candidate("known", "gowaru", language=["fr"], types=["movie"]),
            candidate("new-french", "aio", language=["fr"], types=["movie", "tv"], formats=["m3u8"]),
            candidate("new-french", "yoru", language=["fr"], types=["movie", "tv"], formats=["m3u8"]),
            candidate("new-anime", "gowaru", language=["en"], types=["anime"], formats=["mp4"]),
            candidate("stale-snapshot-new", "yoru", language=["fr"], types=["movie"], manifest_origin="upstream_lkg"),
            # Baselines are intentionally ignored by the new-upstream detector.
            candidate("baseline-only", "published-baseline", language=["fr"], types=["movie"]),
        ],
    }
    report = module.build_report(stage, catalog, sources)
    assert report["configuredUpstreams"] == ["aio", "gowaru", "yoru"]
    assert report["newProviderCount"] == 2, report
    assert report["interestingProviderCount"] == 2, report
    assert [row["canonicalId"] for row in report["providers"]] == ["new-french", "new-anime"], report
    assert report["snapshotOnlyNewProviderIdsIgnored"] == ["stale-snapshot-new"], report
    french = report["providers"][0]
    assert french["sources"] == ["aio", "yoru"]
    assert french["variantCount"] == 2
    assert french["liveManifestObserved"] is True
    assert french["reviewRequired"] is True
    assert french["automaticImportAllowed"] is False
    assert french["automaticActivationAllowed"] is False
    assert report["policy"]["upstreamsReadOnly"] is True
    assert report["policy"]["niakvioCatalogMutationAllowed"] is False
    assert report["policy"]["liveManifestRequiredForNewProvider"] is True
    assert report["policy"]["nativeReaderProofRequiredBeforeFuturePromotion"] is True

    md = module.markdown(report)
    assert "new-french" in md.lower()
    assert "never imports, enables, disables or publishes" in md
    assert "LKG snapshot" in md

    workflow = WORKFLOW.read_text(encoding="utf-8")
    # Exactly one weekly schedule: day-of-week is constrained and no daily wildcard.
    cron_lines = [line.strip() for line in workflow.splitlines() if "cron:" in line]
    assert len(cron_lines) == 1, cron_lines
    fields = cron_lines[0].split("cron:", 1)[1].strip().strip("'\"").split()
    assert len(fields) == 5 and fields[4] not in {"*", ""}, fields
    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "python scripts/discover_candidates.py --require-all-upstreams" in workflow
    assert "--include-disabled" in workflow
    assert "scripts/report_new_upstream_providers.py" in workflow
    assert "git diff --exit-code -- provider_catalog.json manifest.json providers/ provider-overrides.json" in workflow
    assert "git push" not in workflow
    assert "gh pr" not in workflow
    assert "gh issue" not in workflow

    script_source = SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("provider_catalog.json').write", 'provider_catalog.json").write', "manifest.json').write", 'manifest.json").write'):
        assert forbidden not in script_source

    print("weekly upstream provider discovery tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
