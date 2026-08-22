#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/discover_upstream_provider_candidates.mjs"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def scraper(
    provider_id: str,
    *,
    language: str = "en",
    enabled: bool = True,
    formats: list[str] | None = None,
    description: str = "A useful upstream streaming provider with direct media.",
) -> dict:
    return {
        "id": provider_id,
        "name": provider_id.title(),
        "description": description,
        "version": "1.0.0",
        "supportedTypes": ["movie", "tv"],
        "filename": f"providers/{provider_id}.js",
        "enabled": enabled,
        "contentLanguage": [language],
        "formats": formats or ["m3u8"],
        "limited": False,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="niakvio-upstream-discovery-") as raw:
        tmp = Path(raw)
        fixtures = tmp / "fixtures"
        config = tmp / "config.json"
        catalog = tmp / "catalog.json"
        output = tmp / "candidates.json"

        write(config, {
            "schema_version": 1,
            "upstreams": [
                {"id": "gowaru", "repository": "Gowaru/gowaru-nuvio-providers", "branch": "main", "manifest": "manifest.json"},
                {"id": "aio", "repository": "NuvioPlugin/All-in-One-Nuvio", "branch": "main", "manifest": "manifest.json"},
                {"id": "yoru", "repository": "yoruix/nuvio-providers", "branch": "main", "manifest": "manifest.json"},
            ],
        })
        write(catalog, {
            "providers": [
                {"canonicalId": "already-known", "scraper": {"id": "already-known"}},
            ]
        })
        write(fixtures / "gowaru.json", {"scrapers": [
            scraper("already-known", language="fr"),
            scraper("new-french", language="fr"),
            scraper("torrentio", language="fr"),
        ]})
        write(fixtures / "aio.json", {"scrapers": [
            scraper("new-french", language="fr", formats=["mp4"]),
            scraper("new-english", language="en", enabled=False, formats=["unknown"]),
        ]})
        write(fixtures / "yoru.json", {"scrapers": [
            scraper("new-anime", language="fr", formats=["m3u8"]),
        ]})

        run = subprocess.run([
            "node", str(SCRIPT),
            "--config", str(config),
            "--catalog", str(catalog),
            "--fixture-dir", str(fixtures),
            "--output", str(output),
        ], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stdout + run.stderr
        assert "FIELD_UPSTREAM_PROVIDER_DISCOVERY" in run.stdout

        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["configuredSourceCount"] == 3
        assert report["successfulSourceCount"] == 3
        assert report["errors"] == []
        assert report["policy"]["autoImportAllowed"] is False
        assert report["policy"]["autoActivationAllowed"] is False
        assert report["policy"]["humanReviewRequired"] is True
        assert report["policy"]["upstreamWritesAllowed"] is False
        assert report["policy"]["p2pExcluded"] is True

        by_id = {row["canonicalId"]: row for row in report["candidates"]}
        assert "already-known" not in by_id
        assert "torrentio" not in by_id
        assert set(by_id) == {"new-french", "new-english", "new-anime"}

        french = by_id["new-french"]
        assert french["interesting"] is True
        assert french["upstreams"] == ["aio", "gowaru"]
        assert french["upstreamRepositories"] == [
            "Gowaru/gowaru-nuvio-providers",
            "NuvioPlugin/All-in-One-Nuvio",
        ]
        assert set(french["formats"]) == {"m3u8", "mp4"}
        assert french["autoImportAllowed"] is False
        assert french["reviewRequired"] is True
        assert "french_content" in french["reasons"]

        assert by_id["new-anime"]["interesting"] is True
        assert by_id["new-english"]["score"] < french["score"]
        assert report["interestingCandidateCount"] >= 2

    print("upstream provider discovery tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
