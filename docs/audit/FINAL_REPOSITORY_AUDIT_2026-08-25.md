# Final repository audit — 2026-08-25

This ledger records the final repository-wide NiakVIO audit performed after the 5.20.77 ARCHI2 publication transaction. The audit is intentionally based on the validated `main` tree and does not modify upstream Nuvio or provider repositories.

## Scope

- repository architecture, generated-state ownership and cleanup;
- GitHub Actions syntax/security/hygiene;
- native-reader orchestration and resumability;
- provider/Core boundaries and generated-provider fixed points;
- cross-client stream presentation on Nuvio Mobile, Desktop and TV;
- StreamBadge catalog/feed integrity and matcher compatibility;
- release inventories and stale generated provider bundles.

## Applied findings

### Cross-client stream presentation V12

V11 rebuilt `description`, but official plugin readers do not all preserve that field. Mobile/Desktop reconstruct the visible subtitle from `quality + size + language`; TV uses `size` as the plugin-stream description and appends `quality` to the label. That made provider-specific layouts remain visible and allowed sparse rows such as Purstream to collapse to a single `Dual Audio` value.

V12 makes provider output factual input only and projects one canonical Core presentation through the fields actually retained by all official clients:

- normalized `quality` remains a dedicated field for client labels/sorting;
- transport `language` is suppressed after being retained in `presentationFacts` and the canonical envelope, preventing duplicate client formatting;
- `size` carries the complementary multiline compatibility envelope consumed by Mobile/Desktop/TV;
- real byte size remains available as `fileSize` / `presentationFacts.fileSize`;
- `description` remains the full canonical Core presentation for runtimes that preserve it;
- TMDB supplies only safe media context (title/year/episode/genres/runtime/certification); it never invents stream quality/source/codec/audio/language provenance;
- legacy provider descriptions/names are mined only for facts and never reused as final technical layout.

Equivalent Purstream, VegaMovies and HindMoviez inputs are explicitly tested to produce identical client-visible projection. MoviesHunt-style private prose embedded in `size` is also stripped down to the factual file-size token.

### StreamBadge feeds

The 73-badge catalog and Fusion/Dark/Light feeds are validated as executable regex payloads after JSON parsing. The previous catalog carried one excess regex escaping layer; V12 normalizes that source data and regenerates all three feeds.

Official Nuvio plugin result models do not carry `badgeIds`, badge images or rule-installation fields. Native image badges are therefore owned by the official Nuvio StreamBadge renderer and require the corresponding feed to be imported in Nuvio settings. NiakVIO guarantees that the canonical visible text contains the matcher vocabulary on every provider/client, and keeps the multiline emoji presentation as the fallback when no badge feed is active.

Because official clients persist the parsed rules locally at import time, an installation that imported the old over-escaped feed may need to re-import the same Fusion/Dark/Light URL after this change to refresh its stored rules.

### TV native-reader orchestration

The bounded/resumable TV migration was executed and its migration tests passed before materialization:

- per-route hard timeout;
- checkpoint recording and verification;
- resumable evidence reuse tied to input identity and route-log hashes;
- two-shard representative TV execution;
- exact-attempt artifact naming and Brain evidence merge;
- bounded repair retest scope.

The original audit materializer failed only when the GitHub Actions token attempted to push a workflow-file change without `workflows` permission. The validated resulting changes were subsequently materialized through the repository API. The migration one-shot, helper and failure report are retired from the durable tree.

### Repository and CI hygiene

- retired one-shot workflows are removed;
- repository hygiene preserves `main`, the intentional `brain-learning/proposals` branch, and active same-repository PR heads while deleting explicitly retired branches;
- `github-actions-gate.yml` adds pinned actionlint 1.7.12 with verified SHA-256 and ShellCheck integration;
- the tracked-tree audit inventories every repository path and fails only on structural corruption;
- merge-conflict detection requires a real `<<<<<<< / ======= / >>>>>>>` triplet, avoiding false positives from decorative separators;
- generated provider bundles are pruned from authoritative manifest/LKG/provenance references rather than by filename guesswork.

### Provider generated state

V12 was reapplied through the common provider override pipeline. The materializer reported 79 provider reference transitions and then pruned 158 stale content-hashed bundles while retaining the 92 authoritative provider artifacts required by published state. Portfolio audit and provider export-floor validation passed afterward.

## Validation evidence

The targeted V12 materializer run `32859975812` completed successfully. It validated:

- V12 normalizer fixed point;
- Purstream / VegaMovies / HindMoviez / MoviesHunt common presentation projection;
- Mobile + Desktop + TV projection contract;
- 73 StreamBadge catalog entries and Fusion/Dark/Light executable matcher rules;
- Engine v2 presentation parity;
- native corpus device-lab contract;
- repository hygiene contract;
- referenced-provider prune contract;
- full provider portfolio audit;
- strict provider export-floor portfolio;
- release hash generation and release-integrity validation;
- `git diff --check`.

The earlier TV migration run `32855475457` separately proved the TV resume/corpus/exhaustive-reader contracts and release integrity; its only failure was the GitHub token's inability to push a workflow-file mutation.

## Deliberately deferred refactor

`_provider_export_floor()` still has overlapping implementation authority in the normalization/rebuild safety path. The strict implementation is a security boundary already proven across the provider portfolio. This audit does **not** rewrite that boundary merely to remove duplication; consolidation should only occur with an isolated portfolio proof that preserves the strict export floor byte-for-byte.

Historical migration scripts that are no longer runtime-referenced are retained where they provide reproducibility/audit value. Being unreferenced by current workflows is not sufficient evidence that a migration artifact is safe to delete.

## Merge requirements

Before merging this audit into `main`:

1. the audit branch must contain no temporary audit workflow;
2. release hash inventories must be regenerated after this ledger is added;
3. GitHub Actions dependency gate/actionlint must pass on the final PR tree;
4. repository hygiene and V12 presentation tests must pass;
5. the PR must not reintroduce the obsolete pre-finalization Terser hunk;
6. after merge, the audit branch should be deleted and the final `main` tree rechecked for integrity and temporary one-shots.
