#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts/resolve_nuvio_lab_heads.py"

TV_HEAD = "a" * 40
MOBILE_HEAD = "b" * 40
OLD = "c" * 40
CONTRACT = "d" * 40

with tempfile.TemporaryDirectory(dir=ROOT) as raw:
    tmp = Path(raw)
    report = tmp / "report.json"
    report.write_text(json.dumps({
        "clients": {
            "nuvio-tv": {
                "current_head": TV_HEAD,
                "accepted_ref": OLD,
                "contract_ref": CONTRACT,
                "status": "contract_review_required",
                "review_required": True,
            },
            "nuvio-mobile": {
                "current_head": MOBILE_HEAD,
                "accepted_ref": OLD,
                "contract_ref": CONTRACT,
                "status": "safe_advance",
                "review_required": False,
            },
        }
    }), encoding="utf-8")
    gh_output = tmp / "github-output.txt"
    audit = tmp / "audit.json"
    run = subprocess.run([
        "python3", str(RESOLVER),
        "--report", str(report),
        "--clients", "nuvio-tv", "nuvio-mobile",
        "--github-output", str(gh_output),
        "--output", str(audit),
    ], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    outputs = dict(line.split("=", 1) for line in gh_output.read_text(encoding="utf-8").splitlines())
    assert outputs["tv_sha"] == TV_HEAD
    assert outputs["mobile_sha"] == MOBILE_HEAD
    assert outputs["tv_accepted_ref"] == OLD
    assert outputs["tv_contract_ref"] == CONTRACT
    assert outputs["tv_drift_status"] == "contract_review_required"
    assert outputs["tv_adaptation_required"] == "true"
    assert outputs["tv_lab_blocking"] == "false"
    assert outputs["mobile_adaptation_required"] == "false"
    assert outputs["mobile_lab_blocking"] == "false"
    assert outputs["runtime_fingerprint"] == f"tv={TV_HEAD};mobile={MOBILE_HEAD}"
    payload = json.loads(audit.read_text(encoding="utf-8"))
    tv = payload["clients"]["nuvio-tv"]
    assert tv["head"] == TV_HEAD
    assert tv["adaptationRequired"] is True
    assert tv["labBlocking"] is False
    assert tv["adaptationPolicy"] == "latest-head-version-adaptive-preparation"
    assert "contract_review_required is observational/nonblocking" in payload["policy"]
    assert "no stale fallback" in payload["policy"]

    broken = tmp / "broken.json"
    broken.write_text(json.dumps({
        "clients": {
            "nuvio-tv": {
                "current_head": "",
                "accepted_ref": OLD,
                "contract_ref": CONTRACT,
                "status": "verification_inconclusive",
            }
        }
    }), encoding="utf-8")
    refused = subprocess.run([
        "python3", str(RESOLVER),
        "--report", str(broken),
        "--clients", "nuvio-tv",
        "--github-output", str(tmp / "should-not-exist.txt"),
    ], cwd=ROOT, text=True, capture_output=True)
    assert refused.returncode != 0
    assert "refusing stale fallback" in (refused.stdout + refused.stderr)

print("Nuvio latest-HEAD Lab resolver tests passed")
