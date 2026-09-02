# NiakVIO workbench recovery memory

Last updated: 2026-09-03

## Hard safety rule
- Do not write to `main` while this workbench is under development.
- Active branch: `workbench/provider-v3-performance-playback`.
- Stable production reference when the workbench started: `main` at `8116f02289226ab8fb823f7ae03e204f73926a83`.
- All experiments, manifests, workflows, labs, reconstruction and minifier work stay on the workbench until final validation.

## Provider v3 architecture
- 96 providers.
- Runtime JS must be reproducible from ProviderBase + structured DATA + owned Core/Provider Lego.
- Legacy/upstream provider JS is knowledge only, never an executable reconstruction seed.
- Full manual reconstruction must remain possible and must prove 96/96 byte-identical reverse rebuild.
- Routine runs do not repair fix blocks.

## Workflow ownership
- LEARN owns repair attempts. It may repair only in sandbox, validate, then propose PRs for human merge. It must not publish production runtime.
- DEEP owns verification/publication: domain/hub checks, Core/provider contracts, deep health observation, manifest projections, integrity inventories and publication. No adaptive quick/deep repair in DEEP.
- Native labs are observational proof on TV Android, Mobile Android, Mobile iOS, Desktop macOS and Desktop Windows.

## Current runtime tuning
- Commit `58425bf9c0d7b8883c05a63ef532217f3840daea` changes Provider v3 Core default budget from 10s TV / 18s others to 25s TV / 30s Mobile+Desktop.
- Stream presentation V18 extracts quality from standard fields, URL facts, FHD/HD/SD and numeric height.
- Goal: avoid Nuvio showing e.g. Kehflix - Inconnue when safe facts already expose quality.
- Official clients allow substantially longer plugin execution (TV ~120s, Mobile/Desktop ~60s), so NiakVIO must not self-abort at 10s.

## Production state intentionally frozen
- main manifest 5.21.31.
- 96 providers published.
- MOVIX disabled.
- PURSTREAM movie/tv only.
- Do not modify main until workbench is complete and manually accepted.

## Remaining work
1. Simplify DEEP to verification + manifest/report republication only.
2. Keep repair exclusively in LEARN proposal PR path.
3. Add manual full 96/96 reconstruction workflow.
4. Run/inspect TVAndroid, MobileAndroid, MobileIOS, DesktopMACOS, DesktopWindows labs against workbench.
5. Harden stream metadata/badges and playback-readability issues found by labs.
6. Develop NiakVIO JS minifizer only after architecture/runtime gates are stable; preserve all BEGIN/END and STARTFIX/CLOSEFIX comments exactly and prove semantic/runtime parity before enablement.

## Architecture update
- Quick and Deep are verification-only on the workbench since commit `b45048241b1857a7be2a02a2c6ab6340fc0dbe5c`.
- Routine validation builds a temporary stage from the exact 96 published JS bytes; no discovery/promotion/repair.
- Domain/hub checks are read-only in routine runs.
- Manual full reconstruction workflow: `.github/workflows/provider-v3-reconstruct-all.yml`; it refuses direct commits to main and proves 96/96 reverse rebuild before an optional branch commit.

- Core finalizer is now a read-only Provider v3 fixed-point gate.
- Domain refresh is now read-only hub/DNS observation; it never writes provider DATA or provider JS.
