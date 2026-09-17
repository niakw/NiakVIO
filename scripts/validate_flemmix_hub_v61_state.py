#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "health-output" / "v61-flemmix-hub-report.json"
EVIDENCE = ROOT / "automation" / "evidence" / "flemmix-hub-authority-v61.json"
EXPECTED = "https://flemmix.party"
HUB = "https://ww1.wiflix-adresses.fun/"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    report = load(REPORT)
    row = report["providers"]["flemmix"]
    terminal = str(row.get("official_site") or "").rstrip("/")
    if terminal != EXPECTED:
        raise SystemExit(f"V61 hub resolver terminal={terminal!r}, expected={EXPECTED!r}")

    patch = load(ROOT / "provider-overrides.json")["provider_patches"]["flemmix"]
    if str(patch.get("official_site") or "").rstrip("/") != EXPECTED:
        raise SystemExit("V61 provider-overrides authority mismatch")

    model = load(ROOT / "automation" / "provider-v3-static-knowledge.json")["providers"]["flemmix"]["model"]
    for key in ("officialSite", "knownSite"):
        if str(model.get(key) or "").rstrip("/") != EXPECTED:
            raise SystemExit(f"V61 static {key} mismatch: {model.get(key)!r}")

    hubrow = load(ROOT / "provider-hubs.json")["providers"]["flemmix"]
    if str(hubrow.get("hub") or "").rstrip("/") != HUB.rstrip("/"):
        raise SystemExit(f"V61 Flemmix hub changed unexpectedly: {hubrow.get('hub')!r}")
    if str(hubrow.get("direct") or "").rstrip("/") != EXPECTED:
        raise SystemExit(f"V61 registry direct mismatch: {hubrow.get('direct')!r}")

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": 1,
        "hub": HUB,
        "resolved": EXPECTED,
        "selectedSource": row.get("selected_source"),
        "selectedSourceType": row.get("selected_source_type"),
        "candidateScore": row.get("candidate_score"),
        "staticOfficialSite": model.get("officialSite"),
        "staticKnownSite": model.get("knownSite"),
    }
    EVIDENCE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("V61_HUB_TERMINAL", EXPECTED, "source=", row.get("selected_source"), "score=", row.get("candidate_score"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
