#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if new in text:
        print(f"ALREADY_PATCHED {label}: {path}")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor in {path}, got {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"PATCHED {label}: {path}")


def patch_timeouts() -> None:
    path = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
    text = path.read_text(encoding="utf-8")
    for old, new, label in (
        ('cfg.get("provider_timeout_ms", 60_000)', 'cfg.get("provider_timeout_ms", 25_000)', "provider timeout"),
        ('cfg.get("tv_provider_timeout_ms", 60_000)', 'cfg.get("tv_provider_timeout_ms", 25_000)', "tv provider timeout"),
    ):
        if old in text:
            if text.count(old) != 1:
                raise SystemExit(f"{label}: expected one old anchor, got {text.count(old)}")
            text = text.replace(old, new, 1)
        if new not in text:
            raise SystemExit(f"{label}: 25 s authority missing")

    # V33 is the final owner. V32 is only the transient pre-failfast state used
    # when this prepatch is applied to an older V31 branch checkout.
    old_revision = "tmdb-data-contract-launch-gate-v31-pre-network-semantic-gate"
    if old_revision in text:
        text = text.replace(old_revision, "tmdb-data-contract-launch-gate-v32-25s-navigation-budget", 1)
    if not any(
        revision in text
        for revision in (
            "tmdb-data-contract-launch-gate-v32-25s-navigation-budget",
            "tmdb-data-contract-launch-gate-v33-25s-isolated-failfast",
        )
    ):
        raise SystemExit("media owner revision drift")
    path.write_text(text, encoding="utf-8")


def patch_quality() -> None:
    replace_once(
        "scripts/provider_patches/stream_output_sanitizer_v5.py",
        'function recoverQuality(stream,text,url){if(!stream||typeof stream!=="object"||meaningfulQuality(stream.quality))return;var q=qualityFromHls(text,url);if(q)stream.quality=q;else try{delete stream.quality}catch(_e){}}',
        'function recoverQuality(stream,text,url){if(!stream||typeof stream!=="object")return;var q=qualityFromHls(text,url);if(q){stream.quality=q;return}if(!meaningfulQuality(stream.quality))try{delete stream.quality}catch(_e){}}',
        "verified HLS quality authority",
    )


def patch_presentation() -> None:
    path = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
    text = path.read_text(encoding="utf-8")

    old_revision = "all-providers-client-projection-name-mirror-v20"
    new_revision = "all-providers-client-projection-language-detail-v21"
    if new_revision not in text:
        if text.count(old_revision) != 1:
            raise SystemExit("presentation revision anchor drift")
        text = text.replace(old_revision, new_revision, 1)

    language_helper = r'''function detailedLanguage(r,fallback){var raw=s(r&&r.language),u=raw.toLowerCase().replace(/[_-]+/g," ").replace(/\s+/g," ").trim(),map={hi:"Hindi",hindi:"Hindi",ta:"Tamil",tamil:"Tamil",te:"Telugu",telugu:"Telugu",ml:"Malayalam",malayalam:"Malayalam",kn:"Kannada",kannada:"Kannada",bn:"Bengali",bengali:"Bengali",mr:"Marathi",marathi:"Marathi",pa:"Punjabi",punjabi:"Punjabi",gu:"Gujarati",gujarati:"Gujarati",ur:"Urdu",urdu:"Urdu",en:"English",eng:"English",english:"English",ja:"Japanese",jpn:"Japanese",japanese:"Japanese",ko:"Korean",kor:"Korean",korean:"Korean"};if(map[u])return map[u];if(/^(?:vf|vff|vfq|vostfr|vo|multi|multi audio|dual audio)$/i.test(u))return fallback||raw.toUpperCase();if(meaningful(raw)&&raw.length<=32&&/^[A-Za-zÀ-ÿ .()/-]+$/.test(raw))return raw;return fallback||""}
'''
    if "function detailedLanguage(r,fallback)" not in text:
        codec_anchor = "function codec(r){"
        if text.count(codec_anchor) != 1:
            raise SystemExit("presentation codec anchor drift")
        text = text.replace(codec_anchor, language_helper + codec_anchor, 1)

    old_output = "if(f.language)out.language=f.language;if(f.codec)out.codec=f.codec;"
    new_output = "var languageDetailValue=detailedLanguage(r,f.language);if(languageDetailValue)out.language=languageDetailValue;else if(f.language)out.language=f.language;if(f.codec)out.codec=f.codec;"
    if new_output not in text:
        if text.count(old_output) != 1:
            raise SystemExit("presentation output-language anchor drift")
        text = text.replace(old_output, new_output, 1)

    old_title = 'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"");out.name=out.title;'
    new_title = 'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"")+(languageDetailValue?" - "+languageDetailValue:"");out.name=out.title;'
    if new_title not in text:
        if text.count(old_title) != 1:
            raise SystemExit("presentation title anchor drift")
        text = text.replace(old_title, new_title, 1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    patch_timeouts()
    patch_quality()
    patch_presentation()
    print("MANUAL_TV_PREPATCH_OK timeout_ms=25000 verified_quality_authority=1 language_detail=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
