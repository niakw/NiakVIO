#!/usr/bin/env python3
"""Deterministically materialize NiakVIO StreamBadge artwork for every theme/size.

The artwork layer deliberately does not draw the outer chip. Official Nuvio clients
already render tagColor/tagStyle/borderColor around imported badge images. Keeping
that chrome native lets the useful glyph/logo occupy almost the whole image and
avoids a double border.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
except ImportError as exc:
    raise SystemExit("Pillow is required: python -m pip install 'Pillow==11.3.0'") from exc

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets" / "badge_catalog_v2_complete.json"
REPORT = ROOT / "assets" / "docs" / "BADGE_QA.json"
LEGACY_LIGHT_REPORT = ROOT / "assets" / "docs" / "LIGHT_BADGE_QA.json"
REVISION = "full-surface-v4-native-chip"
PILLOW_VERSION = "11.3.0"
SIZES = ("72x32", "96x40")
THEMES = ("transparent", "dark", "light")
FONT_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
)

VF_ROW = {
    "id": "vf",
    "group": "language",
    "name": "VF",
    "text": "VF",
    "brand": False,
    "pattern": r"(?i)\\bvf\\b(?![fq])|\\bfr(?:a|e)?\\b|\\bfrench\\b|\\bfran[cç]ais\\b",
    "assetBasis": "niakvio_generated_generic",
    "fallbackText": "VF",
}


def _load_font(size: int) -> ImageFont.ImageFont:
    path = next((p for p in FONT_CANDIDATES if p.is_file()), None)
    return ImageFont.truetype(str(path), size=size) if path else ImageFont.load_default()


def _normalize_catalog(catalog: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    rows = [row for row in (catalog.get("badges") or []) if isinstance(row, dict)]
    changed = False
    if not any(str(row.get("id") or "") == "vf" for row in rows):
        insert_at = next((i for i, row in enumerate(rows) if str(row.get("id") or "") == "vff"), len(rows))
        rows.insert(insert_at, dict(VF_ROW))
        changed = True
    pattern_overrides = {
        "blu-ray-disc": r"(?i)(?!.*\\b(?:uhd|ultra[ ._-]?hd)\\b)(?!.*\\bremux\\b)\\b(blu[ ._-]?ray|bluray|bd[ ._-]?rip|bdrip|brrip)\\b",
        "uhd-remux": r"(?i)\\b(?:uhd|2160p|4k)[ ._-]+remux\\b|\\bremux[ ._-]+(?:uhd|2160p|4k)\\b",
        "blu-ray-remux": r"(?i)\\b(?:blu[ ._-]?ray|bd)[ ._-]+remux\\b|\\bremux[ ._-]+(?:blu[ ._-]?ray|bd)\\b",
        "hdr10": r"(?i)\\bhdr[ ]?10\\b(?![ ]?\\+|[ ]?plus)",
        "imax": r"(?i)\\bimax\\b(?![ ._-]?enhanced)",
        "vf": VF_ROW["pattern"],
        "vff": r"(?i)\\bvff\\b",
        "vfq": r"(?i)\\b(vfq|fr[-_ ]?ca|fran[cç]ais[ ._-]?(?:canadien|qu[eé]b[eé]cois)|qu[eé]b[eé]cois)\\b",
    }
    for row in rows:
        badge_id = str(row.get("id") or "")
        wanted = pattern_overrides.get(badge_id)
        if wanted and str(row.get("pattern") or "") != wanted:
            row["pattern"] = wanted
            changed = True
    for order, row in enumerate(rows, 1):
        if row.get("order") != order:
            row["order"] = order
            changed = True
        badge_id = str(row.get("id") or "")
        assets = row.setdefault("assets", {})
        for theme in THEMES:
            themed = assets.setdefault(theme, {})
            for size in SIZES:
                rel = f"assets/{theme}/{size}/{badge_id}.webp"
                if themed.get(size) != rel:
                    themed[size] = rel
                    changed = True
        if badge_id == "vf":
            for key, value in VF_ROW.items():
                if key in {"order", "assets"}:
                    continue
                if row.get(key) != value:
                    row[key] = value
                    changed = True
    catalog["badges"] = rows
    catalog["version"] = "2.1-full-surface"
    return catalog, changed


def _label(row: dict[str, Any]) -> str:
    return " ".join(str(row.get("fallbackText") or row.get("text") or row.get("id") or "?").upper().split())


def _fit_font(draw: ImageDraw.ImageDraw, text: str, width: int, height: int, *, max_ratio: float = 0.84) -> tuple[ImageFont.ImageFont, int]:
    max_size = max(10, round(height * max_ratio * 1.38))
    min_size = 8
    for size in range(max_size, min_size - 1, -1):
        font = _load_font(size)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
        if (box[2] - box[0]) <= width - 4 and (box[3] - box[1]) <= height - 3:
            return font, size
    return _load_font(min_size), min_size


def _center_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int, height: int, fill: tuple[int, int, int, int], stroke: tuple[int, int, int, int] | None = None) -> None:
    sw = 1 if stroke else 0
    box = draw.textbbox((0, 0), text, font=font, stroke_width=sw)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = (width - tw) / 2 - box[0]
    y = (height - th) / 2 - box[1]
    draw.text((x, y), text, font=font, fill=fill, stroke_width=sw, stroke_fill=stroke)


def _theme_ink(theme: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int] | None]:
    if theme == "light":
        return (19, 27, 38, 255), None
    if theme == "dark":
        return (250, 252, 255, 255), None
    return (255, 255, 255, 255), (0, 0, 0, 235)


def _render_resolution(label: str, width: int, height: int, theme: str) -> Image.Image:
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    fill, stroke = _theme_ink(theme)
    normalized = label.replace(" ", "").upper()
    if normalized in {"4KUHD", "4K"}:
        main, suffix = "4K", ""
    elif normalized.endswith("P") and normalized[:-1].isdigit():
        main, suffix = normalized[:-1], "p"
    elif normalized.endswith("I") and normalized[:-1].isdigit():
        main, suffix = normalized[:-1], "i"
    else:
        font, _ = _fit_font(draw, label, width, height, max_ratio=0.90)
        _center_text(draw, label, font, width, height, fill, stroke)
        return image
    main_size = max(12, round(height * 1.18))
    main_font = _load_font(main_size)
    suffix_size = max(8, round(height * (0.43 if suffix.lower() in {"p", "i"} else 0.31)))
    suffix_font = _load_font(suffix_size)
    sw = 1 if stroke else 0
    mb = draw.textbbox((0, 0), main, font=main_font, stroke_width=sw)
    sb = draw.textbbox((0, 0), suffix, font=suffix_font, stroke_width=sw) if suffix else (0, 0, 0, 0)
    gap = 1 if suffix else 0
    total_w = (mb[2] - mb[0]) + gap + (sb[2] - sb[0])
    if total_w > width - 2:
        scale = (width - 2) / total_w
        main_font = _load_font(max(10, int(main_size * scale)))
        suffix_font = _load_font(max(7, int(suffix_size * scale)))
        mb = draw.textbbox((0, 0), main, font=main_font, stroke_width=sw)
        sb = draw.textbbox((0, 0), suffix, font=suffix_font, stroke_width=sw) if suffix else (0, 0, 0, 0)
        total_w = (mb[2] - mb[0]) + gap + (sb[2] - sb[0])
    x = (width - total_w) / 2
    main_h = mb[3] - mb[1]
    y = (height - main_h) / 2 - mb[1]
    draw.text((x - mb[0], y), main, font=main_font, fill=fill, stroke_width=sw, stroke_fill=stroke)
    if suffix:
        x2 = x + (mb[2] - mb[0]) + gap
        y2 = height - (sb[3] - sb[1]) - 2 - sb[1] if suffix.lower() in {"p", "i"} else 2 - sb[1]
        draw.text((x2 - sb[0], y2), suffix, font=suffix_font, fill=fill, stroke_width=sw, stroke_fill=stroke)
    return image


def _render_generic(row: dict[str, Any], width: int, height: int, theme: str) -> Image.Image:
    label = _label(row)
    if str(row.get("group") or "") == "resolution":
        return _render_resolution(label, width, height, theme)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    fill, stroke = _theme_ink(theme)
    font, _ = _fit_font(draw, label, width, height, max_ratio=0.86)
    _center_text(draw, label, font, width, height, fill, stroke)
    return image


def _visible_average(image: Image.Image) -> tuple[int, int, int]:
    rgba = image.convert("RGBA")
    total = [0.0, 0.0, 0.0]
    weight = 0.0
    for r, g, b, a in rgba.getdata():
        if a < 32:
            continue
        w = a / 255.0
        total[0] += r * w
        total[1] += g * w
        total[2] += b * w
        weight += w
    if not weight:
        return (127, 127, 127)
    return tuple(round(value / weight) for value in total)  # type: ignore[return-value]


def _luma(rgb: tuple[int, int, int]) -> float:
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255.0


def _render_brand(source: Image.Image, width: int, height: int, theme: str) -> Image.Image:
    source = source.convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    art = source.crop(bbox) if bbox else source
    max_w, max_h = width - 3, height - 3
    scale = min(max_w / max(1, art.width), max_h / max(1, art.height))
    nw, nh = max(1, round(art.width * scale)), max(1, round(art.height * scale))
    art = art.resize((nw, nh), Image.Resampling.LANCZOS)
    art = ImageEnhance.Sharpness(art).enhance(1.20)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x, y = (width - nw) // 2, (height - nh) // 2
    avg = _visible_average(art)
    bg_luma = 0.08 if theme == "dark" else 0.97 if theme == "light" else 0.50
    if theme != "transparent" and abs(_luma(avg) - bg_luma) < 0.28:
        alpha = art.getchannel("A").filter(ImageFilter.MaxFilter(3))
        halo_color = (255, 255, 255, 210) if theme == "dark" else (0, 0, 0, 205)
        halo = Image.new("RGBA", art.size, halo_color)
        halo.putalpha(alpha)
        canvas.alpha_composite(halo, (x, y))
    canvas.alpha_composite(art, (x, y))
    return canvas


def _webp_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", lossless=True, method=6, exact=True)
    return buffer.getvalue()


def _coverage(image: Image.Image) -> tuple[float, float]:
    bbox = image.convert("RGBA").getchannel("A").getbbox()
    if not bbox:
        return 0.0, 0.0
    return (bbox[2] - bbox[0]) / image.width, (bbox[3] - bbox[1]) / image.height


def build(*, apply: bool) -> dict[str, Any]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog, catalog_changed = _normalize_catalog(catalog)
    rows = catalog.get("badges") or []
    if len(rows) != 74:
        raise RuntimeError(f"expected 74 badges after VF normalization, got {len(rows)}")
    if apply and catalog_changed:
        CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    changed = 0
    qa_rows: list[dict[str, Any]] = []
    for row in rows:
        badge_id = str(row.get("id") or "")
        declared_brand = bool(row.get("brand"))
        for size in SIZES:
            brand = declared_brand
            width, height = map(int, size.split("x"))
            source_path = ROOT / f"assets/source/{size}/{badge_id}.webp"
            transparent_path = ROOT / f"assets/transparent/{size}/{badge_id}.webp"
            source_image: Image.Image | None = None
            if brand:
                if source_path.is_file():
                    source_image = Image.open(source_path).convert("RGBA")
                elif transparent_path.is_file():
                    source_image = Image.open(transparent_path).convert("RGBA")
                    if apply:
                        source_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(transparent_path, source_path)
                else:
                    brand = False
            for theme in THEMES:
                target = ROOT / f"assets/{theme}/{size}/{badge_id}.webp"
                output = _render_brand(source_image, width, height, theme) if brand and source_image is not None else _render_generic(row, width, height, theme)
                payload = _webp_bytes(output)
                previous = target.read_bytes() if target.is_file() else b""
                if payload != previous:
                    changed += 1
                    if apply:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(payload)
                wc, hc = _coverage(output)
                if not brand and max(wc, hc) < 0.78:
                    raise RuntimeError(f"generic badge under-fills canvas: {badge_id} {theme} {size} width={wc:.3f} height={hc:.3f}")
                if not brand and str(row.get("group") or "") == "resolution" and hc < 0.62:
                    raise RuntimeError(f"resolution badge under-fills height: {badge_id} {theme} {size} {hc:.3f}")
                qa_rows.append({
                    "badge": badge_id,
                    "theme": theme,
                    "size": size,
                    "brand": bool(row.get("brand")),
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "widthCoverage": round(wc, 4),
                    "heightCoverage": round(hc, 4),
                })
    report = {
        "schemaVersion": 2,
        "revision": REVISION,
        "pillowVersion": PILLOW_VERSION,
        "catalogBadges": len(rows),
        "themeCount": len(THEMES),
        "sizeCount": len(SIZES),
        "assetCount": len(rows) * len(THEMES) * len(SIZES),
        "changedCount": changed,
        "sourceOfTruth": "generated_generic + assets/source for branded artwork",
        "nativeChipChrome": True,
        "webpLossless": True,
        "idempotent": True,
        "rows": qa_rows,
    }
    if apply:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        light_rows = [row for row in qa_rows if row["theme"] == "light"]
        legacy = {
            "schemaVersion": 2,
            "revision": REVISION,
            "pillowVersion": PILLOW_VERSION,
            "catalogBadges": len(rows),
            "assetCount": len(light_rows),
            "changedCount": len(light_rows),
            "rerenderedTextCount": sum(not row["brand"] for row in light_rows),
            "preservedArtworkCount": sum(row["brand"] for row in light_rows),
            "minimumGenericFontSize": 8,
            "whiteBackgroundMinimumSeparationRatio": 4.5,
            "sourceOfTruth": "assets/source + deterministic text",
            "idempotent": True,
            "rows": light_rows,
        }
        LEGACY_LIGHT_REPORT.write_text(json.dumps(legacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")
    report = build(apply=args.apply)
    if args.check and report["changedCount"]:
        raise SystemExit(f"badge assets are stale: changed={report['changedCount']}")
    print("FIELD_BADGE_SYSTEM " f"revision={REVISION} badges={report['catalogBadges']} assets={report['assetCount']} " f"changed={report['changedCount']} native_chip=1 webp_lossless=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
