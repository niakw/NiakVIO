#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "tv": ROOT / ".github/workflows/native-tv-route-reader.yml",
    "mobile_android": ROOT / ".github/workflows/native-mobile-android-reader.yml",
    "mobile_ios": ROOT / ".github/workflows/native-mobile-ios-reader.yml",
    "desktop": ROOT / ".github/workflows/native-desktop-reader-acceptance.yml",
}

texts = {name: path.read_text(encoding="utf-8") for name, path in WORKFLOWS.items()}
for name, workflow in texts.items():
    assert "\n  pull_request:" not in workflow, f"{name} native Lab must not block PR flow"
    assert "\n  push:" in workflow, f"{name} native Lab must collect evidence from main"
    assert "workflow_dispatch:" in workflow, f"{name} native Lab must remain manually runnable"
    assert "github.event.pull_request" not in workflow, f"{name} retained PR-only logic"

fixtures = "interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01"
for name in ("tv", "mobile_android", "desktop"):
    assert fixtures in texts[name], name
assert "interstellar" in texts["mobile_ios"]
assert "breaking-bad-s01e01" in (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8") or "fixture_by_type" in (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")

assert "strategy:" not in texts["tv"], "canonical TV Lab must be exactly one reader job, not sharded"
assert "matrix:" not in texts["tv"], "canonical TV Lab must not create fixture shards"
assert texts["tv"].count("tv-route-reader:") == 1
assert "brain-reader-repair" not in texts["tv"]
assert "brain-reader-repair" not in texts["mobile_android"]
assert "brain-reader-repair" not in texts["mobile_ios"]

learning = (ROOT / ".github/workflows/native-reader-learning-sync.yml").read_text(encoding="utf-8")
assert "workflow_run:" not in learning, "native Labs must never invoke Brain automatically"
assert "workflow_dispatch:" in learning
assert "run_id:" in learning

print("native Lab nonblocking contract passed: tv=single-job android=separate ios=separate brain=decoupled")
