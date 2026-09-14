#!/usr/bin/env python3
"""The native acceptance surface is exactly five first-class client/platform labs."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CURRENT_PROVIDER_COUNT = 46
android = (ROOT / ".github/workflows/native-mobile-android-reader.yml").read_text(encoding="utf-8")
ios = (ROOT / ".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8")
desktop = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

for text in (android, ios, desktop):
    assert ".github/triggers/full-native-lab-validation.json" in text
    assert "workbench/provider-v3-performance-playback" not in text
    assert "workbench/provider-v3-recognition-routes-data" not in text

# 1 TV Android + 1 Mobile Android.
assert "tv-route-reader:" in android
assert "mobile-android-reader:" in android
assert 'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS: "25000"' in android
assert "run_native_corpus_tv_suite.sh" in android
assert "run_native_corpus_mobile_suite.sh" in android
assert android.count("gate_native_declared_provider_matrix.py") >= 2

# 1 Mobile iOS.
assert "mobile-ios-reader:" in ios
assert "runs-on: macos-26" in ios
assert "run_native_corpus_ios_suite.sh" in ios
assert "gate_native_declared_provider_matrix.py" in ios
assert "|| '25000'" in ios

# 2 Desktop matrix entries.
assert "runner: macos-15" in desktop and "os_name: macos" in desktop
assert "runner: windows-2022" in desktop and "os_name: windows" in desktop
assert "run_native_corpus_desktop_suite.sh" in desktop
assert "gate_native_declared_provider_matrix.py" in desktop

platforms = ["TVAndroid", "MobileAndroid", "MobileIOS", "DesktopMACOS", "DesktopWindows"]
assert len(platforms) == 5 and len(set(platforms)) == 5

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
rows = manifest.get("scrapers") or []
assert len(rows) == CURRENT_PROVIDER_COUNT

canonical_valid = {"movie", "tv", "anime"}
transport_valid = canonical_valid
canonical_route_counts = {kind: 0 for kind in canonical_valid}
transport_route_counts = {kind: 0 for kind in transport_valid}
for row in rows:
    provider = str(row.get("id") or "<unknown>")
    transport = [str(v).strip().lower() for v in (row.get("supportedTypes") or []) if str(v).strip()]
    canonical = [str(v).strip().lower() for v in (row.get("canonicalSupportedTypes") or transport) if str(v).strip()]
    assert transport and canonical, provider
    assert set(transport) <= transport_valid, (provider, transport)
    assert set(canonical) <= canonical_valid, (provider, canonical)
    assert set(canonical) <= set(transport), (provider, canonical, transport)
    for kind in canonical_valid:
        canonical_route_counts[kind] += int(kind in canonical)
    for kind in transport_valid:
        transport_route_counts[kind] += int(kind in transport)

    # Episodic anime-only providers need the Nuvio TV launch alias; no legacy
    # `series` alias is synthesized by the current renderer.
    if "anime" in canonical:
        assert "tv" in transport, (provider, canonical, transport)
    # Movie transport exists only for a provider with actual movie capability.
    assert ("movie" in transport) == ("movie" in canonical), (provider, canonical, transport)

# Never freeze yesterday's route totals: the anime -> TV alias may increase the
# launch matrix while canonical counts remain semantic.
for kind in canonical_valid:
    assert transport_route_counts[kind] >= canonical_route_counts[kind]
assert sum(transport_route_counts.values()) >= sum(canonical_route_counts.values())
assert canonical_route_counts["anime"] > 0

print(
    "NATIVE_FIVE_LABS_OK platforms=" + ",".join(platforms)
    + f" providers={CURRENT_PROVIDER_COUNT} canonical_routes=" + str(sum(canonical_route_counts.values()))
    + " transport_routes=" + str(sum(transport_route_counts.values()))
    + " canonical=" + json.dumps(canonical_route_counts, sort_keys=True)
    + " transport=" + json.dumps(transport_route_counts, sort_keys=True)
)