#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "automation" / "target-provider-route-snippets-v3.json"
TARGET_IDS = {"wookafr", "coflix", "streamzo", "frenchstream"}
KEYWORDS = [
    "api/mirrors",
    "mirrors/film",
    "mirrors/series",
    "lecteurvideo",
    "vidzy",
    "uqload",
    "tripplestream",
    "engine/ajax/search",
    "do=search",
    "subaction=search",
    "wp-json",
    "search/",
    "tmdb",
    "getStreams",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    value = value.replace("\\u0026", "&").replace("\\/", "/")
    return re.sub(r"\s+", " ", value).strip()


def contexts(text: str, keyword: str, radius: int = 500, limit: int = 12) -> list[str]:
    out: list[str] = []
    low = text.casefold()
    needle = keyword.casefold()
    start = 0
    while len(out) < limit:
        index = low.find(needle, start)
        if index < 0:
            break
        snippet = clean(text[max(0, index - radius): min(len(text), index + len(keyword) + radius)])
        if snippet not in out:
            out.append(snippet)
        start = index + len(needle)
    return out


def main() -> int:
    manifest = load(ROOT / "manifest.json")
    rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
    }
    report = {"providers": {}}
    for provider_id in sorted(TARGET_IDS):
        row = rows.get(provider_id)
        if not row:
            report["providers"][provider_id] = {"error": "manifest row missing"}
            continue
        filename = str(row.get("filename") or "")
        path = ROOT / filename
        if not path.is_file():
            report["providers"][provider_id] = {"filename": filename, "error": "bundle missing"}
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        entries = {keyword: contexts(text, keyword) for keyword in KEYWORDS}
        report["providers"][provider_id] = {
            "filename": filename,
            "size": len(text),
            "keywords": {key: value for key, value in entries.items() if value},
            "urls": sorted(set(re.findall(r"https?://[^\"'<>\\\s)]+", text)))[:300],
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        provider_id: {
            "filename": data.get("filename"),
            "keywords": sorted((data.get("keywords") or {}).keys()),
            "url_count": len(data.get("urls") or []),
        }
        for provider_id, data in report["providers"].items()
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
