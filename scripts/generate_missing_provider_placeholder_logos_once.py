#!/usr/bin/env python3
"""One-shot generation of placeholder WebP logos for unrecoverable providers.

This is intentionally not part of any recurring publication pipeline. It only
fills providers still listed in assets/providers/index.json -> missing, using the
first alphanumeric character of the provider display name, then marks those rows
as generated placeholders in the committed logo index.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "assets" / "providers" / "index.json"
MANIFEST = ROOT / "manifest.json"
SIZES = {"72x32": (72, 32), "96x40": (96, 40)}
RAW_BASE = "https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def manifest_names() -> dict[str, str]:
    manifest = load(MANIFEST)
    names: dict[str, str] = {}
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip()
        if provider_id:
            names[provider_id.casefold()] = str(row.get("name") or provider_id).strip()
    return names


def initial_for(name: str, provider_id: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ]", "", name)
    if not cleaned:
        cleaned = re.sub(r"[^0-9A-Za-z]", "", provider_id)
    return (cleaned[:1] or "?").upper()


def font_for(height: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(str(path), max(18, int(height * 0.72)))
    return ImageFont.load_default()


def render(path: Path, size: tuple[int, int], letter: str) -> None:
    width, height = size
    image = Image.new("RGBA", size, (28, 31, 38, 255))
    draw = ImageDraw.Draw(image)
    font = font_for(height)
    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - tw) / 2 - bbox[0]
    y = (height - th) / 2 - bbox[1] - 1
    draw.text((x, y), letter, font=font, fill=(255, 255, 255, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="WEBP", lossless=False, quality=82, method=6)


def main() -> int:
    index = load(INDEX)
    missing = index.get("missing") or {}
    providers = index.get("providers") or {}
    if not isinstance(missing, dict) or not isinstance(providers, dict):
        raise ValueError("invalid provider logo index")
    names = manifest_names()
    generated = 0

    for provider_id in sorted(list(missing)):
        key = str(provider_id).casefold()
        name = names.get(key, str(provider_id))
        letter = initial_for(name, str(provider_id))
        assets: dict[str, str] = {}
        urls: dict[str, str] = {}
        for label, size in SIZES.items():
            rel = Path("assets") / "providers" / label / f"{key}.webp"
            render(ROOT / rel, size, letter)
            assets[label] = rel.as_posix()
            urls[label] = f"{RAW_BASE}/{label}/{key}.webp"
        providers[key] = {
            "id": str(provider_id),
            "name": name,
            "slug": key,
            "sourceKind": "generated_initial_placeholder",
            "generated": True,
            "placeholderInitial": letter,
            "contentType": "image/webp",
            "assets": assets,
            "urls": urls,
            "failures": list((missing.get(provider_id) or {}).get("failures") or []),
            "candidateCount": int((missing.get(provider_id) or {}).get("candidateCount") or 0),
        }
        generated += 1

    index["providers"] = providers
    index["missing"] = {}
    index["missingCount"] = 0
    index["importedCount"] = len(providers)
    index["placeholderGeneratedCount"] = int(index.get("placeholderGeneratedCount") or 0) + generated
    index["futurePolicy"] = "committed-assets-only-no-network-regeneration"
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"generated placeholder provider logos: {generated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
