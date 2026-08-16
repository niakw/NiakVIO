# NiakVIO Provider Engine V2

This directory is the clean-room provider-engine refactor. It is intentionally isolated from the current publication pipeline: **nothing in `engine_v2/` is consumed by `main` manifests or provider publication yet**.

## Goal

Build providers from verified knowledge instead of stacking historical patches.

```text
Nuvio client repos -> contract discovery/version watcher
                         |
3 provider upstreams -> provider knowledge/specs
                         |
                         v
                  Resolver Core V2
 discovery -> search -> identity -> detail -> episode -> player -> media
                         |
                evidence at every stage
                         |
                   Repair Brain V2
                         |
               learned/versioned recipes
                         |
                normalized candidates
                         |
              runtime/device adapters
             mobile / desktop / TV
```

## Non-negotiable rules

1. `main` stays the LKG reference during the V2 rebuild.
2. The three provider repositories are sources of knowledge, not trusted final bundles.
3. Hub/DNS/domain discovery precedes provider reconstruction.
4. A broken provider is **repairable/disabled**, not quarantined by default.
5. Quarantine is reserved for suspicious provenance, identity mismatch, unsafe output, hijacked domains or other strong safety evidence.
6. Healthy-sibling knowledge remains useful, but V2 reconstructs a canonical adapter rather than layering another patch on a sibling bundle.
7. Every stage emits evidence. `no_streams` is not a root cause.
8. Repair is bounded: classify -> select a targeted strategy -> probe -> validate. No blind infinite retries.
9. Repair recipes are version-aware. A Nuvio runtime contract change can invalidate a recipe without invalidating the provider itself.
10. Desktop, Mobile and TV are adapters around one canonical request/result contract.
11. Movie, TV/series and anime are first-class corpus dimensions. Breaking Bad is a mandatory TV regression fixture.
12. Diagnostics and scores guide repair; they are not coverage blockers.

## Phase 0 — Nuvio contract discovery

Before rebuilding providers, V2 watches the official Nuvio client repositories and records:

- plugin invocation signature;
- media-type aliases;
- scraper settings injection;
- manifest fields;
- result fields;
- fetch/redirect/header/cookie semantics;
- QuickJS/runtime differences;
- player transport/header handling;
- device-specific capabilities.

The checked-in baseline lives in `config/nuvio-clients.json`. `scripts/check-nuvio-contracts.mjs` compares the baseline to current upstream heads and classifies drift as contract, semantic or unrelated. It is report-only by default.

## Provider knowledge

`config/provider-upstreams.json` declares the three canonical upstreams. A future ingestion step will normalize each upstream implementation into a `ProviderSpec` containing identity, domains/hubs, search/detail/episode/player/media strategies, language capabilities, session requirements and provenance.

## Canonical runtime contract

Providers are reconstructed against one internal request:

```js
{
  tmdbId,
  mediaType: "movie" | "tv" | "anime",
  title,
  year,
  season,
  episode,
  languages,
  device,
  settings
}
```

The core returns normalized stream candidates plus evidence. Device adapters then translate that contract to the native Nuvio runtime. Providers should not contain Desktop/Mobile/TV branching unless a real provider behavior requires it.

## Repair Brain V2

The first implementation is deterministic and explainable. It distinguishes at least:

- `not_invoked`
- `dns_unreachable`
- `transport_blocked`
- `search_gap`
- `identity_mismatch`
- `detail_gap`
- `episode_gap`
- `player_gap`
- `media_extraction_gap`
- `playback_context_gap`
- `media_validation_gap`
- `runtime_contract_drift`
- `healthy`

Each class maps to a small set of targeted, reusable repair strategies. Successful strategies become versioned recipes with evidence and runtime compatibility metadata.

## Evidence matrix

State is tracked by provider × work × media type × language × device × client contract version. A provider can therefore be proven on one fixture/device while remaining unresolved on another without collapsing to a misleading global status.

## Migration order

1. Establish and continuously watch Nuvio contracts.
2. Ingest the three upstream provider repositories.
3. Build normalized ProviderSpecs and provenance.
4. Reconstruct a small representative set of providers from zero.
5. Validate the six-fixture corpus on worker + Mobile + Desktop + TV.
6. Expand provider-by-provider, using evidence and learned recipes.
7. Compare V2 against frozen `main` without changing `main`.
8. Only after V2 is demonstrably better, design the publication cutover.
