# NiakVIO Provider Engine V2 — Evidence & Learning subsystem

`engine_v2/` remains the shared **observation, classification, evidence and Learning** subsystem. It is not the owner of routine Provider v3 publication and it does not make CORE Quick/Deep repair providers.

The current production boundaries are:

```text
ProviderBase v3 + DATA + owned Lego
        |
        v
manual deterministic reconstruction when code bytes change
        |
        v
CORE Quick / Deep verification
        |
        +--> five native observational Labs
        |
        +--> reports / projections / hashes
```

Learning is separate:

```text
observations + sanitized prior memory
        |
        v
engine_v2 classification / bounded repair experiments
        |
        v
candidate skill / provider-facing proposal
        |
        v
tests + reviewable PR
        |
        X  no direct production publication
```

## What Engine V2 owns

- failure classification;
- evidence models and causal diagnosis;
- bounded repair experiments in Learning;
- sanitized recipe/strategy memory;
- native-reader evidence ingestion;
- proposal generation;
- helper logic for domain/identity/media reasoning.

## What it does not own

- no Provider JS reconstruction in Quick/Deep;
- no direct provider publication from Learning;
- no relaxation of identity/media/security gates;
- no Native Lab mutation of provider bytes;
- no automatic substitution of a sibling provider to hide a failure;
- no use of published/upstream JS as canonical ProviderBase seed.

## Failure classes

The classifier distinguishes at least:

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

`no_streams` is an observation, not a root cause.

## Learning Lab

`.github/workflows/brain-learning-lab.yml` runs the bounded Learning world.

It may:

- observe the full catalogue, including disabled providers;
- restore sanitized memory;
- classify failures;
- test bounded provider-facing repairs;
- consume sanitized native reader evidence;
- retain useful successful and failed strategies;
- produce a reviewable proposal.

It may not:

- write Provider JS or manifests to production;
- change CORE invariants from runtime evidence alone;
- reinterpret an inconclusive Lab as a successful repair;
- persist tokens, cookies, signed stream URLs or secret headers.

## Native evidence

Five first-class client/platform dimensions are kept separate:

1. TV Android — NuvioTV;
2. Mobile Android — NuvioMobile;
3. Mobile iOS — NuvioMobile;
4. Desktop macOS — NuvioDesktop;
5. Desktop Windows — NuvioDesktop.

A result from one dimension is never transferred to another. Native Labs are observational and consume exact NiakVIO provider bytes; they do not repair or reconstruct.

## Domain and media rules

Domain observations can inform Learning, but routine domain publication is owned by the separate CONFIG-only Domain Refresh contract.

Media evidence is fail-closed on positive contradiction:

- HTML/JSON is not final media;
- HLS/DASH/container structure matters;
- a playable wrong title/episode is a blocking failure;
- a single broken stream is stream-level evidence, not sufficient provider-wide disablement proof;
- LKG remains valuable when new evidence is inconclusive.

## Relation to Provider v3

The canonical executable architecture is documented in [`../ARCHITECTURE.md`](../ARCHITECTURE.md).

Provider v3 reconstruction is based on:

- clean `provider-bases/`;
- structured DATA/config;
- owned `PROVIDER.*` Lego;
- owned `CORE.*` Lego;
- deterministic materialization + reverse byte proof.

Engine V2 may help learn or propose better structured knowledge, but it never replaces that source-of-truth contract with generated or upstream JavaScript.
