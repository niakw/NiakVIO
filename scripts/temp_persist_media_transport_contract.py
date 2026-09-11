#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/media-type-transport-contract.md"
MEMORY = ROOT / "MEMORY.md"

DOC.parent.mkdir(parents=True, exist_ok=True)
DOC.write_text("""# NiakVIO media type / transport contract

This is the durable contract for separating **canonical content identity** from the **Nuvio provider ABI transport lane**.

## Core rule

Provider selection is based on canonical semantic content type first. Runtime transport aliases are chosen only after provider selection.

| Content | Canonical semantic type | Nuvio runtime transport |
| --- | --- | --- |
| Ordinary/live-action movie | `movie` | `movie` |
| Ordinary/live-action TV series or episode | `tv` | `tv` |
| Anime series / anime episode | `anime` | `tv` |
| Anime movie / theatrical anime film | `anime` | `movie` |

An anime film remains canonical `anime` even when invoked through runtime `movie`. An episodic anime remains canonical `anime` even when invoked through runtime `tv`. Therefore **never hardcode `anime -> tv` globally**.

## Mandatory order

1. Resolve trusted identity and canonical type (`movie`, `tv`, `anime`).
2. Select providers from semantic capability / `canonicalSupportedTypes`.
3. Resolve work shape (movie vs episodic).
4. Translate only the invocation to Nuvio ABI `movie` or `tv`.
5. Invoke the provider.

Transport aliases must never widen semantic capability. An anime-only provider may receive runtime `movie` for an anime film without becoming eligible for ordinary films such as Interstellar.

## Manifest fields

- `canonicalSupportedTypes` is semantic/provider-selection authority.
- `supportedTypes` is client/runtime compatibility metadata and may include transport aliases.
- A transport alias alone must never manufacture canonical capability.

## Recognition

Trusted metadata may refine a Nuvio `movie`/`tv` presentation into canonical `anime`. Animation alone is not sufficient; Western animation remains ordinary movie/TV unless trusted identity says anime.

For canonical anime, transport shape should use, in order: explicit trusted shape metadata; original raw Nuvio shape; season/episode evidence; conservative fallback.

## Labs / evidence

Native Labs should expose both concepts separately:

- `logical_type` / canonical semantic type;
- `request_type` / ABI transport lane.

Expected examples:
- anime episode: `logical_type=anime request_type=tv`;
- anime feature film: `logical_type=anime request_type=movie`.

Evidence that filters anime providers using the runtime alias before canonical selection is invalid.

## Implementation authority

Relevant surfaces include `scripts/native_media_type_contract.py`, `scripts/augment_native_corpus_request_contract.py`, `scripts/provider_semantics.cjs`, provider materialization/projection, and native media-type regressions.

Any implementation that globally maps canonical `anime` to runtime `tv` without preserving movie-vs-episodic shape is a regression.

## Regression floor

Tests must cover all four mapping rows, including a dedicated anime-movie fixture. Passing only an episodic anime fixture is insufficient.
""", encoding="utf-8")

marker = "## Media-type semantic/transport contract — authoritative 2026-09-11"
text = MEMORY.read_text(encoding="utf-8")
if marker not in text:
    checkpoint = """

## Media-type semantic/transport contract — authoritative 2026-09-11

- Durable contract: `docs/media-type-transport-contract.md`.
- Canonical semantic type owns identity/provider selection; runtime transport owns only the Nuvio ABI invocation lane.
- Mapping: ordinary movie `movie -> movie`; ordinary TV/episode `tv -> tv`; anime series/episode `anime -> tv`; anime movie `anime -> movie`.
- Anime films remain canonical `anime`; episodic anime remains canonical `anime`. Never globally rewrite canonical anime to tv.
- `canonicalSupportedTypes` is semantic authority. `supportedTypes` may carry compatibility/transport aliases but must never widen semantic capability.
- Provider selection occurs before runtime aliasing.
- Native Lab evidence should expose `logical_type` and `request_type`, including both anime/tv and anime/movie cases.
- Western animation is not automatically anime; trusted identity is required.
- Current 46-provider workbench and final five-Lab evidence must conform to this contract.
"""
    MEMORY.write_text(text.rstrip() + checkpoint + "\n", encoding="utf-8")

print("MEDIA_TRANSPORT_DURABLE_CHECKPOINT_OK doc=1 memory=1")
