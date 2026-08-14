#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/native-corpus-device-lab.yml"
PREPARE = ROOT / "scripts/prepare_native_corpus_validation.py"
ANALYZER = ROOT / "scripts/analyze_native_corpus_results.cjs"
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
MANIFEST = ROOT / "manifest.json"

workflow = WORKFLOW.read_text(encoding="utf-8")
prepare = PREPARE.read_text(encoding="utf-8")
analyzer = ANALYZER.read_text(encoding="utf-8")
corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

expected_slugs = {
    "interstellar",
    "mon-ninja-et-moi-3",
    "breaking-bad-s01e01",
    "revenant-s01e01",
    "jujutsu-kaisen-s01e01",
    "mushoku-tensei-s01e01",
}
actual_slugs = {
    str(row.get("slug") or "")
    for row in corpus.get("fixtures", [])
    if isinstance(row, dict)
}
assert actual_slugs == expected_slugs, (actual_slugs, expected_slugs)

# Every title must be present in both the Desktop and Android matrix definitions.
for slug in sorted(expected_slugs):
    assert workflow.count(f"- {slug}") == 2, (slug, workflow.count(f"- {slug}"))

for required in (
    "NuvioMedia/NuvioDesktop.git",
    "NuvioMedia/NuvioMobile.git",
    "NuvioMedia/NuvioTV.git",
    "prepare_native_corpus_validation.py",
    "run_native_corpus_android_lab.sh",
    "analyze_native_corpus_results.cjs",
    "ReactiveCircus/android-emulator-runner@",
):
    assert required in workflow, required

# The expensive full corpus is deliberate/manual: normal provider changes must not
# automatically launch 12 native jobs. Promotion explicitly bumps the trigger once.
assert '.github/triggers/native-corpus-device-lab' in workflow
assert '"providers/**"' not in workflow
assert "provider-overrides.json" not in workflow.split("permissions:", 1)[0]

# Preparation must enumerate the manifest itself rather than silently shrinking
# back to the old per-fixture provider lists.
assert "def manifest_providers()" in prepare
assert 'manifest.get("scrapers", [])' in prepare
assert "stage_providers" in prepare
assert "fixtureRow" not in prepare
assert 'row.get("providers")' not in prepare

stageable = []
seen = set()
for row in manifest.get("scrapers", []):
    if not isinstance(row, dict):
        continue
    provider_id = str(row.get("id") or "").strip()
    filename = str(row.get("filename") or "").strip()
    key = provider_id.casefold()
    if not provider_id or not filename or key in seen:
        continue
    seen.add(key)
    stageable.append(provider_id)
assert len(stageable) >= 80, len(stageable)

# The broad lab performs real transport checks inside each official native runtime.
for required in (
    "java.net.HttpURLConnection",
    "probeTransport(row.url, row.headers)",
    "#EXTM3U",
    "hlsDuration",
    "FIELD_NATIVE_TRANSPORT",
    "media_hint64",
    "host64",
):
    assert required in prepare, required

# Never persist the complete provider URL or header values in public Actions output.
assert "url64=" not in prepare
assert "headers64=" not in prepare
assert "row.headers}" not in prepare

# Native rows are evaluated with the same identity engine used by the existing
# Nuvio client lab. HLS duration and transport evidence feed that same verdict path.
assert "streamIdentity" in analyzer
assert "fixture_duration_mismatch" in analyzer
assert "FIELD_NATIVE_CONTRADICTION" in analyzer
assert "FIELD_NATIVE_TRANSPORT_FAILURE" in analyzer
assert "FIELD_NATIVE_RUNTIME_ERROR" in analyzer
assert "FIELD_NATIVE_SLOW" in analyzer
assert "decode(f.url64)" not in analyzer
assert "safeSyntheticUrl" in analyzer

print(
    "native corpus device lab coverage tests passed: "
    f"fixtures={len(expected_slugs)} stageable_providers={len(stageable)} devices=3 sanitized_transport=true"
)
