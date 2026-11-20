#!/usr/bin/env python3
"""Deterministic source-probe tests: identity/bytes, privacy and network bounds."""
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[2] / "scripts/brain_oracles"
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("catalogue_source_probe", HERE / "catalogue_source_probe.py")
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

SHA, RUN = "a" * 40, "44781039914"
PROVIDER, FIXTURE = "anime-sama", "mushoku-tensei-s01e01"
TOKEN_PAGE = """<!doctype html><html><script>
var eps1=["lien:PRIVATE_TOKEN"];var epsJeton="SECRET";
var languesDispo=["vostfr","vf"];</script></html>"""

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    (root / "providers").mkdir()
    (root / "automation").mkdir()
    file = root / "providers/source.js"
    file.write_text("// baseline source", encoding="utf-8")
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    def write(path, obj):
        (root / path).write_text(json.dumps(obj), encoding="utf-8")
    write("manifest.json", {"scrapers": [{
        "id": PROVIDER, "filename": "providers/source.js", "enabled": True
    }]})
    write("provider-overrides.json", {"provider_patches": {
        PROVIDER: {
            "official_site": "https://first.example.org/",
            "provider_lego_options": {"scripts/provider_patches/example.py": {
                "base": "https://first.example.org/",
                "fallbackBases": ["https://second.example.org/"],
                "languages": ["vostfr", "vf"]
            }}
        }
    }})
    write("provider-hubs.json", {"providers": {PROVIDER: {
        "direct": "https://third.example.org/"
    }}})
    write("automation/brain-android-tv-emulator-history.json", {
        "schemaVersion": 1, "authority": "official-android-tv-emulator-diagnostic-only",
        "proofAuthority": False, "publicationAuthority": False,
        "nativePlaybackAuthority": False, "providerMutationAuthority": False,
        "rows": [{
            "provider": PROVIDER, "fixture": FIXTURE,
            "nativeRunId": RUN, "sourceNiakvioSha": SHA,
            "providerArtifactSha256": digest, "manifestScope": "manifest.json",
            "appSelected": True, "readerEvidenceComplete": True,
            "nativeExtractionZeroObserved": True,
            "nativeSourceScriptShapePatterns": ["script_http_missing", "script_html_2xx"],
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False, "providerMutationAuthority": False
        }]
    })
    request = {
        "schemaVersion": 1, "probeKind": "catalogue-inline-source-contract",
        "providerId": PROVIDER, "fixture": FIXTURE,
        "sourceRunId": RUN, "sourceNiakvioSha": SHA,
        "providerArtifactSha256": digest,
        "catalogueSlug": "mushoku-tensei-jobless-reincarnation",
        "season": 1, "voice": "vostfr",
        "proofAuthority": False, "publicationAuthority": False,
        "nativePlaybackAuthority": False, "providerMutationAuthority": False
    }
    observed_urls = []
    def fake_fetch(url):
        observed_urls.append(url)
        assert "/api/" not in url and "/player/" not in url
        if url == "https://first.example.org/catalogue/mushoku-tensei-jobless-reincarnation/":
            return (301, "", False, False,
                    "https://fourth.example.org/catalogue/mushoku-tensei-jobless-reincarnation/?token=SECRET")
        if url.endswith("episodes.js"):
            return 404, "<!doctype html><html><body>not found</body></html>", False, False, ""
        if "/saison1/vostfr/" in url:
            return 200, TOKEN_PAGE, False, False, ""
        return 200, "<!doctype html><html><body>shell</body></html>", False, False, ""

    result = probe.run(root, request, fake_fetch)
    assert len(observed_urls) == result["probeRequestCount"] == 12
    assert result["inlineTokenResponseCount"] == 3
    redirected = [row for row in result["observations"] if row["redirectObserved"]]
    assert len(redirected) == 1
    assert redirected[0]["redirectHostScope"] == "unregistered_candidate"
    assert redirected[0]["redirectTargetHost"] == "fourth.example.org"
    assert redirected[0]["redirectQueryPresent"] is True
    assert redirected[0]["redirectPathScope"] == "same_path"
    assert redirected[0]["redirectPathChangeKind"] == "exact_path"
    assert redirected[0]["redirectCandidateCatalogueSlug"] == ""
    assert all("fourth.example.org" not in url for url in observed_urls)
    assert sum(x["sourceShape"] == "script_http_missing"
               for x in result["observations"]) == 3
    assert {x["originHost"] for x in result["observations"]} == {
        "first.example.org", "second.example.org", "third.example.org"
    }
    assert all(row["redirectTargetHost"] == "" for row in result["observations"]
               if not row["redirectObserved"])
    assert result["independentNetworkNotOfficialClient"] is True
    assert result["sourceContractVerifiedOnOfficialTv"] is False
    assert result["publicationAuthority"] is False

    # No body, token, URL, cookies or media links survive serialization.
    rendered = json.dumps(result)
    for forbidden in ("PRIVATE_TOKEN", "SECRET", "lien:", "epsJeton", "https://"):
        assert forbidden not in rendered, forbidden

    for change in (
        {"providerArtifactSha256": "b" * 64},
        {"sourceRunId": "44781039915"},
        {"providerMutationAuthority": True},
        {"catalogueSlug": "../private"},
        {"voice": "ja"}
    ):
        try:
            probe.attest(root, {**request, **change})
        except ValueError:
            pass
        else:
            raise AssertionError("untrusted request accepted " + str(change))
    # Current provider JS must still have exactly the native-tested SHA256.
    file.write_text("changed provider source", encoding="utf-8")
    try:
        probe.attest(root, request)
    except ValueError as error:
        assert "provider bytes drifted" in str(error)
    else:
        raise AssertionError("provider artifact drift not rejected")

for url in (
    "http://first.example.org/", "https://127.0.0.1",
    "https://localhost", "https://a.internal", "https://a.example.invalid",
    "https://someone:secret@first.example.org", "https://first.example.org:8080"
):
    assert probe.origin(url) == "", url
assert probe.origin("https://first.example.org/") == "first.example.org"
unsafe = probe.redirect_target("https://first.example.org/foo", "http://127.0.0.1/?SECRET", ["first.example.org"])
assert unsafe["redirectHostScope"] == "unsafe_or_oversized" and unsafe["redirectTargetHost"] == ""
missing = probe.redirect_target("https://first.example.org/foo", "", ["first.example.org"])
assert missing["redirectHostScope"] == "location_missing"
same = probe.redirect_target("https://first.example.org/foo", "../bar?private=SECRET", ["first.example.org"])
assert same["redirectHostScope"] == "same_origin" and same["redirectQueryPresent"] is True
trailing = probe.redirect_target("https://first.example.org/catalogue/old/", "/catalogue/old", ["first.example.org"])
assert trailing["redirectPathChangeKind"] == "trailing_slash_only"
new_slug = probe.redirect_target(
    "https://first.example.org/catalogue/old/",
    "/catalogue/new-slug/?private=SECRET", ["first.example.org"]
)
assert new_slug["redirectPathChangeKind"] == "catalogue_slug_changed"
assert new_slug["redirectCandidateCatalogueSlug"] == "new-slug"
assert "SECRET" not in json.dumps(new_slug)
other_route = probe.redirect_target(
    "https://first.example.org/catalogue/old/saison1/vostfr/",
    "/catalogue/old/saison2/vostfr/", ["first.example.org"]
)
assert other_route["redirectPathChangeKind"] == "same_catalogue_other_path"

print("Source contract probe: bounded 12 GET, strict native SHA, privacy and negative tests passed")
