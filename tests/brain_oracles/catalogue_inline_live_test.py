#!/usr/bin/env python3
"""Real-byte, trust-boundary and offline source-shape regression tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/brain_oracles/probe_catalogue_inline_live.py"
spec = importlib.util.spec_from_file_location("catalogue_probe", SOURCE)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

REQ = {
    "schemaVersion": 1,
    "probeKind": "catalogue-inline-source-contract",
    "providerId": "sample-anime",
    "fixture": "mushoku-s01e01",
    "sourceRunId": "44781039914",
    "sourceNiakvioSha": "e7c7c9206182f27df4537465e614b1c5dfacb408",
    "providerArtifactSha256": "",
    "catalogueSlug": "mushoku-tensei",
    "season": 1,
    "voice": "vostfr",
    "proofAuthority": False,
    "publicationAuthority": False,
    "nativePlaybackAuthority": False,
    "providerMutationAuthority": False,
}
LEGACY = 'var eps1=["https://media.invalid/direct?secret=PRIVATE"];'
INLINE = """<!doctype html><html><script>
var eps1=["lien:PRIVATE_ID"];
var epsJeton="PRIVATE_JETON";
var epsMeta={"PRIVATE_ID":["server"]};
var lecteursInfos={"server":{"nom":"Player"}};
var languesDispo=["vostfr","vf"];
</script></html>"""


def write(root: Path, name: str, obj: dict) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    binary = b"synthetic-current-js-immutable\n"
    (root / "providers").mkdir()
    (root / "providers/sample.js").write_bytes(binary)
    request = dict(REQ, providerArtifactSha256=hashlib.sha256(binary).hexdigest())
    row = {
        "provider": "sample-anime", "fixture": "mushoku-s01e01",
        "nativeRunId": request["sourceRunId"],
        "sourceNiakvioSha": request["sourceNiakvioSha"],
        "providerArtifactSha256": request["providerArtifactSha256"],
        "manifestScope": "manifest.json", "appSelected": True,
        "readerEvidenceComplete": True, "nativeExtractionZeroObserved": True,
        "nativeSourceScriptShapePatterns": ["script_html_2xx", "script_http_missing"],
        **{name: False for name in (
            "proofAuthority", "publicationAuthority",
            "nativePlaybackAuthority", "providerMutationAuthority"
        )},
    }
    write(root, "automation/brain-android-tv-emulator-history.json", {
        "schemaVersion": 1, "authority": "official-android-tv-emulator-diagnostic-only",
        "rows": [row],
        **{k: False for k in (
            "proofAuthority", "publicationAuthority",
            "nativePlaybackAuthority", "providerMutationAuthority"
        )},
    })
    write(root, "manifest.json", {
        "scrapers": [{"id": "sample-anime", "filename": "providers/sample.js"}],
    })
    write(root, "provider-overrides.json", {
        "provider_patches": {"sample-anime": {
            "official_site": "https://current.example/",
            "domain_substitutions": {"previous.example": "current.example"},
            "provider_lego_options": {"scripts/provider_patches/sample.py": {
                "base": "https://current.example/",
                "fallbackBases": ["https://fallback.example/", "http://localhost/"],
                "languages": ["vostfr", "vf"],
            }},
        }},
    })
    write(root, "provider-hubs.json", {
        "providers": {"sample-anime": {
            "direct": "https://fallback.example/",
            "direct_candidates": ["https://third.example/", "https://user:pass@secrets.example/"],
        }},
    })
    attested, hosts = probe.attest(root, request)
    assert attested["providerId"] == "sample-anime"
    assert hosts == ["current.example", "fallback.example", "previous.example"], hosts

    paths = []
    def fake_fetch(url: str):
        paths.append(url)
        if url.endswith("/saison1/vostfr/"):
            return 200, INLINE, False, "", ""
        if url.endswith("/episodes.js"):
            return 404, "<html>PRIVATE 404</html>", False, "", ""
        if "/catalogue/?search=" in url:
            return 200, ('<!doctype html><html>'
                         '<a href="/catalogue/mushoku-tensei-extra/">matching</a>'
                         '<a href="https://evil.example/catalogue/private/">bad</a>'
                         '</html>'), False, "", ""
        if url.endswith("/vostfr/"):
            return 200, "<!doctype html><html>fallback</html>", False, "", ""
        return 200, LEGACY, False, "", ""

    report = probe.run(root, request, fetcher=fake_fetch)
    assert report["probeRequestCount"] == 12
    assert sum(x["catalogueSearchLinkCount"] == 1 for x in report["observations"]) == 3
    assert sum(x["catalogueSearchExactSlugPresent"] for x in report["observations"]) == 0
    assert sum(x["catalogueCandidateSlugUnverified"] == "mushoku-tensei-extra"
               for x in report["observations"]) == 3
    assert sum(x["catalogueCandidateTokenOverlapPercent"] == 100
               for x in report["observations"]) == 3
    assert report["inlineTokenResponseCount"] == 3
    assert probe.catalogue_search_matches(
        '<!doctype html><a href="/catalogue/mushoku-tensei/">exact</a>',
        "mushoku-tensei", "current.example"
    )[1] is True
    assert probe.catalogue_search_matches(
        '<!doctype html><a href="https://evil.example/catalogue/mushoku-tensei/">evil</a>',
        "mushoku-tensei", "current.example"
    ) == (0, False, "", 0)
    assert report["independentNetworkNotOfficialClient"] is True
    assert report["sourceContractVerifiedOnOfficialTv"] is False
    assert report["catalogueIdentityVerified"] is False
    assert report["episodeIdentityVerified"] is False
    assert sum(x["sourceShape"] == "catalogue_inline_token_episode"
               for x in report["observations"]) == 3
    assert sum(x["sourceShape"] == "script_http_missing"
               for x in report["observations"]) == 3
    for row_out in report["observations"]:
        assert row_out["routeKind"] in {
            "catalogue", "season_page", "legacy_script", "catalogue_search"
        }
        assert row_out["originHost"] in hosts
        assert row_out["httpStatusClass"] in {"2xx", "4xx"}
        assert row_out["httpStatus"] in {200, 404}
        assert row_out["redirectTargetHost"] == ""
    redirects = probe.run(
        root, request,
        fetcher=lambda url: (302, "", False, "", "fallback.example"),
    )
    assert redirects["probeRequestCount"] == 12
    assert redirects["inlineTokenResponseCount"] == 0
    assert all(x["httpStatus"] == 302
               and x["httpStatusClass"] == "3xx"
               and x["redirectTargetHost"] == "fallback.example"
               and x["redirectTargetCurated"] is True
               for x in redirects["observations"])
    for path in paths:
        assert "/api/lien.php" not in path
        assert "token=" not in path
        assert not any(p in path for p in ("PRIVATE", "secret", "player", "m3u8"))
    rendered = json.dumps(report)
    for secret in ("PRIVATE", "https://", "lien:", "epsJeton", "media.invalid"):
        assert secret not in rendered, secret
    for flag in (
        "proofAuthority", "publicationAuthority",
        "nativePlaybackAuthority", "providerMutationAuthority"
    ):
        assert report[flag] is False

    # Reject forged claims, stale provider bytes, untrusted origins and wrong
    # fixture instead of interpreting stale post-mutation tests as truth.
    for change in (
        {"publicationAuthority": True}, {"sourceRunId": "44781039915"},
        {"providerArtifactSha256": "f" * 64},
        {"catalogueSlug": "../private"}, {"voice": "unknown"},
        {"providerId": "other"},
    ):
        try:
            probe.attest(root, {**request, **change})
            raise AssertionError("accepted forged/stale evidence: " + str(change))
        except ValueError:
            pass
    assert probe.origin_host("http://localhost") == ""
    assert probe.origin_host("https://127.0.0.1") == ""
    assert probe.origin_host("https://user:pass@current.example") == ""
    assert probe.origin_host("https://current.example:8443/") == ""
    assert probe.origin_host("https://current.example/private?token=SECRET") == "current.example"
    # Redirects cannot escape the declared current catalogue or trusted hosts.
    handler = probe._CuratedRedirect(
        ("current.example", "fallback.example"), "mushoku-tensei"
    )
    request_url = urllib.request.Request("https://current.example/catalogue/mushoku-tensei/")
    def redirect(target: str):
        return handler.redirect_request(request_url, None, 301, "Moved", {}, target)
    assert redirect("https://evil.example/catalogue/mushoku-tensei/") is None
    assert redirect("https://current.example/other/path") is None
    assert redirect("http://fallback.example/catalogue/mushoku-tensei/") is None
    assert redirect("https://fallback.example/catalogue/mushoku-tensei/?token=SECRET") is None
    assert redirect("/catalogue/mushoku-tensei/saison1/vostfr/") is not None
    search_handler = probe._CuratedRedirect(
        ("current.example",), "mushoku-tensei"
    )
    search_request = urllib.request.Request(
        "https://current.example/catalogue/?search=mushoku%20tensei"
    )
    assert search_handler.redirect_request(
        search_request, None, 301, "Moved", {},
        "/catalogue/?search=mushoku%20tensei"
    ) is not None
    assert search_handler.redirect_request(
        search_request, None, 301, "Moved", {},
        "/api/lien.php?token=PRIVATE"
    ) is None
    assert redirect("https://fallback.example/catalogue/mushoku-tensei/saison1/vostfr/") is not None
    (root / "providers/sample.js").write_bytes(b"modified!")
    try:
        probe.attest(root, request)
        raise AssertionError("stale current JS accepted")
    except ValueError:
        pass

# Production provenance is deliberately not frozen into this offline contract.
# The workflow builder joins the current materialized bytes to the exact
# official-TV ledger row immediately before any network probe. Keeping an
# old production digest here would turn valid rematerialization into a test
# failure before that fail-closed current-byte attestation can run.
print("Source-contract probe: bounded offline inline/legacy/missing and negative authority checks passed; production bytes are attested dynamically")
