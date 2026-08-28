#!/usr/bin/env python3
"""One-shot full provider branding refresh.

Rebuild every committed provider icon from the best available site/favicon source,
write horizontal 72x32 + 96x40 and native-ready square 96x96 lossless WebP assets,
refresh the committed emoji registry, and fall back to a first-character badge
only when no recoverable artwork exists.

This script is intentionally temporary. The workflow that invokes it deletes the
script and itself after a successful migration.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

try:
    import cairosvg
except Exception:
    cairosvg = None

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets/providers"
INDEX = ASSET_ROOT / "index.json"
EMOJIS = ASSET_ROOT / "emojis.json"
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
HUBS = ROOT / "provider-hubs.json"
TARGETS = {
    "72x32": (72, 32),
    "96x40": (96, 40),
    "96x96": (96, 96),
}
RAW_BASE = "https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers"
UA = "Mozilla/5.0 (compatible; NiakVIO-ProviderBrandingOnce/2.0)"
TIMEOUT = 5
MAX_BYTES = 4 * 1024 * 1024
PAGE_BYTES = 1024 * 1024
MAX_PAGES = 3
MAX_CANDIDATES = 14
MAX_WORKERS = 12
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
)


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def norm_id(value: Any) -> str:
    return str(value or "").strip().casefold()


def provider_slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm_id(value)).strip("-") or "provider"


def clean_name(value: Any, provider_id: str) -> str:
    text = str(value or "").strip()
    while text and not text[0].isalnum():
        text = text[1:].lstrip()
    if text:
        return text
    parts = [part for part in re.split(r"[-_\s]+", provider_id) if part]
    return " ".join(part[:1].upper() + part[1:] for part in parts) or "Provider"


def initial_character(name: str) -> str:
    for char in str(name or "").strip():
        if char.isalnum():
            return char.upper()
    return "?"


def initial_emoji(name: str) -> str:
    for char in str(name or "").upper():
        if "A" <= char <= "Z":
            return chr(0x1F1E6 + ord(char) - ord("A"))
    return chr(0x1F1E6 + ord("S") - ord("A"))


def fetch(url: str, limit: int = MAX_BYTES) -> tuple[bytes, str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "image/avif,image/webp,image/png,image/jpeg,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=TIMEOUT, context=ssl.create_default_context()) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("response_too_large")
        return (
            data,
            str(response.headers.get("content-type") or "").split(";", 1)[0].strip().casefold(),
            str(response.geturl() or url),
        )


class IconParser(HTMLParser):
    def __init__(self, base: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base
        self.items: list[tuple[str, str, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {str(k).casefold(): str(v or "") for k, v in attrs}
        tag = tag.casefold()
        if tag == "link":
            rel = values.get("rel", "").casefold()
            href = values.get("href", "").strip()
            if not href:
                return
            sizes = values.get("sizes", "").casefold()
            size_bonus = 16 if any(token in sizes for token in ("128", "180", "192", "256", "512")) else 0
            if "apple-touch-icon" in rel:
                self.items.append((urljoin(self.base, href), "page_apple_touch_icon", 245 + size_bonus))
            elif "icon" in rel:
                self.items.append((urljoin(self.base, href), "page_icon", 225 + size_bonus))
        elif tag == "meta":
            prop = (values.get("property") or values.get("name") or "").casefold()
            if prop in {"og:logo", "twitter:logo"}:
                self.items.append((urljoin(self.base, values.get("content", "")), "page_meta_logo", 205))


def root_icons(page: str) -> list[tuple[str, str, int]]:
    parsed = urlparse(str(page or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return []
    root = f"{parsed.scheme}://{parsed.netloc}/"
    domain = quote(parsed.hostname or parsed.netloc)
    return [
        (urljoin(root, "apple-touch-icon.png"), "root_apple_touch_icon", 220),
        (urljoin(root, "favicon-512x512.png"), "root_favicon_512", 218),
        (urljoin(root, "favicon-192x192.png"), "root_favicon_192", 215),
        (urljoin(root, "favicon-128x128.png"), "root_favicon_128", 212),
        (urljoin(root, "favicon.png"), "root_favicon_png", 205),
        (urljoin(root, "favicon.ico"), "root_favicon", 195),
        (f"https://www.google.com/s2/favicons?domain={domain}&sz=256", "google_site_favicon", 175),
    ]


def page_icons(page: str) -> list[tuple[str, str, int]]:
    url = str(page or "").strip()
    if not url.startswith(("http://", "https://")):
        return []
    items: list[tuple[str, str, int]] = []
    final = url
    try:
        data, content_type, final = fetch(url, PAGE_BYTES)
        prefix = data.lstrip()[:16].lower()
        if "html" in content_type or prefix.startswith((b"<!doctype", b"<html")):
            parser = IconParser(final)
            parser.feed(data.decode("utf-8", errors="ignore"))
            items.extend(parser.items)
    except Exception:
        pass
    items.extend(root_icons(final))
    return items


def external_url(value: Any) -> str:
    url = str(value or "").strip()
    if not url.startswith(("http://", "https://")):
        return ""
    if "raw.githubusercontent.com/niakw/NiakVIO/" in url:
        return ""
    return url


def pages_for(provider_id: str, old_row: dict[str, Any], patches: dict[str, Any], hubs: dict[str, Any]) -> list[str]:
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    hub = hubs.get(provider_id) if isinstance(hubs.get(provider_id), dict) else {}
    values = [
        patch.get("official_site"),
        patch.get("official_hub"),
        hub.get("direct"),
        hub.get("hub"),
        old_row.get("faviconSourcePage"),
    ]
    out: list[str] = []
    for value in values:
        url = str(value or "").strip()
        if url.startswith(("http://", "https://")) and url not in out:
            out.append(url)
    return out[:MAX_PAGES]


def dedupe(items: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    seen: set[str] = set()
    out: list[tuple[str, str, int]] = []
    for url, kind, score in items:
        url = str(url or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append((url, kind, score))
        if len(out) >= MAX_CANDIDATES:
            break
    return out


def open_image(data: bytes, content_type: str, url: str) -> Image.Image:
    is_svg = (
        "svg" in content_type
        or urlparse(url).path.casefold().endswith(".svg")
        or data.lstrip().startswith(b"<svg")
    )
    if is_svg:
        if cairosvg is None:
            raise ValueError("svg_without_cairosvg")
        data = cairosvg.svg2png(bytestring=data, output_width=512, output_height=512)
    with Image.open(io.BytesIO(data)) as source:
        source.load()
        image = source.convert("RGBA")
    bbox = image.getbbox()
    if bbox is None:
        raise ValueError("empty_image")
    image = image.crop(bbox)
    if min(image.size) < 12:
        raise ValueError("image_too_small")
    if max(image.size) > 4096:
        image.thumbnail((4096, 4096), Image.Resampling.LANCZOS)
    return image


def score_image(image: Image.Image, base: int) -> int:
    width, height = image.size
    ratio = width / max(1, height)
    square_bonus = 55 if 0.78 <= ratio <= 1.28 else 28 if 0.60 <= ratio <= 1.70 else -25
    size_bonus = 38 if min(width, height) >= 192 else 30 if min(width, height) >= 96 else 18 if min(width, height) >= 48 else 5
    return base + square_bonus + size_bonus


def candidate_list(row: dict[str, Any], old_row: dict[str, Any], patches: dict[str, Any], hubs: dict[str, Any]) -> list[tuple[str, str, int]]:
    provider_id = norm_id(row.get("id"))
    items: list[tuple[str, str, int]] = []
    for page in pages_for(provider_id, old_row, patches, hubs):
        items.extend(page_icons(page))
    manifest_logo = external_url(row.get("logo"))
    if manifest_logo:
        items.append((manifest_logo, "manifest_logo", 190))
    for field, base in (("sourceUrl", 185), ("requestedUrl", 180)):
        url = external_url(old_row.get(field))
        if url:
            items.append((url, f"previous_{field}", base))
    return dedupe(items)


def previous_local_image(provider_id: str, old_row: dict[str, Any]) -> Image.Image | None:
    if str(old_row.get("sourceKind") or "").startswith("generated"):
        return None
    slug = str(old_row.get("slug") or provider_slug(provider_id))
    for key in ("96x40", "72x32"):
        path = ASSET_ROOT / key / f"{slug}.webp"
        if not path.is_file():
            continue
        try:
            with Image.open(path) as source:
                source.load()
                image = source.convert("RGBA")
            bbox = image.getbbox()
            if bbox:
                return image.crop(bbox)
        except Exception:
            continue
    return None


def resolve(row: dict[str, Any], old_row: dict[str, Any], patches: dict[str, Any], hubs: dict[str, Any]) -> dict[str, Any]:
    provider_id = norm_id(row.get("id"))
    best: tuple[int, Image.Image, dict[str, Any]] | None = None
    failures: list[str] = []
    candidates = candidate_list(row, old_row, patches, hubs)
    for url, kind, base in candidates:
        try:
            data, content_type, final_url = fetch(url)
            image = open_image(data, content_type, final_url)
            value = score_image(image, base)
            meta = {
                "sourceKind": kind,
                "requestedUrl": url,
                "sourceUrl": final_url,
                "contentType": content_type,
                "originalWidth": image.width,
                "originalHeight": image.height,
                "sourceSha256": hashlib.sha256(data).hexdigest(),
                "score": value,
            }
            if best is None or value > best[0]:
                best = (value, image, meta)
        except Exception as exc:
            failures.append(f"{kind}:{type(exc).__name__}")
    if best is not None:
        return {
            "providerId": provider_id,
            "image": best[1],
            "meta": {**best[2], "candidateCount": len(candidates), "failures": failures[:16]},
        }

    previous = previous_local_image(provider_id, old_row)
    if previous is not None:
        return {
            "providerId": provider_id,
            "image": previous,
            "meta": {
                "sourceKind": "committed_previous_asset",
                "candidateCount": len(candidates),
                "failures": failures[:16],
                "originalWidth": previous.width,
                "originalHeight": previous.height,
            },
        }

    return {
        "providerId": provider_id,
        "image": None,
        "meta": {
            "sourceKind": "generated_initial_fallback",
            "candidateCount": len(candidates),
            "failures": failures[:16],
        },
    }


def render_icon(image: Image.Image, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    work = image.copy()
    bbox = work.getbbox()
    if bbox:
        work = work.crop(bbox)
    padding = 4 if min(width, height) <= 40 else 8
    limit_w = max(1, width - padding)
    limit_h = max(1, height - padding)
    work.thumbnail((limit_w, limit_h), Image.Resampling.LANCZOS)
    canvas.alpha_composite(work, ((width - work.width) // 2, (height - work.height) // 2))
    return canvas


def font_for(height: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(15, int(height * 0.58))
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def render_initial(name: str, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    diameter = max(20, min(width, height) - (4 if min(width, height) <= 40 else 10))
    left = (width - diameter) // 2
    top = (height - diameter) // 2
    right = left + diameter - 1
    bottom = top + diameter - 1
    draw.ellipse((left, top, right, bottom), fill=(32, 33, 36, 245), outline=(255, 255, 255, 210), width=1)
    char = initial_character(name)
    font = font_for(diameter)
    box = draw.textbbox((0, 0), char, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = (width - tw) / 2 - box[0]
    y = (height - th) / 2 - box[1] - 1
    draw.text((x, y), char, font=font, fill=(255, 255, 255, 255))
    return canvas


def write_webp(image: Image.Image, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="WEBP", lossless=True, method=6, exact=True)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = load(MANIFEST, {})
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and norm_id(row.get("id"))]
    old_index = load(INDEX, {})
    old_providers = old_index.get("providers") if isinstance(old_index.get("providers"), dict) else {}
    old_emojis = load(EMOJIS, {})
    old_emoji_rows = old_emojis.get("providers") if isinstance(old_emojis.get("providers"), dict) else {}
    overrides = load(OVERRIDES, {})
    hubs_doc = load(HUBS, {})
    raw_patches = overrides.get("provider_patches") if isinstance(overrides, dict) else {}
    raw_hubs = hubs_doc.get("providers") if isinstance(hubs_doc, dict) else {}
    patches = {norm_id(k): v for k, v in (raw_patches or {}).items()}
    hubs = {norm_id(k): v for k, v in (raw_hubs or {}).items()}

    resolved: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="provider-branding") as pool:
        futures = {}
        for row in rows:
            provider_id = norm_id(row.get("id"))
            old_row = old_providers.get(provider_id) if isinstance(old_providers.get(provider_id), dict) else {}
            futures[pool.submit(resolve, row, old_row, patches, hubs)] = provider_id
        for future in as_completed(futures):
            provider_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "providerId": provider_id,
                    "image": None,
                    "meta": {"sourceKind": "generated_initial_fallback", "failures": [type(exc).__name__], "candidateCount": 0},
                }
            resolved[provider_id] = result

    for key in TARGETS:
        shutil.rmtree(ASSET_ROOT / key, ignore_errors=True)
        (ASSET_ROOT / key).mkdir(parents=True, exist_ok=True)

    providers: dict[str, Any] = {}
    fallback_count = 0
    previous_asset_count = 0
    network_count = 0
    emoji_generated = 0
    emoji_rows: dict[str, Any] = {}

    for row in rows:
        provider_id = norm_id(row.get("id"))
        slug = provider_slug(provider_id)
        old_emoji = old_emoji_rows.get(provider_id) if isinstance(old_emoji_rows.get(provider_id), dict) else {}
        name = str(old_emoji.get("name") or "").strip() or clean_name(row.get("name"), provider_id)
        emoji = str(old_emoji.get("emoji") or "").strip()
        if not emoji:
            emoji = initial_emoji(name)
            emoji_generated += 1
        emoji_rows[provider_id] = {"name": name, "emoji": emoji}

        result = resolved[provider_id]
        image = result.get("image")
        meta = dict(result.get("meta") or {})
        generated = image is None
        if generated:
            fallback_count += 1
        elif meta.get("sourceKind") == "committed_previous_asset":
            previous_asset_count += 1
        else:
            network_count += 1

        assets: dict[str, str] = {}
        urls: dict[str, str] = {}
        hashes: dict[str, str] = {}
        for key, (width, height) in TARGETS.items():
            relative = Path("assets") / "providers" / key / f"{slug}.webp"
            target = ROOT / relative
            rendered = render_initial(name, width, height) if generated else render_icon(image, width, height)
            hashes[key] = write_webp(rendered, target)
            assets[key] = relative.as_posix()
            urls[key] = f"{RAW_BASE}/{key}/{slug}.webp"

        providers[provider_id] = {
            "id": provider_id,
            "name": name,
            "slug": slug,
            "assets": assets,
            "urls": urls,
            "assetSha256": hashes,
            **meta,
        }
        if generated:
            providers[provider_id]["fallbackCharacter"] = initial_character(name)
        print(
            f"FIELD_PROVIDER_BRANDING_ONCE provider={provider_id} "
            f"source={providers[provider_id].get('sourceKind')} square=96x96"
        )

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    index = {
        "schemaVersion": 2,
        "generatedAt": now,
        "generationMode": "one-shot-full-site-icon-refresh",
        "futurePolicy": "committed-assets-only-no-network-regeneration",
        "fallbackPolicy": "one-shot-first-character-webp",
        "nativeStreamLogoTarget": "96x96",
        "format": "webp-lossless",
        "targets": list(TARGETS),
        "providerCount": len(rows),
        "importedCount": len(rows) - fallback_count,
        "networkResolvedCount": network_count,
        "previousAssetRecoveryCount": previous_asset_count,
        "fallbackGeneratedCount": fallback_count,
        "missingCount": 0,
        "missing": {},
        "providers": providers,
        "network": {
            "timeoutSeconds": TIMEOUT,
            "maxPagesPerProvider": MAX_PAGES,
            "maxCandidatesPerProvider": MAX_CANDIDATES,
            "workers": MAX_WORKERS,
        },
    }
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    emoji_doc = {
        "schemaVersion": 1,
        "policy": "committed-provider-default-emoji",
        "generationMode": "one-shot-preserve-semantic-else-initial",
        "generatedAt": now,
        "purpose": (
            "Single source of truth for provider display names and fallback emoji while native Nuvio "
            "local-stream logo support is limited. Existing semantic emoji are preserved; only a newly "
            "seen provider without a curated symbol receives its first alphabetic regional-indicator once."
        ),
        "providers": emoji_rows,
    }
    EMOJIS.write_text(json.dumps(emoji_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"FIELD_PROVIDER_BRANDING_ONCE_SUMMARY providers={len(rows)} network={network_count} "
        f"previous_asset={previous_asset_count} fallback={fallback_count} "
        f"emoji_generated={emoji_generated} targets=72x32,96x40,96x96"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
