#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "run_provider_upstream_parity_v3.py"
MARKER = "PARITY_DEEP_HLS_TERMINAL_V2"


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print("PROVIDER_UPSTREAM_PARITY_DEEP_HLS_V2_ALREADY_CURRENT")
        return 0

    text = once(
        text,
        "from rotating_corpus import default_seed, select_fixtures\n",
        "from rotating_corpus import default_seed, select_fixtures\nfrom parity_hls_terminal_probe import verify_hls_terminal\n",
        "deep HLS import",
    )

    old = '''        kind = _media_kind(final_url, content_type, body)\n        short_vod_seconds = _short_finite_hls_seconds(body) if kind == "hls" else None\n        if short_vod_seconds is not None:\n            return {\n                "verified": False,\n                "kind": "hls",\n                "status": status,\n                "reason": "short_finite_vod",\n                "short_vod_seconds": short_vod_seconds,\n            }\n        return {\n            "verified": bool(kind and 200 <= status < 400),\n            "kind": kind,\n            "status": status,\n            "reason": "media" if kind else "non_media_response",\n        }\n'''
    new = '''        kind = _media_kind(final_url, content_type, body)\n        if kind == "hls":\n            # PARITY_DEEP_HLS_TERMINAL_V2\n            proof = verify_hls_terminal(\n                body,\n                final_url,\n                _safe_headers(stream.get("headers")),\n                timeout,\n                min_vod_seconds=MIN_TERMINAL_VOD_SECONDS,\n            )\n            if not isinstance(proof.get("status"), int):\n                proof["status"] = status\n            return proof\n        return {\n            "verified": bool(kind and 200 <= status < 400),\n            "kind": kind,\n            "status": status,\n            "reason": "media" if kind else "non_media_response",\n        }\n'''
    text = once(text, old, new, "deep HLS terminal call")

    old_report = '''        "terminal_short_vod_seconds": sorted({float(row["short_vod_seconds"]) for row in terminal_rows if isinstance(row.get("short_vod_seconds"), (int, float))}),\n        "error_class": str(error_details.get("code") or error_details.get("name") or "")[:120] or None,\n'''
    new_report = '''        "terminal_short_vod_seconds": sorted({float(row["short_vod_seconds"]) for row in terminal_rows if isinstance(row.get("short_vod_seconds"), (int, float))}),\n        "terminal_media_duration_seconds": sorted({float(row["media_duration_seconds"]) for row in terminal_rows if isinstance(row.get("media_duration_seconds"), (int, float))}),\n        "error_class": str(error_details.get("code") or error_details.get("name") or "")[:120] or None,\n'''
    text = once(text, old_report, new_report, "terminal duration report")

    TARGET.write_text(text, encoding="utf-8")
    print("PROVIDER_UPSTREAM_PARITY_DEEP_HLS_V2_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
