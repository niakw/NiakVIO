#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
HUBS = ROOT / "provider-hubs.json"
INDEX = ROOT / "assets/providers/index.json"
EMOJIS = ROOT / "assets/providers/emojis.json"
TARGETS = {"72x32": (72, 32), "96x40": (96, 40), "96x96": (96, 96)}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_HTML_BYTES = 256 * 1024


def canonical_id(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip()).strip(".-").casefold()
    if not value:
        raise ValueError("provider id is required")
    return value


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def public_http_url(raw: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(str(raw or "").strip())
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.rstrip(".").casefold()
    if host == "localhost" or host.endswith(".local"):
        return False
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
            if item and len(item) >= 5 and item[4]
        }
    except OSError:
        return False
    if not addresses:
        return False
    for value in addresses:
        try:
            if not ipaddress.ip_address(value).is_global:
                return False
        except ValueError:
            return False
    return True


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def fetch(raw_url: str, *, limit: int, timeout: float = 8.0) -> tuple[bytes, str, str]:
    url = str(raw_url or "").strip()
    if not public_http_url(url):
        raise ValueError("non_public_url")
    opener = urllib.request.build_opener(NoRedirect)
    for _ in range(5):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; NiakVIO-ProviderBranding/1.0)",
                "Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.9,text/html;q=0.4,*/*;q=0.1",
            },
        )
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            if error.code in {301, 302, 303, 307, 308}:
                location = error.headers.get("Location", "")
                target = urllib.parse.urljoin(url, location)
                if not public_http_url(target):
                    raise ValueError("redirect_to_non_public_url") from error
                url = target
                continue
            raise
        with response:
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError("response_too_large")
            final_url = response.geturl()
            if not public_http_url(final_url):
                raise ValueError("final_non_public_url")
            content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].strip().casefold()
            return data, final_url, content_type
    raise ValueError("too_many_redirects")


class IconParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {str(key).casefold(): str(value or "") for key, value in attrs}
        if tag.casefold() == "link":
            rel = values.get("rel", "").casefold()
            href = values.get("href", "")
            if href and any(token in rel for token in ("icon", "apple-touch")):
                self.urls.append(href)
        elif tag.casefold() == "meta":
            prop = (values.get("property") or values.get("name") or "").casefold()
            content = values.get("content", "")
            if content and prop in {"og:image", "twitter:image", "twitter:image:src"}:
                self.urls.append(content)


def root_url(raw: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    netloc = parsed.hostname
    if parsed.port:
        netloc += f":{parsed.port}"
    return urllib.parse.urlunsplit((parsed.scheme, netloc, "/", "", ""))


def page_icon_candidates(site: str) -> tuple[list[str], list[str]]:
    candidates: list[str] = []
    failures: list[str] = []
    if not site:
        return candidates, failures
    base = root_url(site)
    if not base:
        return candidates, failures
    try:
        html, final_url, content_type = fetch(base, limit=MAX_HTML_BYTES)
        if "html" in content_type or content_type.startswith("text/") or not content_type:
            parser = IconParser()
            parser.feed(html.decode("utf-8", errors="ignore"))
            for value in parser.urls:
                candidates.append(urllib.parse.urljoin(final_url, value))
    except Exception as error:
        failures.append(f"homepage:{type(error).__name__}")
    for suffix in (
        "apple-touch-icon.png",
        "favicon-512x512.png",
        "favicon-192x192.png",
        "favicon-128x128.png",
        "favicon.png",
        "favicon.ico",
    ):
        candidates.append(urllib.parse.urljoin(base, suffix))
    try:
        host = urllib.parse.urlsplit(base).hostname or ""
        if host:
            candidates.append(
                "https://www.google.com/s2/favicons?domain_url="
                + urllib.parse.quote(base, safe="")
                + "&sz=256"
            )
    except ValueError:
        pass
    return candidates, failures


def decode_image(data: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(data))
    if getattr(image, "n_frames", 1) > 1:
        image.seek(0)
    image.load()
    return image.convert("RGBA")


def generated_fallback(name: str) -> Image.Image:
    image = Image.new("RGBA", (512, 512), (24, 24, 24, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=180) if hasattr(ImageFont, "load_default") else None
    character = next((char.upper() for char in str(name or "") if char.isalnum()), "?")
    bbox = draw.textbbox((0, 0), character, font=font)
    width = max(1, bbox[2] - bbox[0])
    height = max(1, bbox[3] - bbox[1])
    draw.text(((512 - width) / 2, (512 - height) / 2), character, fill=(255, 255, 255, 255), font=font)
    return image


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = size
    max_box = (max(1, int(width * 0.9)), max(1, int(height * 0.9)))
    contained = ImageOps.contain(image.convert("RGBA"), max_box, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    x = (width - contained.width) // 2
    y = (height - contained.height) // 2
    canvas.alpha_composite(contained, (x, y))
    return canvas


def asset_urls(provider_id: str) -> dict[str, str]:
    return {
        key: f"https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/{key}/{provider_id}.webp"
        for key in TARGETS
    }


def choose_emoji(name: str) -> str:
    lowered = str(name or "").casefold()
    if "anime" in lowered:
        return "🌸"
    if "manga" in lowered:
        return "📚"
    if "tv" in lowered:
        return "📺"
    if any(token in lowered for token in ("flix", "film", "movie", "ciné", "cine")):
        return "🎬"
    if "stream" in lowered:
        return "▶️"
    return "🔗"


def clean_display_name(value: str, fallback: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^[^\wÀ-ÿ]+\s*", "", text, flags=re.UNICODE).strip()
    return text or fallback


def process_provider(
    provider_id: str,
    manifest: dict[str, Any],
    hubs: dict[str, Any],
    index: dict[str, Any],
    emojis: dict[str, Any],
    *,
    explicit_name: str = "",
    explicit_site: str = "",
    explicit_logo: str = "",
    explicit_emoji: str = "",
) -> dict[str, Any]:
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    row = next((item for item in rows if canonical_id(item.get("id")) == provider_id), None)
    if row is None:
        raise ValueError(f"{provider_id}: provider absent from manifest")

    existing_index = (index.get("providers") or {}).get(provider_id) or {}
    existing_emoji = (emojis.get("providers") or {}).get(provider_id) or {}
    display_name = clean_display_name(explicit_name or existing_emoji.get("name") or row.get("name"), provider_id)

    hub_row = ((hubs.get("providers") or {}).get(provider_id) or {}) if isinstance(hubs, dict) else {}
    site = (
        str(explicit_site or "").strip()
        or str(hub_row.get("direct") or "").strip()
        or str(hub_row.get("hub") or "").strip()
    )

    candidates: list[tuple[str, str]] = []
    if explicit_logo:
        candidates.append(("explicit_logo", explicit_logo))
    existing_source = str(existing_index.get("sourceUrl") or "").strip()
    if existing_source:
        candidates.append(("previous_sourceUrl", existing_source))
    page_candidates, failures = page_icon_candidates(site)
    candidates.extend(("page_icon", url) for url in page_candidates)

    deduped: list[tuple[str, str]] = []
    seen: set[str] = set()
    for kind, url in candidates:
        normalized = str(url or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append((kind, normalized))

    chosen_image: Image.Image | None = None
    chosen_kind = ""
    chosen_url = ""
    chosen_type = ""
    chosen_bytes = b""
    for kind, url in deduped:
        try:
            data, final_url, content_type = fetch(url, limit=MAX_IMAGE_BYTES)
            if "svg" in content_type or data.lstrip().startswith(b"<svg"):
                failures.append(f"{kind}:svg_unsupported")
                continue
            image = decode_image(data)
            if image.width < 16 or image.height < 16:
                failures.append(f"{kind}:too_small")
                continue
            chosen_image = image
            chosen_kind = kind
            chosen_url = final_url
            chosen_type = content_type
            chosen_bytes = data
            break
        except Exception as error:
            failures.append(f"{kind}:{type(error).__name__}")

    fallback = chosen_image is None
    if chosen_image is None:
        chosen_image = generated_fallback(display_name)
        chosen_kind = "generated_initial_fallback"

    urls = asset_urls(provider_id)
    asset_paths: dict[str, str] = {}
    asset_sha: dict[str, str] = {}
    for key, size in TARGETS.items():
        relative = f"assets/providers/{key}/{provider_id}.webp"
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = fit(chosen_image, size)
        buffer = io.BytesIO()
        rendered.save(buffer, format="WEBP", lossless=True, method=6)
        payload = buffer.getvalue()
        path.write_bytes(payload)
        asset_paths[key] = relative
        asset_sha[key] = hashlib.sha256(payload).hexdigest()

    provider_entry: dict[str, Any] = {
        "id": provider_id,
        "name": display_name,
        "slug": provider_id,
        "sourceKind": chosen_kind,
        "candidateCount": len(deduped),
        "failures": failures[:40],
        "assets": asset_paths,
        "urls": urls,
        "assetSha256": asset_sha,
    }
    if fallback:
        provider_entry["fallbackCharacter"] = next(
            (char.upper() for char in display_name if char.isalnum()),
            "?",
        )
    else:
        provider_entry.update(
            {
                "requestedUrl": chosen_url,
                "sourceUrl": chosen_url,
                "contentType": chosen_type,
                "sourceSha256": hashlib.sha256(chosen_bytes).hexdigest(),
                "originalWidth": chosen_image.width,
                "originalHeight": chosen_image.height,
            }
        )

    index.setdefault("providers", {})[provider_id] = provider_entry
    emoji = str(explicit_emoji or existing_emoji.get("emoji") or "").strip() or choose_emoji(display_name)
    emojis.setdefault("providers", {})[provider_id] = {"name": display_name, "emoji": emoji}
    row["name"] = f"{emoji} {display_name}"
    row["logo"] = urls["96x96"]

    return {
        "provider": provider_id,
        "name": display_name,
        "emoji": emoji,
        "sourceKind": chosen_kind,
        "sourceUrl": chosen_url or None,
        "fallback": fallback,
        "assetSha256": asset_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("only", "full"), default="only")
    parser.add_argument("--provider", default="")
    parser.add_argument("--name", default="")
    parser.add_argument("--site", default="")
    parser.add_argument("--logo-url", default="")
    parser.add_argument("--emoji", default="")
    args = parser.parse_args()

    manifest = load_json(MANIFEST, {})
    hubs = load_json(HUBS, {})
    index = load_json(INDEX, {})
    emojis = load_json(EMOJIS, {})

    index.setdefault("schemaVersion", 2)
    index["futurePolicy"] = "committed-assets-only-no-network-regeneration"
    index["format"] = "webp-lossless"
    index["targets"] = list(TARGETS)
    index.setdefault("providers", {})

    emojis.setdefault("schemaVersion", 1)
    emojis["policy"] = "committed-provider-default-emoji"
    emojis.setdefault("generationMode", "one-shot-preserve-semantic-else-initial")
    emojis.setdefault("providers", {})

    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and str(row.get("id") or "").strip()]
    manifest_ids = [canonical_id(row["id"]) for row in rows]
    if args.mode == "only":
        provider_id = canonical_id(args.provider)
        targets = [provider_id]
    else:
        targets = manifest_ids

    results = []
    for provider_id in targets:
        results.append(
            process_provider(
                provider_id,
                manifest,
                hubs,
                index,
                emojis,
                explicit_name=args.name if len(targets) == 1 else "",
                explicit_site=args.site if len(targets) == 1 else "",
                explicit_logo=args.logo_url if len(targets) == 1 else "",
                explicit_emoji=args.emoji if len(targets) == 1 else "",
            )
        )

    present = set(index.get("providers") or {})
    missing = sorted(set(manifest_ids) - present)
    index["providerCount"] = len(manifest_ids)
    index["missing"] = missing
    index["missingCount"] = len(missing)
    index["generatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    index["generationMode"] = "incremental-only" if args.mode == "only" else "manual-full"
    index["nativeStreamLogoTarget"] = "96x96"

    write_json(MANIFEST, manifest)
    write_json(INDEX, index)
    write_json(EMOJIS, emojis)

    print(
        "FIELD_PROVIDER_BRANDING_ASSETS "
        f"mode={args.mode} providers={len(results)} "
        f"fallbacks={sum(1 for row in results if row['fallback'])} "
        f"missing={len(missing)}"
    )
    for row in results:
        print(
            "FIELD_PROVIDER_BRANDING_PROVIDER "
            f"id={row['provider']} emoji={row['emoji']} source={row['sourceKind']} "
            f"fallback={str(row['fallback']).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
