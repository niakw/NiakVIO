#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_provider_quick_yield as quick  # noqa: E402

EXPECTED = "flemmix.party"
FORBIDDEN = {
    "flemmix.me",
    "flemmix.kim",
    "flemmix.cloud",
    "flemmix.casa",
    "flemmix.garden",
    "flemmix.men",
    "flemmix.vip",
    "flemmix.ws",
    "flemmix.app",
}
EVIDENCE = ROOT / "automation" / "evidence" / "flemmix-runtime-v61.json"


def main() -> int:
    quick.TIMEOUT = 55
    tasks, _ = quick.build_tasks()
    selected = [task for task in tasks if str(task.get("provider_id") or "").casefold() == "flemmix"]
    if not selected:
        raise SystemExit("V61 no Flemmix tasks")
    rows = [quick.run(task) for task in selected]
    observed: set[str] = set()
    compact = []
    for row in rows:
        fetches = []
        for fetch in row.get("debug_fetches") or []:
            if not isinstance(fetch, dict):
                continue
            url = str(fetch.get("url") or "")
            if "themoviedb.org" in url:
                continue
            parsed = urlsplit(url)
            hostname = (parsed.hostname or "").casefold()
            if hostname:
                observed.add(hostname)
            fetches.append({
                "host": hostname,
                "path": parsed.path[:180],
                "status": fetch.get("status"),
                "error": str(fetch.get("error") or "")[:120] or None,
            })
        compact.append({
            "type": row.get("semantic_type"),
            "status": row.get("status"),
            "raw": row.get("raw"),
            "playable": row.get("playable"),
            "verified": row.get("verified"),
            "stage": row.get("debug_stage"),
            "fetches": fetches[:30],
        })

    bad = sorted(observed & FORBIDDEN)
    if bad:
        raise SystemExit("V61 runtime called retired Flemmix hosts: " + ",".join(bad))
    if EXPECTED not in observed:
        raise SystemExit("V61 runtime never reached flemmix.party; observed=" + ",".join(sorted(observed)))

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps({
        "schemaVersion": 1,
        "terminal": EXPECTED,
        "observedHosts": sorted(observed),
        "rows": compact,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("V61_FLEMMIX_PROBE", json.dumps(compact, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
