#!/usr/bin/env python3
"""One-shot provider logo import.

This script is intentionally temporary. It resolves the best available provider
artwork from already-known manifest URLs and official site/hub pages, writes two
small WebP variants, and records provenance in assets/providers/index.json.
The workflow that invokes it deletes this script after a successful import.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import ssl
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

try:
    import cairosvg
except Exception:  # optional; raster sources remain supported
    cairosvg = None

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "assets" / "providers"
INDEX = OUT_ROOT / "index.json"
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
HUBS = ROOT / "provider-hubs.json"
USER_AGENT = "Mozilla/5.0 (compatible; NiakVIO-ProviderLogoImport/1.0; +https://github.com/niakw/NiakVIO)"
MAX_DOWNLOAD = 5 * 1024 * 1024
PAGE_LIMIT = 1024 * 1024
TIMEOUT = 9
TARGETS = ((72, 32), (96, 40))
RAW_BASE = "https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers"


def load_json(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return value


def provider_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).casefold()).strip("-")
    return slug or "provider"


def dedupe(values: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    seen: set[str] = set()
    out: list[tuple[str, str, int]] = []
    for url, kind, score in values:
        value = str(url or "").strip()
        if not value or not value.startswith(("http://", "https://")):
            continue
        key = value.split("#", 1)[0]
        if key in seen:
            continue
        seen.add(key)
        out.append((key, kind, score))
    return out


def fetch_bytes(url: str, *, limit: int = MAX_DOWNLOAD, referer: str | None = None) -> tuple[bytes, str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    req = Request(url, headers=headers)
    context = ssl.create_default_context()
    with urlopen(req, timeout=TIMEOUT, context=context) as response:
        content_type = str(response.headers.get("content-type") or "").split(";", 1)[0].strip().casefold()
        final_url = str(response.geturl() or url)
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("response_too_large")
    return data, content_type, final_url


class BrandParser(HTMLParser):
    def __init__(self, page_url: str, provider_name: str) -> None:
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.provider_token = re.sub(r"[^a-z0-9]", "", provider_name.casefold())
        self.candidates: list[tuple[str, str, int]] = []

    def _add(self, raw: str | None, kind: str, score: int) -> None:
        value = str(raw or "").strip()
        if not value or value.startswith(("data:", "javascript:")):
            return
        self.candidates.append((urljoin(self.page_url, value), kind, score))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {str(k).casefold(): str(v or "") for k, v in attrs}
        tag = tag.casefold()
        if tag == "link":
            rel = values.get("rel", "").casefold()
            href = values.get("href")
            if "apple-touch-icon" in rel:
                self._add(href, "page_apple_touch_icon", 86)
            elif "icon" in rel:
                self._add(href, "page_icon", 70)
        elif tag == "meta":
            prop = (values.get("property") or values.get("name") or "").casefold()
            if prop in {"og:logo", "twitter:logo"}:
                self._add(values.get("content"), "page_meta_logo", 112)
            elif prop in {"og:image", "twitter:image"}:
                self._add(values.get("content"), "page_social_image", 68)
        elif tag == "img":
            src = values.get("src") or values.get("data-src") or values.get("data-lazy-src")
            evidence = " ".join(
                values.get(key, "")
                for key in ("alt", "title", "class", "id", "src", "data-src")
            ).casefold()
            normalized = re.sub(r"[^a-z0-9]", "", evidence)
            if "logo" in evidence or "brand" in evidence or (self.provider_token and self.provider_token in normalized):
                self._add(src, "page_logo_image", 108)


def page_candidates(base: str, provider_name: str) -> list[tuple[str, str, int]]:
    url = str(base or "").strip()
    if not url.startswith(("http://", "https://")):
        return []
    output: list[tuple[str, str, int]] = []
    try:
        data, content_type, final_url = fetch_bytes(url, limit=PAGE_LIMIT)
        if "html" in content_type or data[:256].lstrip().startswith((b"<!DOCTYPE", b"<html", b"<HTML")):
            text = data.decode("utf-8", errors="ignore")
            parser = BrandParser(final_url, provider_name)
            parser.feed(text)
            output.extend(parser.candidates)
        base_url = final_url
    except Exception:
        base_url = url
    origin = urlparse(base_url)
    if origin.scheme and origin.netloc:
        root = f"{origin.scheme}://{origin.netloc}/"
        output.extend(
            [
                (urljoin(root, "favicon.ico"), "root_favicon", 58),
                (urljoin(root, "favicon.png"), "root_favicon_png", 62),
                (urljoin(root, "apple-touch-icon.png"), "root_apple_touch_icon", 76),
                (urljoin(root, "logo.png"), "root_logo_png", 82),
                (urljoin(root, "logo.webp"), "root_logo_webp", 84),
            ]
        )
    return output


def open_image(data: bytes, content_type: str, url: str) -> Image.Image:
    is_svg = "svg" in content_type or urlparse(url).path.casefold().endswith(".svg") or data.lstrip().startswith(b"<svg")
    if is_svg:
        if cairosvg is None:
            raise ValueError("svg_without_cairosvg")
        data = cairosvg.svg2png(bytestring=data, output_width=512, output_height=512)
    with Image.open(io.BytesIO(data)) as source:
        source.load()
        image = source.convert("RGBA")
    if image.width < 8 or image.height < 8:
        raise ValueError("image_too_small")
    if image.width > 8192 or image.height > 8192:
        image.thumbnail((4096, 4096), Image.Resampling.LANCZOS)
    bbox = image.getbbox()
    if bbox is None:
        raise ValueError("empty_image")
    return image


def visual_score(image: Image.Image, base_score: int, kind: str) -> int:
    width, height = image.size
    area_bonus = min(24, int((width * height) ** 0.5 / 24))
    ratio = width / max(1, height)
    ratio_bonus = 8 if 1.3 <= ratio <= 5.5 else 4 if 0.75 <= ratio <= 6.5 else -8
    tiny_penalty = -18 if max(width, height) < 48 else 0
    social_penalty = -12 if "social" in kind and (width >= 600 or height >= 300) else 0
    return base_score + area_bonus + ratio_bonus + tiny_penalty + social_penalty


def render(image: Image.Image, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    work = image.copy()
    bbox = work.getbbox()
    if bbox:
        work = work.crop(bbox)
    max_w = max(1, width - 4)
    max_h = max(1, height - 4)
    work.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    x = (width - work.width) // 2
    y = (height - work.height) // 2
    canvas.alpha_composite(work, (x, y))
    return canvas


def save_webp(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="WEBP", lossless=True, method=6, exact=True)


def manifest_rows() -> list[dict[str, Any]]:
    payload = load_json(MANIFEST, {})
    rows = payload.get("scrapers") if isinstance(payload, dict) else []
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def provider_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    overrides = load_json(OVERRIDES, {})
    patches = overrides.get("provider_patches") if isinstance(overrides, dict) else {}
    if not isinstance(patches, dict):
        patches = {}
    hubs = load_json(HUBS, {})
    hub_rows = hubs.get("providers") if isinstance(hubs, dict) else {}
    if not isinstance(hub_rows, dict):
        hub_rows = {}
    return {str(k).casefold(): v for k, v in patches.items()}, {str(k).casefold(): v for k, v in hub_rows.items()}


def candidate_list(row: dict[str, Any], patches: dict[str, Any], hubs: dict[str, Any]) -> list[tuple[str, str, int]]:
    provider_id = str(row.get("id") or "").strip().casefold()
    name = str(row.get("name") or provider_id)
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    hub = hubs.get(provider_id) if isinstance(hubs.get(provider_id), dict) else {}
    values: list[tuple[str, str, int]] = []
    if row.get("logo"):
        values.append((str(row["logo"]), "manifest_logo", 124))
    manifest_overrides = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
    if manifest_overrides.get("logo"):
        values.append((str(manifest_overrides["logo"]), "override_logo", 128))

    pages: list[str] = []
    for source in (
        patch.get("official_site"), patch.get("official_hub"),
        hub.get("direct"), hub.get("hub"),
    ):
        value = str(source or "").strip()
        if value and value not in pages:
            pages.append(value)
    for page in pages:
        values.extend(page_candidates(page, name))
    return dedupe(values)


def choose_logo(row: dict[str, Any], patches: dict[str, Any], hubs: dict[str, Any]) -> tuple[Image.Image | None, dict[str, Any]]:
    candidates = candidate_list(row, patches, hubs)
    best: tuple[int, Image.Image, dict[str, Any]] | None = None
    failures: list[str] = []
    for url, kind, base_score in candidates[:28]:
        try:
            data, content_type, final_url = fetch_bytes(url, referer=None)
            image = open_image(data, content_type, final_url)
            score = visual_score(image, base_score, kind)
            meta = {
                "sourceUrl": final_url,
                "requestedUrl": url,
                "sourceKind": kind,
                "contentType": content_type,
                "originalWidth": image.width,
                "originalHeight": image.height,
                "sourceSha256": hashlib.sha256(data).hexdigest(),
                "score": score,
            }
            if best is None or score > best[0]:
                best = (score, image, meta)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError, ssl.SSLError) as exc:
            failures.append(f"{kind}:{type(exc).__name__}")
        except Exception as exc:
            failures.append(f"{kind}:{type(exc).__name__}")
        time.sleep(0.03)
    if best is None:
        return None, {"candidateCount": len(candidates), "failures": failures[:12]}
    return best[1], {**best[2], "candidateCount": len(candidates), "failures": failures[:12]}


def main() -> int:
    patches, hubs = provider_sources()
    rows = manifest_rows()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    imported: dict[str, Any] = {}
    failures: dict[str, Any] = {}

    for position, row in enumerate(rows, 1):
        provider_id = str(row.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        slug = provider_slug(provider_id)
        image, provenance = choose_logo(row, patches, hubs)
        if image is None:
            failures[provider_id] = provenance
            print(f"FIELD_PROVIDER_LOGO provider={provider_id} status=missing candidates={provenance.get('candidateCount', 0)}")
            continue
        assets: dict[str, str] = {}
        for width, height in TARGETS:
            rel = f"assets/providers/{width}x{height}/{slug}.webp"
            save_webp(render(image, width, height), ROOT / rel)
            assets[f"{width}x{height}"] = rel
        imported[provider_id] = {
            "id": provider_id,
            "name": str(row.get("name") or provider_id),
            "slug": slug,
            "assets": assets,
            "urls": {
                "72x32": f"{RAW_BASE}/72x32/{slug}.webp",
                "96x40": f"{RAW_BASE}/96x40/{slug}.webp",
            },
            **provenance,
        }
        print(
            f"FIELD_PROVIDER_LOGO provider={provider_id} status=imported "
            f"source={provenance.get('sourceKind')} original={image.width}x{image.height}"
        )

    payload = {
        "schemaVersion": 1,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generationMode": "one-shot-network-import",
        "futurePolicy": "committed-assets-only-no-network-regeneration",
        "targets": ["72x32", "96x40"],
        "format": "webp-lossless",
        "providerCount": len(rows),
        "importedCount": len(imported),
        "missingCount": len(failures),
        "providers": imported,
        "missing": failures,
    }
    INDEX.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FIELD_PROVIDER_LOGO_IMPORT total={len(rows)} imported={len(imported)} missing={len(failures)}")
    if not imported:
        print("No provider logo could be imported", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
