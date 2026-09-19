#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "run_provider_upstream_parity_v3.py"
MARKER = "PARITY_SHORT_FINITE_VOD_V1"


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
        print("PROVIDER_UPSTREAM_PARITY_SHORT_VOD_ALREADY_CURRENT")
        return 0

    text = once(
        text,
        "DEFAULT_PROBE_TIMEOUT = 12\n",
        "DEFAULT_PROBE_TIMEOUT = 12\nMIN_TERMINAL_VOD_SECONDS = 60\n",
        "duration floor constant",
    )

    media_end = '''    if text_head.startswith(b"<HTML") or text_head.startswith(b"<!DOCTYPE"):\n        return None\n    return None\n\n\ndef _probe_terminal(stream: dict[str, Any], timeout: int) -> dict[str, Any]:\n'''
    helper = '''    if text_head.startswith(b"<HTML") or text_head.startswith(b"<!DOCTYPE"):\n        return None\n    return None\n\n\ndef _short_finite_hls_seconds(body: bytes) -> float | None:\n    \"\"\"Return a conclusive short finite media-playlist duration, otherwise None.\n\n    The probe body is intentionally bounded. Therefore duration is authoritative\n    only when ENDLIST is present in the sampled body, proving that the complete\n    finite playlist fit inside the sample. Master playlists are never judged by\n    EXTINF duration here.\n    \"\"\"\n    # PARITY_SHORT_FINITE_VOD_V1\n    try:\n        text = body.decode("utf-8", errors="replace").lstrip("\\ufeffï»¿")\n    except Exception:\n        return None\n    upper = text.upper()\n    if "#EXTM3U" not in upper or "#EXT-X-ENDLIST" not in upper:\n        return None\n    if "#EXT-X-STREAM-INF" in upper:\n        return None\n    durations: list[float] = []\n    for line in text.splitlines():\n        value = line.strip()\n        if not value.upper().startswith("#EXTINF:"):\n            continue\n        try:\n            duration = float(value.split(":", 1)[1].split(",", 1)[0].strip())\n        except (TypeError, ValueError):\n            continue\n        if duration >= 0:\n            durations.append(duration)\n    if not durations:\n        return None\n    total = float(sum(durations))\n    if 0 < total < MIN_TERMINAL_VOD_SECONDS:\n        return round(total, 3)\n    return None\n\n\ndef _probe_terminal(stream: dict[str, Any], timeout: int) -> dict[str, Any]:\n'''
    text = once(text, media_end, helper, "short finite HLS helper")

    old_probe = '''        kind = _media_kind(final_url, content_type, body)\n        return {\n            "verified": bool(kind and 200 <= status < 400),\n            "kind": kind,\n            "status": status,\n            "reason": "media" if kind else "non_media_response",\n        }\n'''
    new_probe = '''        kind = _media_kind(final_url, content_type, body)\n        short_vod_seconds = _short_finite_hls_seconds(body) if kind == "hls" else None\n        if short_vod_seconds is not None:\n            return {\n                "verified": False,\n                "kind": "hls",\n                "status": status,\n                "reason": "short_finite_vod",\n                "short_vod_seconds": short_vod_seconds,\n            }\n        return {\n            "verified": bool(kind and 200 <= status < 400),\n            "kind": kind,\n            "status": status,\n            "reason": "media" if kind else "non_media_response",\n        }\n'''
    text = once(text, old_probe, new_probe, "terminal short-vod rejection")

    old_report = '''        "terminal_reasons": sorted({str(row.get("reason")) for row in terminal_rows if row.get("reason")}),\n        "error_class": str(error_details.get("code") or error_details.get("name") or "")[:120] or None,\n'''
    new_report = '''        "terminal_reasons": sorted({str(row.get("reason")) for row in terminal_rows if row.get("reason")}),\n        "terminal_short_vod_seconds": sorted({float(row["short_vod_seconds"]) for row in terminal_rows if isinstance(row.get("short_vod_seconds"), (int, float))}),\n        "error_class": str(error_details.get("code") or error_details.get("name") or "")[:120] or None,\n'''
    text = once(text, old_report, new_report, "short-vod report evidence")

    TARGET.write_text(text, encoding="utf-8")
    print("PROVIDER_UPSTREAM_PARITY_SHORT_VOD_V1_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
