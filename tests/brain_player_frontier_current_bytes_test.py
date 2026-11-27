#!/usr/bin/env python3
"""Exact-current player frontier must mutate real published bytes in isolation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


frontier_mod = load_module(
    "player_frontier_current_bytes_source",
    SCRIPTS / "fill_brain_learning_guidance_gaps.py",
)
runtime = load_module(
    "player_frontier_current_bytes_runtime",
    SCRIPTS / "adaptive_runtime" / "runtime_repair.py",
)

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
source_history = json.loads(
    (ROOT / "automation/brain-catalogue-source-probe-history.json").read_text(encoding="utf-8")
)
native_history = json.loads(
    (ROOT / "automation/brain-android-tv-emulator-history.json").read_text(encoding="utf-8")
)
config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))

frontier = sorted(
    frontier_mod.attested_source_player_target_frontier(
        source_history, native_history, manifest, ROOT,
    )
)
if not frontier:
    print("FIELD_BRAIN_PLAYER_FRONTIER_CURRENT_BYTES providers=0 skipped=true reason=no-exact-current-frontier")
    raise SystemExit(0)

rows = {
    str(row.get("id") or "").strip().casefold(): row
    for row in manifest.get("scrapers") or []
    if isinstance(row, dict) and row.get("enabled") is True
}
checked = 0
for provider in frontier[:4]:
    row = rows.get(provider)
    assert isinstance(row, dict), (provider, "missing active manifest row")
    filename = str(row.get("filename") or "").strip()
    assert filename.startswith("providers/") and ".." not in filename, (provider, filename)
    published = ROOT / filename
    original = published.read_bytes()
    original_digest = hashlib.sha256(original).hexdigest()

    candidate = {
        "key": f"published:{provider}",
        "canonical_id": provider,
        "source": "published-exact-current",
        "local_path": filename,
        "bytes": len(original),
        "sha256": original_digest,
        "local_patches": [],
        "metadata": {
            "name": str(row.get("name") or provider),
            "supportedTypes": list(row.get("supportedTypes") or []),
        },
        "brain_repair_plan": {
            "failureClass": "media_extraction_gap",
            "experimentVariant": 0,
            "experimentGeneration": 1,
            "llmAdvisorApplied": True,
            "llmAdvisorProfile": "player_media_extractor_v1",
            "allowedProfiles": ["player_media_extractor_v1"],
            "llmAdvisorExperiment": {
                "terminalOnly": True,
                "routePolicy": "owned_only",
                "recipePolicy": "current_plus_provider",
                "roleOrder": ["player", "source", "api", "episode", "detail"],
                "maxDepth": 4,
                "maxPages": 12,
                "maxEmbeds": 16,
                "maxRecipePasses": 3,
            },
        },
    }
    result = {
        "key": candidate["key"],
        "status": "no_streams",
        "evidence": {"streams_playable": 0, "streams_returned": 0},
        "tests": [],
    }

    with tempfile.TemporaryDirectory(prefix=f"brain-player-current-{provider}-") as tmp:
        stage = Path(tmp)
        staged = stage / filename
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(original)

        profiles = runtime.matching_profiles(
            candidate, result, original.decode("utf-8"), config,
        )
        assert "player_media_extractor_v1" in profiles, (provider, profiles)

        repaired, error = runtime.create_repair_candidate(
            stage, candidate, "player_media_extractor_v1", 1,
        )
        assert error is None and isinstance(repaired, dict), (provider, repaired, error)
        assert repaired["runtime_repair"]["profile"] == "player_media_extractor_v1", repaired
        assert repaired["runtime_repair"]["strategy"] == "player_media_extractor_v1", repaired

        mutated = staged.read_bytes()
        assert mutated != original, (provider, "player profile made no byte change")
        assert hashlib.sha256(mutated).hexdigest() != original_digest
        assert int(repaired.get("bytes") or 0) == len(mutated)
        records = repaired.get("local_patches") or []
        assert records and records[-1].get("profile") == "player_media_extractor_v1", records

        check_file = stage / "candidate.js"
        shutil.copyfile(staged, check_file)
        check = subprocess.run(
            ["node", "--check", str(check_file)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        assert check.returncode == 0, (provider, check.stderr)

    # The test is isolation-only: repository production bytes must remain exact.
    assert hashlib.sha256(published.read_bytes()).hexdigest() == original_digest
    checked += 1

print(
    "FIELD_BRAIN_PLAYER_FRONTIER_CURRENT_BYTES "
    f"providers={checked} profile=player_media_extractor_v1 "
    "bytes_mutated=true syntax=true production_write=false"
)
