# NiakVIO media type / transport contract

This is the durable contract separating **canonical content capability** from the **Nuvio launch surface**.

## Core rule

Provider selection is based on canonical semantic capability first. Transport compatibility must never widen that capability.

| Canonical provider capability | Published `supportedTypes` |
| --- | --- |
| `movie` | `movie` |
| `tv` | `tv` |
| `movie + tv` | `movie + tv` |
| anime-only (`anime`) | `anime + tv` |

For an anime-only provider, `canonicalSupportedTypes` remains exactly `["anime"]` while `supportedTypes` is exactly `["anime", "tv"]`.

`tv` is the only synthetic compatibility alias NiakVIO adds for anime-only providers. **Do not synthesize `series`, `show` or `movie`.** In particular, an anime-only provider does not gain a movie lane merely because a work is theatrical or feature-length. `movie` is published only when the provider has canonical movie capability.

## Mandatory order

1. Resolve trusted work identity and semantic type (`movie`, `tv`, `anime`).
2. Gate providers from canonical capability / `canonicalSupportedTypes`.
3. Project only the allowed Nuvio launch compatibility for the selected provider.
4. Invoke the provider on that bounded surface.
5. Keep semantic identity separate from launch transport throughout evidence and output processing.

A launch alias never becomes permission to search or return a different semantic catalogue.

## Manifest fields

- `canonicalSupportedTypes` is semantic/provider-selection authority whenever transport compatibility differs from semantics.
- `supportedTypes` is the Nuvio launch surface.
- Current manifests accept only `movie`, `tv` and `anime` values.
- Anime-only projection is `["anime", "tv"]`; `series` is not part of the published contract.
- `movie` transport is equivalent to canonical movie capability: no artificial anime-to-movie promotion is allowed.

## Recognition and runtime gate

Trusted metadata may refine a presented work into canonical `anime`, but provider compatibility is checked before provider-network work whenever the necessary identity is already known. Animation alone is not sufficient to classify ordinary Western animation as anime.

A provider that is incompatible with the canonical work returns no result; it must not fall back to an arbitrary search on a transport alias.

## Labs / evidence

Native evidence keeps the two concepts separate:

- logical/canonical type: semantic identity used for provider eligibility;
- request/launch type: the bounded surface actually exercised by Nuvio.

Coverage is derived from the current 46-provider manifest. The 50 archived historical providers remain knowledge/provenance only and are not injected into the current transport denominator.

## Implementation authority

Relevant surfaces include `scripts/materialize_provider_v3_all.py`, `scripts/enforce_provider_v3_semantic_transport_contract_v5.py`, `scripts/reapply_published_overrides.py`, `engine_v2/src/provider-catalog.mjs`, `automation/provider-v3-architecture.json` and the native media-type regressions.

## Regression floor

Tests must prove all of the following:

- anime-only canonical capability stays `["anime"]`;
- anime-only launch projection stays `["anime", "tv"]`;
- no `series` synthesis;
- no synthetic `movie` lane for anime-only providers;
- canonical movie capability and published movie transport remain equivalent;
- capability gating occurs before provider-network work when identity is already available.
