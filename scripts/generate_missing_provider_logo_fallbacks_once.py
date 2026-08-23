#!/usr/bin/env python3
"""One-shot fallback logo generator for providers with no recoverable artwork.

Creates compact WebP badges using the first visible provider-name character.
The generated files are committed assets; this script is deleted by its one-shot
workflow and must never become part of recurring provider/catalog generation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "assets" / "providers" / "index.json"
MANIFEST = ROOT / "manifest.json"
SIZES = {"72x32": (72, 32), "96x40": (96, 40)}
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
)


def font_for(height: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(15, int(height * 0.62))
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def first_character(name: str) -> str:
    for char in str(name).strip():
        if char.isalnum():
            return char.upper()
    return "?"


def render(name: str, width: int, height: int, target: Path) -> None:
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    diameter = max(24, min(height - 2, width - 2))
    left = (width - diameter) // 2
    top = (height - diameter) // 2
    right = left + diameter - 1
    bottom = top + diameter - 1
    draw.ellipse((left, top, right, bottom), fill=(32, 33, 36, 245), outline=(255, 255, 255, 210), width=1)
    char = first_character(name)
    font = font_for(height)
    box = draw.textbbox((0, 0), char, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = (width - tw) / 2 - box[0]
    y = (height - th) / 2 - box[1] - 1
    draw.text((x, y), char, font=font, fill=(255, 255, 255, 255))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="WEBP", lossless=True, method=6, exact=True)


def main() -> int:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    names = {
        str(row.get("id") or "").casefold(): str(row.get("name") or row.get("id") or "Provider")
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("id")
    }
    missing = index.get("missing") or {}
    if not isinstance(missing, dict):
        raise SystemExit("assets/providers/index.json missing must be an object")

    generated = 0
    providers = index.setdefault("providers", {})
    for provider_id in sorted(missing):
        key = str(provider_id).casefold()
        name = names.get(key, provider_id)
        slug = key
        assets: dict[str, str] = {}
        urls: dict[str, str] = {}
        hashes: dict[str, str] = {}
        for size_key, (width, height) in SIZES.items():
            relative = Path("assets") / "providers" / size_key / f"{slug}.webp"
            target = ROOT / relative
            render(name, width, height, target)
            assets[size_key] = relative.as_posix()
            urls[size_key] = f"https://raw.githubusercontent.com/niakw/NiakVIO/main/{relative.as_posix()}"
            hashes[size_key] = hashlib.sha256(target.read_bytes()).hexdigest()
        providers[key] = {
            "id": provider_id,
            "name": name,
            "slug": slug,
            "sourceKind": "generated_initial_fallback",
            "fallbackCharacter": first_character(name),
            "assets": assets,
            "urls": urls,
            "assetSha256": hashes,
            "failures": list((missing.get(provider_id) or {}).get("failures") or []),
            "candidateCount": int((missing.get(provider_id) or {}).get("candidateCount") or 0),
        }
        generated += 1

    index["fallbackGeneratedCount"] = int(index.get("fallbackGeneratedCount") or 0) + generated
    index["missing"] = {}
    index["missingCount"] = 0
    index["providerCount"] = len(manifest.get("scrapers") or [])
    index["futurePolicy"] = "committed-assets-only-no-network-regeneration"
    index["fallbackPolicy"] = "one-shot-first-character-webp"
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"FIELD_PROVIDER_LOGO_FALLBACK generated={generated} total_indexed={len(providers)} missing=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
