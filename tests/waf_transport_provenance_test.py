#!/usr/bin/env python3
"""Real-source WAF evidence must not inherit current authority from old lanes."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stamp_waf_transport_provenance import published_bundle_digests, stamp_fresh
from merge_waf_latest_evidence import merge

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "providers").mkdir()
    (root / "vf").mkdir()
    (root / "provider-disabled").mkdir()
    raw = b"/* exact generated provider bytes */\n"
    (root / "providers" / "demo.js").write_bytes(raw)
    (root / "manifest.json").write_text(json.dumps({
        "scrapers": [
            {"id": "demo", "filename": "providers/demo.js", "enabled": True},
            {"id": "unsafe", "filename": "../not-owned.js", "enabled": True},
        ]
    }), encoding="utf-8")
    (root / "vf" / "manifest.json").write_text(json.dumps({
        "scrapers": [
            {"id": "demo", "filename": "../providers/demo.js", "enabled": True},
        ]
    }), encoding="utf-8")
    (root.parent / "not-owned.js").write_text("untrusted", encoding="utf-8")
    digests = published_bundle_digests(root)
    assert digests == {"demo": hashlib.sha256(raw).hexdigest()}

    sample = {
        "rows": [
            {"provider": "demo", "lane": "anime", "outcome": "browser_content_reached",
             "residentialExitNodeProfile": {"outcome": "browser_challenge_persisted"}},
            {"provider": "unregistered", "lane": "anime", "outcome": "browser_content_reached"},
        ],
        "residentialProviderReplay": {
            "rows": [{"provider": "demo", "lane": "anime", "raw": 0, "playable": 0,
                      "verified": 0, "identitySafe": True}],
        },
    }
    source_sha = "a" * 40
    stamped = stamp_fresh(sample, digests, source_sha=source_sha, run_id="123")
    current = stamped["rows"][0]
    receipt = current["transportReceipt"]
    assert receipt["sourceNiakvioSha"] == source_sha
    assert receipt["providerBundleSha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["runId"] == "123"
    assert receipt["proofAuthority"] is False
    assert receipt["publicationAuthority"] is False
    assert current["residentialReceipt"] == receipt
    assert stamped["residentialProviderReplay"]["rows"][0]["residentialReplayReceipt"] == receipt
    assert "transportReceipt" not in stamped["rows"][1]
    assert stamped["freshRunReceipt"]["providerCount"] == 1
    assert "not-owned" not in json.dumps(stamped)

    # The durable ledger can carry forward an older residential profile when
    # only a GitHub lane gets refreshed. Old residential data must not gain a
    # new residentialReceipt when its report includes no new measurement.
    old = {
        "rows": [{
            "provider": "demo", "lane": "anime",
            "outcome": "browser_challenge_persisted",
            "residentialExitNodeProfile": {"outcome": "browser_content_reached"},
            "residentialReceipt": {
                **receipt, "sourceNiakvioSha": "b" * 40,
            },
        }]
    }
    github_only = stamp_fresh(
        {"rows": [{"provider": "demo", "lane": "anime", "outcome": "browser_content_reached"}]},
        digests,
        source_sha="c" * 40, run_id="124",
    )
    durable = merge(old, github_only)
    row = durable["rows"][0]
    assert row["transportReceipt"]["sourceNiakvioSha"] == "c" * 40
    assert row.get("residentialReceipt", {}).get("sourceNiakvioSha") != "c" * 40

    for bad_sha, bad_run in (("a" * 39, "123"), ("a" * 40, "0"), ("a" * 40, "bogus")):
        try:
            stamp_fresh(sample, digests, source_sha=bad_sha, run_id=bad_run)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid provenance accepted")

print("WAF exact-provider provenance and stale-residential guard passed")
