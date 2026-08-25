NIAKVIO BADGE SYSTEM V2 — COMPLETE PACK
========================================

Badge catalog: 73 labels
Themes: transparent + dark/gray Nuvio + white/light Nuvio
Sizes: 72x32 and 96x40 WebP lossless

FOLDER STRUCTURE
----------------
assets/transparent/72x32/   Raw transparent badge assets
assets/transparent/96x40/
assets/dark/72x32/          Ready-to-render variants for gray/dark Nuvio backgrounds
assets/dark/96x40/
assets/light/72x32/         Ready-to-render variants for white/light Nuvio backgrounds
assets/light/96x40/

badge_catalog_v2_complete.json      Full registry + regex + fallback text + every asset path
mapping_core_brain_ui_v2_complete.json  Core/Brain/UI order and truth rules
docs/MAQUETTE_EXEMPLE_FLUX_UNIQUE.txt
previews/MAQUETTE_EXEMPLE_FLUX_UNIQUE_DARK.png
previews/MAQUETTE_EXEMPLE_FLUX_UNIQUE_LIGHT.png
previews/QA_CATALOG_DARK.png
previews/QA_CATALOG_LIGHT.png
docs/VALIDATION_REPORT.txt

THEME RULE
----------
Use assets/dark when the Nuvio application background is gray/dark.
Use assets/light when the Nuvio application background is white/light.
The theme-ready files already contain a subtle chip/background/border so white or black brand marks remain readable regardless of the page behind them.

DISPLAY RULE
------------
The primary stream row should show one compact badge per confirmed fact, in one line when the viewport allows it. The technical text line remains below it. Missing facts simply disappear.

DUAL-MODE RUNTIME RULE
----------------------
NiakVIO always replaces provider-owned stream descriptions with the shared Core presentation.
Technical truth comes from provider/stream facts; TMDB fills only safe media context such as title/year/episode/genres/runtime/age when useful.

If native StreamBadge is active, import one of these feeds according to the Nuvio theme:
- assets/stream-badges-dark.json
- assets/stream-badges-light.json
The technical line deliberately keeps the matcher tokens so the official Nuvio StreamBadge renderer can show the real image assets.

If StreamBadge is inactive, the exact same description remains styled with emoji groups (🎞️ video, 🔊 audio, 🌐 language/subtitles, ⏱ duration, 💾 size, 🔞 age). No provider Unknown/private layout is allowed through.
