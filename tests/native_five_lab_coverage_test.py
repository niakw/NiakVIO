#!/usr/bin/env python3
"""The native acceptance surface is exactly five first-class client/platform labs."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
android=(ROOT/".github/workflows/native-mobile-android-reader.yml").read_text(encoding="utf-8")
ios=(ROOT/".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8")
desktop=(ROOT/".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

for text in (android,ios,desktop):
    assert "workbench/provider-v3-performance-playback" in text
    assert ".github/triggers/full-native-lab-validation.json" in text

# 1 TV Android + 1 Mobile Android. 25 s is the settled per-provider native
# budget used by both Android clients; keep this contract aligned with the
# authoritative reader workflow rather than the superseded 15 s migration value.
assert "tv-route-reader:" in android
assert "mobile-android-reader:" in android
assert 'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS: "25000"' in android
assert "run_native_corpus_tv_suite.sh" in android
assert "run_native_corpus_mobile_suite.sh" in android
assert android.count("gate_native_declared_provider_matrix.py") >= 2

# 1 Mobile iOS
assert "mobile-ios-reader:" in ios
assert "runs-on: macos-26" in ios
assert "run_native_corpus_ios_suite.sh" in ios
assert "gate_native_declared_provider_matrix.py" in ios
assert "|| '40000'" in ios

# 2 Desktop matrix entries
assert "runner: macos-15" in desktop and "os_name: macos" in desktop
assert "runner: windows-2022" in desktop and "os_name: windows" in desktop
assert "run_native_corpus_desktop_suite.sh" in desktop
assert "gate_native_declared_provider_matrix.py" in desktop

platforms=["TVAndroid","MobileAndroid","MobileIOS","DesktopMACOS","DesktopWindows"]
assert len(platforms)==5 and len(set(platforms))==5

manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
rows=manifest.get("scrapers") or []
assert len(rows)==96

valid={"movie","tv","anime"}
canonical_route_counts={kind:0 for kind in valid}
transport_route_counts={kind:0 for kind in valid}
for row in rows:
    provider=str(row.get("id") or "<unknown>")
    transport=[str(v).strip().lower() for v in (row.get("supportedTypes") or []) if str(v).strip()]
    canonical=[str(v).strip().lower() for v in (row.get("canonicalSupportedTypes") or transport) if str(v).strip()]
    assert transport and canonical, provider
    assert set(transport)<=valid, (provider,transport)
    assert set(canonical)<=valid, (provider,canonical)
    assert set(canonical)<=set(transport), (provider,canonical,transport)
    for kind in valid:
        canonical_route_counts[kind]+=int(kind in canonical)
        transport_route_counts[kind]+=int(kind in transport)
    if set(canonical)=={"anime"}:
        # Anime providers are semantically anime-only, but Nuvio must be able to
        # launch both episodic anime and anime movies through tv/movie transport.
        assert {"anime","tv","movie"}<=set(transport), (provider,transport)

# Do not freeze transport counts to an old manifest shape: compatible launch
# aliases legitimately increase them. Canonical counts remain the semantic
# capability surface, while the native matrix traverses the declared transport
# surface actually consumed by Nuvio.
assert transport_route_counts["movie"]>=canonical_route_counts["movie"]
assert transport_route_counts["tv"]>=canonical_route_counts["tv"]
assert transport_route_counts["anime"]>=canonical_route_counts["anime"]
assert sum(transport_route_counts.values())>=sum(canonical_route_counts.values())
assert canonical_route_counts["anime"]>0

print(
    "NATIVE_FIVE_LABS_OK platforms="+",".join(platforms)
    +" providers=96 canonical_routes="+str(sum(canonical_route_counts.values()))
    +" transport_routes="+str(sum(transport_route_counts.values()))
    +" canonical="+json.dumps(canonical_route_counts,sort_keys=True)
    +" transport="+json.dumps(transport_route_counts,sort_keys=True)
)
