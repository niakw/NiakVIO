#!/usr/bin/env python3
"""One-shot favicon-first refinement for tiny provider artwork.

At Nuvio stream/plugin sizes, square site icons are often more readable than full
wordmarks. This migration only uses provider site/hub URLs already known to the
repository, prefers declared/apple/root favicons, writes the two committed WebP
sizes, updates provenance, and is deleted by its workflow after success.

The network phase is intentionally bounded and concurrent because this is a one-
time migration over the full provider inventory, not a recurring runtime job.
This file update intentionally triggers the self-deleting one-shot workflow.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image

try:
    import cairosvg
except Exception:
    cairosvg = None

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "assets/providers/index.json"
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
HUBS = ROOT / "provider-hubs.json"
TARGETS = ((72, 32), (96, 40))
UA = "Mozilla/5.0 (compatible; NiakVIO-FaviconRefine/1.2)"
TIMEOUT = 4
MAX_BYTES = 3 * 1024 * 1024
PAGE_BYTES = 768 * 1024
MAX_PAGES = 2
MAX_CANDIDATES = 10
MAX_WORKERS = 12


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def norm_id(value: Any) -> str:
    return str(value or "").strip().casefold()


def fetch(url: str, limit: int = MAX_BYTES) -> tuple[bytes, str, str]:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    with urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("response_too_large")
        return (
            data,
            str(response.headers.get("content-type") or "").split(";", 1)[0].casefold(),
            str(response.geturl() or url),
        )


class IconParser(HTMLParser):
    def __init__(self, base: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base
        self.items: list[tuple[str, str, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "link":
            return
        values = {str(k).casefold(): str(v or "") for k, v in attrs}
        rel = values.get("rel", "").casefold()
        href = values.get("href", "").strip()
        if not href:
            return
        if "apple-touch-icon" in rel:
            self.items.append((urljoin(self.base, href), "page_apple_touch_icon", 170))
        elif "icon" in rel:
            sizes = values.get("sizes", "").casefold()
            bonus = 10 if any(token in sizes for token in ("128", "192", "256", "512")) else 0
            self.items.append((urljoin(self.base, href), "page_icon", 155 + bonus))


def root_icons(page: str) -> list[tuple[str, str, int]]:
    parsed = urlparse(str(page or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return []
    root = f"{parsed.scheme}://{parsed.netloc}/"
    domain = quote(parsed.hostname or parsed.netloc)
    return [
        (urljoin(root, "apple-touch-icon.png"), "root_apple_touch_icon", 150),
        (urljoin(root, "favicon-192x192.png"), "root_favicon_192", 148),
        (urljoin(root, "favicon-128x128.png"), "root_favicon_128", 146),
        (urljoin(root, "favicon.png"), "root_favicon_png", 140),
        (urljoin(root, "favicon.ico"), "root_favicon", 132),
        (f"https://www.google.com/s2/favicons?domain={domain}&sz=128", "google_site_favicon", 120),
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
    seen: set[str] = set()
    out: list[tuple[str, str, int]] = []
    for item in items:
        if item[0] in seen:
            continue
        seen.add(item[0])
        out.append(item)
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
    if min(image.size) < 16:
        raise ValueError("icon_too_small")
    return image


def score(image: Image.Image, base: int) -> int:
    w, h = image.size
    ratio = w / max(1, h)
    square = 35 if 0.75 <= ratio <= 1.35 else 15 if 0.55 <= ratio <= 1.8 else -30
    size_bonus = 35 if min(w, h) >= 128 else 25 if min(w, h) >= 64 else 12 if min(w, h) >= 32 else 0
    return base + square + size_bonus


def render(image: Image.Image, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    work = image.copy()
    work.thumbnail((height - 4, height - 4), Image.Resampling.LANCZOS)
    x = (width - work.width) // 2
    y = (height - work.height) // 2
    canvas.alpha_composite(work, (x, y))
    return canvas


def pages_for(provider_id: str, patches: dict[str, Any], hubs: dict[str, Any]) -> list[str]:
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    hub = hubs.get(provider_id) if isinstance(hubs.get(provider_id), dict) else {}
    values = [patch.get("official_site"), patch.get("official_hub"), hub.get("direct"), hub.get("hub")]
    out: list[str] = []
    for value in values:
        url = str(value or "").strip()
        if url.startswith(("http://", "https://")) and url not in out:
            out.append(url)
    return out[:MAX_PAGES]


def refine_candidate(provider_id: str, pages: list[str]) -> dict[str, Any] | None:
    candidates: list[tuple[str, str, int]] = []
    # Page markup gives the best declared icon; root/google fallbacks stay available
    # even when page HTML is unavailable.
    for page in pages:
        candidates.extend(page_icons(page))
    seen: set[str] = set()
    unique: list[tuple[str, str, int]] = []
    for candidate in candidates:
        if candidate[0] in seen:
            continue
        seen.add(candidate[0])
        unique.append(candidate)
        if len(unique) >= MAX_CANDIDATES:
            break

    best: tuple[int, Image.Image, dict[str, Any]] | None = None
    failures: list[str] = []
    for url, kind, base in unique:
        try:
            data, content_type, final_url = fetch(url)
            image = open_image(data, content_type, final_url)
            value = score(image, base)
            meta = {
                "sourceUrl": final_url,
                "requestedUrl": url,
                "sourceKind": kind,
                "contentType": content_type,
                "originalWidth": image.width,
                "originalHeight": image.height,
                "sourceSha256": hashlib.sha256(data).hexdigest(),
                "score": value,
                "faviconRefined": True,
                "faviconSourcePage": pages[0],
            }
            if best is None or value > best[0]:
                best = (value, image, meta)
        except Exception as exc:
            failures.append(f"{kind}:{type(exc).__name__}")

    if best is None:
        return None
    value, image, meta = best
    ratio = image.width / max(1, image.height)
    if not (0.55 <= ratio <= 1.8) or min(image.size) < 32:
        return None
    return {
        "providerId": provider_id,
        "image": image,
        "meta": meta,
        "candidateCount": len(unique),
        "failures": failures[:12],
    }


def main() -> int:
    index = load(INDEX, {})
    manifest = load(MANIFEST, {})
    overrides = load(OVERRIDES, {})
    hubs_doc = load(HUBS, {})
    patches_raw = overrides.get("provider_patches") if isinstance(overrides, dict) else {}
    hubs_raw = hubs_doc.get("providers") if isinstance(hubs_doc, dict) else {}
    patches = {norm_id(k): v for k, v in (patches_raw or {}).items()}
    hubs = {norm_id(k): v for k, v in (hubs_raw or {}).items()}
    providers = index.setdefault("providers", {})

    work: list[tuple[str, list[str]]] = []
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = norm_id(row.get("id"))
        if not provider_id or not isinstance(providers.get(provider_id), dict):
            continue
        pages = pages_for(provider_id, patches, hubs)
        if pages:
            work.append((provider_id, pages))

    refined: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="favicon") as pool:
        futures = {pool.submit(refine_candidate, provider_id, pages): provider_id for provider_id, pages in work}
        for future in as_completed(futures):
            provider_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print(f"FIELD_PROVIDER_FAVICON_REFINE_SKIP provider={provider_id} error={type(exc).__name__}")
                continue
            if result is not None:
                refined.append(result)

    changed = 0
    for result in sorted(refined, key=lambda value: value["providerId"]):
        provider_id = result["providerId"]
        current = providers[provider_id]
        image = result["image"]
        meta = result["meta"]
        slug = str(current.get("slug") or re.sub(r"[^a-z0-9]+", "-", provider_id).strip("-"))
        for width, height in TARGETS:
            rel = ROOT / "assets" / "providers" / f"{width}x{height}" / f"{slug}.webp"
            render(image, width, height).save(rel, format="WEBP", lossless=True, method=6, exact=True)
        preserved = {k: current.get(k) for k in ("id", "name", "slug", "assets", "urls") if k in current}
        providers[provider_id] = {
            **preserved,
            **meta,
            "candidateCount": result["candidateCount"],
            "failures": result["failures"],
            "previousSourceKind": current.get("sourceKind"),
            "previousSourceUrl": current.get("sourceUrl"),
        }
        changed += 1
        print(
            f"FIELD_PROVIDER_FAVICON_REFINE provider={provider_id} source={meta['sourceKind']} "
            f"original={image.width}x{image.height}"
        )

    index["faviconRefinement"] = {
        "mode": "one-shot-site-icon-preference",
        "attemptedProviders": len(work),
        "refinedProviders": changed,
        "completedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "network": {
            "timeoutSeconds": TIMEOUT,
            "maxPagesPerProvider": MAX_PAGES,
            "maxCandidatesPerProvider": MAX_CANDIDATES,
            "workers": MAX_WORKERS,
        },
    }
    index["futurePolicy"] = "committed-assets-only-no-network-regeneration"
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FIELD_PROVIDER_FAVICON_REFINEMENT attempted={len(work)} refined={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
