# NiakVIO Provider Engine V2 — ARCHI2

`engine_v2/` is the canonical production control plane for NiakVIO. Since the ARCHI2 cutover, it is no longer an isolated experiment: publication, provider catalog preservation, runtime repair planning, evidence and device-contract validation are coordinated around this architecture.

## Production pipeline

```text
3 upstreams + published LKG
        |
        v
provider discovery / sibling selection
        |
hubs / DNS / public address discovery / LKG
        |
        v
canonical ProviderSpec + staged provider bundles
        |
        v
NiakVIO Brain
classify cause -> choose bounded skill -> probe -> validate -> learn/defer
        |
        v
strict identity + media validation
        |
        v
Mobile / Desktop / TV evidence
        |
        v
canonical provider catalog -> general + VF manifests
        |
        v
atomic versions / integrity / LKG publication
```

`no_streams`, `blocked`, `unavailable`, `provider_unreachable` and runtime errors are observations, not terminal repair decisions. Quarantine remains reserved for positive safety/identity evidence.

## NiakVIO Brain

The Brain is the repair orchestrator. It is intentionally separated from the validators: it may propose/create/adapt repair skills, but it cannot relax the rules that decide whether a result is safe and playable.

### Production world

- classify the first causal gap rather than patching from a global status;
- prefer a healthy sibling when it already proves the canonical provider;
- reuse a learned skill when compatible;
- otherwise select a targeted built-in skill;
- allow validated production discoveries to become learned skills immediately;
- promote a skill to cross-provider auto-application only after repeated success and enough provider diversity;
- keep Quick bounded and give unresolved providers another chance on the next cron;
- LKG is a safe fallback after the repair budget, never a fake diagnosis or a blind upstream/default-provider shortcut.

### Back doors / stop conditions

The Brain must stop and emit `deferred_retry` when it detects a loop, exceeds its mutation/time/generated-code budget, or would need to rewrite its own core during production. A later cron can retry with new evidence.

The production Brain can evolve skills and provider-facing primitives. Core invariants (classification contract, validation boundary, budgets, fail-closed publication) are proposal-only from production so a difficult provider cannot teach the Brain to weaken its own tests.

### Learning Lab world

A daily bounded Learning Lab runs separately from publication. It can explore failed patterns, compose candidate skills, propose primitive improvements and suggest core changes. Its outputs are artifacts and, when useful, a reviewable PR. It cannot publish manifests/providers or mutate production state.

The Learning Lab intentionally persists only generalized technical knowledge. Raw URLs/tokens/header values, private notes and source spreadsheet/prompt text are excluded from proposals.

## Failure classes

The Brain distinguishes at least:

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
- `unknown_failure`
- `healthy`

A provider that has no usable API can still be repaired through the HTML/player path: catalogue/search -> detail -> embed/player -> scripts/XHR/JSON -> final HLS/DASH/direct media, while preserving Referer/Origin/cookies when required.

## Domain / hub recovery

Known hubs, redirects, Telegram public pages, direct candidates and historical LKG routes are tried first. If those routes fail, the bounded search fallback can discover a provider address source through a public search engine; a Telegram result is opened, the latest relevant message id is preferred, and the announced terminal is validated before it can update routing state.

## Device Lab visual sub-lab

The Native corpus Device Lab remains the real Mobile/Desktop/TV proof. A visual sub-lab renders its sanitized logs into JSON/HTML timelines so invocation -> provider result -> transport can be inspected quickly. Internal catalogue/detail/player stages are shown only when actually observed; the visualizer never invents missing hops or persists raw stream URLs/tokens/header values.

## Non-negotiable rules

1. Published LKG remains authoritative when a candidate is not demonstrably better.
2. Upstreams are knowledge sources, not automatically trusted final bundles.
3. Domain discovery precedes structural provider mutation.
4. Broken providers are repair inputs; safety quarantine requires positive evidence.
5. A healthy sibling is a useful canonical source, not an excuse to stack endless patches.
6. Every accepted repair requires real playable evidence and no positive identity/duration contradiction.
7. File extension alone is never final-media proof.
8. Movie, TV and anime are first-class regression dimensions; Breaking Bad remains a mandatory TV fixture.
9. Mobile/Desktop/TV contracts are separate evidence dimensions around one canonical request/result model.
10. Versions/cache identifiers are finalized atomically with publication so changed provider bytes cannot keep stale Nuvio identifiers.
