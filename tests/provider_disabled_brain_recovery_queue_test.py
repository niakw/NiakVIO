#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_provider_disabled_recovery_queue.py"
spec = importlib.util.spec_from_file_location("disabled_recovery_queue_test", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory(prefix="niakvio-disabled-recovery-") as td:
    root = Path(td)
    (root / "automation").mkdir()
    (root / "provider-disabled").mkdir()
    def write(path, value):
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    for provider in ("regressed", "nonfunctional", "manual", "active"):
        (root / "provider-disabled" / f"{provider}--nuvio--demo.js").write_text(
            f"// {provider}\n", encoding="utf-8"
        )

    write("manifest.json", {
        "scrapers": [
            {"id":"regressed","enabled":False,"filename":"provider-disabled/regressed--nuvio--demo.js"},
            {"id":"nonfunctional","enabled":False,"filename":"provider-disabled/nonfunctional--nuvio--demo.js"},
            {"id":"manual","enabled":False,"filename":"provider-disabled/manual--nuvio--demo.js"},
        ]
    })
    write("vf/manifest.json", {
        "scrapers": [
            {"id":"regressed","enabled":False,"filename":"../provider-disabled/regressed--nuvio--demo.js"},
        ]
    })
    write("automation/provider-disabled-lifecycle.json", {
        "updatedAt":"2026-11-14",
        "disabled": {
            "regressed":{"state":"disabled-retained","reason":"auto_off_current_architecture_regression","disabledAt":"2026-11-14","purgeAfter":"2026-11-21"},
            "nonfunctional":{"state":"disabled-retained","reason":"auto_off_current_architecture_nonfunctional","disabledAt":"2026-11-14","purgeAfter":"2026-11-21"},
            "manual":{"state":"disabled-retained","reason":"manual_off_zero_playable_movie","disabledAt":"2026-11-14","purgeAfter":"2026-11-21"},
        },
        "archived": {}
    })
    write("automation/provider-census-status.json", {
        "runId":"demo",
        "providers":[
            {"provider":"regressed","status":"DISABLED","dominantIssue":"provider_js_broken"},
            {"provider":"nonfunctional","status":"DISABLED","dominantIssue":"provider_network_zero_result"},
        ]
    })

    payload = mod.build(root)
    assert payload["proofAuthority"] is False
    assert payload["executionAuthority"] is False
    assert payload["publicationAuthority"] is False
    assert payload["eligibleCount"] == 2, payload
    rows = {row["provider"]:row for row in payload["providers"]}
    assert set(rows) == {"regressed","nonfunctional"}, rows
    assert rows["regressed"]["scopes"] == ["france","global"], rows["regressed"]
    assert rows["regressed"]["family"] == "current-architecture-regression"
    assert rows["nonfunctional"]["family"] == "current-architecture-nonfunctional"
    assert all(row["productionExecutionAllowed"] is False for row in rows.values())
    assert all(row["publicationAllowed"] is False for row in rows.values())
    assert len(rows["regressed"]["assetSha256"]) == 64

print("Disabled provider Brain recovery queue contract passed")
