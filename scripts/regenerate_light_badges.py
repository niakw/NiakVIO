#!/usr/bin/env python3
"""Regenerate every light-theme badge with guaranteed native-size contrast.

Transparent artwork remains the immutable visual source. Generic/short labels are
re-rendered at the largest safe font size; branded or complex artwork is preserved
on an automatically selected contrast plate. The result is deterministic and
idempotent because assets/light is never used as source input.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageFilter
except ImportError as exc:  # pragma: no cover - CI installs the pinned build dep.
    raise SystemExit("Pillow is required: python -m pip install 'Pillow==11.3.0'") from exc

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets" / "badge_catalog_v2_complete.json"
REPORT = ROOT / "assets" / "docs" / "LIGHT_BADGE_QA.json"
REVISION = "light-contrast-v3-native-size"
PILLOW_VERSION = "11.3.0"
FONT_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
)


def luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for value in rgb:
        c = value / 255.0
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    l1, l2 = luminance(a), luminance(b)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def visible_average(image: Image.Image) -> tuple[int, int, int]:
    rgba = image.convert("RGBA")
    total = [0.0, 0.0, 0.0]
    weight = 0.0
    for r, g, b, a in rgba.getdata():
        if a < 24:
            continue
        w = a / 255.0
        total[0] += r * w
        total[1] += g * w
        total[2] += b * w
        weight += w
    if weight <= 0:
        return (127, 127, 127)
    return tuple(int(round(value / weight)) for value in total)  # type: ignore[return-value]


def font_for(text: str, width: int, height: int) -> tuple[ImageFont.ImageFont, int]:
    max_size = max(9, int(height * 0.52))
    min_size = 7 if width <= 72 else 8
    font_path = next((path for path in FONT_CANDIDATES if path.is_file()), None)
    for size in range(max_size, min_size - 1, -1):
        font = ImageFont.truetype(str(font_path), size=size) if font_path else ImageFont.load_default()
        box = font.getbbox(text)
        tw, th = box[2] - box[0], box[3] - box[1]
        if tw <= width - 10 and th <= height - 8:
            return font, size
    font = ImageFont.truetype(str(font_path), size=min_size) if font_path else ImageFont.load_default()
    return font, min_size


def plate(width: int, height: int, *, dark: bool) -> tuple[Image.Image, tuple[int, int, int], tuple[int, int, int]]:
    background = (18, 22, 29) if dark else (246, 248, 251)
    outline = (0, 0, 0) if not dark else (255, 255, 255)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    radius = max(5, min(width, height) // 4)
    draw.rounded_rectangle(
        (1, 1, width - 2, height - 2),
        radius=radius,
        fill=(*background, 255),
        outline=(*outline, 255),
        width=2,
    )
    return canvas, background, outline


def render_generic(text: str, width: int, height: int) -> tuple[Image.Image, dict[str, Any]]:
    canvas, background, outline = plate(width, height, dark=True)
    draw = ImageDraw.Draw(canvas)
    label = " ".join(str(text or "").strip().upper().split()) or "?"
    font, size = font_for(label, width, height)
    box = draw.textbbox((0, 0), label, font=font, stroke_width=0)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = (width - tw) / 2 - box[0]
    y = (height - th) / 2 - box[1] - 0.5
    draw.text((x, y), label, font=font, fill=(255, 255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0, 255))
    return canvas, {
        "mode": "rerendered_text",
        "fontSize": size,
        "plate": "dark",
        "backgroundVsWhiteContrast": round(contrast_ratio(background, (255, 255, 255)), 2),
        "outlineVsWhiteContrast": round(contrast_ratio(outline, (255, 255, 255)), 2),
    }


def render_artwork(source: Image.Image, width: int, height: int) -> tuple[Image.Image, dict[str, Any]]:
    source = source.convert("RGBA")
    average = visible_average(source)
    # Dark artwork gets a light plate; light artwork gets a dark plate.
    dark_plate = luminance(average) >= 0.42
    canvas, background, outline = plate(width, height, dark=dark_plate)

    alpha = source.getchannel("A")
    bbox = alpha.getbbox()
    art = source.crop(bbox) if bbox else source
    max_w, max_h = max(1, width - 8), max(1, height - 7)
    scale = min(max_w / max(1, art.width), max_h / max(1, art.height), 1.35)
    nw, nh = max(1, round(art.width * scale)), max(1, round(art.height * scale))
    art = art.resize((nw, nh), Image.Resampling.LANCZOS)
    art = ImageEnhance.Contrast(art).enhance(1.12)
    art = ImageEnhance.Sharpness(art).enhance(1.35)

    # A one-pixel opposite-luminance halo separates transparent logo strokes from
    # the chosen plate without repainting official/brand colours.
    art_alpha = art.getchannel("A")
    halo_alpha = art_alpha.filter(ImageFilter.MaxFilter(3))
    halo_color = (0, 0, 0, 210) if not dark_plate else (255, 255, 255, 220)
    halo = Image.new("RGBA", art.size, halo_color)
    halo.putalpha(halo_alpha)
    x, y = (width - nw) // 2, (height - nh) // 2
    canvas.alpha_composite(halo, (x, y))
    canvas.alpha_composite(art, (x, y))
    return canvas, {
        "mode": "preserved_artwork",
        "fontSize": None,
        "plate": "dark" if dark_plate else "light",
        "sourceAverageRgb": list(average),
        "backgroundVsWhiteContrast": round(contrast_ratio(background, (255, 255, 255)), 2),
        "outlineVsWhiteContrast": round(contrast_ratio(outline, (255, 255, 255)), 2),
    }


def should_rerender(row: dict[str, Any]) -> bool:
    text = str(row.get("fallbackText") or row.get("text") or "").strip()
    # Keep branded and complex/long artwork intact. Short generic labels benefit
    # most from native-size typography instead of scaled source artwork.
    return not bool(row.get("brand")) and 1 <= len(text) <= 11


def build(*, apply: bool) -> dict[str, Any]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    changed = 0
    total = 0
    min_font: int | None = None
    for badge in catalog.get("badges") or []:
        if not isinstance(badge, dict):
            continue
        assets = badge.get("assets") or {}
        for size in ("72x32", "96x40"):
            src_rel = str(((assets.get("transparent") or {}).get(size)) or "")
            dst_rel = str(((assets.get("light") or {}).get(size)) or "")
            if not src_rel or not dst_rel:
                raise RuntimeError(f"missing light/transparent asset mapping: {badge.get('id')} {size}")
            src, dst = ROOT / src_rel, ROOT / dst_rel
            if not src.is_file():
                raise RuntimeError(f"missing transparent source: {src_rel}")
            width, height = map(int, size.split("x"))
            source = Image.open(src).convert("RGBA")
            if source.size != (width, height):
                raise RuntimeError(f"unexpected source dimensions: {src_rel} {source.size}")
            text = str(badge.get("fallbackText") or badge.get("text") or badge.get("id") or "")
            if should_rerender(badge):
                output, info = render_generic(text, width, height)
            else:
                output, info = render_artwork(source, width, height)
            if info.get("fontSize"):
                min_font = int(info["fontSize"]) if min_font is None else min(min_font, int(info["fontSize"]))
            total += 1
            previous = dst.read_bytes() if dst.is_file() else b""
            from io import BytesIO
            buffer = BytesIO()
            output.save(buffer, format="WEBP", lossless=True, method=6)
            payload = buffer.getvalue()
            if payload != previous:
                changed += 1
                if apply:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(payload)
            rows.append({
                "badge": badge.get("id"),
                "size": size,
                "source": src_rel,
                "output": dst_rel,
                "bytes": len(payload),
                **info,
            })

    # A dark backplate or dark outline must separate every light badge from white.
    for row in rows:
        assert max(float(row["backgroundVsWhiteContrast"]), float(row["outlineVsWhiteContrast"])) >= 4.5, row
    report = {
        "schemaVersion": 1,
        "revision": REVISION,
        "pillowVersion": PILLOW_VERSION,
        "catalogBadges": len(catalog.get("badges") or []),
        "assetCount": total,
        "changedCount": changed,
        "rerenderedTextCount": sum(row["mode"] == "rerendered_text" for row in rows),
        "preservedArtworkCount": sum(row["mode"] == "preserved_artwork" for row in rows),
        "minimumGenericFontSize": min_font,
        "whiteBackgroundMinimumSeparationRatio": 4.5,
        "sourceOfTruth": "assets/transparent",
        "idempotent": True,
        "rows": rows,
    }
    if apply:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write regenerated assets/light files")
    parser.add_argument("--check", action="store_true", help="fail if checked-in light assets differ from deterministic output")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")
    report = build(apply=args.apply)
    if args.check and report["changedCount"]:
        raise SystemExit(f"light badge assets are stale: changed={report['changedCount']}")
    print(
        "FIELD_LIGHT_BADGE_CONTRAST "
        f"revision={REVISION} assets={report['assetCount']} changed={report['changedCount']} "
        f"rerendered={report['rerenderedTextCount']} preserved={report['preservedArtworkCount']} "
        f"min_font={report['minimumGenericFontSize']} white_separation=4.5"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
